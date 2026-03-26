# Build Plan — SAP O2C Graph Query System

## Snapshot
- **Stack**: Python + FastAPI + SQLite + NetworkX + OpenRouter (Llama 3.1 8B) + Next.js + react-force-graph-2d
- **Deploy**: Render (Web Service + persistent disk) + Docker fallback
- **Estimated time**: 5–7 hours

---

## Phase 0: Bootstrap (20 min)

### Backend
- [ ] Create folder structure:
  ```bash
  mkdir -p o2c-graph/{backend/{db,graph,llm,routers,prompts},frontend,data}
  cd o2c-graph
  ```
- [ ] Copy the dataset into `data/sap-o2c-data/` (unzip the provided archive)
- [ ] Create `backend/requirements.txt`:
  ```
  fastapi==0.111.0
  uvicorn==0.30.1
  openai==1.35.7
  networkx==3.3
  python-dotenv==1.0.1
  pydantic==2.7.4
  pydantic-settings==2.3.4
  slowapi==0.1.9
  httpx==0.27.0
  ```
- [ ] `pip install -r requirements.txt`
- [ ] Create `.env.example`:
  ```
  OPENROUTER_API_KEY="sk-or-..."
  DATA_DIR="./data/sap-o2c-data"
  DB_PATH="./o2c.db"
  ```

### Frontend
- [ ] `npx create-next-app@latest frontend --typescript --tailwind --app --src-dir=false`
- [ ] `cd frontend && npm install react-force-graph-2d axios`

### Repo
- [ ] `git init`, `.gitignore` (include `.env`, `o2c.db`, `data/`)
- [ ] Initial commit: `initial project layout`

---

## Phase 0.5: Security & Config Foundation (20 min)

Before writing any routes, lay down the security and config infrastructure. Everything else builds on top of this.

### `backend/config.py`
- [ ] `pydantic-settings` `Settings` class with all env vars
- [ ] Import `from config import settings` everywhere — no raw `os.environ` calls elsewhere

### `backend/middleware/rate_limit.py`
- [ ] `Limiter(key_func=get_remote_address)` singleton
- [ ] Export the `limiter` instance for use in routers

### `backend/middleware/security_headers.py`
- [ ] `SecurityHeaders(BaseHTTPMiddleware)` that adds:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `X-XSS-Protection: 1; mode=block`

### `backend/db/query_runner.py`
- [ ] `run_query(sql: str, conn) -> list[dict]`
  - Validate SQL starts with SELECT or WITH
  - Reject multiple statements (more than one semicolon)
  - Execute, fetch up to 100 rows, return as list of dicts
  - All LLM-generated SQL goes through this — never `conn.execute(llm_sql)` directly elsewhere

### `backend/models/schemas.py`
- [ ] `QueryRequest` Pydantic model with `question` field validator:
  - Strip whitespace
  - Reject empty or >500 chars
  - Strip non-printable characters
- [ ] `GraphNode`, `GraphEdge`, `GraphResponse` models (typed contracts for API responses)

### `frontend/lib/api.ts`
- [ ] Centralized API client — all `axios` calls live here, nowhere else
- [ ] `queryChat(question)`, `fetchGraph()`, `fetchNode(id)`, `fetchStatus()`

### `frontend/types/api.ts`
- [ ] TypeScript interfaces for all API response shapes
- [ ] No `any` types anywhere in the frontend

Commit: `add security middleware, config, and input validation layer`

---

## Phase 1: SQLite Schema + Data Loader (45 min)

### `backend/db/schema.sql`

Write CREATE TABLE statements for all 19 entity types. Key tables:

