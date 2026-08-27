import json
import re
import sqlite3


STOPWORDS = frozenset(
    "i me my myself we our ours ourselves you your yours yourself yourselves "
    "he him his himself she her hers herself it its itself they them their theirs "
    "themselves what which who whom this that these those am is are was were be "
    "been being have has had having do does did doing a an the and but if or "
    "because as until while of at by for with about against between through during "
    "before after above below to from up down in out on off over under again further "
    "then once here there when where why how all both each few more most other some "
    "such no nor not only own same so than too very s t can will just don should now".split()
)

BM25_WEIGHTS = (0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0)


class BM25Index:
    def __init__(self, catalog_path: str):
        self._conn = sqlite3.connect(":memory:")
        self._conn.execute(
            "CREATE VIRTUAL TABLE products USING fts5("
            "parent_asin UNINDEXED, title, categories, features, details, store, description"
            ")"
        )
        self._load_catalog(catalog_path)

    def _load_catalog(self, path: str):
        with open(path) as f:
            rows = []
            for line in f:
                p = json.loads(line)
                rows.append((
                    p["parent_asin"],
                    p.get("title", ""),
                    " ".join(p.get("categories", [])) if isinstance(p.get("categories"), list) else str(p.get("categories", "")),
                    " ".join(p.get("features", [])) if isinstance(p.get("features"), list) else str(p.get("features", "")),
                    " ".join(f"{k} {v}" for k, v in p["details"].items()) if isinstance(p.get("details"), dict) else str(p.get("details", "")),
                    p.get("store", ""),
                    " ".join(p.get("description", [])) if isinstance(p.get("description"), list) else str(p.get("description", "")),
                ))
        self._conn.executemany(
            "INSERT INTO products(parent_asin, title, categories, features, details, store, description) VALUES (?,?,?,?,?,?,?)",
            rows,
        )
        self._conn.commit()

    def _tokenize(self, text: str) -> str:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return " ".join(t for t in tokens if t not in STOPWORDS)

    def search(self, query: str, top_k: int = 50) -> list[tuple[str, float]]:
        terms = self._tokenize(query)
        if not terms:
            return []
        match_query = " OR ".join(terms.split())
        cur = self._conn.execute(
            "SELECT parent_asin, bm25(products, ?, ?, ?, ?, ?, ?) AS score "
            "FROM products WHERE products MATCH ? "
            "ORDER BY score LIMIT ?",
            (*BM25_WEIGHTS, match_query, top_k),
        )
        return [(row[0], -row[1]) for row in cur.fetchall()]
