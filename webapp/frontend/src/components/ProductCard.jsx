import './ProductCard.css'

function truncate(str, len) {
  return str.length > len ? str.slice(0, len) + '…' : str
}

function MatchIcon({ ok }) {
  if (ok) {
    return (
      <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
        <path d="M3 8.5l3.2 3.2L13 4.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
      <path d="M4 4l8 8M12 4l-8 8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  )
}

function MatchTicks({ matches }) {
  const entries = Object.entries(matches || {})
  if (entries.length === 0) return null
  return (
    <ul className="match-ticks">
      {entries.map(([attr, ok]) => (
        <li
          key={attr}
          className={ok ? 'tick-yes' : 'tick-no'}
          aria-label={`${attr} ${ok ? 'matched' : 'not matched'}`}
        >
          <MatchIcon ok={ok} />
          <span>{attr}</span>
        </li>
      ))}
    </ul>
  )
}

export default function ProductCard({ rec, rank, hue, isTop }) {
  const initial = (rec.store || '?')[0].toUpperCase()
  const stars = rec.rating != null
    ? '★'.repeat(Math.round(rec.rating)) + '☆'.repeat(5 - Math.round(rec.rating))
    : null

  return (
    <div className={`product-card${isTop ? ' top-pick' : ''}`} style={{ animationDelay: `${(rank - 1) * 40}ms` }}>
      <div className="card-header">
        <div className="monogram" style={{ background: `hsl(${hue}, 40%, 35%)` }}>
          {initial}
        </div>
        <div className="card-meta">
          <div className="card-title">{rec.title}</div>
          <div className="card-store">{rec.store}</div>
        </div>
        <span className="card-rank">#{rank}</span>
      </div>

      <div className="card-body">
        {rec.price != null ? (
          <span className="card-price">${rec.price.toFixed(2)}</span>
        ) : (
          <span className="card-price no-price">Price unavailable</span>
        )}
        {stars && <span className="card-rating">{stars} {rec.rating}</span>}
        {rec.review_count > 0 && (
          <span className="card-reviews">({rec.review_count.toLocaleString()})</span>
        )}
      </div>

      {rec.categories?.length > 1 && (
        <div className="card-category">
          {rec.categories.slice(1, 4).join(' > ')}
        </div>
      )}

      {rec.features?.length > 0 && (
        <div className="card-features">
          {rec.features.slice(0, 2).map((f, i) => (
            <span key={i} className="feature-tag">{truncate(f, 40)}</span>
          ))}
        </div>
      )}

      <MatchTicks matches={rec.matches} />

      <div className="score-bar">
        <div className="score-bar-fill" style={{ width: `${(rec.score * 100).toFixed(0)}%` }} />
      </div>
    </div>
  )
}
