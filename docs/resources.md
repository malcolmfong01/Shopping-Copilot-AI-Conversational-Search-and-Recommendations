# Resources & Strategic Insights

## Official Links

| Resource | URL |
|----------|-----|
| Participant Repository | https://github.com/TechJam2026/techjam-conversational-search |
| Participant Kit Release (data download) | https://github.com/TechJam2026/techjam-conversational-search/releases/tag/participant-kit |
| Amazon Reviews 2023 (original source) | https://amazon-reviews-2023.github.io/ |
| Technical Workshop Webinar (28 Aug, 4:00-4:45pm SGT) | https://vc-my.larkoffice.com/j/484622806 |

## Competition Context

- **Event**: TikTok TechJam 2026
- **Track**: 4 of 5
- **Duration**: 3-day hackathon
- **Submission**: Via Devpost
- **Webinar**: 28 August 2026, 4:00-4:45pm SGT

---

## Key Design Insights (Learned During Development)

### Already implemented (retrieval pipeline)

| Insight | Status |
|---------|--------|
| Asking attributes each turn is critical (baseline never asks → 0.107) | Done — heuristic priority order |
| "feature" is the most discriminating attribute to ask early | Done — asked on turn 2 |
| Hard constraint filtering kills recall; soft scoring preserves it | Done — partial match scoring |
| Multiple values for same attribute need accumulation, not overwrite | Done — pipe-separated storage |
| Intent override requires flushing state while preserving category | Done — `flush_constraints()` |

### Remaining opportunities (LLM layer)

1. **MRR is the biggest remaining lever.** Current MRR=0.637 means the target lands around position 2-3 on average. LLM re-ranking to push it to #1 consistently would add ~0.05-0.10 to composite.
2. **Attribute selection can be smarter.** The heuristic priority order works well but an LLM analyzing candidate distributions could pick more optimal attributes per session.
3. **User profile is unused.** `preference_tags` and `summary` are available but currently ignored. Could inform re-ranking or initial retrieval.
4. **Only first 10 unique valid ASINs are scored.** Don't waste top-10 slots on low-confidence picks — better to be precise than pad the list.
