// Mirrors the backend API schemas (backend/app/infrastructure/api/schemas).

export interface User {
  id: string;
  name: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  file_type: string;
  char_count: number;
  message: string;
}

export interface Attribute {
  name: string;
  data_type: string;
  is_required: boolean;
  description?: string;
}

export interface Entity {
  name: string;
  description?: string;
  attributes: Attribute[];
}

export interface Relationship {
  source: string;
  target: string;
  relationship_type: string;
  label?: string;
}

export interface Action {
  name: string;
  description?: string;
  actor?: string;
  target_entity?: string;
  http_method: string;
  endpoint: string;
}

export interface AnalysisResponse {
  document_id: string;
  project_name: string;
  description?: string;
  entities: Entity[];
  relationships: Relationship[];
  actions: Action[];
  entity_count: number;
  relationship_count: number;
  action_count: number;
}

export interface Diagram {
  id: string;
  diagram_type: string;
  title: string;
  mermaid_code: string;
  is_valid: boolean;
  validation_errors: string[];
}

export interface DiagramSetResponse {
  document_id: string;
  diagrams: Diagram[];
  all_valid: boolean;
  errors: string[];
}

export interface ScaffoldResponse {
  document_id: string;
  project_name: string;
  directory_tree: string;
  file_count: number;
  download_url: string;
}

export type JobStatus = "queued" | "running" | "completed" | "failed";

export interface JobResponse {
  job_id: string;
  document_id: string;
  status: JobStatus;
  success: boolean;
  errors: string[];
  analysis: AnalysisResponse | null;
  diagrams: DiagramSetResponse | null;
  scaffold: ScaffoldResponse | null;
}

export type AgentEventType =
  | "agent_start"
  | "agent_progress"
  | "agent_complete"
  | "agent_error"
  | "pipeline_start"
  | "pipeline_complete"
  | "pipeline_error";

export interface AgentEvent {
  type: AgentEventType;
  agent_name: string;
  message: string;
  timestamp: string;
}
