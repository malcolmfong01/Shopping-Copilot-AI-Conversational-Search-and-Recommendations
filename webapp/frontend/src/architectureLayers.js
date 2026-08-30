/**
 * One continuous walkthrough (Men's Running Shoes) for Architecture mode.
 * Diagram topology matches Agent.respond + HybridRetriever.search.
 * Explanations stay plain English; techNote is a footnote.
 */

export const WALKTHROUGH =
  "Same example as Product → Try Example: shopping for men's running shoes."

export const MAIN_LAYERS = [
  {
    id: 'input',
    group: 'trunk',
    label: 'Shopper speaks',
    short: 'User message',
    story: 'The shopper types what they want in normal language. Nothing has been searched yet — we only have the words they said.',
    how: 'We take the latest chat message as the starting point for this turn.',
    before: "I'm looking for Men's Running Shoes. A key requirement is: breathable mesh upper.",
    after: 'That full sentence is handed to the next step to pull out the useful bits.',
    techNote: 'Session turns are capped at 10 (competition rule).',
  },
  {
    id: 'extract',
    group: 'trunk',
    label: 'Extract shopping tags',
    short: 'Constraint extract',
    story: 'We turn the sentence into a tag dictionary — category, feature, color, budget, and so on. Later messages add to that dictionary. This is pattern matching, not an LLM “understanding” the shopper.',
    how: 'We look for known phrase patterns (“looking for…”, “key requirement is…”, “what matters is…”) and map each value to a tag name (feature, color, material…). If the shopper changes direction (“actually…”), we clear the other tags, keep category, then extract the new need.',
    before: "I'm looking for Men's Running Shoes. A key requirement is: breathable mesh upper.",
    after: [
      'category → Men\'s Running Shoes',
      'feature → breathable mesh upper',
      '',
      'Later turn adds:',
      'color → black',
      'budget → under $80',
    ].join('\n'),
    techNote: 'Keys are category, feature, color, … — not “must-have.” Multiple features stack with | (e.g. mesh|Nike).',
  },
  {
    id: 'query',
    group: 'keyword',
    label: 'Build a short keyword string',
    short: 'build_query()',
    story: 'One consumer of the tags is keyword search. We build a short string for BM25 only. Budget never goes in this string — it is checked later against price.',
    how: 'Drop prefixes (“color:”). Skip budget. If the category name is more than two words, keep the last two (“Men\'s Running Shoes” → “Running Shoes”). If a tag has several values stacked with |, keep only the last one. Those cuts are for FTS: generic parent words (Women, Shoes) would flood the results.',
    before: [
      'category: Men\'s Running Shoes',
      'feature: breathable mesh upper',
      'color: black',
      'budget: under $80  ← skipped here',
    ].join('\n'),
    after: 'Running Shoes breathable mesh upper black',
    techNote: 'Soft rank still sees the full category string. This shortening is BM25-only.',
  },
  {
    id: 'tags',
    group: 'tags',
    label: 'Full tags',
    short: 'Unchanged dict',
    story: 'The same dictionary is not replaced by the keyword string. Soft rank (and meaning search, if on) still see the full category, every stacked | value, and budget.',
    how: 'No extra transform — we pass the extracted tags through as-is.',
    before: [
      'category: Men\'s Running Shoes',
      'feature: breathable mesh upper',
      'color: black',
      'budget: under $80',
    ].join('\n'),
    after: 'Same dict — full category and budget still present',
    techNote: 'Two consumers, one dict: short string → BM25; full tags → soft rank (and dense query if enabled).',
  },
  {
    id: 'bm25',
    group: 'keyword',
    label: 'Find keyword matches',
    short: 'BM25 search',
    story: 'We search the whole catalog for products whose title and details contain those words. Stronger title matches rank higher. The catalog shrinks from tens of thousands to a few hundred candidates.',
    how: 'Every product is scored by how well its text matches the search words — like a smarter Ctrl+F across 50,000 items. Tokens are OR’d after stopwords are dropped.',
    before: 'Search words: Running Shoes breathable mesh upper black\nCatalog size: ~50,000 products',
    after: '~200 products that look textually relevant (still too many to show)',
    techNote: 'BM25 via SQLite FTS5, weighted columns (title highest). Depth k=200. This step alone is most of our score gain (~8× baseline).',
  },
  {
    id: 'soft',
    group: 'merge',
    label: 'Prefer products that fit the tags',
    short: 'Soft constraint rank',
    story: 'We take the BM25 list (or the blended list if meaning search ran) and score it with the full tags — including budget vs price, and the un-shortened category. Near-misses stay in the pool instead of being thrown away for missing one detail.',
    how: 'Full matches go first (up to 8). Near-misses are kept. Strong BM25 hits that miss only one tag are interleaved. Then we cap at about 50.',
    before: [
      '~200 keyword matches + full tags',
      'Check: Men\'s Running Shoes · breathable mesh · black · under $80',
    ].join('\n'),
    after: [
      '~50 candidates',
      'Front: match all tags',
      'Then: strong BM25 near-misses mixed in',
      'Then: other partial matches',
    ].join('\n'),
    techNote: 'Not a hard filter and not a plain sort-by-fraction. Interleaving high-BM25 partials is its own measured lift.',
  },
  {
    id: 'llm',
    group: 'merge',
    bypass: true,
    label: 'AI re-rank — or keep order',
    short: 'LLM re-rank',
    story: 'This stage is attempted every turn. The model only reorders the top 20 candidates. It does not choose BM25 vs dense, and it does not extract tags. If there is no API key, or the reply is not valid JSON, we keep retrieval order and search still works.',
    how: 'Send short product blurbs + preferences to Groq or Gemini; it returns a ranked list of up to 10 indices. Remaining slots fill from the retrieval list.',
    before: 'Top 20 from the fit step + “wants black breathable running shoes under $80”',
    after: [
      '10 products, possibly reordered',
      '— or the same 10 in retrieval order (bypass)',
    ].join('\n'),
    techNote: 'Optional in practice, not optional in the code path: we always call it, then no-op on failure. Helps MRR when it works.',
  },
  {
    id: 'ask',
    group: 'merge',
    label: 'Pick the next question',
    short: 'Attribute select',
    story: 'We choose one attribute to ask about next so the following turn can add a tag and shrink the list. This is a separate decision from re-ranking.',
    how: 'If an API key works, we ask the model which unasked attribute best splits the current pool. If that fails, we use a fixed priority list (feature first, then material, color, …).',
    before: '~50 candidates + tags we already have + attributes already asked',
    after: 'ask_attribute → e.g. size  (source: LLM or heuristic)',
    techNote: 'Different LLM call from re-rank. Heuristic fallback is feature-first — not “always category on turn 1.”',
  },
  {
    id: 'output',
    group: 'merge',
    label: 'Show 10 and reply',
    short: 'Display',
    story: 'We put the top 10 on the right and send a short chat line with the follow-up question. The sentence is a template, not written by the re-ranker.',
    how: 'Render the 10 products. Chat text is “Based on your preferences, I’d recommend: {title}.” plus a canned question for the chosen attribute.',
    before: 'Ordered ASINs + ask_attribute',
    after: [
      '10 product cards',
      'Agent: “Based on your preferences…” + “What size do you need?”',
    ].join('\n'),
    techNote: 'Card “scores” in the demo are display ranks, not BM25 scores. Fewer turns = better efficiency (MTTC).',
  },
]