```sql
CREATE TABLE IF NOT EXISTS sales_order_headers (
    sales_order TEXT PRIMARY KEY,
    sales_order_type TEXT,
    sales_organization TEXT,
    sold_to_party TEXT,
    creation_date TEXT,
    total_net_amount REAL,
    overall_delivery_status TEXT,
    overall_billing_status TEXT,
    transaction_currency TEXT,
    requested_delivery_date TEXT
);

CREATE TABLE IF NOT EXISTS sales_order_items (
    sales_order TEXT,
    sales_order_item TEXT,
    material TEXT,
    requested_quantity REAL,
    net_amount REAL,
    material_group TEXT,
    production_plant TEXT,
    storage_location TEXT,
    PRIMARY KEY (sales_order, sales_order_item)
);

CREATE TABLE IF NOT EXISTS outbound_delivery_headers (
    delivery_document TEXT PRIMARY KEY,
    creation_date TEXT,
    shipping_point TEXT,
    overall_goods_movement_status TEXT,
    overall_picking_status TEXT,
    header_billing_block_reason TEXT
);

CREATE TABLE IF NOT EXISTS outbound_delivery_items (
    delivery_document TEXT,
    delivery_document_item TEXT,
    reference_sd_document TEXT,   -- links to sales_order
    reference_sd_document_item TEXT,
    actual_delivery_quantity REAL,
    plant TEXT,
    storage_location TEXT,
    PRIMARY KEY (delivery_document, delivery_document_item)
);

CREATE TABLE IF NOT EXISTS billing_document_headers (
    billing_document TEXT PRIMARY KEY,
    billing_document_type TEXT,
    creation_date TEXT,
    billing_document_date TEXT,
    billing_document_is_cancelled INTEGER,
    total_net_amount REAL,
    transaction_currency TEXT,
    company_code TEXT,
    fiscal_year TEXT,
    accounting_document TEXT,
    sold_to_party TEXT
);

CREATE TABLE IF NOT EXISTS billing_document_items (
    billing_document TEXT,
    billing_document_item TEXT,
    material TEXT,
    billing_quantity REAL,
    net_amount REAL,
    reference_sd_document TEXT,   -- links to delivery
    reference_sd_document_item TEXT,
    PRIMARY KEY (billing_document, billing_document_item)
);

CREATE TABLE IF NOT EXISTS journal_entry_items (
    accounting_document TEXT,
    accounting_document_item TEXT,
    company_code TEXT,
    fiscal_year TEXT,
    gl_account TEXT,
    reference_document TEXT,      -- links to billing_document
    profit_center TEXT,
    amount_in_transaction_currency REAL,
    transaction_currency TEXT,
    posting_date TEXT,
    customer TEXT,
    clearing_date TEXT,
    clearing_accounting_document TEXT,
    PRIMARY KEY (accounting_document, accounting_document_item)
);

CREATE TABLE IF NOT EXISTS payments (
    accounting_document TEXT,
    accounting_document_item TEXT,
    company_code TEXT,
    fiscal_year TEXT,
    clearing_date TEXT,
    clearing_accounting_document TEXT,
    amount_in_transaction_currency REAL,
    transaction_currency TEXT,
    customer TEXT,
    posting_date TEXT,
    PRIMARY KEY (accounting_document, accounting_document_item)
);

CREATE TABLE IF NOT EXISTS business_partners (
    business_partner TEXT PRIMARY KEY,
    customer TEXT,
    business_partner_full_name TEXT,
    city_name TEXT,               -- from addresses join
    country TEXT,
    is_blocked INTEGER
);

CREATE TABLE IF NOT EXISTS products (
    product TEXT PRIMARY KEY,
    product_type TEXT,
    product_old_id TEXT,
    gross_weight REAL,
    weight_unit TEXT,
    product_group TEXT,
    base_unit TEXT,
    description TEXT              -- from product_descriptions join
);

CREATE TABLE IF NOT EXISTS plants (
    plant TEXT PRIMARY KEY,
    plant_name TEXT,
    sales_organization TEXT,
    factory_calendar TEXT
);
```

### `backend/db/loader.py`

- [ ] `load_all(data_dir: Path, db_path: Path)` — main entry point
- [ ] Helper `read_jsonl(path: Path) -> list[dict]` that handles multi-part files (glob `*.jsonl` in each folder)
- [ ] One `insert_*` function per table, using `executemany` for speed
- [ ] Run schema.sql first, then insert each entity
- [ ] Print a simple summary after load: `loaded 100 sales orders, 167 items, ...`
- [ ] Add a `--reload` flag that drops and recreates the DB (useful during dev)

