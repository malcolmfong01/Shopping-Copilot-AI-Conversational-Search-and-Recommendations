import os

from src.ranking.llm_ranker import rank_candidates


class DummyState:
    constraints = {
        "material": "cotton",
        "color": "black",
    }

    def get_context_summary(self):
        return "User prefers cotton and black."


def test_rank_candidates_prefers_exact_constraint_matches_when_llm_fails(monkeypatch):
    monkeypatch.delenv("DEBUG_LLM", raising=False)

    def fake_llm_call(prompt, max_tokens=200, temperature=0.0):
        return None

    import src.ranking.llm_ranker as ranker

    monkeypatch.setattr(ranker, "llm_call", fake_llm_call)

    candidates = [
        {
            "parent_asin": "BAG-1",
            "title": "Nylon backpack",
            "categories": ["bags"],
            "features": ["waterproof"],
            "details": {},
            "description": ["Lightweight outdoor bag"],
            "price": 45,
        },
        {
            "parent_asin": "SHIRT-7",
            "title": "Cotton black T-shirt",
            "categories": ["clothing"],
            "features": ["soft", "organic cotton"],
            "details": {"color": "black"},
            "description": ["Cotton jersey tee in black"],
            "price": 30,
        },
    ]

    result = rank_candidates(candidates, DummyState())

    assert result[0] == "SHIRT-7"
