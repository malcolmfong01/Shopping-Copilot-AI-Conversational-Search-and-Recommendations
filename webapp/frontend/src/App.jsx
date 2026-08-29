import { useState, useCallback, useRef } from 'react'
import Header from './components/Header'
import ChatPanel from './components/ChatPanel'
import ResultsPanel from './components/ResultsPanel'
import './App.css'

const EXAMPLE_MESSAGES = [
  "I'm looking for Men's Running Shoes. A key requirement is: breathable mesh upper.",
  "For that, what matters is: color: black; budget: under $80.",
  "For that, what matters is: size: 10; brand: Nike.",
]

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [turn, setTurn] = useState(0)
  const [messages, setMessages] = useState([])
  const [constraints, setConstraints] = useState({})
  const [recommendations, setRecs] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(false)
  const turnRef = useRef(0)

  const startSession = useCallback(async () => {
    const res = await fetch('/api/new-session', { method: 'POST' })
    const data = await res.json()
    setSessionId(data.session_id)
    setTurn(0)
    turnRef.current = 0
    setMessages([])
    setConstraints({})
    setRecs([])
    setStats({})
    return data.session_id
  }, [])

  const sendMessage = useCallback(async (text, overrideSession, overrideTurn) => {
    const sid = overrideSession || sessionId
    const nextTurn = overrideTurn != null ? overrideTurn : turnRef.current + 1
    turnRef.current = nextTurn
    setTurn(nextTurn)
    setLoading(true)

    setMessages(prev => [...prev, { role: 'user', content: text }])

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sid, message: text, turn: nextTurn }),
      })
      const data = await res.json()

      setMessages(prev => [...prev, {
        role: 'agent',
        content: data.message,
        askAttribute: data.ask_attribute,
      }])
      setConstraints(data.constraints || {})
      setRecs(data.recommendations || [])
      setStats({
        candidateCount: data.candidate_count,
        shown: (data.recommendations || []).length,
        query: data.query,
        timingMs: data.timing_ms,
      })
    } catch {
      setMessages(prev => [...prev, {
        role: 'agent',
        content: 'Something went wrong. Please try again.',
      }])
    }

    setLoading(false)
  }, [sessionId])

  const handleNewSession = useCallback(async () => {
    await startSession()
  }, [startSession])

  const handleExample = useCallback(async () => {
    const sid = await startSession()
    for (let i = 0; i < EXAMPLE_MESSAGES.length; i++) {
      await new Promise(r => setTimeout(r, i === 0 ? 400 : 1800))
      await sendMessage(EXAMPLE_MESSAGES[i], sid, i + 1)
    }
  }, [startSession, sendMessage])

  const handleSend = useCallback(async (text) => {
    if (!sessionId) {
      const sid = await startSession()
      await sendMessage(text, sid, 1)
    } else {
      await sendMessage(text)
    }
  }, [sessionId, startSession, sendMessage])

  return (
    <>
      <Header turn={turn} onNew={handleNewSession} />
      <main className="main-layout">
        <ChatPanel
          messages={messages}
          loading={loading}
          onSend={handleSend}
          onExample={handleExample}
        />
        <ResultsPanel
          constraints={constraints}
          recommendations={recommendations}
          stats={stats}
        />
      </main>
    </>
  )
}
