import { useEffect, useMemo, useState } from 'react'
import {
  MAIN_LAYERS,
  DENSE_LAYERS,
  WALKTHROUGH,
  denseStatusLabel,
  liveChipForLayer,
} from '../architectureLayers'
import './ArchitectureView.css'

const SHOW_DENSE_KEY = 'shopping-copilot-show-dense-path'
const DENSE_LAYER_IDS = new Set(DENSE_LAYERS.map((l) => l.id))

function Arrow({ dashed }) {
  return (
    <div className={`arch-connector${dashed ? ' is-dashed' : ''}`} aria-hidden="true">
      <svg viewBox="0 0 16 28" width="16" height="28">
        <path
          d="M8 2v20M3 16l5 6 5-6"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={dashed ? '3 3' : undefined}
        />
      </svg>
    </div>
  )
}

function statusClass(status) {
  return `arch-status arch-status-${status.replace(/\s+/g, '-')}`
}

function LayerCard({
  layer,
  selected,
  onSelect,
  chip,
  status,
}) {
  return (
    <button
      type="button"
      className={`arch-layer${selected ? ' is-selected' : ''}${layer.optional ? ' is-optional' : ''}`}
      aria-pressed={selected}
      onClick={() => onSelect(layer.id)}
    >
      <div className="arch-layer-top">
        <span className="arch-layer-label">{layer.label}</span>
        {layer.optional && <span className="arch-optional-tag">Optional</span>}
        {status && <span className={statusClass(status)}>{status}</span>}
      </div>
      <span className="arch-layer-short">{layer.short}</span>
      {chip && <span className="arch-live-chip" title={chip}>{chip}</span>}
    </button>
  )
}

function DetailPanel({ layer, status, chip, denseAvailable }) {
  if (!layer) {
    return (
      <aside className="arch-detail" aria-live="polite">
        <h3>Select a step</h3>
        <p className="arch-detail-short">
          Click any step to see how the shopper’s message turns into recommendations —
          before, how, and after.
        </p>
        <p className="arch-walkthrough-banner">{WALKTHROUGH}</p>
      </aside>
    )
  }

  return (
    <aside className="arch-detail" aria-live="polite">
      <p className="arch-walkthrough-banner">{WALKTHROUGH}</p>
      <h3>{layer.label}</h3>
      <p className="arch-detail-short">
        <span className="arch-tech-pill">{layer.short}</span>
      </p>
      {layer.optional && (
        <p className="arch-detail-status">
          Optional side path —{' '}
          {denseAvailable
            ? 'this server can run it'
            : 'not turned on for this demo'}
          {status ? <> ({status})</> : null}. Keyword search is enough for our score; this
          path is here so you can see the full hybrid design.
        </p>
      )}
      <h4>In this stage</h4>
      <p>{layer.story}</p>
      <h4>How</h4>
      <p>{layer.how}</p>
      <h4>Before → After</h4>
      <div className="arch-example">
        <div>
          <span className="arch-example-label">Before</span>
          <code>{layer.before}</code>
        </div>
        <div className="arch-transform-arrow" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path d="M12 4v14M6 12l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div>
          <span className="arch-example-label">After</span>
          <code>{layer.after}</code>
        </div>
      </div>
      {chip && (
        <>
          <h4>From your live Product session</h4>
          <p className="arch-live-line">{chip}</p>
        </>
      )}
      {layer.techNote && (
        <p className="arch-tech-note">
          <span className="arch-tech-note-label">Tech note</span>
          {layer.techNote}
        </p>
      )}
    </aside>
  )
}

