
import { useState, useRef, useEffect, type FormEvent } from 'react'
import {
  Send,
  Bot,
  User,
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
      behavior: 'smooth',
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
    <section className="flex h-full min-h-[580px] flex-col overflow-hidden rounded-2xl border border-atlas-mist bg-white shadow-sm">

      {/* Chat header */}
      <div className="flex shrink-0 items-center justify-between border-b border-atlas-mist px-5 py-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-atlas-cyan/10 text-atlas-deep-cyan">
            <Bot size={23} />
          </div>

          <div className="min-w-0">
            <h3 className="font-heading text-sm font-bold sm:text-base">
              Ask Atlas
            </h3>
            <p className="mt-0.5 text-xs text-atlas-slate">
              Your personal document assistant
            </p>
          </div>
        </div>

        <div className="hidden items-center gap-2 rounded-full bg-green-50 px-3 py-1.5 text-xs font-medium text-green-700 sm:flex">
          <span className="h-2 w-2 rounded-full bg-green-500" />
          Ready
        </div>
      </div>

      {/* Messages area */}
      <div className="min-h-0 flex-1 space-y-6 overflow-y-auto bg-atlas-pearl/60 px-4 py-6 sm:px-7 sm:py-8">

        {loadingHistory && (
          <div className="flex min-h-full items-center justify-center">
            <div className="text-center">
              <LoaderCircle
                size={26}
                className="mx-auto animate-spin text-atlas-cyan"
              />
              <p className="mt-4 text-sm font-medium text-atlas-slate">
                Loading conversation...
              </p>
            </div>
          </div>
        )}

        {!loadingHistory && messages.length === 0 && (
          <div className="flex min-h-full flex-col items-center justify-center px-4 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-atlas-cyan/10 text-atlas-cyan">
              <Sparkles size={30} />
            </div>

            <h4 className="mt-6 font-heading text-xl font-bold tracking-tight sm:text-2xl">
              What would you like to know?
            </h4>

            <p className="mt-3 max-w-md text-sm leading-7 text-atlas-slate">
              Ask questions about your uploaded documents. AtlasGPT
              will search your knowledge base and use relevant
              information to answer.
            </p>

            <div className="mt-7 flex items-center gap-2 rounded-xl border border-atlas-mist bg-white px-4 py-3 text-xs text-atlas-slate">
              <MessageSquare size={15} className="text-atlas-cyan" />
              Start by typing a question below.
            </div>
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
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
                message.role === 'user'
                  ? 'bg-atlas-navy text-white'
                  : 'bg-atlas-cyan/10 text-atlas-deep-cyan'
              }`}
            >
              {message.role === 'user' ? (
                <User size={17} />
              ) : (
                <Bot size={18} />
              )}
            </div>

            <div
              className={`max-w-[88%] whitespace-pre-wrap break-words rounded-2xl px-4 py-3.5 text-sm leading-7 sm:max-w-[80%] sm:px-5 ${
                message.role === 'user'
                  ? 'rounded-tr-md bg-atlas-cyan text-white shadow-sm'
                  : 'rounded-tl-md border border-atlas-mist bg-white text-atlas-navy'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-atlas-cyan/10 text-atlas-deep-cyan">
              <Bot size={18} />
            </div>

            <div className="flex items-center gap-2 rounded-2xl rounded-tl-md border border-atlas-mist bg-white px-4 py-3.5 text-sm text-atlas-slate">
              <LoaderCircle size={16} className="animate-spin text-atlas-cyan" />
              AtlasGPT is thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error message */}
      {error && (
        <div className="shrink-0 border-t border-red-100 bg-red-50 px-5 py-3 text-sm text-red-600 sm:px-6">
          {error}
        </div>
      )}

      {/* Message input */}
      <form
        onSubmit={handleSubmit}
        className="shrink-0 border-t border-atlas-mist bg-white p-4 sm:p-5"
      >
        <div className="flex items-center gap-3 rounded-xl border border-atlas-mist bg-atlas-pearl p-2 transition focus-within:border-atlas-cyan focus-within:ring-2 focus-within:ring-atlas-cyan/10">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask something about your documents..."
            maxLength={4000}
            disabled={sending || loadingHistory}
            className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-atlas-navy outline-none placeholder:text-atlas-slate/70 disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={!input.trim() || sending || loadingHistory}
            aria-label="Send message"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-atlas-cyan text-white shadow-sm transition hover:bg-atlas-deep-cyan disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Send size={18} />
          </button>
        </div>

        <p className="mt-3 text-center text-[11px] text-atlas-slate">
          AtlasGPT answers using your uploaded knowledge sources.
        </p>
      </form>
    </section>
  )
}
