import { useEffect, useMemo, useState } from 'react'
import './PipelineInspector.css'

const STAGE_IDS = ['extract', 'bm25', 'soft', 'llm', 'ask']
const REVEAL_MS = 160

function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function formatCount(n) {
  if (n == null) return '—'
  return Number(n).toLocaleString()
}

function buildStages(pipeline) {
  if (!pipeline) {
    return [
      { id: 'extract', label: 'Extract', value: '—' },
      { id: 'bm25', label: 'BM25', value: '—' },
      { id: 'soft', label: 'Soft rank', value: '—' },
      { id: 'llm', label: 'LLM rank', value: '—' },
      { id: 'ask', label: 'Ask', value: '—' },
    ]
  }

  const funnel = pipeline.funnel || {}
  const newKeys = Object.keys(pipeline.new_constraints || {})
  const extractValue = pipeline.intent_override
    ? 'override'
    : (newKeys.length ? `+${newKeys.length}` : '0 new')

  const llmUsed = pipeline.llm?.used
  const moved = pipeline.llm?.moved_up || []
  const llmValue = llmUsed ? (moved.length ? `${moved.length} moved` : 'reranked') : 'fallback'

  return [
    { id: 'extract', label: 'Extract', value: extractValue },
    {
      id: 'bm25',
      label: 'BM25',
      value: `${formatCount(pipeline.bm25_hits)} / ${formatCount(funnel.bm25)}`,
    },
    {
      id: 'soft',
      label: 'Soft rank',
      value: `${formatCount(pipeline.soft?.full_match)} full`,
    },
    { id: 'llm', label: 'LLM rank', value: llmValue },
    { id: 'ask', label: 'Ask', value: pipeline.ask?.attribute || '—' },
  ]
}

function stageDetail(id, pipeline) {
  if (!pipeline) return 'Send a message to run the pipeline.'

  if (id === 'extract') {
    const parts = Object.entries(pipeline.new_constraints || {}).map(
      ([attr, val]) => `${attr}: ${val}`,
    )
    const prefix = pipeline.intent_override ? 'Intent override flushed prior constraints. ' : ''
    if (!parts.length) return `${prefix}No new constraints this turn.`
    return `${prefix}New: ${parts.join(' · ')}`
  }

  if (id === 'bm25') {
    const catalog = pipeline.funnel?.catalog
    const denseNote = pipeline.dense_used ? ' Dense fusion was on.' : ''
    return `Query “${pipeline.query || '—'}”. Catalog ${formatCount(catalog)} → BM25 k=${formatCount(pipeline.funnel?.bm25)}.${denseNote}`
  }

  if (id === 'soft') {
    const soft = pipeline.soft || {}
    return `${formatCount(soft.full_match)} full-match, ${formatCount(soft.partial_kept)} partial kept → ${formatCount(pipeline.funnel?.soft)} candidates.`
  }

  if (id === 'llm') {
    const moved = pipeline.llm?.moved_up || []
    if (!pipeline.llm?.used) {
      return 'Retrieval order kept (LLM unavailable or returned invalid ranks).'
    }
    if (!moved.length) return 'LLM re-ranked top 20 → 10; order already matched retrieval.'
    const sample = moved.slice(0, 3).map((m) => `#${m.from} rose to #${m.to}`).join('; ')
    return `Re-ranked 20 → 10. ${sample}.`
  }

  const src = pipeline.ask?.source === 'llm' ? 'LLM' : 'heuristic'
  return `Next question: ${pipeline.ask?.attribute || '—'} (${src}).`
}

function defaultStage(pipeline) {
  if (pipeline?.llm?.used && (pipeline.llm.moved_up || []).length) return 'llm'
  return 'extract'
}

export default function PipelineInspector({ pipeline }) {
  const stages = useMemo(() => buildStages(pipeline), [pipeline])
  const skipAnim = !pipeline || prefersReducedMotion()
  const [revealed, setRevealed] = useState(skipAnim && pipeline ? STAGE_IDS.length : 0)
  const [selected, setSelected] = useState(() => (
    skipAnim && pipeline ? defaultStage(pipeline) : null
  ))

  useEffect(() => {
    if (!pipeline || prefersReducedMotion()) return undefined
    const timers = STAGE_IDS.map((_, i) =>
      setTimeout(() => {
        setRevealed(i + 1)
        if (i + 1 === STAGE_IDS.length) setSelected(defaultStage(pipeline))
      }, (i + 1) * REVEAL_MS),
    )
    return () => timers.forEach(clearTimeout)
  }, [pipeline])

  const totalMs = pipeline?.timing_ms?.total
  const detailId = selected || (revealed >= STAGE_IDS.length ? defaultStage(pipeline) : null)

  return (
    <div className="pipeline-inspector">
      <div className="pipeline-stepper" role="group" aria-label="Retrieval pipeline stages">
        {stages.map((stage, i) => {
          const isOn = revealed > i
          const isSelected = selected === stage.id
          return (
            <div key={stage.id} className="pipeline-step">
              {i > 0 && (
                <svg className="pipeline-arrow" viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
                  <path d="M3 8h9M8 4l4 4-4 4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
              <button
                type="button"
                className={`pipeline-stage${isOn ? ' is-on' : ''}${isSelected ? ' is-selected' : ''}`}
                aria-pressed={isSelected}
                disabled={!pipeline || !isOn}
                onClick={() => setSelected(stage.id)}
              >
                <span className="pipeline-stage-label">{stage.label}</span>
                <span className="pipeline-stage-value">{isOn ? stage.value : '—'}</span>
              </button>
            </div>
          )
        })}
        <div className="pipeline-time">
          <span className="pipeline-stage-label">Time</span>
          <span className="pipeline-stage-value">
            {totalMs != null ? `${totalMs}ms` : '—'}
          </span>
        </div>
      </div>
      <p className="pipeline-detail" role="status">
        {detailId ? stageDetail(detailId, pipeline) : 'Waiting for pipeline…'}
      </p>
    </div>
  )
}
