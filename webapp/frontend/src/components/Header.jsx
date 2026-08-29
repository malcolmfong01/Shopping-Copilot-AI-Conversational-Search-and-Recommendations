import './Header.css'

export default function Header({ turn, onNew }) {
  return (
    <header className="header">
      <div className="header-left">
        <svg className="logo" viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
          <line x1="3" y1="6" x2="21" y2="6"/>
          <path d="M16 10a4 4 0 01-8 0"/>
        </svg>
        <h1>Shopping Copilot</h1>
        <span className="badge">TechJam 2026</span>
      </div>
      <div className="header-right">
        <span className="score-badge">Hit Rate 97% · 8x Baseline</span>
        <span className="turn-counter">Turn {turn}/10</span>
        <button className="btn-secondary" onClick={onNew}>New Session</button>
      </div>
    </header>
  )
}