Commit: `set up sqlite schema and jsonl loader`

---

## Phase 2: Graph Construction (30 min)

### `backend/graph/builder.py`

- [ ] `build_graph(conn: sqlite3.Connection) -> nx.DiGraph`
  - Query each entity type and create nodes
  - Node IDs follow pattern: `so_740506`, `del_80738040`, `bp_310000108`, etc.
  - Each node: `{ id, type, label, properties }`
  - Add edges based on foreign key relationships (see AI_rules.md section 7)
  - **Skip** product_storage_locations as nodes — too many. Just store as product properties.
  - Return the graph

- [ ] `get_neighbors(graph: nx.DiGraph, node_id: str, depth: int = 1) -> subgraph`
  - Used by the "expand node" feature in the UI
  - Returns nodes within `depth` hops of `node_id`

### `backend/graph/serializer.py`

- [ ] `to_frontend(graph: nx.DiGraph) -> dict`
  - Return `{ nodes: [...], links: [...] }` — the format react-force-graph-2d expects
  - Nodes: `{ id, label, type, properties }`
  - Links: `{ source, target, type }`

Commit: `add networkx graph builder for core o2c entities`

---

## Phase 3: LLM Integration (60 min)

### `backend/llm/client.py`

```python
from openai import OpenAI
import os

_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
        )
    return _client
```

### `backend/prompts/sql_prompt.py`

- [ ] `SCHEMA_CONTEXT` — paste all table schemas as a string
- [ ] `FEW_SHOT_EXAMPLES` — 4 example Q&A pairs:
  ```
  Q: Which products appear in the most billing documents?
  SQL: SELECT i.material, COUNT(DISTINCT i.billing_document) as doc_count
       FROM billing_document_items i
       GROUP BY i.material ORDER BY doc_count DESC LIMIT 10;

  Q: Show me all deliveries for sales order 740506
  SQL: SELECT dh.* FROM outbound_delivery_headers dh
       JOIN outbound_delivery_items di ON dh.delivery_document = di.delivery_document
       WHERE di.reference_sd_document = '740506';

  Q: Find sales orders that were delivered but never billed
  SQL: SELECT DISTINCT di.reference_sd_document as sales_order
       FROM outbound_delivery_items di
       WHERE di.reference_sd_document NOT IN (
           SELECT DISTINCT bi.reference_sd_document
           FROM billing_document_items bi
           WHERE bi.reference_sd_document IS NOT NULL
       );

  Q: Trace the full flow for billing document 90504259
  SQL: SELECT 'sales_order' as stage, soh.sales_order as doc_id, soh.total_net_amount as amount
       FROM billing_document_items bi
       JOIN outbound_delivery_items di ON bi.reference_sd_document = di.delivery_document
       JOIN sales_order_headers soh ON di.reference_sd_document = soh.sales_order
       WHERE bi.billing_document = '90504259'
       UNION ALL
       SELECT 'delivery', dh.delivery_document, NULL
       FROM billing_document_items bi
       JOIN outbound_delivery_headers dh ON bi.reference_sd_document = dh.delivery_document
       WHERE bi.billing_document = '90504259'
       UNION ALL
       SELECT 'billing', '90504259', bdh.total_net_amount
       FROM billing_document_headers bdh WHERE bdh.billing_document = '90504259';
  ```
- [ ] `build_sql_prompt(question: str) -> list[dict]` — returns messages array for the LLM

### `backend/llm/guardrails.py`

- [ ] `is_on_topic(question: str) -> bool`
  - Short LLM call: "Does this question relate to SAP Order-to-Cash business data (sales orders, deliveries, billing, payments, customers, products)? Answer yes or no."
  - Parse response for "yes"/"no"
  - Cache results for repeated identical questions

### `backend/llm/sql_generator.py`

