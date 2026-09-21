export type UserRole = "super_admin" | "user";

// Document types are an admin/user-extensible taxonomy (see DocumentType below),
// not a fixed set — anyone can add a missing one wherever it's picked.
export interface DocumentType {
  id: string;
  name: string;
  created_at: string;
}

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
  doc_type_name: string;
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
  doc_type_id: string;
  doc_type_name: string;
  zone_id: string;
  zone_name: string;
  project_id: string;
  project_name: string;
  status: DocumentStatus;
  status_detail: string | null;
  uploaded_by: string | null;
  created_at: string;
  last_uploaded_at: string;
  checklist_item_id: string | null;
  review_status: "approved" | "rejected" | null;
  review_feedback: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
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
  doc_type_name: string;
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

export type ChecklistItemStatus = "not_uploaded" | "pending_review" | "approved" | "rejected";
export type ProjectChecklistStatus = "no_checklist" | "pending" | "completed";

export interface ChecklistItem {
  id: string;
  project_id: string;
  document_type_id: string;
  document_type_name: string;
  description: string | null;
  order_index: number;
  created_at: string;
}

export interface ChecklistDocument {
  id: string;
  filename: string;
  status: DocumentStatus;
  review_status: "approved" | "rejected" | null;
  review_feedback: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  uploaded_by: string | null;
  created_at: string;
  url: string;
}

export interface ChecklistItemWithStatus {
  id: string;
  document_type_id: string;
  document_type_name: string;
  description: string | null;
  order_index: number;
  item_status: ChecklistItemStatus;
  latest_document: ChecklistDocument | null;
  documents: ChecklistDocument[];
}

export interface ProjectChecklist {
  project_id: string;
  project_name: string;
  project_status: ProjectChecklistStatus;
  project_status_label: string;
  approved_count: number;
  total_items: number;
  items: ChecklistItemWithStatus[];
}

export const CHECKLIST_ITEM_STATUS_LABELS: Record<ChecklistItemStatus, string> = {
  not_uploaded: "Not uploaded",
  pending_review: "Pending review",
  approved: "Approved",
  rejected: "Rejected",
};

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

export const STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: "Pending",
  parsing: "Parsing",
  embedding: "Embedding",
  graph_building: "Building graph",
  completed: "Completed",
  failed: "Failed",
};

// Parsing (apps/api/api/services/parsing.py) auto-detects format via `unstructured`,
// so the backend accepts any of these — this list just drives the file picker/dropzone.
export const ACCEPTED_FILE_TYPES =
  ".pdf,.docx,.xlsx,.csv,.txt,.pptx,application/pdf," +
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document," +
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet," +
  "application/vnd.openxmlformats-officedocument.presentationml.presentation," +
  "text/csv,text/plain";

export const ACCEPTED_FILE_TYPES_LABEL = "PDF, Word, Excel, PowerPoint, CSV, or text files";
