import ProductCard from './ProductCard'
import './ResultsPanel.css'

function hashString(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash)
}

const PILL_CLASSES = {
  category: 'pill-category',
  color: 'pill-color',
  material: 'pill-material',
  budget: 'pill-budget',
}

export default function ResultsPanel({ constraints, recommendations, stats }) {
  const constraintEntries = Object.entries(constraints)

  return (
    <section className="results-panel">
      <div className="constraints-bar">
        <span className="constraints-label">Understood:</span>
        <div className="constraint-pills">
          {constraintEntries.length === 0 && (
            <span className="no-constraints">No constraints yet</span>
          )}
          {constraintEntries.map(([attr, val]) => (
            <span key={attr} className={`pill ${PILL_CLASSES[attr] || 'pill-default'}`}>
              <span className="pill-attr">{attr}</span>
              <span className="pill-val">{val}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="products-grid">
        {recommendations.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <p>Recommendations appear here as you chat</p>
          </div>
        ) : (
          recommendations.map((rec, i) => (
            <ProductCard
              key={rec.parent_asin}
              rec={rec}
              rank={i + 1}
              hue={hashString(rec.store || 'Store') % 360}
              isTop={i === 0}
            />
          ))
        )}
      </div>

      <div className="pipeline-stats">
        <div className="stat">
          <span className="stat-label">Catalog</span>
          <span className="stat-value">50,000</span>
        </div>
        <span className="stat-arrow">&rarr;</span>
        <div className="stat">
          <span className="stat-label">Candidates</span>
          <span className="stat-value">{stats.candidateCount?.toLocaleString() ?? '—'}</span>
        </div>
        <span className="stat-arrow">&rarr;</span>
        <div className="stat">
          <span className="stat-label">Shown</span>
          <span className="stat-value">{stats.shown ?? '—'}</span>
        </div>
        <div className="stat-divider" />
        <div className="stat">
          <span className="stat-label">Query</span>
          <span className="stat-value stat-query" title={stats.query || ''}>
            {stats.query || '—'}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Time</span>
          <span className="stat-value">
            {stats.timingMs != null ? `${stats.timingMs}ms` : '—'}
          </span>
        </div>
      </div>
    </section>
  )
}
