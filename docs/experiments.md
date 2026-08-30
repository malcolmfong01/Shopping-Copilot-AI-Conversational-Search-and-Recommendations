# Experiments Log

Score formula: `0.50 * hit_rate@10 + 0.30 * MRR + 0.20 * efficiency`
Baseline (no retrieval optimization): **0.107**

---

## Summary

| # | Experiment | Score | Delta | Kept? |
|---|-----------|-------|-------|-------|
| 1 | BM25 + FTS5 column weights | 0.714 | +0.607 | Yes |
| 2 | Attribute priority: feature first | 0.789 | +0.075 | Yes |
| 3 | Soft scoring (partial constraint match) | 0.820 | +0.031 | Yes |
| 4 | Pipe-separated constraint accumulation | 0.848 | +0.028 | Yes |
| 5 | Interleave high-BM25 partial matches | 0.853 | +0.005 | Yes |
| 6 | Title-token boost (replace BM25 order) | ~0.80 | -0.05 | **Reverted** |
| 7 | Wider retrieval (k=300) | ~0.81 | -0.04 | **Reverted** |
| 8 | Fixed near_threshold=0.5 | ~0.82 | -0.03 | **Reverted** |
| 9 | Dense retrieval (MiniLM-L6-v2 + RRF) | 0.850 | -0.003 | **Disabled** (opt-in) |
| 10 | Bug fixes: prefix strip, constraint key, full text match | 0.853 | +0.002 | Yes (keyword extract reverted) |
| 11 | Include description field in soft-rank text matching | 0.853 | ~0 | Yes |

**Final score: 0.853 (8.0x baseline)**

---

## Detailed Notes

### 1. BM25 + FTS5 Column Weights

- SQLite FTS5 with weighted columns (title, categories, features, store)
- Basic constraint extraction from evaluator response patterns
- Heuristic attribute selection (category first, then feature)
- Score: 0.714

### 2. Attribute Priority Reorder

- Moved "feature" to turn 2 (was category)
- Features like "waterproof", "RFID blocking" are highly discriminating for BM25
- Category still extracted from turn 1 message passively
- Score: 0.789 (+0.075)

### 3. Soft Scoring

- **Problem:** Hard constraint filter dropped products missing ANY constraint. One miss = excluded.
- **Fix:** Score products 0.0-1.0 by fraction of constraints matched. Sort by score. No hard exclusion unless 0.0.
- Dynamic `near_threshold` adapts to constraint count
- Products matching N-1 of N constraints rank highly instead of being discarded
- Score: 0.820 (+0.031)

### 4. Pipe-Separated Constraint Accumulation

- **Problem:** "For that, what matters is: Water Resistant; 3 Year Battery" — both classify as "feature". Only last one survived (overwrite).
- **Fix:** `accumulate=True` stores as `value1|value2`. Filter checks each part independently.
- Also fixed "What I need is:" (intent override) to accumulate instead of overwrite
- Score: 0.848 (+0.028)

### 5. Interleave High-BM25 Partial Matches

- Products ranking top-10 in BM25 that score >= near_threshold on constraints get inserted at positions 9-10
- Catches products that BM25 strongly favors but miss one constraint by a technicality
- Score: 0.853 (+0.005)

### 6. Title-Token Boost (REVERTED)

- Replaced BM25 ordering with title-token overlap scoring
- Title tokens are too sparse a signal — BM25 already weighs title highly
- Hurt score by ~0.05. Reverted.

### 7. Wider Retrieval k=300 (REVERTED)

- Increased initial BM25 retrieval from k=200 to k=300
- More candidates = more noise in the filtered set
- Hurt MRR. Reverted to k=200.

### 8. Fixed near_threshold=0.5 (REVERTED)

- Tried fixing near_threshold at 0.5 instead of dynamic `(N-1)/N`
- Dynamic threshold adapts better to varying constraint counts
- Reverted.

### 9. Dense Retrieval (EVALUATED — DISABLED)

- Model: sentence-transformers/all-MiniLM-L6-v2 (384-dim)
- FAISS IndexFlatIP for cosine similarity search
- Tuned: RRF K=10, α=0.75/0.25, depth=50, conditional skip
- Best mini-eval score: 0.850 (vs BM25-only 0.853)
- **Root cause:** evaluator generates literal substring constraints from product fields → BM25 is near-optimal by construction; dense confuses near-synonyms (cotton ≈ polyester)
- Code kept for architecture writeup. Opt-in via `ENABLE_DENSE=1`.
- Full analysis: 17 failure modes documented in `tasks/malcolm.md`

### 10. Bug Fixes (3 kept, 1 reverted)

- **Prefix stripping:** "color: black" → "black" in all extraction paths (was only stripped in "what matters is:" handler)
- **Constraint key check:** `n_constraints` counted budget values instead of checking budget key
- **Full text match:** `_matches_all()` uses `_full_searchable_text()` including details + description fields
- ~~**Keyword query extraction:** material/color constraints extract known keywords instead of raw accumulated text~~ — **REVERTED**: stripped useful BM25 terms (e.g. "heather" from "Heather Grey: 90% Cotton"), causing 0.853 → 0.828
- Mini-eval: 0.849 → 0.851 (+0.002, no regression on any scenario)

### 11. Description Field in Soft-Rank

- 26K/50K products have a `description` field. Evaluator generates constraints from it, but our soft-ranking was missing it.
- Added to `_full_searchable_text()` to match evaluator's `searchable_text()`.
- Mini-eval: no change on 20-session set (description-dependent products not in mini set). Protects against misses on the 800-session private eval.

---

## Remaining 6 Misses (Analysis)

All remaining misses are deep-BM25 failures with ultra-generic constraints:
- "polyester + Imported + Button closure" matches 40+ products
- Target product is indistinguishable from dozens of similar items via text alone
- **Solution needed:** LLM re-ranker (Yanyox's task) using semantic understanding of user intent
