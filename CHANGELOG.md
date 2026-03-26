# Project Changelog & Debugging Log

This document serves as the project's debugging log to comply with the evaluation guidelines. It tracks bugs discovered during development and the root cause analyses / fixes applied.

## [0.1.0] - 2026-03-26

**Feature Additions:**
- Initialized FastAPI backend and Next.js frontend
- SQLite database schema generation 
- JSONL data loader
- Graph visualization using NetworkX and React Force Graph
- LLM prompt orchestration via OpenRouter

**Debugging & Fixes:**
- **Bug:** `networkx==3.3` installation failure in pip.
  - **Root Cause:** NetworkX 3.3 requires Python <= 3.12, but the environment runs Python 3.13.2.
  - **Fix:** Pinned `networkx==3.4.2` in `backend/requirements.txt` to support the newer python runtime.
- **Bug:** `pydantic-core` build failure requiring Rust compiler.
  - **Root Cause:** Older versions of Pydantic don't have pre-compiled wheels for Python 3.13, causing pip to attempt building from source.
  - **Fix:** Bumped `pydantic>=2.9.0` and `fastapi==0.115.0` to use pre-built wheels.
- **Bug:** SQLite throwing `sqlite3.ProgrammingError: Error binding parameter... type 'dict' is not supported` during ingestion.
  - **Root Cause:** Several JSONL entries contain nested JSON structures (dicts and lists), which SQLite cannot bind natively as params.
  - **Fix:** Implemented `_flatten_val()` in `backend/db/loader.py` to `json.dumps()` nested dicts and lists into strings.
- **Bug:** SQLite complaining about missing columns during `product_storage_locations` insertion.
  - **Root Cause:** A mismatch between hand-coded snake_case schema naming and automated camelCase conversion (e.g. `dateOfLastPostedCntUnRstrcdStk`).
  - **Fix:** Made the SQL query dynamically filter properties based on existing SQLite `PRAGMA table_info()` schema definition to gracefully drop trailing extra properties without breaking the pipeline.
- **Bug:** Next.js build failing on TypeScript / ESLint checks.
  - **Root Cause:** The generic typing for react-force-graph-2d callback parameters produced `no-explicit-any` errors, and a leftover destructured `_` variable caused `no-unused-vars`.
  - **Fix:** Refactored typescript typing to satisfy ESLint.
