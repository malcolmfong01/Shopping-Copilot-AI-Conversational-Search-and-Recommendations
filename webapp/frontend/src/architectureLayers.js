/**
 * One continuous walkthrough (Men's Running Shoes) for Architecture mode.
 * Each layer shows Before → How → After in plain English; techNote is a footnote.
 */

export const WALKTHROUGH =
  "Same example as Product → Try Example: shopping for men's running shoes."

export const MAIN_LAYERS = [
  {
    id: 'input',
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
    label: 'Understand the request',
    short: 'Constraint extract',
    story: 'We read the sentence and turn it into simple shopping tags — product type, must-have feature, later color, budget, and so on. Later messages add more tags instead of starting over.',
    how: 'We look for known phrase patterns (“looking for…”, “key requirement is…”, “what matters is…”) and map each answer to a tag name.',
    before: "I'm looking for Men's Running Shoes. A key requirement is: breathable mesh upper.",
    after: [
      'category → Men\'s Running Shoes',
      'must-have → breathable mesh upper',
      '',
      'Later turn adds:',
      'color → black',
      'budget → under $80',
    ].join('\n'),
    techNote: 'Stored as structured constraints. Multiple features can stack (e.g. mesh|Nike). Saying “actually…” can clear old tags and start a new direction.',
  },
  {
    id: 'query',
    label: 'Turn tags into search words',
    short: 'Build query',
    story: 'Tags become a short keyword string we can search with. Money/budget stays out of this string — it is checked later when we look at prices.',
    how: 'We drop label prefixes (“color:”), skip budget, and keep the useful words from each tag.',
    before: [
      'category: Men\'s Running Shoes',
      'must-have: breathable mesh upper',
      'color: black',
      'budget: under $80  ← not used here',
    ].join('\n'),
    after: 'Running Shoes breathable mesh upper black',
    techNote: 'Long category names keep the last two words (e.g. “Running Shoes”).',
  },
  {
    id: 'bm25',
    label: 'Find keyword matches',
    short: 'BM25 search',
    story: 'We search the whole catalog for products whose title and details contain those words. Stronger title matches rank higher. The catalog shrinks from tens of thousands to a few hundred candidates.',
    how: 'Every product is scored by how well its text matches the search words — like a smarter Ctrl+F across 50,000 items.',
    before: 'Search words: Running Shoes breathable mesh upper black\nCatalog size: ~50,000 products',
    after: '~200 products that look textually relevant (still too many to show)',
    techNote: 'BM25 via SQLite FTS5, weighted columns (title highest). Depth k=200. This step alone is most of our score gain (~8× baseline).',
  },
  {
    id: 'soft',
    label: 'Prefer products that fit the tags',
    short: 'Soft constraint rank',
    story: 'Of those ~200, we check each tag: does this shoe mention breathable mesh? Is it black? Is price under $80? Products that match more tags rise. Near-misses stay in the pool instead of being thrown away for missing one detail.',
    how: 'Score = fraction of your tags the product satisfies. Sort by that score; keep about 50.',
    before: [
      '~200 keyword matches',
      'Tags to check: shoes · breathable mesh · black · under $80',
    ].join('\n'),
    after: [
      '~50 candidates',
      'Best: match most/all tags',
      'Next: match some tags (still useful)',
    ].join('\n'),
    techNote: 'Soft ranking (not a hard filter). Experimentally a large lift vs discarding any miss.',
  },
  {
    id: 'llm',
    label: 'AI picks the best order',
    short: 'LLM re-rank',
    story: 'We show the AI the top 20 candidates and the shopper’s preferences, and ask it to put the best matches first. If no AI key is set, we keep the previous order — search still works.',
    how: 'Send short product blurbs + preferences to the model; it returns a ranked list of up to 10.',
    before: 'Top 20 from the fit step + “wants black breathable running shoes under $80”',
    after: [
      'Best 10 products, reordered for the shopper',
      '— or same order if AI unavailable (fallback)',
    ].join('\n'),
    techNote: 'Groq / Gemini when configured. Improves “was the right item near #1?” (MRR).',
  },
  {
    id: 'output',
    label: 'Show picks & ask what’s next',
    short: 'Ask + output',
    story: 'We show the top 10 and ask one smart follow-up (size, material, brand…) so the next turn can shrink the list further — fewer back-and-forths to the right product.',
    how: 'Pick the attribute that best splits the remaining candidates, then write a short reply with the question.',
    before: 'Top 10 shoes + what we already know',
    after: [
      'Recommendations on the right',
      'Agent: “Based on your preferences…” + “What size do you need?”',
    ].join('\n'),
    techNote: 'Fewer turns = better efficiency score (MTTC). Attribute choice is heuristic or LLM.',
  },
]

/** Optional Dense → RRF branch (same walkthrough story). */
export const DENSE_LAYERS = [
  {
    id: 'dense',
    label: 'Second opinion by meaning',
    short: 'Dense retrieval',
    optional: true,
    story: 'Alongside keyword search, we can also find products that “mean” the same thing even if the exact words differ. Off by default in this demo — keywords already work best for this competition’s data.',
    how: 'Turn the request into a sentence embedding and find nearest products in vector space.',
    before: '“looking for Men\'s Running Shoes made of breathable mesh in black”',
    after: '~50 products that feel semantically close (when this path is turned on)',
    techNote: 'MiniLM + FAISS. Opt-in ENABLE_DENSE=1. Evaluated; does not beat BM25 here (near-synonym noise).',
  },
  {
    id: 'rrf',
    label: 'Blend the two ranked lists',
    short: 'RRF merge',
    optional: true,
    story: 'When both keyword search and meaning search run, we merge their rankings into one list before the “fit your tags” step. Keyword results get more weight.',
    how: 'Combine positions from both lists (products high on either list stay high).',
    before: 'List A: keyword ranking\nList B: meaning ranking',
    after: 'One merged ranking → then “Prefer products that fit the tags”',
    techNote: 'Reciprocal Rank Fusion, α≈0.75 keyword / 0.25 dense. Dense may be skipped when tags are already very specific.',
  },
]

export function denseStatusLabel({ denseAvailable, denseUsed, hasPipeline }) {
  if (!denseAvailable) return 'not enabled'
  if (!hasPipeline) return 'available'
  if (denseUsed) return 'used this turn'
  return 'skipped this turn'
}

export function liveChipForLayer(layerId, pipeline) {
  if (!pipeline) return null
  const funnel = pipeline.funnel || {}
  switch (layerId) {
    case 'extract': {
      const n = Object.keys(pipeline.new_constraints || {}).length
      return n ? `+${n} tags this turn` : null
    }
    case 'query':
      return pipeline.query ? `“${pipeline.query}”` : null
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
    case 'output':
      return pipeline.ask?.attribute ? `next ask: ${pipeline.ask.attribute}` : null
    default:
      return null
  }
}
