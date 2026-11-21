import type {
  AuthResponse, ChatResponse, DeleteDocumentResponse, DocumentListResponse,
  UploadResponse, User, ConversationListResponse, ConversationMessagesResponse,
} from '../types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      credentials: 'include',
      headers: { ...options.headers },
    })
  } catch {
    throw new ApiError('Cannot reach AtlasGPT. Check that the API server is running.', 0)
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string; message?: string } | null
    throw new ApiError(payload?.detail || payload?.message || `Request failed (${response.status}).`, response.status)
  }

  if (response.status === 204) return undefined as T
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) return undefined as T
  return await response.json() as T
}

export const authApi = {
  guest: () => apiRequest<AuthResponse>('/auth/guest', { method: 'POST' }),
  register: (email: string, password: string) => apiRequest<AuthResponse>('/auth/register', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }),
  }),
  login: (email: string, password: string) => apiRequest<AuthResponse>('/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }),
  }),
  me: () => apiRequest<User>('/auth/me'),
  logout: () => apiRequest<AuthResponse>('/auth/logout', { method: 'POST' }),
}

export interface IngestionJob {
  id: string
  filename: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  chunks: number
  error: string | null
  attempts: number
}

export const documentApi = {
  list: () => apiRequest<DocumentListResponse>('/documents'),
  uploadAsync: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiRequest<{ message: string; job_id: string; filename: string; status: string }>('/documents/upload-async', {
      method: 'POST', body: formData,
    })
  },
  job: (jobId: string) => apiRequest<{ job: IngestionJob }>(`/documents/jobs/${encodeURIComponent(jobId)}`),
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiRequest<UploadResponse>('/documents/upload', { method: 'POST', body: formData })
  },
  delete: (filename: string) => apiRequest<DeleteDocumentResponse>(`/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' }),
}

export const chatApi = {
  send: (message: string, conversationId: string) => apiRequest<ChatResponse>('/chat', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  }),
}

export const conversationApi = {
  list: () => apiRequest<ConversationListResponse>('/conversations'),
  getMessages: (conversationId: string) => apiRequest<ConversationMessagesResponse>(`/conversations/${encodeURIComponent(conversationId)}/messages`),
  delete: (conversationId: string) => apiRequest<{ message: string; conversation_id: string }>(`/conversations/${encodeURIComponent(conversationId)}`, { method: 'DELETE' }),
}
