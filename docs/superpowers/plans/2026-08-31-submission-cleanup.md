# Submission Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `yanyox-llm-ranking` submission-ready by applying clean-code hygiene with zero ranking/LLM behavior changes, then replace internal/WIP docs with a tight judge-facing doc set.

**Architecture:** Treat hygiene and docs as two sequential layers. Layer 1 only touches presentation (imports, docstrings, debug plumbing, ownership banners, whitespace) while preserving prompts, sort keys, model IDs, provider order, fallbacks, and return shapes. Layer 2 deletes teammate task notes, folds any still-useful dense-retrieval analysis into `docs/experiments.md`, and rewrites `README.md` plus cross-links so judges get overview → reproduce → limits without reading private WIP.

**Tech Stack:** Python 3.11+/uv, pytest (`uv sync --extra dev`), Markdown docs, existing Groq/Gemini client and BM25 + soft-rank + LLM re-rank pipeline.

**Spec:** Branch review of `yanyox-llm-ranking` vs `origin/main` (8 commits, core delta in `src/llm_client.py`, `src/ranking/llm_ranker.py`, `src/agent.py`, encoding fixes, `tests/test_rank_candidates.py`) plus submission requirements in `docs/deliverables.md`.

## Global Constraints

- **No logic changes:** do not alter ranking algorithms, prompt text, model names, `reasoning_effort` defaults, provider preference order (`GROQ_API_KEY` before `GOOGLE_API_KEY`), fallback ordering, constraint scoring math, agent response schema, or evaluator behavior.
- **Allowed hygiene:** import placement, docstring/comment wording, ownership banners, whitespace, consolidating identical `DEBUG_LLM` print gates behind one helper with the same messages/gates, type annotation polish that does not change runtime, dead wording removal.
- **Docs must stay honest:** published scores must match measured results. BM25-only full-eval composite is **0.853**. Do not invent a full-eval LLM score; if only mini-eval LLM numbers exist, label them as mini-eval (n=20) and keep BM25 0.853 as the validated spine.
- **Secrets stay out of git:** never commit `.env`, API keys, or `results/*.log` (already gitignored via `results/`).
- **Frequent commits:** one commit per completed task below.
- **Verify after code tasks:** `uv sync --extra dev && uv run pytest tests/ -q` must pass with the same outcomes as before the edit.

---

## File Structure

| Path | Responsibility after cleanup |
|------|------------------------------|
| `src/llm_client.py` | Provider client + shared `DEBUG_LLM` helper; accurate module docstring |
| `src/ranking/llm_ranker.py` | LLM re-rank + template messages; no ownership banner; debug via shared helper |
| `src/dialog/attribute_selector.py` | Attribute selection; no ownership banner (behavior untouched) |
| `src/agent.py` | Agent orchestration; top-level imports only (behavior untouched) |
| `README.md` | Single judge entrypoint: scores, architecture, setup, structure, team, limits, doc index |
| `docs/experiments.md` | Optimization log including dense failure summary + LLM ranking status |
| `docs/deliverables.md` | Rules/scoring/checklist; no links into deleted `tasks/` |
| `docs/evaluation.md` | How to run eval; current known scores; optional LLM env notes |
| `docs/demo-script.md` | Keep (demo video aid) |
| `docs/problem-statement.md` | Keep (challenge source) |
| `docs/data-guide.md` | Keep |
| `docs/agent-api-contract.md` | Keep |
| `docs/resources.md` | Slim official links only |
| `tasks/malcolm.md` | **Delete** after folding dense summary into experiments |
| `tasks/yanyox.md` | **Delete** (outdated internal onboarding; claims ranker is pass-through) |
| `docs/superpowers/plans/*` | Keep as agent working notes; do not link from README (not judge-facing) |

Out of scope for this plan: rewriting ranking prompts for score gains, enabling dense by default, recording the demo video, Devpost copy, pushing/merging PRs.

---

### Task 1: Freeze regression baseline (tests)

**Files:**
- Test (run only): `tests/test_rank_candidates.py`, `tests/test_pipeline_trace.py`
- No source edits in this task

**Interfaces:**
- Consumes: existing test suite
- Produces: confirmed green baseline before hygiene edits

- [ ] **Step 1: Install test deps and run the full unit suite**

Run:

```bash
uv sync --extra dev
uv run pytest tests/ -q
```

