# Retrieval Pipeline — Remaining Tasks

## Current Score: 0.853 (BM25-only, no LLM) — CONFIRMED full eval

---

## 1. Dense Retrieval — DONE (ship BM25-only)

Ran on Apple Silicon (arm64). Dense hybrid was validated, tuned, and Phase-2 query-fixed; it still trails BM25.

| Stage | Mini eval (20) `recommended_technical_score` |
|---|---|
| Initial hybrid (untuned) | **0.839** |
| Tuned fusion (K=10, α=0.75/0.25, depth=50, conditional skip) | **0.848** |
| Phase 2 + `build_dense_query()` (NL constraints, full category) | **0.850** |
| BM25-only baseline | **0.853** |

**Decision: ship BM25-only for scoring.** Hybrid never cleared 0.853. Dense stays wired (activates only if `data/embeddings/minilm.npy` exists — gitignored) so the architecture can be explained; competition / Yanyox baseline runs without embeddings → BM25-only.

### Why dense does not help (full issue list)

**A. Fusion mechanics (partially mitigated, still hurt on mini eval)**
1. **RRF K too large (was 60):** rank scores flatten; dense’s wrong mid/tail ranks dilute BM25’s correct top order.
2. **Equal BM25/dense weight (was 1.0/1.0):** weaker dense signal had the same vote as strong BM25.
3. **Dense fetch too deep (was 200):** long tail of semantically “nearby but wrong” ASINs entered fusion.
4. **Asymmetric candidate pools:** BM25 uses `retrieval_k = top_k * 4` (200); dense was capped at 50 after tuning — fusion still mixes incompatible rank lists.
5. **Conditional skip is a blunt gate:** dense is disabled only when ≥2 *specific* (non-budget, non-pipe) constraints exist. Early turns and pipe-accumulated features still fuse dense noise; late multi-constraint turns (where BM25 is already strong) skip the only cases where a better dense model might help.

**B. Query ↔ document embedding mismatch**
6. **BM25 query is keyword fragments:** `build_query()` keeps last 2 category words and only the last `|`-part of multi-value constraints — tuned for FTS, hostile to sentence encoders.
7. **Phase 2 NL query still mismatched:** `build_dense_query()` builds phrases like “looking for X made of Y”, but catalog vectors were trained/encoded as a bag of fields, not those templates — template words are out-of-distribution vs doc side.
8. **Empty/weak constraint turns:** with no constraints, dense falls back to raw user utterance (often evaluator boilerplate), which embeds poorly against product text.

**C. Catalog embedding is an impoverished document view vs BM25**
9. **Missing fields in `precompute.build_searchable_text`:** embeddings use title + categories + `features[:5]` + store only. BM25 FTS indexes **details + full features + description** with column weights — dense never sees a large fraction of the signal BM25 uses.
10. **No price/budget in embeddings:** budget constraints cannot influence dense similarity at all; only post-hoc soft_rank can.
11. **General-purpose MiniLM-L6-v2:** 384-d web/NLI model, not e-commerce / product-title trained; weak on SKU-level near-duplicates.
12. **IndexFlatIP / cosine only:** no lexical prior, no attribute filters inside FAISS — pure semantic neighbors in a catalog full of near-clones.

**D. Pipeline stage interactions**
13. **`_soft_rank` runs after fusion:** soft constraint reordering was tuned on BM25 order; it can erase whatever ranking benefit dense contributed.
14. **Same soft_rank / attribute heuristics for both paths:** remaining public-set misses are largely “ultra-generic constraints matching 40+ products” (`docs/experiments.md`) — dense cosine cannot disambiguate those clones either; need LLM re-ranker (Yanyox).
15. **Buying vs browsing asymmetry (mini eval):** buying Hit@10 stayed at 0.875 while browsing hit 1.0 — hybrid regression concentrated where precise lexical match matters more than semantics.

**E. Evaluation / ops caveats**
16. **Mini eval n=20 is noisy:** ~0.003–0.014 gaps; enough to decide “doesn’t beat 0.853”, not enough to fine-tune fusion blindly.
17. **Activation footgun:** if someone precomputes embeddings locally, Agent auto-enables dense and can silently regress below the shipped BM25 baseline.

### Fixes tried (kept in code for architecture writeup)
- RRF K: 60 → 10; alpha 0.75 BM25 / 0.25 dense; dense depth 200 → 50
- Conditional fusion: skip dense when ≥2 specific constraints; try/except → BM25-only
- Phase 2: `build_dense_query()` in `src/retrieval/hybrid.py` (NL constraints, full category, all `|` values)

---

## 2. Full Eval With Best Pipeline — DONE

BM25-only full 200-session eval on Apple Silicon:

| Metric | Score |
|---|---|
| `recommended_technical_score` | **0.853** |
| Hit@10 | 0.97 |
| MRR | 0.673 |
| MTTC | 2.68 |
| Efficiency | 0.832 |

This is the baseline Yanyox builds on top of.

---

## 3. Support Yanyox + Demo

- Help test LLM re-ranker against the BM25-only retrieval pipeline
- Demo video: record a conversational walkthrough showing edge cases (preference shifts, multi-turn narrowing)
- **Demo is 10% of the grade — don't skip it**