- [ ] `generate_sql(question: str) -> str`
  - Call LLM with sql_prompt, temperature=0.0
  - Strip markdown code fences if present (LLM sometimes wraps in ```sql```)
  - Validate it starts with SELECT (reject INSERT/UPDATE/DROP)
  - Return clean SQL string

### `backend/llm/responder.py`

- [ ] `build_answer(question: str, sql: str, rows: list) -> str`
  - Call LLM with answer prompt, temperature=0.3
  - Return natural language answer
  - If rows is empty, return "No matching records found in the dataset."

Commit: `wire up text-to-sql pipeline with openrouter llama`

Commit: `add guardrail check for off-topic queries`

---

## Phase 4: API Routes (30 min)

### `backend/routers/graph.py`

- [ ] `GET /api/graph` — `@limiter.limit("30/minute")`
  - Returns the full graph JSON (nodes + links) as `GraphResponse`
  - Limit to core entities only on first load (SalesOrders, Deliveries, BillingDocs, Customers)
- [ ] `GET /api/graph/node/{node_id}` — `@limiter.limit("60/minute")`
  - Validate `node_id` matches `^[a-z]+_[a-zA-Z0-9]+$` before hitting the graph
  - Returns one node's properties + immediate neighbors

### `backend/routers/query.py`

- [ ] `POST /api/query` — accepts `QueryRequest` (validated Pydantic model)
  - `@limiter.limit("10/minute")` — rate limit this route aggressively
  1. Run guardrail check — if off-topic, return the canned message immediately
  2. Generate SQL via `sql_generator`
  3. Execute via `run_query()` (not raw `conn.execute`) — enforces SELECT-only rule
  4. Generate natural language answer from results
  5. Return typed `QueryResponse`

### `backend/routers/status.py`

- [ ] `GET /api/status`
  - Backend: always OK
  - DB: `SELECT COUNT(*) FROM sales_order_headers` — check latency
  - LLM: one-token OpenRouter call — check latency
  - Return `{ backend, db, llm }` each with `{ ok, latency_ms }`

### `backend/main.py`

- [ ] Create FastAPI app
- [ ] On startup: load data if DB doesn't exist, build graph into memory
- [ ] Register routers
- [ ] Add `CORSMiddleware` — origins from `settings.allowed_origins`, not wildcard
- [ ] Add `SecurityHeaders` middleware (X-Content-Type-Options, X-Frame-Options, etc.)
- [ ] Add `slowapi` limiter to app state: `app.state.limiter = limiter`
- [ ] Add `SlowAPIMiddleware` to app

Commit: `add graph and query api routes`

---

## Phase 5: Frontend (90 min)

### `app/page.tsx` — Main Page

Layout: two-column split. Left 60%: graph. Right 40%: chat.

- [ ] On mount: fetch `/api/graph`, render in GraphView
- [ ] When a node is clicked: fetch `/api/graph/node/{id}`, open NodePanel sidebar
- [ ] Chat input at bottom of right panel

### `components/GraphView.tsx`

