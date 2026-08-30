"""Pipeline trace metadata used by the demo inspector."""

import json

from src.agent import Agent
from src.retrieval.bm25 import BM25Index
from src.retrieval.hybrid import HybridRetriever


def _write_catalog(path, products):
    path.write_text("\n".join(json.dumps(p) for p in products) + "\n")


CATALOG = [
    {
        "parent_asin": "SHOE-BLACK",
        "title": "Men's Running Shoes black breathable mesh upper",
        "categories": ["Clothing", "Shoes", "Men's Running Shoes"],
        "features": ["breathable mesh upper", "lightweight"],
        "store": "Nike",
        "price": 70.0,
        "details": {"Color": "Black", "Size": "10"},
        "description": "Running shoes for men",
    },
    {
        "parent_asin": "SHOE-WHITE",
        "title": "Men's Running Shoes white leather",
        "categories": ["Clothing", "Shoes", "Men's Running Shoes"],
        "features": ["leather upper"],
        "store": "Adidas",
        "price": 95.0,
        "details": {"Color": "White"},
        "description": "Leather running shoes",
    },
    {
        "parent_asin": "SHOE-CHEAP",
        "title": "Men's Running Shoes black mesh",
        "categories": ["Clothing", "Shoes", "Men's Running Shoes"],
        "features": ["breathable mesh upper"],
        "store": "Generic",
        "price": 40.0,
        "details": {"Color": "Black"},
        "description": "Budget mesh runners",
    },
]


def test_search_records_last_search_meta(tmp_path):
    catalog_path = tmp_path / "catalog.jsonl"
    _write_catalog(catalog_path, CATALOG)
    catalog = {p["parent_asin"]: p for p in CATALOG}
    retriever = HybridRetriever(BM25Index(str(catalog_path)), None, catalog)

    results = retriever.search(
        "running shoes black",
        constraints={"category": "Men's Running Shoes", "color": "black", "budget": "under $80"},
        top_k=50,
    )

    meta = retriever.last_search_meta
    assert meta["bm25_k"] == 200
    assert meta["bm25_hits"] >= 1
    assert meta["dense_used"] is False
    assert meta["full_match_count"] >= 1
    assert meta["returned"] == len(results)
    assert meta["returned"] <= 50


def test_constraint_matches_per_attribute(tmp_path):
    catalog_path = tmp_path / "catalog.jsonl"
    _write_catalog(catalog_path, CATALOG)
    catalog = {p["parent_asin"]: p for p in CATALOG}
    retriever = HybridRetriever(BM25Index(str(catalog_path)), None, catalog)
    constraints = {"color": "black", "budget": "under $80", "feature": "breathable mesh upper"}

    black = retriever.constraint_matches(catalog["SHOE-BLACK"], constraints)
    assert black == {"color": True, "budget": True, "feature": True}

    white = retriever.constraint_matches(catalog["SHOE-WHITE"], constraints)
    assert white["color"] is False
    assert white["budget"] is False
    assert white["feature"] is False


def test_dense_available_false_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("ENABLE_DENSE", raising=False)
    catalog_path = tmp_path / "catalog.jsonl"
    _write_catalog(catalog_path, CATALOG)
    agent = Agent(str(catalog_path))
    assert agent.dense_available is False


def test_agent_debug_info_includes_pipeline(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    catalog_path = tmp_path / "catalog.jsonl"
    _write_catalog(catalog_path, CATALOG)
    agent = Agent(str(catalog_path))
    agent.reset("s1", {"summary": "tester"})

    agent.respond(
        "s1",
        "I'm looking for Men's Running Shoes. A key requirement is: breathable mesh upper.",
        turn=1,
    )
    debug = agent.get_debug_info("s1")
    pipeline = debug["pipeline"]

    assert pipeline["intent_override"] is False
    assert "category" in pipeline["new_constraints"]
    assert pipeline["constraints"]["category"]
    assert pipeline["query"]
    assert pipeline["funnel"]["catalog"] == 3
    assert pipeline["funnel"]["bm25"] == 200
    assert pipeline["funnel"]["llm_in"] <= 20
    assert pipeline["funnel"]["shown"] <= 10
    assert "full_match" in pipeline["soft"]
    assert pipeline["llm"]["used"] is False
    assert isinstance(pipeline["llm"]["moved_up"], list)
    assert pipeline["ask"]["attribute"]
    assert pipeline["ask"]["source"] in ("llm", "heuristic")
