
import { useEffect, useState, type ChangeEvent } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import {
  FileText,
  MessageSquare,
  Plus,
  LogOut,
  Menu,
  Trash2,
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
        <div className="atlas-sidebar__bottom">
          <div className="atlas-account-mark">A</div><div className="atlas-account-copy"><b>Personal workspace</b><span>Private session</span></div>
          <button onClick={handleLogout} disabled={loggingOut} aria-label="Sign out" className="atlas-logout"><LogOut size={17}/></button>
        </div>
      </aside>

      <section className="atlas-workspace__main">
        <header className="atlas-workspace__topbar">
          <div className="atlas-topbar-title"><button className="atlas-mobile-menu" onClick={() => setSidebarOpen(true)} aria-label="Open navigation"><Menu size={20}/></button><div><span className="atlas-overline">ATLASGPT / KNOWLEDGE SPACE</span><h1>Your workspace</h1></div></div>
          <div className="atlas-topbar-actions"><span className="atlas-session-status"><i/> SESSION ACTIVE</span><ThemeToggle/></div>
        </header>

        <div className="atlas-workspace__content">
          <div className="atlas-workspace__heading"><div><span className="atlas-overline">THE CONVERSATION DESK</span><h2>Explore your material.</h2><p>Ask questions. Follow the evidence. Build understanding.</p></div><div className="atlas-workspace__heading-index">FIELD NOTE <b>01 / 01</b></div></div>
          <div className="atlas-workspace__grid">
            <section className="atlas-chat-column">
              {!conversationsLoading && selectedConversationId ? <ChatPanel key={selectedConversationId} conversationId={selectedConversationId} onConversationUpdated={handleConversationUpdated}/> : <div className="atlas-chat-loading">Preparing your workspace…</div>}
            </section>

            <aside className="atlas-library" id="documents">
              <div className="atlas-library__head"><div><span className="atlas-overline">SOURCE INDEX</span><h3>Your documents</h3></div><span className="atlas-library__count">{documents.length.toString().padStart(2,'0')}</span></div>
              <p className="atlas-library__intro">The material behind your conversations.</p>
              <label htmlFor="document-upload" className={`atlas-dropzone ${uploading ? 'is-uploading' : ''}`}>
                <span className="atlas-dropzone__icon"><Plus size={21}/></span><b>{uploading ? 'Processing request' : 'Add to your atlas'}</b><span>Drop a file here or browse to select</span><small>PDF · DOCX · TXT &nbsp; / &nbsp; UP TO 10 MB</small>
                <input id="document-upload" type="file" accept=".pdf,.txt,.docx" onChange={handleFileUpload} disabled={uploading}/>
              </label>
              {uploadError && <p className="atlas-feedback is-error" role="alert">{uploadError}</p>}
              {uploadSuccess && <p className="atlas-feedback is-success" role="status">{uploadSuccess}</p>}
              {deleteError && <p className="atlas-feedback is-error" role="alert">{deleteError}</p>}
              {deleteSuccess && <p className="atlas-feedback is-success" role="status">{deleteSuccess}</p>}
              <div className="atlas-library__divider"><span>INDEXED SOURCES</span><span>{documents.length} FILES</span></div>
              <div className="atlas-source-list">
                {documentsLoading ? <p className="atlas-library__empty">Reading your source index…</p> : documentsError ? <p className="atlas-library__empty">{documentsError}</p> : documents.length === 0 ? <div className="atlas-library__empty-state"><FileText size={25}/><b>No sources yet</b><span>Your uploaded documents will be listed here.</span></div> : documents.map((doc,index) => (
                  <article className="atlas-source" key={doc.source}><span className="atlas-source__index">{String(index+1).padStart(2,'0')}</span><div className="atlas-source__info"><b title={doc.source}>{doc.source}</b><span>{doc.chunks} indexed segments</span></div><button onClick={() => handleDeleteDocument(doc.source)} disabled={Boolean(deletingDocument)} aria-label={`Delete ${doc.source}`} title="Remove source">{deletingDocument === doc.source ? '…' : <Trash2 size={15}/>}</button></article>
                ))}
              </div>
              <div className="atlas-library__note"><ShieldCheck size={15}/><span>Answers are informed by the documents in this workspace. Verify important details against your original sources.</span></div>
            </aside>
          </div>
        </div>
        <footer className="atlas-workspace__footer"><span>ATLASGPT / KNOWLEDGE, BEAUTIFULLY CONNECTED.</span><span>YOUR SOURCES. YOUR CONTEXT.</span></footer>
      </section>
    </motion.main>
  )
}
