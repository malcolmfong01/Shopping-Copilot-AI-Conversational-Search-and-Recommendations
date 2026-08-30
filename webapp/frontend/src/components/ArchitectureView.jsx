import { useEffect, useMemo, useState } from 'react'
import {
  MAIN_LAYERS,
  DENSE_LAYERS,
  WALKTHROUGH,
  denseStatusLabel,
  llmBypassLabel,
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
  const extra = [
    layer.optional ? ' is-optional' : '',
    layer.bypass ? ' is-bypass' : '',
  ].join('')

  return (
    <button
      type="button"
      className={`arch-layer${selected ? ' is-selected' : ''}${extra}`}
      aria-pressed={selected}
      onClick={() => onSelect(layer.id)}
    >
      <div className="arch-layer-top">
        <span className="arch-layer-label">{layer.label}</span>
        {layer.optional && <span className="arch-optional-tag">Optional</span>}
        {layer.bypass && <span className="arch-bypass-tag">Can skip</span>}
        {status && <span className={statusClass(status)}>{status}</span>}
      </div>
      <span className="arch-layer-short">{layer.short}</span>
      {chip && <span className="arch-live-chip" title={chip}>{chip}</span>}
    </button>
  )
}

function LayerStack({
  layers,
  selectedId,
  onSelect,
  chip,
  statusFor,
  dashedArrows,
}) {
  return layers.map((layer, i) => (
    <div key={layer.id} className="arch-node" role="listitem">
      {i > 0 && <Arrow dashed={dashedArrows} />}
      <LayerCard
        layer={layer}
        selected={selectedId === layer.id}
        onSelect={onSelect}
        chip={chip(layer.id)}
        status={statusFor(layer.id)}
      />
    </div>
  ))
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
          {status ? <> ({status})</> : null}. Built from the full tags, not the
          BM25 keyword string. Keyword search is what we ship for score.
        </p>
      )}
      {layer.bypass && (
        <p className="arch-detail-status">
          Bypass stage — attempted every turn; if it fails we keep retrieval
          order{status ? <> ({status})</> : null}. The model reorders candidates;
          it does not pick the search path.
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
      return stored === '1'
    } catch {
      return false
    }
  })
  const [selectedId, setSelectedId] = useState('extract')

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
  ) ? 'tags' : selectedId
  const selectedLayer = layersById[activeSelectedId] || MAIN_LAYERS[0]

  const hasPipeline = Boolean(pipeline)
  const denseStatus = denseStatusLabel({
    denseAvailable: Boolean(denseAvailable),
    denseUsed: Boolean(pipeline?.dense_used),
    hasPipeline,
  })
  const llmStatus = llmBypassLabel({
    hasPipeline,
    used: Boolean(pipeline?.llm?.used),
  })

  const trunk = MAIN_LAYERS.filter((l) => l.group === 'trunk')
  const keywordPath = MAIN_LAYERS.filter((l) => l.group === 'keyword')
  const tagsPath = MAIN_LAYERS.filter((l) => l.group === 'tags')
  const mergePath = MAIN_LAYERS.filter((l) => l.group === 'merge')

  function chip(id) {
    if (id === 'dense' || id === 'rrf') {
      if (!denseAvailable && id === 'dense') return null
      return liveChipForLayer(id, denseAvailable ? pipeline : null)
    }
    return liveChipForLayer(id, pipeline)
  }

  function statusFor(id) {
    if (id === 'dense' || id === 'rrf') return denseStatus
    if (id === 'llm') return llmStatus
    if (id === 'ask' && pipeline?.ask?.source) {
      return pipeline.ask.source === 'llm' ? 'LLM' : 'heuristic'
    }
    return null
  }

  const rejoin = showDensePath
    ? 'BM25 list + optional dense blend, scored with full tags'
    : 'BM25 list scored with full tags (not the shortened query)'

  return (
    <section className="architecture-view" aria-label="Pipeline architecture">
      <div className="arch-toolbar">
        <div>
          <h2>How a message becomes recommendations</h2>
          <p>
            This is the real data flow: tags split into a keyword string and a full
            dictionary. Meaning search is optional and off in the shipped score.
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
          <LayerStack
            layers={trunk}
            selectedId={activeSelectedId}
            onSelect={setSelectedId}
            chip={chip}
            statusFor={statusFor}
          />

          <Arrow />
          <div className="arch-fork" role="group" aria-label="Tags feed two paths">
            <p className="arch-fork-caption">Same tags, two consumers</p>
            <div className="arch-fork-cols">
              <div className="arch-fork-col">
                <p className="arch-fork-label">Keyword string → BM25</p>
                <LayerStack
                  layers={keywordPath}
                  selectedId={activeSelectedId}
                  onSelect={setSelectedId}
                  chip={chip}
                  statusFor={statusFor}
                />
              </div>
              <div className="arch-fork-col">
                <p className="arch-fork-label">Full tags → matching</p>
                <LayerStack
                  layers={tagsPath}
                  selectedId={activeSelectedId}
                  onSelect={setSelectedId}
                  chip={chip}
                  statusFor={statusFor}
                />
                {showDensePath && (
                  <div className="arch-branch" role="group" aria-label="Optional meaning-search path">
                    <div className="arch-branch-label">Optional — from full tags, not BM25 words</div>
                    <Arrow dashed />
                    <LayerStack
                      layers={DENSE_LAYERS}
                      selectedId={activeSelectedId}
                      onSelect={setSelectedId}
                      chip={chip}
                      statusFor={statusFor}
                      dashedArrows
                    />
                  </div>
                )}
              </div>
            </div>
            <p className="arch-fork-rejoin">{rejoin}</p>
          </div>

          {mergePath.map((layer) => (
            <div
              key={layer.id}
              className={`arch-node${layer.bypass ? ' arch-bypass-wrap' : ''}`}
              role="listitem"
            >
              <Arrow />
              <LayerCard
                layer={layer}
                selected={activeSelectedId === layer.id}
                onSelect={setSelectedId}
                chip={chip(layer.id)}
                status={statusFor(layer.id)}
              />
              {layer.bypass && (
                <p className="arch-bypass-note">
                  If no key or invalid JSON → keep retrieval order
                </p>
              )}
            </div>
          ))}
        </div>

        <DetailPanel
          layer={selectedLayer}
          status={
            selectedLayer?.optional
              ? denseStatus
              : selectedLayer?.bypass
                ? llmStatus
                : statusFor(selectedLayer?.id)
          }
          chip={chip(selectedLayer?.id)}
          denseAvailable={denseAvailable}
        />
      </div>
    </section>
  )
}
