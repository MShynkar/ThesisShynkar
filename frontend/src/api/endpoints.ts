import { api } from './client';
import type {
  AuditLogEntry,
  Document,
  DocumentList,
  SearchHistoryEntry,
  SearchResponse,
  Token,
  User,
} from '@/types';

// ---- Auth ----------------------------------------------------------------

export const authApi = {
  login: async (username: string, password: string): Promise<Token> => {
    const res = await api.post<Token>('/auth/login/json', { username, password });
    return res.data;
  },
  register: async (data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }): Promise<User> => {
    const res = await api.post<User>('/auth/register', data);
    return res.data;
  },
  me: async (): Promise<User> => {
    const res = await api.get<User>('/auth/me');
    return res.data;
  },
};

// ---- Documents -----------------------------------------------------------

export const documentsApi = {
  list: async (params: {
    page?: number;
    page_size?: number;
    category?: string;
    tag?: string;
    owned_only?: boolean;
  } = {}): Promise<DocumentList> => {
    const res = await api.get<DocumentList>('/documents', { params });
    return res.data;
  },
  get: async (id: string): Promise<Document> => {
    const res = await api.get<Document>(`/documents/${id}`);
    return res.data;
  },
  upload: async (
    file: File,
    meta: {
      title: string;
      access_level: string;
      category?: string;
      tags?: string[];
      doc_metadata?: Record<string, unknown>;
    }
  ): Promise<Document> => {
    const form = new FormData();
    form.append('file', file);
    form.append('title', meta.title);
    form.append('access_level', meta.access_level);
    if (meta.category) form.append('category', meta.category);
    form.append('tags', JSON.stringify(meta.tags || []));
    form.append('doc_metadata', JSON.stringify(meta.doc_metadata || {}));
    const res = await api.post<Document>('/documents', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  update: async (
    id: string,
    data: Partial<{
      title: string;
      access_level: string;
      category: string | null;
      tags: string[];
      doc_metadata: Record<string, unknown>;
    }>
  ): Promise<Document> => {
    const res = await api.patch<Document>(`/documents/${id}`, data);
    return res.data;
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/documents/${id}`);
  },
  reprocess: async (id: string): Promise<Document> => {
    const res = await api.post<Document>(`/documents/${id}/reprocess`);
    return res.data;
  },
};

// ---- Search --------------------------------------------------------------

export const searchApi = {
  query: async (body: {
    query: string;
    top_k?: number;
    threshold?: number;
    hybrid?: boolean;
    generate_answer?: boolean;
  }): Promise<SearchResponse> => {
    const res = await api.post<SearchResponse>('/search', body);
    return res.data;
  },
  history: async (skip = 0, limit = 50): Promise<SearchHistoryEntry[]> => {
    const res = await api.get<SearchHistoryEntry[]>('/search/history', {
      params: { skip, limit },
    });
    return res.data;
  },
  deleteHistory: async (id: string): Promise<void> => {
    await api.delete(`/search/history/${id}`);
  },
};

// ---- Admin ---------------------------------------------------------------

export interface UserListResponse {
  items: User[];
  total: number;
  page: number;
  page_size: number;
}

export const adminApi = {
  listUsers: async (page = 1, pageSize = 50): Promise<UserListResponse> => {
    const res = await api.get<UserListResponse>('/admin/users', {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },
  createUser: async (data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
    role: string;
    is_active?: boolean;
  }): Promise<User> => {
    const res = await api.post<User>('/admin/users', data);
    return res.data;
  },
  updateUser: async (
    id: string,
    data: Partial<{ full_name: string; is_active: boolean; role: string }>
  ): Promise<User> => {
    const res = await api.patch<User>(`/admin/users/${id}`, data);
    return res.data;
  },
  deleteUser: async (id: string): Promise<void> => {
    await api.delete(`/admin/users/${id}`);
  },
  audit: async (page = 1, pageSize = 50): Promise<{
    items: AuditLogEntry[];
    total: number;
    page: number;
    page_size: number;
  }> => {
    const res = await api.get('/admin/audit', { params: { page, page_size: pageSize } });
    return res.data;
  },
};
