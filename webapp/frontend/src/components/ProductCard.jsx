import './ProductCard.css'

function truncate(str, len) {
  return str.length > len ? str.slice(0, len) + '…' : str
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

      <div className="score-bar">
        <div className="score-bar-fill" style={{ width: `${(rec.score * 100).toFixed(0)}%` }} />
      </div>
    </div>
  )
}