Expected: PASS (all tests in `tests/`). Note the count (currently 2 test modules).

- [ ] **Step 2: Record baseline commit SHA and dirty status**

Run:

```bash
git status -sb
git rev-parse --short HEAD
```

Expected: clean tree on `yanyox-llm-ranking` (or only this plan file untracked/committed). If unrelated dirty files exist, stop and ask the user before continuing.

- [ ] **Step 3: Commit the plan file if not already committed**

```bash
git add docs/superpowers/plans/2026-08-31-submission-cleanup.md
git commit -m "$(cat <<'EOF'
docs: add submission cleanup implementation plan

EOF
)"
```

---

### Task 2: LLM client hygiene (no behavior change)

**Files:**
- Modify: `src/llm_client.py`
- Test: `tests/test_rank_candidates.py` (indirect; suite must stay green)

**Interfaces:**
- Consumes: existing `llm_call(prompt: str, max_tokens: int = 200, temperature: float = 0.0) -> str | None`, `last_usage`, `_debug`
- Produces: same public API; module docstring must state **Groq first, Gemini second** (matches runtime `if groq_key` / `elif google_key`)

- [ ] **Step 1: Write a failing docstring/consistency note as a comment test is unnecessary — instead add a tiny regression assertion that provider preference is Groq-first when both keys exist**

Add to `tests/test_rank_candidates.py` **or** create `tests/test_llm_client.py` with:

```python
import src.llm_client as llm_client


def test_llm_call_prefers_groq_when_both_keys_set(monkeypatch):
    calls = []

    def fake_groq(prompt, max_tokens, temperature, api_key):
        calls.append(("groq", api_key))
        return "ok"

    def fake_gemini(prompt, max_tokens, temperature, api_key):
        calls.append(("gemini", api_key))
        return "gemini"

    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("GOOGLE_API_KEY", "google_test")
    monkeypatch.setattr(llm_client, "_groq_call", fake_groq)
    monkeypatch.setattr(llm_client, "_gemini_call", fake_gemini)

    assert llm_client.llm_call("hello") == "ok"
    assert calls == [("groq", "gsk_test")]
```

- [ ] **Step 2: Run the new test (should PASS already — this locks preference before docstring edits)**

Run: `uv run pytest tests/test_llm_client.py::test_llm_call_prefers_groq_when_both_keys_set -v`

Expected: PASS (documents current logic; do not change provider order).

- [ ] **Step 3: Fix module docstring only**

Replace the top docstring in `src/llm_client.py` with:

```python
"""Provider-agnostic LLM client. Supports Groq and Google Gemini.

Usage:
    from src.llm_client import llm_call

    response = llm_call("Your prompt here", max_tokens=200)

Set one of these environment variables (checked in this order):
    GROQ_API_KEY=gsk_...       (Groq — preferred when set)
    GOOGLE_API_KEY=...         (Google Gemini — used if Groq key is absent)

If neither is set, returns None (callers fall back to heuristics).

Optional:
    DEBUG_LLM=1                (print provider call diagnostics)
    GROQ_REASONING_EFFORT=...  (low|medium|high; default medium)
"""
```

Do not change `_debug`, `_groq_call`, `_gemini_call`, model strings, or exception handling.

- [ ] **Step 4: Re-run preference test + full suite**

Run: `uv run pytest tests/ -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/llm_client.py tests/test_llm_client.py
git commit -m "$(cat <<'EOF'
docs: align llm_client docstring with Groq-first provider order

EOF
)"
```

---

### Task 3: Ranker / attribute module hygiene (no behavior change)

**Files:**
- Modify: `src/ranking/llm_ranker.py`
- Modify: `src/dialog/attribute_selector.py` (module docstring only)
- Modify: `src/agent.py` (import placement only)
- Test: `tests/test_rank_candidates.py`, `tests/test_pipeline_trace.py`

**Interfaces:**
- Consumes: `llm_call`, `SessionState`, existing `rank_candidates` / `generate_message` / `select_attribute`
- Produces: identical return values for identical inputs; debug output still gated on `DEBUG_LLM=1`

- [ ] **Step 1: Write failing test that debug helper is used — skip unit-testing prints; instead lock fallback order with the existing test**

Run existing fallback test first:

```bash
uv run pytest tests/test_rank_candidates.py::test_rank_candidates_prefers_exact_constraint_matches_when_llm_fails -v
```

Expected: PASS before edits.