- [ ] Wrap `react-force-graph-2d` (import dynamically with `next/dynamic` — it's browser-only)
- [ ] Color nodes by type:
  - SalesOrder: blue
  - Delivery: green
  - BillingDocument: orange
  - Customer: purple
  - Product: teal
  - Plant: gray
  - JournalEntry: yellow
  - Payment: red
- [ ] On node click: call `onNodeClick(nodeId)` prop
- [ ] On node right-click or double-click: "expand" — fetch neighbors and merge into graph state
- [ ] Show node label on hover

### `components/NodePanel.tsx`

- [ ] Slide-in panel on the right (or overlay on the graph side)
- [ ] Show node type badge + all properties in a clean key-value list
- [ ] "Expand in graph" button
- [ ] Close button

### `components/ChatPanel.tsx`

- [ ] Message history (scrollable)
- [ ] Input field + send button
- [ ] On send: POST `/api/query`, add user + assistant messages to history
- [ ] Show SQL in a collapsed `<details>` block below each answer (so evaluators can inspect it)
- [ ] Loading spinner while waiting for response
- [ ] If `on_topic: false`: show the guardrail message in a different style (gray, italic)

### `components/MessageBubble.tsx`

- [ ] User messages: right-aligned, accent color
- [ ] Assistant messages: left-aligned, white/light card
- [ ] SQL details collapsible block under assistant messages

### `app/status/page.tsx`

- [ ] Three status cards: Backend, SQLite DB, LLM
- [ ] Colored dot + latency per card
- [ ] Auto-refresh every 30s

Commits during this phase (one per component):
```
add graph visualization component with node coloring
add node metadata panel with expand button
add chat panel with query api integration
add sql details block under chat responses
add status page
```

---

## Phase 6: Required Files (20 min)

- [ ] `README.md`:
  ```
  ## Architecture
  - SQLite for relational storage (dataset is ~17K rows, no infra needed)
  - NetworkX for in-memory graph (visualization + traversal)
  - FastAPI backend, Next.js frontend
  - LLM: Llama 3.1 8B via OpenRouter (free tier)
  - Two-step LLM pipeline: guardrail check → SQL generation → execution → answer

  ## DB Choice
  Chose SQLite over Neo4j because...

  ## LLM Prompting Strategy
  ...

  ## Guardrails
  ...

  ## What's done / not done
  ...
  ```
- [ ] `AI_NOTES.md`
- [ ] `ABOUTME.md`
- [ ] `PROMPTS_USED.md`
- [ ] `.env.example`

---

## Phase 7: Docker + Render Deploy (30 min)

### `Dockerfile.backend`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend
COPY data/ ./data
RUN python backend/db/loader.py  # pre-build the DB
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `docker-compose.yml`
```yaml
services:
  backend:
    build:
      dockerfile: Dockerfile.backend
    ports: ["8000:8000"]
    env_file: .env

  frontend:
    build:
      dockerfile: Dockerfile.frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on: [backend]
```

### `render.yaml`
```yaml
services:
  - type: web
    name: o2c-backend
    env: python
    buildCommand: pip install -r backend/requirements.txt && python backend/db/loader.py
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    disk:
      name: o2c-db
      mountPath: /app/data
      sizeGB: 1
    envVars:
      - key: OPENROUTER_API_KEY
        sync: false
      - key: DB_PATH
        value: /app/data/o2c.db
      - key: DATA_DIR
        value: /app/data/sap-o2c-data

  - type: web
    name: o2c-frontend
    env: node
    buildCommand: cd frontend && npm ci && npm run build
    startCommand: cd frontend && npm run start
    envVars:
      - key: NEXT_PUBLIC_API_URL
        value: https://o2c-backend.onrender.com
```

- [ ] Test full flow locally with `docker compose up --build`
- [ ] Deploy to Render, verify live URL
- [ ] Test all 3 example queries from the assignment on the live app

Commit: `set up docker-compose and render.yaml`

---

## Phase 8: docs/ Folder + CHANGELOG.md (45 min)

Write these as you go — not all at the end. Start the file when the feature is built, fill in the details while context is fresh.

### `docs/overview.md`
- [ ] What the project is, why it was built, what problem it solves
- [ ] One-paragraph architecture summary
- [ ] Link to all other docs files

### `docs/architecture.md`
- [ ] Full system diagram (ASCII or Mermaid)
- [ ] Component responsibilities (backend modules, frontend components)
- [ ] Data flow narrative: from JSONL files to rendered graph to answered query

### `docs/system-design-hld.md`
- [ ] High-level design: components, how they talk to each other
- [ ] Why these components were chosen
- [ ] Trade-offs of the chosen architecture vs alternatives

### `docs/system-design-lld.md`
- [ ] Low-level: each class, each module, each function signature that matters
- [ ] The text-to-SQL pipeline step by step with example inputs/outputs
- [ ] Graph construction logic in detail
- [ ] Request lifecycle for a `/api/query` call

### `docs/api-reference.md`
- [ ] Every endpoint: method, path, request body, response body, error codes
- [ ] Example curl commands for each endpoint
- [ ] Rate limit headers explained

### `docs/database-schema.md`
- [ ] All 11 SQLite tables with columns, types, primary keys, indexes
- [ ] ER diagram (ASCII/Mermaid)
- [ ] Why SQLite over Postgres/Neo4j/other options
- [ ] Index strategy and why

### `docs/graph-model.md`
- [ ] Node types, ID patterns, properties per type
- [ ] Edge types and what they represent in the business domain
- [ ] Why certain entities (product_storage_locations) are excluded
- [ ] NetworkX choice: why not a proper graph DB

### `docs/llm-pipeline.md`
- [ ] The 3-step pipeline: guardrail → SQL generation → answer generation
- [ ] Full prompt templates with explanation of each section
- [ ] Few-shot example rationale
- [ ] Why Llama 3.1 8B via OpenRouter
- [ ] Known failure modes and mitigations

### `docs/security.md`
- [ ] All security controls with explanation of *why* each one matters
- [ ] Rate limiting: limits chosen, what they protect against
- [ ] SQL injection: why LLM-generated SQL is a vector, how `run_query()` guards it
- [ ] XSS: what headers do, why `dangerouslySetInnerHTML` is banned
- [ ] Input sanitization: what the Pydantic validators strip and why
- [ ] What is NOT covered (no auth, no virus scanning) and why

### `docs/scalability.md`
- [ ] Current scale: what the system handles today
- [ ] 10x scale: what breaks first, how to fix it
- [ ] 100x scale: which components need redesign
- [ ] 1B users / enterprise-global scale: full re-architecture path
  - Replace SQLite with distributed Postgres (Citus) or BigQuery
  - Replace in-memory NetworkX with a proper graph DB (Neo4j cluster, or Amazon Neptune)
  - LLM: move to dedicated inference cluster, add semantic caching
  - Add CDN, edge caching for graph data
  - Observability: distributed tracing, SLOs, alerting
- [ ] What stays the same at any scale (the pipeline concept, prompt strategy)

### `docs/frontend.md`
- [ ] Component tree and responsibilities
- [ ] State management approach (local state, no Redux needed)
- [ ] Why react-force-graph-2d (not D3 directly, not Cytoscape)
- [ ] Dynamic import pattern for SSR compatibility

### `docs/deployment.md`
- [ ] Render deployment step-by-step
- [ ] Docker Compose local setup
- [ ] Environment variables reference
- [ ] First-run sequence (data loading, DB creation)
- [ ] How to redeploy without losing the SQLite file

### `docs/uml-diagrams.md`
- [ ] Sequence diagram: full query lifecycle (user input → answer)
- [ ] Sequence diagram: graph node expand
- [ ] Class diagram: backend module dependencies
- [ ] ER diagram: SQLite schema relationships
- [ ] Component diagram: frontend

### `docs/future-improvements.md`
- [ ] Conversation memory (multi-turn SQL context)
- [ ] Node highlighting in graph when query results reference them
- [ ] Streaming LLM responses
- [ ] Graph clustering (identify order flow clusters)
- [ ] Hybrid semantic + SQL search
- [ ] Export graph as JSON/PNG
- [ ] Adding new SAP entity types

### `docs/uml-diagrams.md` — detailed Mermaid diagrams
- [ ] Sequence: full query lifecycle (`user input → guardrail → SQL gen → execute → answer`)
- [ ] Sequence: graph node expand (`click → GET /api/graph/node/{id} → merge into graph`)
- [ ] Class diagram: backend module dependencies (which module imports which)
- [ ] ER diagram: all SQLite table relationships in Mermaid `erDiagram` syntax
- [ ] Component diagram: frontend components and their props/events

### `docs/scalability.md` — must be genuinely thoughtful
- [ ] Current hard limits: SQLite write lock, in-memory graph size, OpenRouter free tier rate
- [ ] 10x: which service breaks first, exact fix (paid OpenRouter + Postgres)
- [ ] 100x: multiple workers, Redis cache for graph, semantic response cache
- [ ] 1B users: k8s + API gateway + Neo4j cluster + distributed Postgres + dedicated GPU inference + CDN + distributed tracing
- [ ] What never changes regardless of scale: the text-to-SQL pipeline, prompt design, graph model

### `CHANGELOG.md` — start on day 1, update after every commit

The CHANGELOG is not documentation you write at the end. It's a living log. Start it when you start coding.

- [ ] Create the file with a header and an unreleased section
- [ ] After each commit, add an entry — takes 2 minutes, saves hours of archaeology later
- [ ] The "Fixed" sections are the most valuable — document the bug, the root cause, and how you found it

**Starter template:**
```markdown
# Changelog

All notable changes are documented here. Format loosely follows Keep a Changelog.

## [Unreleased]

## [0.1.0] — YYYY-MM-DD

### Added
- initial project layout, folder structure, gitignore

## [0.1.1] — YYYY-MM-DD

### Added
- SQLite schema for 11 core tables
- JSONL loader with multi-part file support (globs *.jsonl per folder)

## [0.1.2] — YYYY-MM-DD

### Added
- slowapi rate limiting: 10/min on /api/query, 30/min on graph routes
- X-Content-Type-Options, X-Frame-Options, X-XSS-Protection headers on all responses
- QueryRequest Pydantic model with 500-char limit and non-printable char stripping

### Fixed
- loader was only reading the first *.jsonl part file per entity folder
  root cause: used `glob(...)[0]` instead of iterating all matches
  found: first query for sales order items returned half the expected rows

## [0.1.3] — YYYY-MM-DD

### Added
- NetworkX graph builder with 8 node types and 8 edge types
- graph serializer: converts DiGraph to {nodes, links} JSON for react-force-graph-2d

## [0.1.4] — YYYY-MM-DD

### Added
- run_query() SQL safety guard: SELECT/WITH allowlist, single-statement enforcement
- OpenRouter client singleton (openai SDK, openrouter.ai base URL)
- LLM guardrail: short classification call before generating any SQL

### Fixed
- billing→delivery join was using billing_document instead of reference_sd_document
  root cause: misread the schema — billing_document_items.reference_sd_document is the delivery doc ID
  found: full-flow trace for billing doc 90504259 returned empty delivery row

## [0.1.5] — YYYY-MM-DD

### Added
- text-to-SQL prompt with schema context and 4 few-shot examples
- answer generation prompt
- /api/query route wiring all three steps together

[continue from here...]
```

Commit: `add docs folder with all technical documentation`
Commit: `add changelog with entries from project start`

---

## Example Queries — Must Work at Demo Time

Before submitting, verify these all return sensible SQL-backed answers:

1. "Which products are associated with the highest number of billing documents?"
2. "Trace the full flow of billing document 90504259"
3. "Find sales orders that were delivered but not billed"
4. "Which customer has the highest total billing amount?"
5. "Show me all cancelled billing documents"
6. "What is the total payment received for sales order 740506?"

And these guardrail cases must return the canned message:
- "What is the capital of France?"
- "Write me a poem"
- "How do I code a binary search tree?"

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| LLM generates DROP/DELETE SQL | `run_query()` enforces SELECT-only before execution |
| SQL injection via user input | Parameterized queries everywhere; LLM SQL goes through `run_query()` |
| DDoS / abuse of LLM endpoint | `slowapi` 10/min on `/api/query`, 30/min on graph routes |
| XSS via API response content | Security headers middleware + React's default JSX escaping (no dangerouslySetInnerHTML) |
| Secrets in code or logs | `pydantic-settings` reads from env; logging never emits env values |
| Config drift across environments | Single `config.py` with `Settings`; all modules import from there |
| Graph too large to render | Start with core subset, lazy-load on expand |
| react-force-graph-2d SSR issue | Dynamic import with `ssr: false` in Next.js |
| OpenRouter free tier rate limit | Single sequential query per chat message, retry once on 429 |
| Dataset JSONL files split across parts | Glob all `*.jsonl` in each folder, not just first file |
| product_storage_locations (16K rows) kills graph | Don't create graph nodes for it — store as product metadata only |
| Frontend API changes break multiple files | All `axios` calls centralized in `frontend/lib/api.ts` |
