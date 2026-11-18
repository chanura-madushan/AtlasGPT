
import { useState, useRef, useEffect, type FormEvent } from 'react'
import { Send, Bot, User, LoaderCircle } from 'lucide-react'

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

        // A new conversation has no messages yet.
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
      behavior: 'smooth',
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
    <section className="flex min-h-[500px] flex-col overflow-hidden rounded-2xl border border-atlas-mist bg-white">

      {/* Chat header */}
      <div className="flex items-center gap-3 border-b border-atlas-mist p-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-atlas-cyan/10 text-atlas-deep-cyan">
          <Bot size={21} />
        </div>

        <div>
          <h3 className="font-heading font-bold">Ask Atlas</h3>
          <p className="text-xs text-atlas-slate">
            Answers grounded in your documents
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto p-5">

        {loadingHistory && (
          <div className="flex min-h-64 items-center justify-center gap-2 text-sm text-atlas-slate">
            <LoaderCircle size={18} className="animate-spin" />
            Loading conversation...
          </div>
        )}

        {!loadingHistory && messages.length === 0 && (
          <div className="flex min-h-64 flex-col items-center justify-center text-center">
            <Bot size={32} className="text-atlas-cyan" />

            <h4 className="mt-4 font-heading font-bold">
              Start a conversation
            </h4>

            <p className="mt-2 max-w-xs text-sm leading-6 text-atlas-slate">
              Ask questions about your uploaded documents.
            </p>
          </div>
        )}

        {!loadingHistory && messages.map((message, index) => (
          <div
            key={`${index}-${message.role}`}
            className={`flex items-start gap-3 ${
              message.role === 'user' ? 'flex-row-reverse' : ''
            }`}
          >
            <div
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                message.role === 'user'
                  ? 'bg-atlas-navy text-white'
                  : 'bg-atlas-cyan/10 text-atlas-deep-cyan'
              }`}
            >
              {message.role === 'user' ? (
                <User size={16} />
              ) : (
                <Bot size={16} />
              )}
            </div>

            <div
              className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-6 ${
                message.role === 'user'
                  ? 'bg-atlas-cyan text-white'
                  : 'bg-atlas-cloud text-atlas-navy'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex items-center gap-2 text-sm text-atlas-slate">
            <LoaderCircle size={17} className="animate-spin" />
            AtlasGPT is thinking...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error message */}
      {error && (
        <p className="px-5 pb-2 text-sm text-red-600">
          {error}
        </p>
      )}

      {/* Message input */}
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-3 border-t border-atlas-mist p-4"
      >
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask something about your documents..."
          maxLength={4000}
          disabled={sending || loadingHistory}
          className="min-w-0 flex-1 rounded-xl border border-atlas-mist bg-atlas-pearl px-4 py-3 text-sm outline-none transition focus:border-atlas-cyan disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={!input.trim() || sending || loadingHistory}
          aria-label="Send message"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-atlas-cyan text-white transition hover:bg-atlas-deep-cyan disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send size={18} />
        </button>
      </form>
    </section>
  )
}
