# Data Files

## Required Files

| File | Size | Source |
|------|------|--------|
| `catalog.jsonl` | ~50MB uncompressed | Downloaded from GitHub Releases (gzipped) |
| `public_set.jsonl` | ~small | Downloaded from participant repo `data/` |

## How to Get Them

Run the download script:

```bash
chmod +x data/download.sh
./data/download.sh
```

Or manually:

1. **catalog.jsonl.gz** — download from https://github.com/TechJam2026/techjam-conversational-search/releases/tag/participant-kit, then `gunzip data/catalog.jsonl.gz`
2. **public_set.jsonl** — download from https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/data/public_set.jsonl

## Verify Integrity

A SHA256 checksum file is available in the participant kit release. After downloading:

```bash
sha256sum -c data/checksums.sha256
```

## What Each File Contains

- **catalog.jsonl**: 50,000 products (Clothing, Shoes & Jewelry). One JSON object per line. See `docs/data-guide.md` for schema.
- **public_set.jsonl**: 200 evaluation sessions with ground-truth target products. See `docs/data-guide.md` for schema.

## Notes

- These files are `.gitignore`d — they won't be committed to the repo
- The catalog is read-only during evaluation (no mutations allowed)
- Private evaluation uses 800 separate sessions not included here