/** Optional Dense → RRF branch: parallel to BM25, query built from full tags. */
export const DENSE_LAYERS = [
  {
    id: 'dense',
    label: 'Second opinion by meaning',
    short: 'Dense retrieval',
    optional: true,
    story: 'Alongside keyword search we can embed a sentence built from the full tags — not from the shortened BM25 string — and find products that “mean” the same thing. Off unless ENABLE_DENSE=1. Keywords already score better on this catalog.',
    how: 'Turn full tags into a sentence (“looking for … made of … in …”), embed it, nearest neighbors in vector space. Skipped when two or more specific (non-budget, non-pipe) tags already exist.',
    before: '“looking for Men\'s Running Shoes made of breathable mesh in black”',
    after: '~50 products that feel semantically close (only if this path is on)',
    techNote: 'MiniLM + FAISS. Evaluated; 0.850 vs BM25 0.853. Near-synonym noise (cotton ≈ polyester).',
  },
  {
    id: 'rrf',
    label: 'Blend the two ranked lists',
    short: 'RRF merge',
    optional: true,
    story: 'When both paths run, we merge their rankings into one candidate list, then that list plus the full tags go into soft rank. Keyword positions get more weight.',
    how: 'Reciprocal rank fusion: products high on either list stay high.',
    before: 'List A: BM25 ranking\nList B: dense ranking',
    after: 'One merged list → “Prefer products that fit the tags”',
    techNote: 'α≈0.75 BM25 / 0.25 dense. If dense is off or skipped, this merge does not run — BM25 list goes straight to soft rank.',
  },
]

export function denseStatusLabel({ denseAvailable, denseUsed, hasPipeline }) {
  if (!denseAvailable) return 'not enabled'
  if (!hasPipeline) return 'available'
  if (denseUsed) return 'used this turn'
  return 'skipped this turn'
}

export function llmBypassLabel({ hasPipeline, used }) {
  if (!hasPipeline) return 'bypass if no key'
  if (used) return 'used this turn'
  return 'bypassed this turn'
}

export function liveChipForLayer(layerId, pipeline) {
  if (!pipeline) return null
  const funnel = pipeline.funnel || {}
  switch (layerId) {
    case 'extract': {
      const n = Object.keys(pipeline.new_constraints || {}).length
      if (pipeline.intent_override) {
        return n ? `override · +${n} tags` : 'override flushed'
      }
      return n ? `+${n} tags this turn` : null
    }
    case 'query':
      return pipeline.query ? `“${pipeline.query}”` : null
    case 'tags': {
      const n = Object.keys(pipeline.constraints || {}).length
      return n ? `${n} tags kept in full` : null
    }
    case 'bm25':
      return pipeline.bm25_hits != null
        ? `${Number(pipeline.bm25_hits).toLocaleString()} matches`
        : null
    case 'dense':
      return denseStatusLabel({
        denseAvailable: true,
        denseUsed: pipeline.dense_used,
        hasPipeline: true,
      })
    case 'rrf':
      return pipeline.dense_used ? 'lists blended' : null
    case 'soft':
      return pipeline.soft
        ? `${pipeline.soft.full_match ?? 0} full fits → ${funnel.soft ?? '—'} kept`
        : null
    case 'llm': {
      if (pipeline.llm?.used) {
        const m = (pipeline.llm.moved_up || []).length
        return m ? `${m} moved up` : 'AI reordered'
      }
      return 'kept search order'
    }
    case 'ask': {
      const attr = pipeline.ask?.attribute
      if (!attr) return null
      const src = pipeline.ask?.source === 'llm' ? 'LLM' : 'heuristic'
      return `ask ${attr} (${src})`
    }
    case 'output':
      return funnel.shown != null ? `show ${funnel.shown}` : null
    default:
      return null
  }
}
