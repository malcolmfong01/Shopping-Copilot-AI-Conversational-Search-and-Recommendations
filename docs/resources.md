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

## Strategic Insights

### 1. The baseline's critical weakness is not asking questions

The BM25 starter always sets `ask_attribute: null`, so the simulator never reveals constraints. Simply asking the right attribute each turn will massively outperform it.

### 2. Attribute selection strategy is the highest-leverage decision

Each turn you can only ask ONE attribute. Choosing the most discriminating attribute (the one that most narrows the candidate set) is key to efficiency (MTTC).

### 3. Hit Rate dominates the score (50% weight)

Getting the right product into top-10 at all matters more than ranking it #1 (MRR at 30%) or getting there fast (efficiency at 20%). Optimize for recall first.

### 4. The 10-turn limit creates strategic pressure

With max 10 turns and MTTC penalizing slow convergence, the agent must balance:
- Asking enough questions to narrow the field (reduces candidate pool)
- Not asking too many questions before recommending (wastes turns)

### 5. Intent override is the hardest scenario

At turn 3-4, the user completely changes what they want. The agent must:
- Detect the shift (new constraints don't match old ones)
- Flush accumulated state
- Re-start retrieval with new intent

### 6. Order of recommendations matters

MRR scores 1/rank — putting the target at position 1 gives MRR=1.0 vs position 10 giving MRR=0.1. The LLM re-ranking stage should push the most likely match to the top.

### 7. Only first 10 unique valid ASINs are scored

Even though you can send up to 100 recommendations, only the first 10 unique ones in the catalog count. Don't waste those slots on invalid ASINs or duplicates.

### 8. User profile is available but the baseline ignores it

The `user_profile` contains `preference_tags` and `summary` that can inform initial retrieval before any questions are asked. This is free signal.
