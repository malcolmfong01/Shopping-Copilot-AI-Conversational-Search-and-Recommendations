#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

REPO="TechJam2026/techjam-conversational-search"
RELEASE_TAG="participant-kit"

echo "=== Downloading competition data ==="

# Download catalog.jsonl.gz from GitHub Releases
if [ -f "catalog.jsonl" ]; then
    echo "[skip] catalog.jsonl already exists"
else
    echo "[download] catalog.jsonl.gz from GitHub Releases..."
    gh release download "$RELEASE_TAG" \
        --repo "$REPO" \
        --pattern "catalog.jsonl.gz" \
        --dir .
    echo "[extract] gunzipping catalog.jsonl.gz..."
    gunzip catalog.jsonl.gz
    echo "[done] catalog.jsonl ($(wc -l < catalog.jsonl) lines)"
fi

# Download public_set.jsonl from repo
if [ -f "public_set.jsonl" ]; then
    echo "[skip] public_set.jsonl already exists"
else
    echo "[download] public_set.jsonl from repo..."
    gh api "repos/$REPO/contents/data/public_set.jsonl" \
        --jq '.download_url' | xargs curl -sL -o public_set.jsonl
    echo "[done] public_set.jsonl ($(wc -l < public_set.jsonl) lines)"
fi

# Download checksum if available
if [ ! -f "checksums.sha256" ]; then
    echo "[download] checksums (if available)..."
    gh release download "$RELEASE_TAG" \
        --repo "$REPO" \
        --pattern "*.sha256" \
        --dir . 2>/dev/null || echo "[info] no checksum file in release"
fi

echo ""
echo "=== Data ready ==="
echo "  catalog.jsonl:    $([ -f catalog.jsonl ] && echo 'OK' || echo 'MISSING')"
echo "  public_set.jsonl: $([ -f public_set.jsonl ] && echo 'OK' || echo 'MISSING')"
echo ""
echo "See docs/data-guide.md for schema documentation."