export default function ArchitectureView({ pipeline, denseAvailable }) {
  const [showDensePath, setShowDensePath] = useState(() => {
    try {
      const stored = sessionStorage.getItem(SHOW_DENSE_KEY)
      return stored == null ? true : stored === '1'
    } catch {
      return true
    }
  })
  const [selectedId, setSelectedId] = useState('bm25')

  useEffect(() => {
    try {
      sessionStorage.setItem(SHOW_DENSE_KEY, showDensePath ? '1' : '0')
    } catch {
      /* ignore */
    }
  }, [showDensePath])

  const layersById = useMemo(() => {
    const map = {}
    for (const layer of MAIN_LAYERS) map[layer.id] = layer
    for (const layer of DENSE_LAYERS) map[layer.id] = layer
    return map
  }, [])

  const activeSelectedId = (
    !showDensePath && DENSE_LAYER_IDS.has(selectedId)
  ) ? 'bm25' : selectedId
  const selectedLayer = layersById[activeSelectedId] || MAIN_LAYERS[0]

  const hasPipeline = Boolean(pipeline)
  const denseStatus = denseStatusLabel({
    denseAvailable: Boolean(denseAvailable),
    denseUsed: Boolean(pipeline?.dense_used),
    hasPipeline,
  })

  const mainBeforeSoft = MAIN_LAYERS.filter((l) =>
    ['input', 'extract', 'query', 'bm25'].includes(l.id),
  )
  const mainFromSoft = MAIN_LAYERS.filter((l) =>
    ['soft', 'llm', 'output'].includes(l.id),
  )

  function chip(id) {
    if (id === 'dense' || id === 'rrf') {
      if (!denseAvailable && id === 'dense') return null
      return liveChipForLayer(id, denseAvailable ? pipeline : null)
    }
    return liveChipForLayer(id, pipeline)
  }

  function statusFor(id) {
    if (id === 'dense' || id === 'rrf') return denseStatus
    return null
  }

  return (
    <section className="architecture-view" aria-label="Pipeline architecture">
      <div className="arch-toolbar">
        <div>
          <h2>How a message becomes recommendations</h2>
          <p>
            Follow one shoe-shopping example through each step. Product mode is the live demo;
            this view is the walkthrough for judges.
          </p>
        </div>
        <label className="arch-dense-toggle">
          <input
            type="checkbox"
            checked={showDensePath}
            onChange={(e) => setShowDensePath(e.target.checked)}
          />
          Show optional “meaning search” path
        </label>
      </div>

      <div className="arch-body">
        <div className="arch-diagram" role="list">
          {mainBeforeSoft.map((layer, i) => (
            <div key={layer.id} className="arch-node" role="listitem">
              {i > 0 && <Arrow />}
              <LayerCard
                layer={layer}
                selected={activeSelectedId === layer.id}
                onSelect={setSelectedId}
                chip={chip(layer.id)}
              />
            </div>
          ))}

          {showDensePath && (
            <div className="arch-branch" role="group" aria-label="Optional meaning-search path">
              <div className="arch-branch-label">Optional — search by meaning too</div>
              <Arrow dashed />
              <div className="arch-branch-rail">
                {DENSE_LAYERS.map((layer, i) => (
                  <div key={layer.id} className="arch-node">
                    {i > 0 && <Arrow dashed />}
                    <LayerCard
                      layer={layer}
                      selected={activeSelectedId === layer.id}
                      onSelect={setSelectedId}
                      chip={chip(layer.id)}
                      status={statusFor(layer.id)}
                    />
                  </div>
                ))}
              </div>
              <p className="arch-branch-join">
                When on, blends back in before “Prefer products that fit the tags”
              </p>
            </div>
          )}

          {mainFromSoft.map((layer) => (
            <div key={layer.id} className="arch-node" role="listitem">
              <Arrow />
              <LayerCard
                layer={layer}
                selected={activeSelectedId === layer.id}
                onSelect={setSelectedId}
                chip={chip(layer.id)}
              />
            </div>
          ))}
        </div>

        <DetailPanel
          layer={selectedLayer}
          status={selectedLayer?.optional ? denseStatus : null}
          chip={chip(selectedLayer?.id)}
          denseAvailable={denseAvailable}
        />
      </div>
    </section>
  )
}
