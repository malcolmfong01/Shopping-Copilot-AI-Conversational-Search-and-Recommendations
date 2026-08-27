import json
from pathlib import Path

from src.dialog.attribute_selector import compute_candidate_stats, select_attribute
from src.dialog.intent_detector import detect_intent_override
from src.dialog.state import StateManager
from src.ranking.llm_ranker import generate_message, rank_candidates
from src.retrieval.bm25 import BM25Index
from src.retrieval.dense import DenseIndex
from src.retrieval.hybrid import HybridRetriever


class Agent:
    def __init__(self, catalog_path: str):
        self._catalog_path = Path(catalog_path)
        self._catalog = self._load_catalog()
        self._state_mgr = StateManager()

        self._bm25 = BM25Index(str(self._catalog_path))

        embeddings_dir = self._catalog_path.parent / "embeddings"
        self._dense = DenseIndex(
            str(embeddings_dir / "bge_base.npy"),
            str(embeddings_dir / "asin_index.json"),
        )

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

        candidates = self._hybrid.search(query, constraints=state.constraints, top_k=20)
        state.last_candidates = candidates

        ranked_asins = rank_candidates(candidates, state)

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
        """Extract constraints from user message based on context.

        This is a simple heuristic — the LLM modules can do better.
        """
        msg_lower = user_message.lower()

        if state.attributes_asked:
            last_asked = state.attributes_asked[-1]
            if last_asked == "category":
                for keyword in ["dress", "shoes", "shirt", "pants", "jacket", "bag", "hat", "skirt", "sweater", "boots"]:
                    if keyword in msg_lower:
                        state.add_constraint("category", keyword)
                        break
            elif last_asked == "color":
                for color in ["black", "white", "red", "blue", "green", "pink", "brown", "grey", "navy", "beige", "purple", "yellow", "orange"]:
                    if color in msg_lower:
                        state.add_constraint("color", color)
                        break
            elif last_asked == "budget":
                import re
                price_match = re.search(r"\$?(\d+)", msg_lower)
                if price_match:
                    state.add_constraint("budget", price_match.group(0))
                elif "cheap" in msg_lower or "affordable" in msg_lower:
                    state.add_constraint("budget", "under $30")
                elif "expensive" in msg_lower or "premium" in msg_lower or "luxury" in msg_lower:
                    state.add_constraint("budget", "over $100")
            else:
                if len(user_message.strip()) > 2 and "don't" not in msg_lower and "no preference" not in msg_lower:
                    state.add_constraint(last_asked, user_message.strip())