- [ ] **Step 2: Apply hygiene edits to `src/ranking/llm_ranker.py`**

Exact allowed edits:

1. Replace module docstring with:

```python
"""LLM-based candidate re-ranking and reply templates.

rank_candidates() sends the top candidates plus session context to the LLM
and returns ordered parent_asins (best first, max 10). Falls back to
constraint-match order when the LLM is unavailable or returns invalid JSON.

generate_message() builds a short template reply (cosmetic; not scored).
"""
```

2. Import the existing debug helper instead of duplicating `print` gates:

```python
from src.llm_client import llm_call, _debug
```

3. Replace every `if os.environ.get("DEBUG_LLM") == "1": print(...)` block with equivalent `_debug(...)` calls using the **same message text** (including the `### ` prefix already added inside `_debug`). Example:

```python
_debug(f"rank_candidates CALLED: candidates={len(candidates)}")
```

Because `_debug` already prefixes `### `, strip the duplicated `### ` from the message strings when moving them.

4. Remove trailing whitespace on blank lines inside `rank_candidates` (lines that are spaces-only today).

5. Keep the prompt string, `max_tokens=600`, sort key, `_constraint_match_score`, and fallback path **byte-for-byte identical** aside from whitespace/debug call sites.

6. `os` may still be needed only if something else uses it; if the only uses were `DEBUG_LLM` checks, remove the unused `import os` after switching to `_debug`.

- [ ] **Step 3: Strip ownership banner from attribute selector**

In `src/dialog/attribute_selector.py`, change the first line of the module docstring from ownership wording to a neutral description. Do not edit any functions.

Example:

```python
"""Attribute selection for the next clarifying question.

select_attribute() chooses the most discriminating unasked attribute given
candidate value distributions. Uses an LLM helper when available, otherwise
heuristics.
"""
```

(Keep the rest of the existing docstring body if it already describes the API; only remove `OWNED BY YANYOX` and rewrite the opening so it reads as product docs.)

- [ ] **Step 4: Move `import os` to module top in `src/agent.py`**

Change:

```python
import json
import re
from pathlib import Path
```

to:

```python
import json
import os
import re
from pathlib import Path
```

And delete the inline `import os` inside `__init__`. Leave every other line untouched.

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/ -q`

Expected: PASS. Manually sanity-check that `DEBUG_LLM=1` still prints when calling `rank_candidates` with a monkeypatched `llm_call` if you want; optional.

- [ ] **Step 6: Commit**

```bash
git add src/ranking/llm_ranker.py src/dialog/attribute_selector.py src/agent.py
git commit -m "$(cat <<'EOF'
refactor: clean LLM ranking module presentation without behavior changes

EOF
)"
```

---

### Task 4: Fold useful `tasks/` content into experiments, then delete `tasks/`

**Files:**
- Modify: `docs/experiments.md`
- Delete: `tasks/malcolm.md`
- Delete: `tasks/yanyox.md`
- Modify: any remaining links (handled fully in Task 5 if missed)

**Interfaces:**
- Consumes: dense failure summary currently only in `tasks/malcolm.md`
- Produces: self-contained `docs/experiments.md` so deleting `tasks/` loses no judge-facing insight

- [ ] **Step 1: Append two sections to `docs/experiments.md` after experiment 11 / before or replacing “Remaining 6 Misses”**

Add (adapt wording; keep numbers exact):

```markdown
### 12. LLM Re-ranking (Groq)

- Module: `src/ranking/llm_ranker.py` via `src/llm_client.py`
- Model path: Groq when `GROQ_API_KEY` is set (preferred); Gemini when only `GOOGLE_API_KEY` is set
- Behavior: re-rank top-20 → top-10 JSON indices; on failure, constraint-match fallback (exact matches first)
- Debug: `DEBUG_LLM=1`
- **Validated spine remains BM25 + soft-rank at 0.853** on the full 200-session public eval without requiring an LLM key
- Mini-eval with LLM (n=20), when measured locally, must be labeled separately and must not overwrite the 0.853 full-eval claim unless a new full 200-session run is recorded

### Dense retrieval — why it stays opt-in

Ship BM25-only for scoring (`ENABLE_DENSE` unset). MiniLM + FAISS hybrid peaked at **0.850** vs BM25 **0.853** on mini-eval after tuning (RRF K=10, α=0.75/0.25, depth=50, conditional skip).

