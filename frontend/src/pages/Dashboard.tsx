
import { useEffect, useState, type ChangeEvent } from 'react'
import {
  FileText,
  MessageSquare,
  Plus,
  Settings,
  LogOut,
  Menu,
  X,
  Sparkles,
  Trash2,
} from 'lucide-react'

import { useAuth } from '../contexts/AuthContext'
import {
  ApiError,
  documentApi,
  conversationApi,
} from '../services/api'

import type { Conversation } from '../types'
import ChatPanel from '../components/chat/ChatPanel'

export default function Dashboard() {
  const { logout } = useAuth()

  // Sidebar and logout states
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)

  // Conversation states
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversationId, setSelectedConversationId] = useState(
    () => localStorage.getItem('atlasgpt_active_conversation') || '',
  )
  const [conversationsLoading, setConversationsLoading] = useState(true)
  const [conversationsError, setConversationsError] = useState('')
  const [deletingConversation, setDeletingConversation] = useState('')

  // Document states
  const [documents, setDocuments] = useState<
    { source: string; chunks: number }[]
  >([])
  const [documentsLoading, setDocumentsLoading] = useState(true)
  const [documentsError, setDocumentsError] = useState('')

  // Document upload states
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [uploadSuccess, setUploadSuccess] = useState('')

  // Document deletion states
  const [deletingDocument, setDeletingDocument] = useState('')
  const [deleteError, setDeleteError] = useState('')
  const [deleteSuccess, setDeleteSuccess] = useState('')

  // Persist the selected conversation across page refreshes.
  useEffect(() => {
    if (selectedConversationId) {
      localStorage.setItem(
        'atlasgpt_active_conversation',
        selectedConversationId,
      )
    }
  }, [selectedConversationId])

  // Load the user's conversations when the dashboard opens.
  useEffect(() => {
    let cancelled = false

    async function loadConversations() {
      try {
        const response = await conversationApi.list()

        if (cancelled) return

        setConversations(response.conversations)

        const savedConversationId = localStorage.getItem(
          'atlasgpt_active_conversation',
        )

        const savedConversationExists = response.conversations.some(
          (conversation) =>
            conversation.conversation_id === savedConversationId,
        )

        if (savedConversationExists && savedConversationId) {
          setSelectedConversationId(savedConversationId)
        } else if (response.conversations.length > 0) {
          setSelectedConversationId(
            response.conversations[0].conversation_id,
          )
        } else {
          setSelectedConversationId(`web-${crypto.randomUUID()}`)
        }
      } catch {
        if (cancelled) return

        setConversationsError('Could not load your conversations.')

        setSelectedConversationId(
          (current) => current || `web-${crypto.randomUUID()}`,
        )
      } finally {
        if (!cancelled) {
          setConversationsLoading(false)
        }
      }
    }

    loadConversations()

    return () => {
      cancelled = true
    }
  }, [])

  // Refresh the conversation list after a successful message.
  async function handleConversationUpdated() {
    try {
      const response = await conversationApi.list()

      setConversations(response.conversations)
      setConversationsError('')
    } catch {
      setConversationsError('Could not refresh your conversations.')
    }
  }

  // Start a new conversation.
  function handleNewConversation() {
    const newConversationId = `web-${crypto.randomUUID()}`

    setSelectedConversationId(newConversationId)
    setSidebarOpen(false)
    setConversationsError('')
  }

  // Switch to an existing conversation.
  function handleSelectConversation(conversationId: string) {
    setSelectedConversationId(conversationId)
    setSidebarOpen(false)
  }

  // Delete one conversation.
  async function handleDeleteConversation(conversationId: string) {
    const confirmed = window.confirm(
      'Are you sure you want to delete this conversation? This cannot be undone.',
    )

    if (!confirmed) return

    setDeletingConversation(conversationId)
    setConversationsError('')

    try {
      await conversationApi.delete(conversationId)

      const updatedConversations = conversations.filter(
        (conversation) => conversation.conversation_id !== conversationId,
      )

      setConversations(updatedConversations)

      if (selectedConversationId === conversationId) {
        if (updatedConversations.length > 0) {
          setSelectedConversationId(
            updatedConversations[0].conversation_id,
          )
        } else {
          setSelectedConversationId(`web-${crypto.randomUUID()}`)
        }
      }
    } catch {
      setConversationsError('Could not delete this conversation.')
    } finally {
      setDeletingConversation('')
    }
  }

  // Sign the user out.
  async function handleLogout() {
    setLoggingOut(true)

    try {
      await logout()
    } catch {
      setLoggingOut(false)
    }
  }

  // Load the user's documents.
  useEffect(() => {
    async function loadDocuments() {
      try {
        const response = await documentApi.list()
        setDocuments(response.documents)
      } catch {
        setDocumentsError('Could not load your documents.')
      } finally {
        setDocumentsLoading(false)
      }
    }

    loadDocuments()
  }, [])

  // Upload a document.
  async function handleFileUpload(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0]

    if (!file) return

    setUploadError('')
    setUploadSuccess('')

    const allowedExtensions = ['pdf', 'txt', 'docx']
    const extension = file.name.split('.').pop()?.toLowerCase()

    if (!extension || !allowedExtensions.includes(extension)) {
      setUploadError('Only PDF, TXT, and DOCX files are supported.')
      event.target.value = ''
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File size must not exceed 10 MB.')
      event.target.value = ''
      return
    }

    setUploading(true)

    try {
      const response = await documentApi.upload(file)

      const updatedDocuments = await documentApi.list()
      setDocuments(updatedDocuments.documents)

      setUploadSuccess(`${response.filename} uploaded successfully.`)
    } catch (error) {
      setUploadError(
        error instanceof ApiError
          ? error.message
          : 'Document upload failed. Please try again.',
      )
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  // Delete a document after confirmation.
  async function handleDeleteDocument(filename: string) {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${filename}"? This action cannot be undone.`,
    )

    if (!confirmed) return

    setDeletingDocument(filename)
    setDeleteError('')
    setDeleteSuccess('')

    try {
      await documentApi.delete(filename)

      const updatedDocuments = await documentApi.list()
      setDocuments(updatedDocuments.documents)

      setDeleteSuccess(`${filename} deleted successfully.`)
    } catch (error) {
      setDeleteError(
        error instanceof ApiError
          ? error.message
          : 'Document deletion failed. Please try again.',
      )
    } finally {
      setDeletingDocument('')
    }
  }

  return (
    <main className="flex min-h-screen bg-atlas-pearl text-atlas-navy">

      {/* Mobile sidebar background */}
      {sidebarOpen && (
        <button
          aria-label="Close sidebar"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-atlas-navy/30 lg:hidden"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-atlas-mist bg-white transition-transform duration-300 lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand */}
        <div className="flex h-20 items-center justify-between border-b border-atlas-mist px-6">
          <a
            href="/"
            className="font-heading text-2xl font-bold tracking-tight"
          >
            AtlasGPT<span className="text-atlas-cyan">.</span>
          </a>

          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-lg p-2 text-atlas-slate hover:bg-atlas-cloud lg:hidden"
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
        </div>

        {/* New conversation */}
        <div className="p-5">
          <button
            onClick={handleNewConversation}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-atlas-cyan px-4 py-3 font-semibold text-white transition hover:bg-atlas-deep-cyan"
          >
            <Plus size={19} />
            New conversation
          </button>
        </div>

        {/* Conversation navigation */}
        <nav className="flex-1 space-y-2 overflow-y-auto px-4">
          <div className="flex w-full items-center gap-3 rounded-xl bg-atlas-cyan/10 px-4 py-3 text-sm font-semibold text-atlas-deep-cyan">
            <MessageSquare size={19} />
            Conversations
          </div>

          <div className="space-y-1 pt-2">
            <p className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-atlas-slate">
              Recent conversations
            </p>

            {conversationsLoading ? (
              <p className="px-3 py-2 text-xs text-atlas-slate">
                Loading conversations...
              </p>
            ) : conversationsError ? (
              <p className="px-3 py-2 text-xs text-red-600">
                {conversationsError}
              </p>
            ) : conversations.length === 0 ? (
              <p className="px-3 py-2 text-xs leading-5 text-atlas-slate">
                Your conversations will appear here.
              </p>
            ) : (
              conversations.map((conversation) => (
                <div
                  key={conversation.conversation_id}
                  className={`group flex items-center gap-1 rounded-lg transition ${
                    selectedConversationId === conversation.conversation_id
                      ? 'bg-atlas-cloud'
                      : 'hover:bg-atlas-cloud'
                  }`}
                >
                  <button
                    onClick={() =>
                      handleSelectConversation(conversation.conversation_id)
                    }
                    className={`flex min-w-0 flex-1 items-center gap-3 rounded-lg px-3 py-3 text-left text-sm ${
                      selectedConversationId === conversation.conversation_id
                        ? 'font-semibold text-atlas-deep-cyan'
                        : 'text-atlas-slate'
                    }`}
                  >
                    <MessageSquare size={16} className="shrink-0" />

                    <span className="truncate">
                      {conversation.title || 'Untitled conversation'}
                    </span>
                  </button>

                  <button
                    onClick={() =>
                      handleDeleteConversation(conversation.conversation_id)
                    }
                    disabled={Boolean(deletingConversation)}
                    title="Delete conversation"
                    aria-label={`Delete ${conversation.title || 'conversation'}`}
                    className="mr-2 rounded-lg p-2 text-atlas-slate opacity-0 transition hover:bg-red-50 hover:text-red-600 group-hover:opacity-100 focus:opacity-100 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="border-t border-atlas-mist pt-3">
            <button
              onClick={() =>
                document.getElementById('documents')?.scrollIntoView({
                  behavior: 'smooth',
                })
              }
              className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-atlas-slate transition hover:bg-atlas-cloud"
            >
              <FileText size={19} />
              My documents
            </button>
          </div>
        </nav>

        {/* Account and settings */}
        <div className="border-t border-atlas-mist p-4">
          <div className="mb-3 flex items-center gap-3 rounded-xl bg-atlas-cloud p-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-atlas-cyan/15 font-heading text-lg font-bold text-atlas-deep-cyan">
              A
            </div>

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">
                AtlasGPT Account
              </p>
              <p className="text-xs text-atlas-slate">
                Personal workspace
              </p>
            </div>
          </div>

          <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-atlas-slate transition hover:bg-atlas-cloud">
            <Settings size={18} />
            Settings
          </button>

          <button
            onClick={handleLogout}
            disabled={loggingOut}
            className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-red-600 transition hover:bg-red-50 disabled:opacity-50"
          >
            <LogOut size={18} />
            {loggingOut ? 'Signing out...' : 'Sign out'}
          </button>
        </div>
      </aside>

      {/* Main workspace */}
      <section className="flex min-h-screen min-w-0 flex-1 flex-col">

        {/* Top navigation */}
        <header className="flex h-20 items-center justify-between border-b border-atlas-mist bg-white px-5 sm:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-atlas-slate hover:bg-atlas-cloud lg:hidden"
              aria-label="Open sidebar"
            >
              <Menu size={21} />
            </button>

            <div>
              <h1 className="font-heading text-lg font-bold">
                Workspace
              </h1>
              <p className="hidden text-xs text-atlas-slate sm:block">
                Your personal knowledge space
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-atlas-mist bg-atlas-pearl px-3 py-2 text-xs font-medium text-atlas-deep-cyan">
            <span className="h-2 w-2 rounded-full bg-atlas-cyan" />
            AI assistant
          </div>
        </header>

        {/* Dashboard content */}
        <div className="flex-1 p-6 sm:p-10">
          <div className="mx-auto w-full max-w-4xl">

            {/* Welcome section */}
            <div className="mb-8 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-atlas-cyan/10 text-atlas-deep-cyan">
                <Sparkles size={30} />
              </div>

              <h2 className="mt-7 font-heading text-3xl font-bold tracking-tight sm:text-4xl">
                Your knowledge starts here.
              </h2>

              <p className="mx-auto mt-4 max-w-lg text-sm leading-7 text-atlas-slate sm:text-base">
                Upload your documents, ask questions, and explore
                information through conversations grounded in your
                own sources.
              </p>
            </div>

            {/* Chat interface */}
            {!conversationsLoading && selectedConversationId && (
              <div className="mb-8">
                <ChatPanel
                  key={selectedConversationId}
                  conversationId={selectedConversationId}
                  onConversationUpdated={handleConversationUpdated}
                />
              </div>
            )}

            {/* Document management */}
            <div
              id="documents"
              className="rounded-2xl border border-atlas-mist bg-white p-6"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-heading text-lg font-bold">
                  Your documents
                </h3>

                <span className="text-xs text-atlas-slate">
                  {documents.length}{' '}
                  {documents.length === 1 ? 'document' : 'documents'}
                </span>
              </div>

              {/* Upload button */}
              <div className="mt-5">
                <label
                  htmlFor="document-upload"
                  className={`inline-flex cursor-pointer items-center gap-2 rounded-xl bg-atlas-cyan px-4 py-3 text-sm font-semibold text-white transition hover:bg-atlas-deep-cyan ${
                    uploading ? 'cursor-not-allowed opacity-50' : ''
                  }`}
                >
                  <Plus size={18} />
                  {uploading ? 'Uploading...' : 'Upload document'}
                </label>

                <input
                  id="document-upload"
                  type="file"
                  accept=".pdf,.txt,.docx"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="hidden"
                />

                <p className="mt-2 text-xs text-atlas-slate">
                  PDF, TXT or DOCX · Maximum 10 MB
                </p>

                {/* Upload feedback */}
                {uploadError && (
                  <p className="mt-3 text-sm text-red-600">
                    {uploadError}
                  </p>
                )}

                {uploadSuccess && (
                  <p className="mt-3 text-sm text-green-700">
                    {uploadSuccess}
                  </p>
                )}

                {deleteError && (
                  <p className="mt-3 text-sm text-red-600">
                    {deleteError}
                  </p>
                )}

                {deleteSuccess && (
                  <p className="mt-3 text-sm text-green-700">
                    {deleteSuccess}
                  </p>
                )}
              </div>

              {/* Document states */}
              {documentsLoading ? (
                <p className="mt-5 text-sm text-atlas-slate">
                  Loading your documents...
                </p>
              ) : documentsError ? (
                <p className="mt-5 text-sm text-red-600">
                  {documentsError}
                </p>
              ) : documents.length === 0 ? (
                <p className="mt-5 text-sm text-atlas-slate">
                  You haven't uploaded any documents yet.
                </p>
              ) : (
                <div className="mt-4 divide-y divide-atlas-mist">
                  {documents.map((document) => (
                    <div
                      key={document.source}
                      className="flex items-center justify-between gap-4 py-4"
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        <FileText
                          size={20}
                          className="shrink-0 text-atlas-cyan"
                        />

                        <p className="truncate text-sm font-medium">
                          {document.source}
                        </p>
                      </div>

                      <div className="flex shrink-0 items-center gap-3">
                        <span className="text-xs text-atlas-slate">
                          {document.chunks} chunks
                        </span>

                        <button
                          onClick={() =>
                            handleDeleteDocument(document.source)
                          }
                          disabled={Boolean(deletingDocument)}
                          title={`Delete ${document.source}`}
                          aria-label={`Delete ${document.source}`}
                          className="rounded-lg p-2 text-red-500 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          <Trash2 size={17} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <p className="mt-8 text-center text-xs text-atlas-slate">
              Your personal knowledge workspace.
            </p>
          </div>
        </div>
      </section>
    </main>
  )
}
