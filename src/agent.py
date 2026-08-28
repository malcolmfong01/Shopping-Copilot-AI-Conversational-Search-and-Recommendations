import json
import re
from pathlib import Path

from src.dialog.attribute_selector import compute_candidate_stats, select_attribute
from src.dialog.intent_detector import detect_intent_override
from src.dialog.state import StateManager
from src.ranking.llm_ranker import generate_message, rank_candidates
from src.retrieval.bm25 import BM25Index
from src.retrieval.hybrid import HybridRetriever

try:
    from src.retrieval.dense import DenseIndex
except ImportError:
    DenseIndex = None


class Agent:
    def __init__(self, catalog_path: str):
        self._catalog_path = Path(catalog_path)
        self._catalog = self._load_catalog()
        self._state_mgr = StateManager()

        self._bm25 = BM25Index(str(self._catalog_path))

        embeddings_dir = self._catalog_path.parent / "embeddings"
        embeddings_file = embeddings_dir / "bge_base.npy"
        if DenseIndex is not None and embeddings_file.exists():
            self._dense = DenseIndex(
                str(embeddings_file),
                str(embeddings_dir / "asin_index.json"),
            )
        else:
            self._dense = None

        self._hybrid = HybridRetriever(self._bm25, self._dense, self._catalog)

        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0

    def _load_catalog(self) -> dict[str, dict]:
        catalog = {}
        with open(self._catalog_path) as f:
            for line in f:
                product = json.loads(line)
                catalog[product["parent_asin"]] = product
        return catalog

    def reset(self, session_id: str, user_profile: dict):
        self._state_mgr.reset(session_id, user_profile)

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int = 10) -> dict:
        state = self._state_mgr.get(session_id)
        if state is None:
            self._state_mgr.reset(session_id, {})
            state = self._state_mgr.get(session_id)

        state.update(user_message, turn)

        if detect_intent_override(state, user_message):
            state.flush_constraints()

        self._extract_constraints(state, user_message)

        query = state.build_query()

        candidates = self._hybrid.search(query, constraints=state.constraints, top_k=50)
        state.last_candidates = candidates

        # Pass top-20 to LLM for re-ranking; remaining 30 are fallback
        ranked_asins = rank_candidates(candidates[:20], state)

        # If LLM returned fewer than top_k, fill from remaining candidates
        ranked_set = set(ranked_asins)
        for c in candidates[20:]:
            if len(ranked_asins) >= top_k:
                break
            if c["parent_asin"] not in ranked_set:
                ranked_asins.append(c["parent_asin"])
                ranked_set.add(c["parent_asin"])

        candidate_stats = compute_candidate_stats(candidates)
        ask_attribute = select_attribute(state, candidate_stats)

        recommendations = [
            {"parent_asin": asin, "score": 1.0 - i * 0.05}
            for i, asin in enumerate(ranked_asins[:top_k])
        ]

        rec_products = [self._catalog[asin] for asin in ranked_asins[:top_k] if asin in self._catalog]
        message = generate_message(state, rec_products, ask_attribute)

        state.add_agent_response(message, ask_attribute)

        return {
            "message": message,
            "ask_attribute": ask_attribute,
            "recommendations": recommendations,
            "usage": {
                "prompt_tokens": self._total_prompt_tokens,
                "completion_tokens": self._total_completion_tokens,
            },
        }

    def _extract_constraints(self, state, user_message: str):
        msg = user_message.strip()

        # Pattern: "For that, what matters is: X; Y."
        matters_match = re.search(r"what matters is:\s*(.+?)\.?$", msg, re.I)
        if matters_match:
            raw_values = [v.strip() for v in matters_match.group(1).split(";") if v.strip()]
            for val in raw_values:
                attr = self._classify_constraint(val)
                state.add_constraint(attr, val)
            return

        # Pattern: "I'm looking for {category}" — always extract category first
        looking_match = re.search(r"I'm looking for\s+(.+?)(?:\.|,|$)", msg, re.I)
        if looking_match and state.turn == 1:
            category = looking_match.group(1).strip()
            if category and "still exploring" not in category.lower():
                state.add_constraint("category", category)

        # Pattern: "A key requirement is: X." (buying scenarios — same message as category)
        key_req_match = re.search(r"key requirement is:\s*(.+?)\.?$", msg, re.I)
        if key_req_match:
            val = key_req_match.group(1).strip()
            attr = self._classify_constraint(val)
            state.add_constraint(attr, val)
            return

        # If we already extracted category above, we're done for turn 1
        if looking_match and state.turn == 1:
            return

        # Pattern: "What I need is: X." (intent override)
        need_match = re.search(r"what I need is:\s*(.+?)\.?$", msg, re.I)
        if need_match:
            val = need_match.group(1).strip()
            attr = self._classify_constraint(val)
            state.add_constraint(attr, val)
            return

        # Skip negative/empty responses
        if "don't have" in msg.lower() or "no preference" in msg.lower() or "not quite right" in msg.lower():
            return

        # Fallback: if we asked something and got a meaningful response, store it
        if state.attributes_asked and len(msg) > 3:
            last_asked = state.attributes_asked[-1]
            state.add_constraint(last_asked, msg)

    @staticmethod
    def _classify_constraint(value: str) -> str:
        lowered = value.lower()
        if "budget" in lowered or re.search(r"(?:\$|under|around)\s*\d", lowered):
            return "budget"
        if any(m in lowered for m in ("cotton", "polyester", "nylon", "leather", "wool", "spandex", "silk", "rayon", "fabric")):
            return "material"
        if any(c in lowered for c in ("color", "black", "white", "blue", "red", "pink", "green", "brown", "gray", "grey", "purple", "yellow", "orange")):
            return "color"
        if any(s in lowered for s in ("size", "sizing", "width", "wide", "narrow")):
            return "size"
        if any(s in lowered for s in ("department", "style", "fit", "sleeve", "neck", "casual", "formal")):
            return "style"
        if any(u in lowered for u in ("hiking", "running", "gym", "winter", "outdoor", "work", "travel", "sport")):
            return "use_case"
        return "feature"