Root causes (summary):
1. Evaluator constraints are literal substrings → BM25 is near-optimal by construction
2. Dense doc text omits details/description that FTS indexes
3. Keyword `build_query()` is hostile to sentence encoders
4. Soft-rank after fusion can erase dense ordering gains
5. Near-duplicate catalog items are not separable by 384-d cosine alone

Full narrative of reverted experiments remains in sections 6–9 above. Dense code stays for architecture explanation; do not enable for demos or scoring.
```

Also update the Summary table with row 12 and change the closing “Final score” blurb to:

```markdown
**Validated retrieval score (no LLM key): 0.853 (8.0× baseline)**

LLM re-ranking is integrated for optional MRR gains when an API key is present; treat full-eval LLM numbers as TBD until a 200-session run is checked into the narrative with a real `results/*.json` summary.
```

Rewrite the old “Solution needed: LLM re-ranker (Yanyox's task)” line so it no longer sounds like unfinished teammate homework — e.g. “LLM re-ranking addresses residual ambiguous near-duplicates.”

- [ ] **Step 2: Delete internal task specs**

```bash
git rm tasks/malcolm.md tasks/yanyox.md
rmdir tasks 2>/dev/null || true
```

- [ ] **Step 3: Grep for stale links**

Run:

```bash
rg -n 'tasks/malcolm|tasks/yanyox|OWNED BY|malcolm\.md|yanyox\.md' README.md docs/ src/ || true
```

Expected: hits only in files you will fix in Task 5 (or none).

- [ ] **Step 4: Commit**

```bash
git add docs/experiments.md
git add -u tasks
git commit -m "$(cat <<'EOF'
docs: fold task notes into experiments and remove internal specs

EOF
)"
```

---

### Task 5: Judge-facing README + docs index cleanup

**Files:**
- Modify: `README.md`
- Modify: `docs/deliverables.md`
- Modify: `docs/evaluation.md`
- Modify: `docs/resources.md`
- Keep unchanged content-wise unless links break: `docs/problem-statement.md`, `docs/data-guide.md`, `docs/agent-api-contract.md`, `docs/demo-script.md`

**Interfaces:**
- Consumes: scores and architecture from experiments / current code
- Produces: README that satisfies deliverables checklist items for overview, setup, reproduction, limitations, team

- [ ] **Step 1: Rewrite `README.md` Docs / Project Structure / Current Score sections**

Use this structure (fill tables exactly):

```markdown
# Shopping Copilot: AI Conversational Search and Recommendations

TikTok TechJam 2026 — Track 4

---

## Current Score

| Metric | Baseline | Current (BM25 + soft-rank, no LLM key) |
|--------|----------|----------------------------------------|
| Hit Rate@10 | 12.5% | **97%** |
| MRR | 0.068 | **0.673** |
| MTTC | 9.81 turns | **2.68 turns** |
| **Composite** | **0.107** | **0.853** |

Scoring: `0.50 * hit_rate@10 + 0.30 * MRR + 0.20 * efficiency`

LLM re-ranking is available when `GROQ_API_KEY` or `GOOGLE_API_KEY` is set. Quote a full 200-session LLM composite here only after measuring it; until then keep the BM25 spine as the published score.

---

## Architecture
(...keep existing ASCII pipeline; change the dense sentence to point at docs/experiments.md instead of tasks/malcolm.md...)

---

## Quick Start
(...keep prerequisites / eval / LLM / webapp blocks; fix LLM section to say Groq preferred, Gemini fallback...)

### LLM Features

```bash
uv sync --extra groq
export GROQ_API_KEY="gsk_..."
# optional fallback if Groq unset:
# uv sync --extra gemini && export GOOGLE_API_KEY="..."
```

---

## Project Structure
(...remove `tasks/` line from the tree...)

---

## Team
(...keep Malcolm / Yanyox table...)

---

## Limitations
(...keep three bullets; retarget dense analysis link to docs/experiments.md...)

---

## Docs

| Doc | Description |
|-----|-------------|
| [deliverables.md](docs/deliverables.md) | Rules, scoring, deliverables, judging, checklist |
| [experiments.md](docs/experiments.md) | Optimization log, dense opt-in rationale, LLM status |
| [evaluation.md](docs/evaluation.md) | Eval config and how to run |
| [data-guide.md](docs/data-guide.md) | Catalog/session schemas, simulator behavior |
| [problem-statement.md](docs/problem-statement.md) | Original challenge description |
| [agent-api-contract.md](docs/agent-api-contract.md) | Agent ↔ evaluator message contract |
| [demo-script.md](docs/demo-script.md) | 90–120s demo video outline |
| [resources.md](docs/resources.md) | Official competition links |
```
```

