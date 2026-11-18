export interface AuthResponse {
  message: string
}

export interface User {
  user_id: number
  authenticated: boolean
}

export interface ChatResponse {
  reply: string
}

export interface Document {
  source: string
  chunks: number
}

export interface DocumentListResponse {
  documents: Document[]
}

export interface UploadResponse {
  message: string
  filename: string
  chunks: number
}

export interface DeleteDocumentResponse {
  message: string
  filename: string
}

export interface Conversation {
  conversation_id: string
  title: string
  updated_at: string
}

export interface ConversationListResponse {
  conversations: Conversation[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ConversationMessagesResponse {
  conversation_id: string
  messages: ChatMessage[]
}