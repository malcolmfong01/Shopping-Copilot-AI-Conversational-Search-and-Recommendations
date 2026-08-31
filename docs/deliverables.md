# Deliverables, Rules & Judging — TechJam 2026 Track 4

Deadline: **1 September 2026**.

---

## Rules & Constraints

| Constraint | Detail |
|-----------|--------|
| Max turns | 10 per session (forced termination if exceeded) |
| Catalog | Read-only, no mutations or mock ASINs |
| LLM | No keys provided; teams supply their own. A paid LLM is NOT required. |
| Execution | In-memory only; no external vector DB clusters |
| Input | Pre-cleaned text only (no images, audio, typos) |
| Sessions | Isolated single-user (no concurrency) |

### Scoring

```
technical_score = 0.50 * hit_rate@10 + 0.30 * MRR + 0.20 * efficiency
efficiency = clip((11 - MTTC) / 10, 0, 1)
```

| Metric | Weight | What it rewards |
|--------|--------|-----------------|
| Hit Rate@10 | 50% | Finding the target product in top-10 at all |
| MRR | 30% | Ranking the target higher (1/rank) |
| Efficiency (MTTC) | 20% | Finding it in fewer turns |

- 200 public sessions for development (separate users/products from private)
- **800 private sessions for final ranking** (different products)

### On "Hybrid Retrieval"

The problem statement says "combining keyword, category, and vector similarity." Our pipeline:
- **Keyword**: BM25 via SQLite FTS5
- **Category/Structured**: Soft constraint scoring on material, color, budget, category
- **Semantic**: LLM re-ranking (strictly more powerful than a 384-dim vector embedding)

Dense vector retrieval (MiniLM + FAISS) is implemented but opt-in (`ENABLE_DENSE=1`). It was thoroughly evaluated and does not improve BM25 for this evaluator's constraint pattern. See [experiments.md](experiments.md) for analysis.

---

## Deliverables

### 1. Written Project Description (via Devpost)

- How your solution addresses the problem statement
- Development tools used (e.g. VSCode, Colab, Jupyter)
- APIs used (e.g. OpenAI GPT-4o, Google Maps API)
- Libraries and frameworks used (e.g. Hugging Face Transformers, PyTorch, scikit-learn, pandas)
- Datasets and assets used

### 2. Public Code/GitHub Repository

- Well-structured, commented code covering all components
- README with:
  - Project overview
  - Setup and installation instructions
  - Steps to reproduce results
  - Reflection on limitations and what you'd improve given more time
  - Team member contributions (if applicable)

### 3. Demo Video

- Demonstrates solution working end-to-end (inference results, API usage, or result analysis)
- Uploaded to YouTube (public visibility)
- Linked in Devpost description
- No third-party trademarks or copyrighted content without permission

**Note**: If a front-end interface is not applicable, a walkthrough video showing API usage, inference examples, or result analysis is accepted.

---

## Judging Criteria

| Category | Weight | What reviewers look for |
|----------|--------|------------------------|
| **Technical Execution** | 35% | Strong engineering fundamentals, well-structured code, thoughtful architecture, effective use of APIs/models. Demo runs reliably. Technical complexity reflects deliberate, capable decision-making. |
| **Innovation & Problem Insight** | 20% | Originality in idea and approach. Sharpness of problem understanding — how clearly the team framed the challenge, why it matters, and how directly the solution addresses it. |
| **Impact & Relevance** | 20% | Clear potential to deliver value to real users/stakeholders. Meaningful reach, tangible benefit, relevance beyond solving for the hackathon prompt alone. |
| **Feasibility & Practicality** | 15% | Realistic and buildable beyond a prototype. Technically and operationally sustainable. Resource usage proportionate, architecture holds under real-world conditions, grounded rather than speculative. |
| **Presentation & Communication** | 10% | [Final Event Only] Coherent story from problem to solution to potential. Able to respond to questions with depth, demonstrating genuine understanding. |

---

## Submission Checklist

- [ ] Final score validated on full 200-session eval
- [ ] LLM re-ranking integrated and tested
- [ ] Demo video recorded and uploaded to YouTube
- [ ] Devpost submission with project description
- [ ] Code pushed to public GitHub repo
- [ ] README updated with final scores and reproduction steps
