
import { useState, useRef, useEffect, type FormEvent } from 'react'
import {
  Send,
  LoaderCircle,
  Sparkles,
  MessageSquare,
} from 'lucide-react'

import {
  chatApi,
  conversationApi,
  ApiError,
} from '../../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatPanelProps {
  conversationId: string
  onConversationUpdated: () => void
}

export default function ChatPanel({
  conversationId,
  onConversationUpdated,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [error, setError] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Load saved messages whenever the selected conversation changes.
  useEffect(() => {
    let cancelled = false

    async function loadMessages() {
      setMessages([])
      setError('')
      setLoadingHistory(true)

      try {
        const response = await conversationApi.getMessages(conversationId)

        if (!cancelled) {
          setMessages(response.messages)
        }
      } catch (err) {
        if (cancelled) return

        if (err instanceof ApiError && err.status === 404) {
          setMessages([])
        } else {
          setError(
            err instanceof ApiError
              ? err.message
              : 'Could not load conversation history.',
          )
        }
      } finally {
        if (!cancelled) {
          setLoadingHistory(false)
        }
      }
    }

    loadMessages()

    return () => {
      cancelled = true
    }
  }, [conversationId])

  // Scroll to the latest message.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'auto',
      block: 'end',
    })
  }, [messages, sending])

  // Send a message to the selected conversation.
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const message = input.trim()

    if (!message || sending || loadingHistory) return

    setError('')
    setInput('')
    setSending(true)

    const previousMessages = messages
    setMessages((previous) => [
      ...previous,
      { role: 'user', content: message },
    ])

    try {
      const response = await chatApi.send(
        message,
        conversationId,
      )

      setMessages((previous) => [
        ...previous,
        { role: 'assistant', content: response.reply },
      ])

      onConversationUpdated()
    } catch (err) {
      // Do not leave an unsaved optimistic message in the conversation.
      // Restore the draft so the user can retry without losing their text.
      setMessages(previousMessages)
      setInput(message)
      setError(
        err instanceof ApiError
          ? err.message
          : 'Could not reach AtlasGPT. Please try again.',
      )
    } finally {
      setSending(false)
    }
  }

  return (
    <section className="atlas-chat claude-chat">
      <header className="atlas-chat__header"><div className="atlas-chat__identity"><span className="atlas-chat__avatar"><span>A</span></span><div><b>Ask Atlas</b><small>Grounded in your source material</small></div></div><span className="atlas-chat__secure"><i/> PRIVATE SESSION</span></header>
      <div className="atlas-chat__messages">
        {loadingHistory && <div className="atlas-chat__empty"><LoaderCircle  size={24}/><p>Opening this conversation…</p></div>}
        {!loadingHistory && messages.length === 0 && <div className="atlas-chat__welcome"><span className="atlas-chat__welcome-mark"><Sparkles size={24}/></span><span className="atlas-overline">A QUESTION IS A GOOD PLACE TO START</span><h3>What are you trying<br/>to understand?</h3><p>Ask about your uploaded documents. AtlasGPT searches relevant passages and uses them to inform its response.</p><div className="atlas-chat__suggestion"><MessageSquare size={15}/> Try asking for a summary, an explanation, or a comparison.</div></div>}
        {!loadingHistory && messages.map((message,index) => <article className={`atlas-message ${message.role === 'user' ? 'is-user' : 'is-assistant'}`} key={`${index}-${message.role}`}><span className="atlas-message__role">{message.role === 'user' ? 'YOU' : 'ATLAS'}</span><div className="atlas-message__body">{message.content}</div></article>)}
        {sending && <div className="atlas-message is-assistant"><span className="atlas-message__role">ATLAS</span><div className="atlas-message__body atlas-chat__thinking"><LoaderCircle  size={16}/> Looking through your context…</div></div>}<div ref={messagesEndRef}/>
      </div>
      {error && <div className="atlas-chat__error" role="alert">{error}</div>}
      <form onSubmit={handleSubmit} className="atlas-chat__composer"><div className="atlas-chat__input-wrap"><input value={input} onChange={event=>setInput(event.target.value)} placeholder="Ask a question about your sources…" maxLength={4000} disabled={sending || loadingHistory}/><button type="submit" disabled={!input.trim() || sending || loadingHistory} aria-label="Send message"><Send size={17}/></button></div><div className="atlas-chat__composer-foot"><span>Answers are generated from your available source context.</span><span>{input.length}/4000</span></div></form>
    </section>
  )
}
