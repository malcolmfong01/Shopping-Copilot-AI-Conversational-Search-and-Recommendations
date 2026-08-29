import json
import os
import sys
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agent import Agent

app = Flask(__name__, static_folder=None)

CATALOG_PATH = ROOT / "data" / "catalog.jsonl"
FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"

print("Loading catalog and building index...", flush=True)
t0 = time.time()
agent = Agent(str(CATALOG_PATH))
print(f"Ready in {time.time() - t0:.1f}s — {len(agent._catalog)} products loaded", flush=True)


@app.after_request
def cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/new-session", methods=["POST", "OPTIONS"])
def new_session():
    if request.method == "OPTIONS":
        return "", 204
    session_id = str(uuid.uuid4())
    profile = {
        "preference_tags": ["fit", "comfort", "style"],
        "summary": "General shopper looking for clothing.",
    }
    agent.reset(session_id, profile)
    return jsonify({"session_id": session_id, "user_profile": profile})


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json()
    session_id = data["session_id"]
    message = data["message"]
    turn = data.get("turn", 1)

    t0 = time.time()
    result = agent.respond(session_id, message, turn)
    elapsed_ms = int((time.time() - t0) * 1000)

    debug = agent.get_debug_info(session_id)

    enriched_recs = []
    for rec in result.get("recommendations", []):
        asin = rec["parent_asin"]
        product = agent._catalog.get(asin, {})
        enriched_recs.append({
            "parent_asin": asin,
            "score": rec["score"],
            "title": product.get("title", "Unknown Product"),
            "price": product.get("price"),
            "categories": product.get("categories", []),
            "rating": product.get("average_rating"),
            "review_count": product.get("rating_number", 0),
            "store": product.get("store", ""),
            "features": product.get("features", [])[:3],
        })

    return jsonify({
        "message": result["message"],
        "ask_attribute": result.get("ask_attribute"),
        "recommendations": enriched_recs,
        "constraints": debug.get("constraints", {}),
        "query": debug.get("query", ""),
        "candidate_count": debug.get("candidate_count", 0),
        "attributes_asked": debug.get("attributes_asked", []),
        "timing_ms": elapsed_ms,
        "turn": turn,
    })


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if FRONTEND_DIST.exists():
        file_path = FRONTEND_DIST / path
        if file_path.is_file():
            return send_from_directory(str(FRONTEND_DIST), path)
        return send_from_directory(str(FRONTEND_DIST), "index.html")
    return "<h1>Run <code>npm run build</code> in webapp/frontend/ first</h1>", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\nShopping Copilot API: http://localhost:{port}\n", flush=True)
    app.run(debug=False, port=port)
