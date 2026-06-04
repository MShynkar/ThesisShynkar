export type Role = 'admin' | 'manager' | 'user' | 'guest';

export type AccessLevel = 'public' | 'internal' | 'confidential' | 'restricted';

export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed';

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Document {
  id: string;
  title: string;
  filename: string;
  file_size: number;
  mime_type: string;
  owner_id: string;
  access_level: AccessLevel;
  category: string | null;
  tags: string[];
  doc_metadata: Record<string, unknown>;
  status: DocumentStatus;
  error_message: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentList {
  items: Document[];
  total: number;
  page: number;
  page_size: number;
}

export interface Source {
  chunk_id: string;
  document_id: string;
  document_title: string;
  chunk_index: number;
  content: string;
  similarity: number;
}

export interface SearchResponse {
  query: string;
  answer: string | null;
  sources: Source[];
  elapsed_ms: number;
}

export interface SearchHistoryEntry {
  id: string;
  query: string;
  answer: string | null;
  sources: Source[];
  result_count: number;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}
