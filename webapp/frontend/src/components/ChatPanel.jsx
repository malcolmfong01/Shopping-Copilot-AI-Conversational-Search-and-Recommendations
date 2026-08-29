import { useState, useRef, useEffect } from 'react'
import './ChatPanel.css'

export default function ChatPanel({ messages, loading, onSend, onExample }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    onSend(input.trim())
    setInput('')
  }

  return (
    <section className="chat-panel">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="system-msg">
            Start a conversation or click <strong>Try Example</strong> below.
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`msg msg-${msg.role}`}>
            <span>{msg.content}</span>
            {msg.askAttribute && (
              <span className="ask-tag">Asking: {msg.askAttribute}</span>
            )}
          </div>
        ))}
        {loading && (
          <div className="typing-indicator">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="chat-input-area">
        <div className="example-row">
          <button className="btn-example" onClick={onExample} disabled={loading}>
            Try Example
          </button>
        </div>
        <form className="chat-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="I'm looking for running shoes..."
            disabled={loading}
            autoFocus
          />
          <button type="submit" className="btn-send" disabled={loading || !input.trim()}>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </form>
      </div>
    </section>
  )
}
