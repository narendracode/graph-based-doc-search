"""Thin wrapper around a deliberately sparse Neo4j knowledge graph.

Nodes: Document, Zone, Project, Entity (type + name).
Relations: (Document)-[:BELONGS_TO]->(Zone|Project), (Document)-[:MENTIONS]->(Entity).
"""

import uuid

from neo4j import Driver, GraphDatabase

from api.config import get_settings

settings = get_settings()

_driver: Driver | None = None


def _ensure_constraints(driver: Driver) -> None:
    """Our merge key is (type, name), not name alone — a bare uniqueness constraint
    on name would reject two different-typed entities that happen to share a name."""
    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT entity_type_name_unique IF NOT EXISTS "
            "FOR (e:Entity) REQUIRE (e.type, e.name) IS UNIQUE"
        )


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
        _ensure_constraints(_driver)
    return _driver


def upsert_document(
    document_id: uuid.UUID,
    filename: str,
    zone_id: uuid.UUID,
    zone_name: str,
    project_id: uuid.UUID,
    project_name: str,
) -> None:
    with get_driver().session() as session:
        session.run(
            """
            MERGE (d:Document {id: $doc_id})
            SET d.filename = $filename
            MERGE (z:Zone {id: $zone_id}) SET z.name = $zone_name
            MERGE (p:Project {id: $project_id}) SET p.name = $project_name
            MERGE (d)-[:BELONGS_TO]->(z)
            MERGE (d)-[:BELONGS_TO]->(p)
            """,
            doc_id=str(document_id),
            filename=filename,
            zone_id=str(zone_id),
            zone_name=zone_name,
            project_id=str(project_id),
            project_name=project_name,
        )


def retag_document(
    document_id: uuid.UUID,
    filename: str,
    zone_id: uuid.UUID,
    zone_name: str,
    project_id: uuid.UUID,
    project_name: str,
) -> None:
    """Moves a document's BELONGS_TO edges to a new zone/project — used when a
    document's zone/project is corrected after upload. Drops the old edges first so a
    re-tagged document doesn't stay (incorrectly) linked to its previous zone/project."""
    with get_driver().session() as session:
        session.run(
            """
            MATCH (d:Document {id: $doc_id})-[r:BELONGS_TO]->(t)
            WHERE t:Zone OR t:Project
            DELETE r
            """,
            doc_id=str(document_id),
        )
    upsert_document(document_id, filename, zone_id, zone_name, project_id, project_name)


def upsert_entities(document_id: uuid.UUID, entities: list[dict]) -> None:
    """entities: [{"type": "Organization", "name": "..."}, ...] — kept intentionally small."""
    if not entities:
        return
    with get_driver().session() as session:
        session.run(
            """
            MATCH (d:Document {id: $doc_id})
            UNWIND $entities AS ent
            MERGE (e:Entity {type: ent.type, name: ent.name})
            MERGE (d)-[:MENTIONS]->(e)
            """,
            doc_id=str(document_id),
            entities=entities,
        )


def delete_document(document_id: uuid.UUID) -> None:
    with get_driver().session() as session:
        session.run(
            """
            MATCH (d:Document {id: $doc_id})
            DETACH DELETE d
            """,
            doc_id=str(document_id),
        )
        # Clean up entities left with no remaining document mentions.
        session.run(
            """
            MATCH (e:Entity) WHERE NOT (e)<-[:MENTIONS]-(:Document)
            DELETE e
            """
        )


def document_graph(document_id: uuid.UUID) -> dict:
    """Nodes/edges for the small neighborhood around one document — what it's tagged
    with (zone/project) and what was extracted from it (entities) — for a UI preview
    of what the knowledge graph actually holds for this document."""
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (d:Document {id: $doc_id})
            OPTIONAL MATCH (d)-[:BELONGS_TO]->(tag)
            OPTIONAL MATCH (d)-[:MENTIONS]->(e:Entity)
            RETURN d, collect(DISTINCT tag) AS tags, collect(DISTINCT e) AS entities
            """,
            doc_id=str(document_id),
        )
        record = result.single()
        if record is None:
            return {"nodes": [], "edges": []}

        doc_node = record["d"]
        nodes = [
            {"id": f"document:{document_id}", "label": doc_node.get("filename", "Document"), "type": "Document"}
        ]
        edges = []
        for tag in record["tags"]:
            tag_type = next(iter(tag.labels), "Tag")
            tag_id = f"{tag_type.lower()}:{tag.get('id') or tag.get('name')}"
            nodes.append({"id": tag_id, "label": tag.get("name", "?"), "type": tag_type})
            edges.append({"source": f"document:{document_id}", "target": tag_id, "type": "BELONGS_TO"})
        for entity in record["entities"]:
            entity_id = f"entity:{entity.get('type')}:{entity.get('name')}"
            nodes.append({"id": entity_id, "label": entity.get("name", "?"), "type": entity.get("type", "Entity")})
            edges.append({"source": f"document:{document_id}", "target": entity_id, "type": "MENTIONS"})

        return {"nodes": nodes, "edges": edges}


def related_documents(document_id: uuid.UUID, limit: int = 5) -> list[dict]:
    """Raw relatedness data — which entities/project this document shares with each
    candidate. Kept structured (not a pre-baked sentence) so the API layer can turn it
    into a business-readable explanation and pull a supporting excerpt from the text."""
    with get_driver().session() as session:
        by_entity = session.run(
            """
            MATCH (d:Document {id: $doc_id})-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(other:Document)
            WHERE other.id <> $doc_id
            WITH other, collect(DISTINCT {name: e.name, type: e.type}) AS shared_entities
            RETURN other.id AS id, other.filename AS filename, shared_entities
            ORDER BY size(shared_entities) DESC LIMIT $limit
            """,
            doc_id=str(document_id),
            limit=limit,
        ).data()
        results = [
            {"id": r["id"], "filename": r["filename"], "shared_entities": r["shared_entities"], "shared_project": None}
            for r in by_entity
        ]
        if len(results) >= limit:
            return results

        by_project = session.run(
            """
            MATCH (d:Document {id: $doc_id})-[:BELONGS_TO]->(p:Project)<-[:BELONGS_TO]-(other:Document)
            WHERE other.id <> $doc_id
            RETURN DISTINCT other.id AS id, other.filename AS filename, p.name AS project_name
            LIMIT $limit
            """,
            doc_id=str(document_id),
            limit=limit - len(results),
        ).data()
        seen = {r["id"] for r in results}
        for r in by_project:
            if r["id"] not in seen:
                results.append(
                    {
                        "id": r["id"],
                        "filename": r["filename"],
                        "shared_entities": [],
                        "shared_project": r["project_name"],
                    }
                )
                seen.add(r["id"])
        return results[:limit]
