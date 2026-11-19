
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

  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversationId, setSelectedConversationId] = useState(
    () => localStorage.getItem('atlasgpt_active_conversation') || '',
  )
  const [conversationsLoading, setConversationsLoading] = useState(true)
  const [conversationsError, setConversationsError] = useState('')
  const [deletingConversation, setDeletingConversation] = useState('')

  const [documents, setDocuments] = useState<
    { source: string; chunks: number }[]
  >([])
  const [documentsLoading, setDocumentsLoading] = useState(true)
  const [documentsError, setDocumentsError] = useState('')

  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [uploadSuccess, setUploadSuccess] = useState('')

  const [deletingDocument, setDeletingDocument] = useState('')
  const [deleteError, setDeleteError] = useState('')
  const [deleteSuccess, setDeleteSuccess] = useState('')

  // Persist selected conversation.
  useEffect(() => {
    if (selectedConversationId) {
      localStorage.setItem(
        'atlasgpt_active_conversation',
        selectedConversationId,
      )
    }
  }, [selectedConversationId])

  // Load conversations.
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

  // Refresh conversations after a successful message.
  async function handleConversationUpdated() {
    try {
      const response = await conversationApi.list()
      setConversations(response.conversations)
      setConversationsError('')
    } catch {
      setConversationsError('Could not refresh your conversations.')
    }
  }

  function handleNewConversation() {
    setSelectedConversationId(`web-${crypto.randomUUID()}`)
    setSidebarOpen(false)
    setConversationsError('')
  }

  function handleSelectConversation(conversationId: string) {
    setSelectedConversationId(conversationId)
    setSidebarOpen(false)
  }

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

  async function handleLogout() {
    setLoggingOut(true)

    try {
      await logout()
    } catch {
      setLoggingOut(false)
    }
  }

  // Load documents.
  useEffect(() => {
    let cancelled = false

    async function loadDocuments() {
      try {
        const response = await documentApi.list()

        if (cancelled) return

        setDocuments(response.documents)
        setDocumentsError('')
      } catch {
        if (cancelled) return

        setDocumentsError('Could not load your documents.')
      } finally {
        if (!cancelled) {
          setDocumentsLoading(false)
        }
      }
    }

    loadDocuments()

    return () => {
      cancelled = true
    }
  }, [])

  // Upload document.
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

      setUploadSuccess(`${response.filename} uploaded successfully.`)

      try {
        const updatedDocuments = await documentApi.list()
        setDocuments(updatedDocuments.documents)
        setDocumentsError('')
      } catch {
        setDocumentsError(
          'Upload succeeded, but the document list could not be refreshed. Reload the page to update it.',
        )
      }
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

  // Delete document.
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

      // Update the UI immediately after successful deletion.
      setDocuments((current) =>
        current.filter((document) => document.source !== filename),
      )

      setDeleteSuccess(`${filename} deleted successfully.`)

      try {
        const updatedDocuments = await documentApi.list()
        setDocuments(updatedDocuments.documents)
        setDocumentsError('')
      } catch {
        setDocumentsError(
          'Document deleted, but the document list could not be refreshed. Reload the page to update it.',
        )
      }
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
    <main className="flex min-h-screen bg-atlas-cloud text-atlas-navy">

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <button
          aria-label="Close sidebar"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-atlas-navy/40 backdrop-blur-sm lg:hidden"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-atlas-mist bg-white transition-transform duration-300 lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-atlas-mist px-6">
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

        <div className="p-5">
          <button
            onClick={handleNewConversation}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-atlas-cyan px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-atlas-deep-cyan"
          >
            <Plus size={18} />
            New conversation
          </button>
        </div>

        <nav className="flex-1 space-y-3 overflow-y-auto px-4">
          <div className="flex items-center gap-3 rounded-xl bg-atlas-cyan/10 px-4 py-3 text-sm font-semibold text-atlas-deep-cyan">
            <MessageSquare size={18} />
            Conversations
          </div>

          <div className="space-y-1 pt-2">
            <p className="px-3 py-2 text-[11px] font-bold uppercase tracking-widest text-atlas-slate">
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
                    <MessageSquare size={15} className="shrink-0" />
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
              <FileText size={18} />
              My documents
            </button>
          </div>
        </nav>

        {/* Account */}
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

        {/* Top bar */}
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-atlas-mist bg-white px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-atlas-slate transition hover:bg-atlas-cloud lg:hidden"
              aria-label="Open sidebar"
            >
              <Menu size={21} />
            </button>

            <div>
              <h1 className="font-heading text-base font-bold sm:text-lg">
                Knowledge workspace
              </h1>
              <p className="hidden text-xs text-atlas-slate sm:block">
                Your documents. Your knowledge. One workspace.
              </p>
            </div>
          </div>

          <div className="rounded-full border border-atlas-mist bg-atlas-pearl px-3 py-2 text-xs font-medium text-atlas-deep-cyan">
            Personal workspace
          </div>
        </header>

        {/* Workspace layout */}
        <div className="flex-1 p-3 sm:p-5">
          <div className="mx-auto grid w-full max-w-[1800px] grid-cols-1 gap-4 xl:h-[calc(100vh-104px)] xl:grid-cols-[minmax(0,1fr)_270px]">

            {/* Main chat column */}
            <section className="flex min-h-[650px] min-w-0 flex-col">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Sparkles
                      size={18}
                      className="text-atlas-cyan"
                    />
                    <h2 className="font-heading text-lg font-bold">
                      AI Assistant
                    </h2>
                  </div>

                  <p className="mt-1 text-xs text-atlas-slate sm:text-sm">
                    Ask questions about your uploaded documents.
                  </p>
                </div>

                <span className="hidden rounded-full bg-white px-3 py-1.5 text-xs font-medium text-atlas-slate sm:inline-flex">
                  Private workspace
                </span>
              </div>

              {!conversationsLoading && selectedConversationId ? (
                <div className="min-h-[580px] flex-1 xl:min-h-0">
                  <ChatPanel
                    key={selectedConversationId}
                    conversationId={selectedConversationId}
                    onConversationUpdated={handleConversationUpdated}
                  />
                </div>
              ) : (
                <div className="flex min-h-[580px] flex-1 items-center justify-center rounded-2xl border border-atlas-mist bg-white">
                  <div className="text-center">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-atlas-cyan/10 text-atlas-cyan">
                      <MessageSquare size={23} />
                    </div>
                    <p className="mt-4 text-sm font-semibold">
                      Loading your workspace
                    </p>
                    <p className="mt-1 text-xs text-atlas-slate">
                      Preparing your conversations...
                    </p>
                  </div>
                </div>
              )}
            </section>

            {/* Documents panel */}
            <aside
              id="documents"
              className="flex min-w-0 flex-col rounded-2xl border border-atlas-mist bg-white p-4 sm:p-5 xl:min-h-0 xl:overflow-y-auto"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <FileText
                      size={18}
                      className="text-atlas-cyan"
                    />
                    <h3 className="font-heading text-base font-bold">
                      Documents
                    </h3>
                  </div>

                  <p className="mt-1 text-xs text-atlas-slate">
                    Your knowledge sources
                  </p>
                </div>

                <span className="rounded-lg bg-atlas-cloud px-2.5 py-1 text-xs font-semibold text-atlas-deep-cyan">
                  {documents.length}
                </span>
              </div>

              {/* Upload area */}
              <div className="mt-5 rounded-xl border border-dashed border-atlas-mist bg-atlas-pearl p-4">
                <div className="text-center">
                  <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-atlas-cyan/10 text-atlas-cyan">
                    <Plus size={21} />
                  </div>

                  <p className="mt-3 text-sm font-semibold">
                    Add a document
                  </p>

                  <p className="mt-1 text-xs leading-5 text-atlas-slate">
                    Upload a file to expand your knowledge base.
                  </p>

                  <label
                    htmlFor="document-upload"
                    className={`mt-4 inline-flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg bg-atlas-cyan px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-atlas-deep-cyan ${
                      uploading ? 'cursor-not-allowed opacity-50' : ''
                    }`}
                  >
                    <Plus size={16} />
                    {uploading ? 'Uploading...' : 'Upload file'}
                  </label>

                  <input
                    id="document-upload"
                    type="file"
                    accept=".pdf,.txt,.docx"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    className="hidden"
                  />

                  <p className="mt-2 text-[11px] text-atlas-slate">
                    PDF, TXT, DOCX · Max 10 MB
                  </p>
                </div>
              </div>

              {/* Upload and deletion feedback */}
              {uploadError && (
                <p className="mt-3 rounded-lg bg-red-50 p-3 text-xs leading-5 text-red-600">
                  {uploadError}
                </p>
              )}

              {uploadSuccess && (
                <p className="mt-3 rounded-lg bg-green-50 p-3 text-xs leading-5 text-green-700">
                  {uploadSuccess}
                </p>
              )}

              {deleteError && (
                <p className="mt-3 rounded-lg bg-red-50 p-3 text-xs leading-5 text-red-600">
                  {deleteError}
                </p>
              )}

              {deleteSuccess && (
                <p className="mt-3 rounded-lg bg-green-50 p-3 text-xs leading-5 text-green-700">
                  {deleteSuccess}
                </p>
              )}

              <div className="my-5 border-t border-atlas-mist" />

              {/* Document list */}
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-atlas-slate">
                  Uploaded files
                </h4>

                <span className="text-[11px] text-atlas-slate">
                  {documents.length} total
                </span>
              </div>

              {documentsLoading ? (
                <p className="mt-4 text-xs text-atlas-slate">
                  Loading documents...
                </p>
              ) : documentsError ? (
                <p className="mt-4 text-xs text-red-600">
                  {documentsError}
                </p>
              ) : documents.length === 0 ? (
                <div className="py-8 text-center">
                  <FileText
                    size={26}
                    className="mx-auto text-atlas-mist"
                  />
                  <p className="mt-3 text-xs font-medium text-atlas-slate">
                    No documents yet
                  </p>
                  <p className="mt-1 text-[11px] leading-5 text-atlas-slate">
                    Your uploaded files will appear here.
                  </p>
                </div>
              ) : (
                <div className="mt-2 divide-y divide-atlas-mist">
                  {documents.map((document) => (
                    <div
                      key={document.source}
                      className="flex items-start gap-2 py-3"
                    >
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-atlas-cyan/10 text-atlas-cyan">
                        <FileText size={16} />
                      </div>

                      <div className="min-w-0 flex-1">
                        <p
                          className="break-words text-xs font-semibold leading-5 text-atlas-navy"
                          title={document.source}
                        >
                          {document.source}
                        </p>

                        <p className="mt-1 text-[11px] text-atlas-slate">
                          {document.chunks} chunks
                        </p>
                      </div>

                      <button
                        onClick={() =>
                          handleDeleteDocument(document.source)
                        }
                        disabled={Boolean(deletingDocument)}
                        title={`Delete ${document.source}`}
                        aria-label={`Delete ${document.source}`}
                        className="shrink-0 rounded-lg p-2 text-atlas-slate transition hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {deletingDocument === document.source ? (
                          <span className="text-[10px]">...</span>
                        ) : (
                          <Trash2 size={15} />
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-auto pt-5">
                <div className="rounded-xl bg-atlas-cloud p-3">
                  <p className="text-xs font-semibold text-atlas-navy">
                    Knowledge workspace
                  </p>
                  <p className="mt-1 text-[11px] leading-5 text-atlas-slate">
                    Your conversations use your uploaded sources to provide grounded answers.
                  </p>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </section>
    </main>
  )
}
