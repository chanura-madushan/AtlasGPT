import { useEffect, useState, type ChangeEvent } from 'react'
import { FileText, MessageSquare, Plus, LogOut, Trash2, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { ApiError, documentApi, conversationApi } from '../services/api'
import type { Conversation } from '../types'
import ChatPanel from '../components/chat/ChatPanel'
import ThemeToggle from '../components/theme/ThemeToggle'

export default function Dashboard() {
  const { logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversationId, setSelectedConversationId] = useState(() => localStorage.getItem('atlasgpt_active_conversation') || '')
  const [conversationsLoading, setConversationsLoading] = useState(true)
  const [conversationsError, setConversationsError] = useState('')
  const [deletingConversation, setDeletingConversation] = useState('')
  const [documents, setDocuments] = useState<{ source: string; chunks: number }[]>([])
  const [documentsLoading, setDocumentsLoading] = useState(true)
  const [documentsError, setDocumentsError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [uploadSuccess, setUploadSuccess] = useState('')
  const [deletingDocument, setDeletingDocument] = useState('')
  const [deleteError, setDeleteError] = useState('')
  const [deleteSuccess, setDeleteSuccess] = useState('')
  const [showSources, setShowSources] = useState(false)

  useEffect(() => {
    if (selectedConversationId) localStorage.setItem('atlasgpt_active_conversation', selectedConversationId)
  }, [selectedConversationId])

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const response = await conversationApi.list()
        if (cancelled) return
        setConversations(response.conversations)
        const saved = localStorage.getItem('atlasgpt_active_conversation')
        const exists = response.conversations.some(item => item.conversation_id === saved)
        setSelectedConversationId(exists && saved ? saved : response.conversations[0]?.conversation_id || `web-${crypto.randomUUID()}`)
      } catch {
        if (!cancelled) {
          setConversationsError('Could not load conversations.')
          setSelectedConversationId(current => current || `web-${crypto.randomUUID()}`)
        }
      } finally {
        if (!cancelled) setConversationsLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const response = await documentApi.list()
        if (!cancelled) setDocuments(response.documents)
      } catch {
        if (!cancelled) setDocumentsError('Could not load documents.')
      } finally {
        if (!cancelled) setDocumentsLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  async function handleConversationUpdated() {
    try {
      const response = await conversationApi.list()
      setConversations(response.conversations)
      setConversationsError('')
    } catch {
      setConversationsError('Could not refresh conversations.')
    }
  }

  function handleNewConversation() {
    setSelectedConversationId(`web-${crypto.randomUUID()}`)
    setSidebarOpen(false)
    setConversationsError('')
  }

  async function handleDeleteConversation(id: string) {
    if (!window.confirm('Delete this conversation? This cannot be undone.')) return
    setDeletingConversation(id)
    try {
      await conversationApi.delete(id)
      const updated = conversations.filter(item => item.conversation_id !== id)
      setConversations(updated)
      if (selectedConversationId === id) setSelectedConversationId(updated[0]?.conversation_id || `web-${crypto.randomUUID()}`)
    } catch {
      setConversationsError('Could not delete this conversation.')
    } finally {
      setDeletingConversation('')
    }
  }

  async function handleLogout() {
    setLoggingOut(true)
    try { await logout() } catch { setLoggingOut(false) }
  }

  async function handleFileUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setUploadError('')
    setUploadSuccess('')
    const extension = file.name.split('.').pop()?.toLowerCase()
    if (!extension || !['pdf', 'txt', 'docx'].includes(extension)) {
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
    setUploadSuccess('Adding document to your sources…')
    try {
      const accepted = await documentApi.uploadAsync(file)
      let completed = false
      for (let attempt = 0; attempt < 90; attempt += 1) {
        await new Promise(resolve => window.setTimeout(resolve, 2000))
        const result = await documentApi.job(accepted.job_id)
        const job = result.job
        if (job.status === 'queued') setUploadSuccess(`${job.filename} · queued`)
        else if (job.status === 'processing') setUploadSuccess(`${job.filename} · processing`)
        else if (job.status === 'failed') throw new Error(job.error || 'Document processing failed.')
        else if (job.status === 'completed') {
          setUploadSuccess(`${job.filename} added · ${job.chunks} sections indexed`)
          completed = true
          break
        }
      }
      if (!completed) setUploadSuccess(`${accepted.filename} is still processing. Refresh your sources shortly.`)
      const refreshed = await documentApi.list()
      setDocuments(refreshed.documents)
      setDocumentsError('')
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Document upload failed.')
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  async function handleDeleteDocument(filename: string) {
    if (!window.confirm(`Delete "${filename}"? This cannot be undone.`)) return
    setDeletingDocument(filename)
    setDeleteError('')
    setDeleteSuccess('')
    try {
      await documentApi.delete(filename)
      setDocuments(current => current.filter(item => item.source !== filename))
      setDeleteSuccess(`${filename} deleted.`)
      const refreshed = await documentApi.list()
      setDocuments(refreshed.documents)
    } catch (error) {
      if (error instanceof ApiError) setDeleteError(error.message)
      else setDeleteError('Document deletion failed.')
    } finally {
      setDeletingDocument('')
    }
  }

  return (
    <main className="claude-app">
      {sidebarOpen && <button className="claude-scrim" aria-label="Close sidebar" onClick={() => setSidebarOpen(false)} />}
      <aside className={`claude-sidebar ${sidebarOpen ? 'is-open' : ''}`}>
        <div className="claude-sidebar__top">
          <a className="claude-wordmark" href="/">atlas<span>gpt</span></a>
          <button className="claude-icon-button claude-sidebar__collapse" onClick={() => setSidebarOpen(false)} aria-label="Close sidebar"><PanelLeftClose size={18}/></button>
        </div>
        <button className="claude-new-chat" onClick={handleNewConversation}><Plus size={17}/> New chat</button>
        <div className="claude-sidebar__label">RECENT</div>
        <nav className="claude-history" aria-label="Conversation history">
          {conversationsLoading ? <p className="claude-muted">Loading conversations…</p> : conversationsError ? <p className="claude-muted">{conversationsError}</p> : conversations.length === 0 ? <p className="claude-muted">Your conversations will appear here.</p> : conversations.map(item => (
            <div className={`claude-history__item ${selectedConversationId === item.conversation_id ? 'is-active' : ''}`} key={item.conversation_id}>
              <button onClick={() => { setSelectedConversationId(item.conversation_id); setSidebarOpen(false) }}><MessageSquare size={15}/><span>{item.title || 'New conversation'}</span></button>
              <button className="claude-history__delete" onClick={() => handleDeleteConversation(item.conversation_id)} disabled={Boolean(deletingConversation)} aria-label="Delete conversation"><Trash2 size={14}/></button>
            </div>
          ))}
        </nav>
        <div className="claude-sidebar__bottom">
          <button className="claude-sources-toggle" onClick={() => setShowSources(value => !value)} aria-expanded={showSources}><FileText size={16}/> Your sources <span>{documents.length}</span></button>
          {showSources && <div className="claude-source-panel">
            <label className={`claude-upload ${uploading ? 'is-disabled' : ''}`}><Plus size={15}/>{uploading ? 'Processing…' : 'Add documents'}<input type="file" accept=".pdf,.txt,.docx" onChange={handleFileUpload} disabled={uploading}/></label>
            <p className="claude-muted">PDF, DOCX or TXT · 10 MB max</p>
            {uploadError && <p className="claude-error">{uploadError}</p>}{uploadSuccess && <p className="claude-success">{uploadSuccess}</p>}{deleteError && <p className="claude-error">{deleteError}</p>}{deleteSuccess && <p className="claude-success">{deleteSuccess}</p>}
            {documentsLoading ? <p className="claude-muted">Loading sources…</p> : documentsError ? <p className="claude-error">{documentsError}</p> : documents.length === 0 ? <p className="claude-muted">No documents added yet.</p> : documents.map(doc => <div className="claude-source" key={doc.source}><div><b>{doc.source}</b><small>{doc.chunks} indexed sections</small></div><button onClick={() => handleDeleteDocument(doc.source)} disabled={Boolean(deletingDocument)} aria-label={`Delete ${doc.source}`}><Trash2 size={14}/></button></div>)}
          </div>}
          <div className="claude-account"><span className="claude-account__avatar">A</span><span className="claude-account__name">AtlasGPT workspace</span><ThemeToggle/><button className="claude-icon-button" onClick={handleLogout} disabled={loggingOut} aria-label="Sign out"><LogOut size={16}/></button></div>
        </div>
      </aside>

      <section className="claude-main">
        <header className="claude-topbar">
          <button className="claude-icon-button claude-mobile-menu" onClick={() => setSidebarOpen(true)} aria-label="Open sidebar"><PanelLeftOpen size={19}/></button>
          <span className="claude-topbar__title">AtlasGPT <span> / </span> New chat</span>
          <span className="claude-topbar__status">Private workspace</span>
        </header>
        <div className="claude-chat-area">
          {selectedConversationId && !conversationsLoading
            ? <ChatPanel key={selectedConversationId} conversationId={selectedConversationId} onConversationUpdated={handleConversationUpdated}/>
            : <div className="claude-loading">Opening your workspace…</div>}
        </div>
      </section>
    </main>
  )
}
