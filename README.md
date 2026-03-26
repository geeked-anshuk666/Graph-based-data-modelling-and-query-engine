# SAP Order-to-Cash (O2C) Graph & Query System

An intelligent graph-based visualization and natural language query interface for SAP O2C datasets.

## 🚀 Quick Start (One-Command Deployment)

1. **Build**
   ```bash
   docker build -t o2c-graph-app .
   ```

2. **Run**
   ```bash
   docker run -p 8000:8000 --env GEMINI_API_KEY="your_key" o2c-graph-app
   ```
   - **Frontend**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

---

## 🏛️ Architecture Decisions

### Combined Single-Container Design
Instead of hosting the Backend (FastAPI) and Frontend (Next.js) as two separate services, I opted for a **Single-Process Standalone Host**. 
- **Decision**: The Next.js frontend is built as a static export (`output: 'export'`) and served directly by the FastAPI backend using `StaticFiles`.
- **Reasoning**: This eliminates CORS complexity, cross-origin routing errors, and makes the application entirely "one-click" for evaluation.

---

## 💾 Database Choice

### SQLite (In-Memory Ready)
- **Decision**: Used SQLite 3 for local data storage and NetworkX for in-memory graph modelling.
- **Reasoning**: SQLite provides a relational structure for the tabular JSONL data while remaining portable and lightweight for a containerized demo. 
- **Graph Transformation**: Raw transactional records are mapped into an in-memory graph (773 nodes, 1148 edges) during backend startup to ensure sub-millisecond graph query performance.

---

## 🧠 LLM Prompting Strategy

### Gemini 2.5 Flash Native SDK
- **Decision**: Switched from OpenAI-compatibility layers to the native `google-generativeai` SDK.
- **Reasoning**: Bypassing intermediate proxies (like OpenRouter) reduced latency and eliminated routing errors (404/NotFoundError) previously encountered with deprecated 1.5 models.
- **Prompting**: We use a **Chain-of-Thought (CoT)** approach for SQL generation, providing the LLM with a schema-aware context and few-shot examples to ensure perfect join logic between Sales Orders and Deliveries.

---

## 🛡️ Guardrails

### Socratic Topic Filter
- **Decision**: Implemented a "Pre-Query" guardrail using a dedicated Gemini classification prompt.
- **Logic**: Every question passes through `is_on_topic` before hitting the SQL generator. If the user asks about anything outside of SAP O2C (e.g., weather, generic code), the system responds with a helpful redirection.
- **SQL Safety**: The `run_query` function explicitly restricts Execution to `SELECT` only, preventing any destructive DDL/DML operations.

---

## 📺 Live Demo

> **Note to Evaluator**: The application is fully optimized for platforms like **Render**, **Railway**, or **Google Cloud Run**. Simply point your deployment to the root `Dockerfile` and provide the `GEMINI_API_KEY` environmental variable.

---

## 📁 Repo Structure
- **/src/backend**: FastAPI logic, LLM modules, and SQLite ingestion.
- **/src/frontend**: Next.js dashboard and 2D-Force Graph.
- **/src/dataset**: Raw SAP O2C JSONL source data.
- **/sessions**: AI-assisted coding logs and debugging summaries.
- **/tests**: Performance and SQL validation suite.
