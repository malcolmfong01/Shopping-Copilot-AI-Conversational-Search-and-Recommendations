# Data Guide

## Catalog (`data/catalog.jsonl`)

50,000 products from Amazon Reviews 2023 — Clothing, Shoes & Jewelry category.

Each line is a JSON object with:

| Field | Type | Description |
|-------|------|-------------|
| `parent_asin` | string | Primary key (product identifier) |
| `title` | string | Product title |
| `categories` | list[string] | Category hierarchy |
| `features` | list or dict | Product features/bullet points |
| `details` | dict | Structured product details (material, dimensions, etc.) |
| `store` | string | Store/brand name |
| `description` | string or list | Full product description |
| `price` | number or null | Price in USD |

**Source**: Amazon Reviews 2023 (McAuley Lab, UCSD). Join key: `parent_asin`. Text + structured metadata only (no images/videos).

---

## Public Development Sessions (`data/public_set.jsonl`)

200 labeled sessions for local testing. Each line:

| Field | Type | Description |
|-------|------|-------------|
| `sample_id` | string | Unique session identifier |
| `scenario_type` | string | One of: `buying`, `browsing`, `intent_override`, `boundary` |
| `user_profile` | object | Simulated user's profile (see below) |
| `ground_truth` | object | `{"parent_asin": "<target product ASIN>"}` |

### User Profile Fields

| Field | Type | Description |
|-------|------|-------------|
| `purchase_frequency` | string | How often they buy (e.g., "frequent", "occasional") |
| `average_prior_rating` | number or null | Their typical rating behavior |
| `rating_style` | string | How they rate products |
| `preference_tags` | list[string] | General preference keywords |
| `summary` | string | Natural language profile summary |

---

## Scenario Distribution

| Scenario | Count | Behavior |
|----------|-------|----------|
| buying | 80 | Clear purchase intent, reveals constraints progressively |
| browsing | 80 | Open-ended exploration, vaguer preferences |
| intent_override | 30 | User changes mind at turn 3 or 4 — completely new target |
| boundary | 10 | Refuses first attribute question with "I don't have a preference" |

---

## How the Simulator Generates User Replies

The evaluator simulates the user. The flow:

1. **`intent_card(product)`** generates from the ground-truth product:
   - `target_category`: the product's category
   - `hard_constraints`: must-have attributes (derived from product metadata)
   - `soft_preferences`: nice-to-have attributes

2. **`initial_message(sample, category, disclosed)`** creates the opening user message based on scenario type

3. **Each turn**, the agent returns `ask_attribute`. The simulator then:
   - If `ask_attribute` is valid and matches an undisclosed constraint/preference → reveals it
   - If `ask_attribute` is valid but nothing left to reveal → generic response
   - If `ask_attribute` is `null` → "Ask me about one specific attribute"
   - If scenario is `boundary` and it's the first question → "I don't have a preference"
   - If scenario is `intent_override` and it's turn 3-4 → completely new intent revealed

4. **`customer_reply(sample, ask_attribute, disclosed, boundary_used)`** produces the actual text response

---

## Private Evaluation

- 800 additional sessions retained by the organizer
- Public and private evaluation sessions use **separate users and target products**
- Same scoring formula applied
- Final ranking determined by private set scores

---

## Data Integrity

A SHA256 checksum file is provided in the participant kit release for verifying the downloaded catalog.
