# Agent API Contract

The agent communicates with the evaluator via three message types.

## 1. Reset Request (start of session)

Sent once at the beginning of each session to initialize the agent's state.

```json
{
  "session_id": "<string, min length 1>",
  "user_profile": {
    "purchase_frequency": "<string>",
    "average_prior_rating": "<number | null>",
    "rating_style": "<string>",
    "preference_tags": ["<string>"],
    "summary": "<string>"
  }
}
```

The agent should use `user_profile` to personalize its strategy (e.g., a frequent buyer with high ratings may need less guidance).

## 2. Turn Request (each conversation turn)

Sent every turn with the user's message.

```json
{
  "session_id": "<string>",
  "user_message": "<string>",
  "turn": "<integer, 1-10>",
  "top_k": 10
}
```

- `turn` increments from 1 to 10 (hard limit)
- `top_k` is always 10 for scoring purposes

## 3. Turn Response (agent's reply)

What the agent must return each turn.

```json
{
  "message": "<string - conversational reply to the user>",
  "ask_attribute": "<string | null>",
  "recommendations": [
    {"parent_asin": "<string>", "score": "<number>"}
  ],
  "usage": {
    "prompt_tokens": "<integer >= 0>",
    "completion_tokens": "<integer >= 0>"
  }
}
```

### Field Details

#### `message`
A natural-language reply shown to the simulated user. Should be conversational — ask questions, acknowledge preferences, explain recommendations.

#### `ask_attribute`
Controls what the simulator reveals next. Must be one of:

| Value | What it asks about |
|-------|-------------------|
| `"category"` | Product category/type |
| `"material"` | Material/fabric |
| `"color"` | Color preference |
| `"size"` | Size requirement |
| `"style"` | Style/aesthetic |
| `"brand"` | Brand preference |
| `"budget"` | Price range |
| `"feature"` | Specific features |
| `"use_case"` | Intended use/occasion |
| `"other"` | Catch-all for other attributes |
| `null` | Don't ask (simulator responds with "Ask me about one specific attribute") |

**Critical**: Setting this to `null` wastes a turn. Always ask something.

#### `recommendations`
- Max 100 items can be sent
- Only the first 10 **unique valid ASINs** are scored
- Order matters for MRR (put highest-confidence items first)
- ASINs not in the catalog are silently dropped
- Duplicates are deduplicated (first occurrence kept)

#### `usage`
Report token consumption. Not scored but required for feasibility assessment.

## Agent Interface (Python)

The agent must implement:

```python
class Agent:
    def __init__(self, catalog_path: str):
        """Load catalog and initialize any indexes."""
        ...

    def reset(self, session_id: str, user_profile: dict):
        """Called at session start. Initialize session state."""
        ...

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        """Return a turn_response dict."""
        ...
```
