export type UserRole = "super_admin" | "user";

export type DocType =
  | "approval"
  | "contract"
  | "project_plan"
  | "invoice"
  | "agreement"
  | "other";

export type DocumentStatus =
  | "pending"
  | "parsing"
  | "embedding"
  | "graph_building"
  | "completed"
  | "failed";

export interface Me {
  id: string;
  username: string;
  role: UserRole;
}

export interface Zone {
  id: string;
  name: string;
  code: string;
  is_default: boolean;
}

export interface Project {
  id: string;
  name: string;
  code: string;
  is_default: boolean;
}

export interface UserOut {
  id: string;
  username: string;
  role: UserRole;
  is_active: boolean;
}

export interface UserDetail extends UserOut {
  zones: Zone[];
  projects: Project[];
}

export interface DocumentListItem {
  id: string;
  filename: string;
  doc_type: DocType;
  zone_name: string;
  project_name: string;
  status: DocumentStatus;
  uploaded_by: string | null;
  created_at: string;
  last_uploaded_at: string;
  url: string;
}

export interface DocumentOut {
  id: string;
  filename: string;
  doc_type: DocType;
  zone_id: string;
  zone_name: string;
  project_id: string;
  project_name: string;
  status: DocumentStatus;
  status_detail: string | null;
  uploaded_by: string | null;
  created_at: string;
  last_uploaded_at: string;
}

export interface ShareUser {
  user_id: string;
  username: string;
  granted_by: string | null;
  created_at: string;
}

export interface ShareZone {
  zone_id: string;
  zone_name: string;
  granted_by: string | null;
  created_at: string;
}

export interface ShareProject {
  project_id: string;
  project_name: string;
  granted_by: string | null;
  created_at: string;
}

export interface DocumentShares {
  users: ShareUser[];
  zones: ShareZone[];
  projects: ShareProject[];
}

export interface RelatedDocument {
  id: string;
  filename: string;
  url: string;
  reason: string;
  excerpt: string | null;
  uploaded_by: string | null;
  created_at: string;
  last_uploaded_at: string;
}

export interface SearchResultItem {
  id: string;
  filename: string;
  doc_type: DocType;
  snippet: string;
  score: number;
  url: string;
  uploaded_by: string | null;
  created_at: string;
  last_uploaded_at: string;
}

export interface AutocompleteItem {
  id: string;
  filename: string;
  url: string;
}

export interface ChunkOut {
  id: string;
  chunk_index: number;
  content: string;
  has_embedding: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface DocumentGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Citation {
  id: string;
  filename: string;
  url: string;
}

export interface ChatMessageOut {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface ChatSessionOut {
  id: string;
  messages: ChatMessageOut[];
}

export const DOC_TYPES: { value: DocType; label: string }[] = [
  { value: "approval", label: "Approval" },
  { value: "contract", label: "Contract" },
  { value: "project_plan", label: "Project Plan" },
  { value: "invoice", label: "Invoice" },
  { value: "agreement", label: "Agreement" },
  { value: "other", label: "Other" },
];

export const STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: "Pending",
  parsing: "Parsing",
  embedding: "Embedding",
  graph_building: "Building graph",
  completed: "Completed",
  failed: "Failed",
};
