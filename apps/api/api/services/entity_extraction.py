"""Deliberately light LLM-based entity extraction feeding the sparse Neo4j graph.

Only a handful of entity types are extracted, and only from a bounded excerpt of the
document — this graph is meant to power "related documents" and light structure, not
to be an exhaustive knowledge base.
"""

import json

from api.services.ollama_client import generate_json

ENTITY_TYPE_HINTS = {
    "Organization": "a company, contractor, government body, or authority",
    "Person": "a named individual — e.g. a signatory, project engineer, or approving officer",
    "ContractRef": "a contract, approval, invoice, or agreement reference number",
    "Amount": "a monetary value",
    "Date": "a specific date",
}
ENTITY_TYPES = list(ENTITY_TYPE_HINTS)
MAX_EXCERPT_CHARS = 4000
# LLMs occasionally emit these as a literal string in place of a real value.
JUNK_NAMES = {"null", "none", "n/a", "na", "unknown", "-", "nil", "undefined"}

PROMPT_TEMPLATE = """Extract at most 8 key entities from the document excerpt below.
Only use these entity types:
{type_hints}

Skip anything not clearly one of these types. Respond with JSON only, in this exact
shape: {{"entities": [{{"type": "Organization", "name": "..."}}, ...]}}

Document excerpt:
---
{excerpt}
---
"""


def _type_hints_block() -> str:
    return "\n".join(f"- {t}: {hint}" for t, hint in ENTITY_TYPE_HINTS.items())


def extract_entities(text: str) -> list[dict]:
    excerpt = text[:MAX_EXCERPT_CHARS]
    prompt = PROMPT_TEMPLATE.format(type_hints=_type_hints_block(), excerpt=excerpt)
    try:
        raw = generate_json(prompt)
        data = json.loads(raw)
        entities = data.get("entities", []) if isinstance(data, dict) else []
    except (json.JSONDecodeError, KeyError, ValueError):
        return []

    cleaned = []
    seen = set()
    for ent in entities:
        if not isinstance(ent, dict):
            continue
        etype, name = ent.get("type"), ent.get("name")
        if etype not in ENTITY_TYPES or not isinstance(name, str):
            continue
        name = name.strip()[:200]
        if not name or name.lower() in JUNK_NAMES or (etype, name) in seen:
            continue
        seen.add((etype, name))
        cleaned.append({"type": etype, "name": name})
    return cleaned
