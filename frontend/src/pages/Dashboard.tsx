
import { useEffect, useState, type ChangeEvent } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import {
  FileText,
  MessageSquare,
  Plus,
  LogOut,
  Menu,
  Trash2,
  ShieldCheck,
} from 'lucide-react'

import { useAuth } from '../hooks/useAuth'
import {
  ApiError,
  documentApi,
  conversationApi,
} from '../services/api'

import type { Conversation } from '../types'
import ChatPanel from '../components/chat/ChatPanel'
import ThemeToggle from '../components/theme/ThemeToggle'

export default function Dashboard() {
  const { logout } = useAuth()
  const reduceMotion = useReducedMotion()

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

  // Queue ingestion and display the real worker state instead of fake progress.
  async function handleFileUpload(event: ChangeEvent<HTMLInputElement>) {
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
    setUploadSuccess('Sending document to the processing queue…')
    try {
      const accepted = await documentApi.uploadAsync(file)
      setUploadSuccess(`${accepted.filename} accepted · waiting for processing`)

      let completed = false
      for (let attempt = 0; attempt < 90; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000))
        const result = await documentApi.job(accepted.job_id)
        const job = result.job

        if (job.status === 'queued') {
          setUploadSuccess(`${job.filename} · queued for processing`)
        } else if (job.status === 'processing') {
          setUploadSuccess(`${job.filename} · processing document`)
        } else if (job.status === 'failed') {
          throw new Error(job.error || 'Document processing failed.')
        } else if (job.status === 'completed') {
          setUploadSuccess(`${job.filename} processed successfully · ${job.chunks} chunks indexed`)
          completed = true
          break
        }
      }

      if (!completed) {
        setUploadSuccess(`${accepted.filename} is still processing. You can continue using AtlasGPT; refresh the document list shortly.`)
      }
      const updatedDocuments = await documentApi.list()
      setDocuments(updatedDocuments.documents)
      setDocumentsError('')
    } catch (error) {
      setUploadError(error instanceof ApiError || error instanceof Error
        ? error.message
        : 'Document upload failed. Please try again.')
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
    <motion.main initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} className="atlas-workspace">
      {sidebarOpen && <button aria-label="Close navigation" className="atlas-mobile-scrim" onClick={() => setSidebarOpen(false)} />}
      <aside className={`atlas-sidebar ${sidebarOpen ? 'is-open' : ''}`}>
        <a href="/" className="atlas-brand"><span className="atlas-brand__symbol">A</span><span>ATLAS<span>GPT</span><i>.</i></span></a>
        <div className="atlas-sidebar__section-label">YOUR SPACE</div>
        <button className="atlas-new-chat" onClick={handleNewConversation}><Plus size={17}/> New conversation</button>
        <div className="atlas-sidebar__section-label atlas-sidebar__section-label--spaced">RECENT THREADS</div>
        <nav className="atlas-thread-list" aria-label="Recent conversations">
          {conversationsLoading ? <p className="atlas-sidebar-empty">Loading threads…</p> : conversationsError ? <p className="atlas-sidebar-empty">{conversationsError}</p> : conversations.length === 0 ? <p className="atlas-sidebar-empty">Your conversations will appear here.</p> : conversations.map((conversation) => (
            <div className={`atlas-thread ${selectedConversationId === conversation.conversation_id ? 'is-active' : ''}`} key={conversation.conversation_id}>
              <button onClick={() => handleSelectConversation(conversation.conversation_id)}><MessageSquare size={15}/><span>{conversation.title || 'Untitled conversation'}</span></button>
              <button className="atlas-thread__delete" onClick={() => handleDeleteConversation(conversation.conversation_id)} disabled={Boolean(deletingConversation)} aria-label={`Delete ${conversation.title || 'conversation'}`}><Trash2 size={14}/></button>
            </div>
          ))}
        </nav>
        <button className="atlas-sidebar__documents" onClick={() => document.getElementById('documents')?.scrollIntoView({behavior:'smooth'})}><FileText size={16}/> Document library <span>{documents.length}</span></button>
        <div className="atlas-sidebar__bottom"><div className="atlas-account-mark">A</div><div className="atlas-account-copy"><b>Personal workspace</b><span>Private session</span></div><button onClick={handleLogout} disabled={loggingOut} aria-label="Sign out" className="atlas-logout"><LogOut size={17}/></button></div>
      </aside>
      <section className="atlas-workspace__main">
        <header className="atlas-workspace__topbar"><div className="atlas-topbar-title"><button className="atlas-mobile-menu" onClick={() => setSidebarOpen(true)} aria-label="Open navigation"><Menu size={20}/></button><div><span className="atlas-overline">ATLASGPT / KNOWLEDGE SPACE</span><h1>Your workspace</h1></div></div><div className="atlas-topbar-actions"><span className="atlas-session-status"><i/> SESSION ACTIVE</span><ThemeToggle/></div></header>
        <div className="atlas-workspace__content">
          <div className="atlas-workspace__heading"><div><span className="atlas-overline">THE CONVERSATION DESK</span><h2>Explore your material.</h2><p>Ask questions. Follow the evidence. Build understanding.</p></div><div className="atlas-workspace__heading-index">FIELD NOTE <b>01 / 01</b></div></div>
          <div className="atlas-workspace__grid">
            <section className="atlas-chat-column">{!conversationsLoading && selectedConversationId ? <ChatPanel key={selectedConversationId} conversationId={selectedConversationId} onConversationUpdated={handleConversationUpdated}/> : <div className="atlas-chat-loading">Preparing your workspace…</div>}</section>
            <aside className="atlas-library" id="documents">
              <div className="atlas-library__head"><div><span className="atlas-overline">SOURCE INDEX</span><h3>Your documents</h3></div><span className="atlas-library__count">{documents.length.toString().padStart(2,'0')}</span></div>
              <p className="atlas-library__intro">The material behind your conversations.</p>
              <label htmlFor="document-upload" className={`atlas-dropzone ${uploading ? 'is-uploading' : ''}`}><span className="atlas-dropzone__icon"><Plus size={21}/></span><b>{uploading ? 'Processing request' : 'Add to your atlas'}</b><span>Drop a file here or browse to select</span><small>PDF · DOCX · TXT / UP TO 10 MB</small><input id="document-upload" type="file" accept=".pdf,.txt,.docx" onChange={handleFileUpload} disabled={uploading}/></label>
              {uploadError && <p className="atlas-feedback is-error" role="alert">{uploadError}</p>}{uploadSuccess && <p className="atlas-feedback is-success" role="status">{uploadSuccess}</p>}{deleteError && <p className="atlas-feedback is-error" role="alert">{deleteError}</p>}{deleteSuccess && <p className="atlas-feedback is-success" role="status">{deleteSuccess}</p>}
              <div className="atlas-library__divider"><span>INDEXED SOURCES</span><span>{documents.length} FILES</span></div>
              <div className="atlas-source-list">{documentsLoading ? <p className="atlas-library__empty">Reading your source index…</p> : documentsError ? <p className="atlas-library__empty">{documentsError}</p> : documents.length === 0 ? <div className="atlas-library__empty-state"><FileText size={25}/><b>No sources yet</b><span>Your uploaded documents will be listed here.</span></div> : documents.map((doc,index) => <article className="atlas-source" key={doc.source}><span className="atlas-source__index">{String(index+1).padStart(2,'0')}</span><div className="atlas-source__info"><b title={doc.source}>{doc.source}</b><span>{doc.chunks} indexed segments</span></div><button onClick={() => handleDeleteDocument(doc.source)} disabled={Boolean(deletingDocument)} aria-label={`Delete ${doc.source}`} title="Remove source">{deletingDocument === doc.source ? '…' : <Trash2 size={15}/>}</button></article>)}</div>
              <div className="atlas-library__note"><ShieldCheck size={15}/><span>Answers are informed by the documents in this workspace. Verify important details against your original sources.</span></div>
            </aside>
          </div>
        </div>
        <footer className="atlas-workspace__footer"><span>ATLASGPT / KNOWLEDGE, BEAUTIFULLY CONNECTED.</span><span>YOUR SOURCES. YOUR CONTEXT.</span></footer>
      </section>
    </motion.main>
  )
}
