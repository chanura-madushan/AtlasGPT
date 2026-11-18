
import type {
  AuthResponse,
  ChatResponse,
  DeleteDocumentResponse,
  DocumentListResponse,
  UploadResponse,
  User,
  ConversationListResponse,
  ConversationMessagesResponse,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: {
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)

    throw new ApiError(
      error?.detail || 'Something went wrong',
      response.status,
    )
  }

  return response.json()
}

export const authApi = {
  register: (email: string, password: string) =>
    apiRequest<AuthResponse>('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    apiRequest<AuthResponse>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }),

  me: () =>
    apiRequest<User>('/auth/me'),

  logout: () =>
    apiRequest<AuthResponse>('/auth/logout', {
      method: 'POST',
    }),
}

export const documentApi = {
  list: () =>
    apiRequest<DocumentListResponse>('/documents'),

  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    return apiRequest<UploadResponse>('/documents/upload', {
      method: 'POST',
      body: formData,
    })
  },

  delete: (filename: string) =>
    apiRequest<DeleteDocumentResponse>(
      `/documents/${encodeURIComponent(filename)}`,
      {
        method: 'DELETE',
      },
    ),
}

export const chatApi = {
  send: (message: string, conversationId: string) =>
    apiRequest<ChatResponse>('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    }),
}

export const conversationApi = {
  list: () =>
    apiRequest<ConversationListResponse>('/conversations'),

  getMessages: (conversationId: string) =>
    apiRequest<ConversationMessagesResponse>(
      `/conversations/${encodeURIComponent(conversationId)}/messages`,
    ),

  delete: (conversationId: string) =>
    apiRequest<{ message: string; conversation_id: string }>(
      `/conversations/${encodeURIComponent(conversationId)}`,
      {
        method: 'DELETE',
      },
    ),
}