- [ ] **Step 2: Patch `docs/deliverables.md`**

Replace the dense analysis sentence that links to `tasks/malcolm.md` with a link to `experiments.md`. Leave scoring tables intact.

- [ ] **Step 3: Patch `docs/evaluation.md`**

After “Baseline Results”, add:

```markdown
## Current Validated Results (Public 200)

| Metric | Value |
|--------|-------|
| hit_rate@10 | 0.97 (97%) |
| mrr | 0.673 |
| mttc | 2.68 |
| **technical_score** | **0.853** |

These numbers are for the BM25 + soft-rank pipeline with LLM disabled/unavailable. To exercise LLM re-ranking during eval, export `GROQ_API_KEY` (or `GOOGLE_API_KEY`) before running the evaluator.
```

Also extend “Running the Evaluator” with mini-eval note only if a script flag already exists in-repo; do not invent CLI flags.

- [ ] **Step 4: Slim `docs/resources.md`**

Keep Official Links table. Remove or shorten past-webinar fluff if it reads like internal notes. Keep a one-line pointer to `experiments.md` for design history. Delete “Strategic Insights” padding that duplicates experiments.

- [ ] **Step 5: Link check**

Run:

```bash
rg -n 'tasks/|OWNED BY|0\.90\+|Llama 3\.3|malcolm\.md|yanyox\.md' README.md docs/
```

Expected: no `tasks/` references; no aspirational **0.90+** published as if measured; no ownership banners in docs.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/deliverables.md docs/evaluation.md docs/resources.md
git commit -m "$(cat <<'EOF'
docs: tighten README and judge-facing documentation for submission

EOF
)"
```

---

### Task 6: Final submission gate

**Files:**
- Verify only (no further edits unless gate fails)

**Interfaces:**
- Consumes: all prior tasks
- Produces: verified clean branch ready for human review / PR

- [ ] **Step 1: Re-run unit tests**

```bash
uv sync --extra dev
uv run pytest tests/ -q
```

Expected: PASS

- [ ] **Step 2: Confirm no logic drift in ranking prompt / sort**

```bash
git diff origin/main...HEAD -- src/ranking/llm_ranker.py | rg -n 'RANKING STRATEGY|constraint_match_score|openai/gpt-oss|max_tokens=600' || true
git status -sb
```

Expected: working tree clean; prompt/strategy strings still present (unchanged intent).

- [ ] **Step 3: Confirm deleted internal docs and live links**

```bash
test ! -e tasks/malcolm.md
test ! -e tasks/yanyox.md
rg -n '\]\(tasks/|\]\(\.\./tasks/' README.md docs/ || echo 'no tasks links'
ls docs/*.md
```

Expected: `tasks` specs gone; docs set is the eight judge-facing files listed in Task 5 (plus this plan under `docs/superpowers/` which is not linked).

- [ ] **Step 4: Optional commit only if gate required tiny link fixes**

If Step 3 found stale links, fix and commit:

```bash
git add -u
git commit -m "$(cat <<'EOF'
docs: fix leftover submission link targets

EOF
)"
```

Otherwise make no empty commit.

---

## Self-Review

1. **Spec coverage:** Branch hygiene (llm client, ranker, attribute banner, agent imports) → Tasks 2–3. Useless internal docs removal → Task 4. Judge README/docs → Task 5. Verification → Tasks 1 & 6. No ranking logic edits in any task.
2. **Placeholder scan:** No TBD implementation steps; score honesty explicitly constrained.
3. **Type consistency:** Public APIs remain `llm_call`, `rank_candidates`, `generate_message`, `select_attribute`, `Agent.respond`.

## Assumptions (surfaced)

- “Clean up without touching any logic” means presentation-only in Python; prompt text counts as logic and stays frozen.
- Deleting `tasks/` is desired for submission; dense analysis must survive inside `experiments.md`.
- Do not publish an LLM full-eval composite unless the user provides a measured 200-session result during execution.
- `docs/superpowers/plans/` may remain unlinked (agent process docs), not advertised in README.
