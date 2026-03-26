# Architecture — SAP O2C Graph Query System

## System Overview

A fullstack application that ingests a SAP Order-to-Cash dataset, builds a relational database and an in-memory graph, visualizes the graph interactively, and answers natural language questions by translating them into SQL in real time.

```
┌──────────────────────────────────────────────────────────────────────┐
│                           BROWSER                                    │
│                                                                      │
│  ┌─────────────────────────────────┐  ┌────────────────────────────┐│
│  │         Graph View (60%)        │  │      Chat Panel (40%)      ││
│  │                                 │  │                            ││
│  │  react-force-graph-2d           │  │  [User] Which products...  ││
│  │                                 │  │  [AI]   Product S890736... ││
│  │  ● SalesOrder  ● Delivery       │  │         (SQL: SELECT...)   ││
│  │  ● BillingDoc  ● Customer       │  │                            ││
│  │  ● Product     ● Plant          │  │  [input box + send]        ││
│  │                                 │  │                            ││
│  │  click node → NodePanel         │  │                            ││
│  └─────────────────────────────────┘  └────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
          │ GET /api/graph                │ POST /api/query
          │ GET /api/graph/node/{id}      │
          ▼                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (Port 8000)                     │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                        ROUTERS                              │    │
│  │  /api/graph  /api/graph/node/{id}  /api/query  /api/status  │    │
│  └──────────────────────────────┬──────────────────────────────┘    │
│                                 │                                    │
│  ┌──────────────────────────────┼──────────────────────────────┐    │
│  │              SERVICE LAYER   │                              │    │
│  │                              │                              │    │
│  │  graph/builder.py            │  llm/guardrails.py           │    │
│  │  graph/serializer.py         │  llm/sql_generator.py        │    │
│  │                              │  llm/responder.py            │    │
│  │  db/loader.py                │                              │    │
│  │  db/connection.py            │                              │    │
│  └──────────────────────────────┴──────────────────────────────┘    │
└───────────────────┬──────────────────────────────┬───────────────────┘
                    │                              │
                    ▼                              ▼
     ┌──────────────────────┐         ┌────────────────────────┐
     │   SQLite (o2c.db)    │         │  OpenRouter API        │
     │                      │         │                        │
     │  19 tables           │         │  meta-llama/           │
     │  ~17K rows           │         │  llama-3.1-8b-         │
     │  loaded on startup   │         │  instruct:free         │
     │                      │         │                        │
     │  NetworkX graph      │         │  (via openai SDK)      │
     │  built in-memory     │         └────────────────────────┘
     │  at startup          │
     └──────────────────────┘
```

---

## Why SQLite (Not Neo4j or a Graph DB)

The dataset has ~17K rows across 19 entity types. The natural language queries are best expressed as SQL joins — "find orders that have deliveries but no billing" is a classic relational query, not a graph traversal.

Neo4j would require a running server, authentication, Cypher query generation (less well-supported by LLMs than SQL), and would complicate the deployment significantly.

SQLite gives us: zero infrastructure, fast startup, familiar SQL for the LLM to generate, and easy debugging (just open the .db file). We build the graph structure in-memory with NetworkX purely for visualization and node-expansion — we don't need to query it for the chat feature.

The graph complements the relational layer — it's not a replacement.

---

## Data Flow — Query Execution

```
User types: "Which products appear in the most billing documents?"
                          │
                          ▼
              POST /api/query { question: "..." }
                          │
        ┌─────────────────▼─────────────────────┐
        │  1. GUARDRAIL CHECK                    │
        │     LLM call (temp=0.0, max_tokens=10) │
        │     "Is this about O2C data? yes/no"   │
        │     If no → return canned message      │
        └─────────────────┬─────────────────────┘
                          │ yes
        ┌─────────────────▼─────────────────────┐
        │  2. SQL GENERATION                     │
        │     LLM call (temp=0.0, max_tokens=500)│
        │     System: schema + few-shot examples │
        │     User: the question                 │
        │     Returns: raw SQL string            │
        │     Validate: must start with SELECT   │
        └─────────────────┬─────────────────────┘
                          │
        ┌─────────────────▼─────────────────────┐
        │  3. SQL EXECUTION                      │
        │     sqlite3.execute(sql)               │
        │     Fetch up to 100 rows               │
        │     If error → return friendly message │
        └─────────────────┬─────────────────────┘
                          │
        ┌─────────────────▼─────────────────────┐
        │  4. ANSWER GENERATION                  │
        │     LLM call (temp=0.3, max_tokens=300)│
        │     System: "Answer based on this data"│
        │     User: question + sql + rows        │
        │     Returns: natural language answer   │
        └─────────────────┬─────────────────────┘
                          │
                          ▼
              { answer, sql, rows, on_topic: true }
```

---

## LLM Prompting Strategy

### SQL Generation Prompt

The system prompt contains three things:

**1. Full schema context** — all table names, column names, and types. The LLM needs to know exactly what's available. No hallucinated table names if the schema is explicit.

**2. Relationship hints** — comments in the schema explaining the foreign keys:
```sql
-- outbound_delivery_items.reference_sd_document = sales_order_headers.sales_order
-- billing_document_items.reference_sd_document = outbound_delivery_headers.delivery_document
-- billing_document_headers.accounting_document = journal_entry_items.accounting_document
```

**3. Few-shot examples** — 4 Q&A pairs covering the assignment's example queries. This is the most important part. LLMs generate much better SQL with examples than with instructions alone.

The user turn is just: `Generate SQL for: {question}`. Nothing else.

### Answer Generation Prompt

Simpler. System: "You are answering questions about SAP business data. Answer in 2-4 sentences based only on the provided query results. Do not make up data."

User turn: the question + the SQL + the result rows (JSON, truncated to 50 rows if needed).

### Guardrail Prompt

One-shot classification. System: "You classify questions as on-topic or off-topic for an SAP Order-to-Cash dataset. On-topic questions ask about sales orders, deliveries, billing documents, payments, customers, or products. Answer only 'yes' or 'no'."

User turn: the question.

---

## Graph Data Model

### Node Types and IDs

| Type | ID Pattern | Example |
|------|-----------|---------|
| SalesOrder | `so_{salesOrder}` | `so_740506` |
| Delivery | `del_{deliveryDocument}` | `del_80737721` |
| BillingDocument | `bill_{billingDocument}` | `bill_90504259` |
| Customer | `bp_{businessPartner}` | `bp_310000108` |
| Product | `prod_{product}` | `prod_S8907367001003` |
| Plant | `plant_{plant}` | `plant_1920` |
| JournalEntry | `je_{accountingDocument}` | `je_9400000260` |
| Payment | `pay_{accountingDocument}` | `pay_9400635977` |

### Edge Types

```
SalesOrder ──[HAS_ITEM]──────────────► SalesOrderItem (virtual, embedded in SO node)
SalesOrder ──[SOLD_TO]───────────────► Customer
Delivery   ──[REFERENCES_ORDER]──────► SalesOrder
BillingDoc ──[REFERENCES_DELIVERY]───► Delivery
BillingDoc ──[BILLED_TO]─────────────► Customer
BillingDoc ──[POSTED_TO]─────────────► JournalEntry
JournalEntry ──[CLEARED_BY]──────────► Payment
SalesOrderItem ──[CONTAINS_PRODUCT]──► Product
Delivery ──[SHIPPED_FROM]────────────► Plant
```

### What Does NOT Become a Graph Node

- `sales_order_schedule_lines` — supporting detail, embedded in SalesOrder properties
- `customer_company_assignments` / `customer_sales_area_assignments` — embedded in Customer
- `product_descriptions` — merged into Product node as a property
- `product_plants` (3K rows) — aggregated as a count on Product node
- `product_storage_locations` (16K rows) — completely excluded from graph, only in SQLite

---

## SQLite Schema — Key Relationships

```
sales_order_headers
    │ sales_order
    ├──────────────────── sales_order_items.sales_order
    │                         │ material ─────────────── products.product
    │                         │ production_plant ──────── plants.plant
    │
    │ sold_to_party ────────── business_partners.business_partner
    │
outbound_delivery_items
    │ reference_sd_document ── sales_order_headers.sales_order
    │ delivery_document ─────── outbound_delivery_headers.delivery_document
    │
billing_document_items
    │ reference_sd_document ── outbound_delivery_headers.delivery_document
    │ billing_document ──────── billing_document_headers.billing_document
    │
billing_document_headers
    │ accounting_document ───── journal_entry_items.accounting_document
    │ sold_to_party ─────────── business_partners.business_partner
    │
journal_entry_items
    │ clearing_accounting_document ── payments.accounting_document
    │ customer ──────────────────── business_partners.business_partner
```

This chain is the O2C flow:
```
SalesOrder → DeliveryItem (ref SO) → BillingItem (ref Delivery) → JournalEntry (ref BillingDoc) → Payment
```

---

## Frontend Component Design

```
app/page.tsx
├── GraphView (left panel)
│   ├── ForceGraph2D (react-force-graph-2d, dynamic import)
│   │   ├── nodes: colored by type
│   │   ├── links: labeled by edge type
│   │   └── events: onClick, onRightClick (expand)
│   └── NodePanel (overlay, shown on click)
│       ├── type badge
│       ├── properties list (key: value)
│       └── "Expand neighbors" button
│
└── ChatPanel (right panel)
    ├── MessageList (scrollable)
    │   └── MessageBubble
    │       ├── user: right-aligned
    │       └── assistant:
    │           ├── answer text
    │           └── <details> SQL block (collapsed by default)
    └── InputBar
        ├── text input
        └── send button
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/graph` | Returns initial graph (core entities, ~500 nodes) |
| GET | `/api/graph/node/{id}` | Returns one node's properties + immediate neighbors |
| POST | `/api/query` | Natural language → SQL → answer |
| GET | `/api/status` | Health check: backend, SQLite, LLM |

### `POST /api/query` request/response

```json
// Request
{ "question": "Which products are in the most billing documents?" }

// Response
{
  "answer": "Product S8907367001003 appears in 12 billing documents, making it the most frequently billed item...",
  "sql": "SELECT material, COUNT(DISTINCT billing_document) as cnt FROM billing_document_items GROUP BY material ORDER BY cnt DESC LIMIT 5",
  "rows": [
    { "material": "S8907367001003", "cnt": 12 },
    ...
  ],
  "on_topic": true
}

// Off-topic response
{
  "answer": "This system is set up to answer questions about the SAP Order-to-Cash dataset only. Try asking about sales orders, deliveries, billing documents, or payments.",
  "sql": null,
  "rows": [],
  "on_topic": false
}
```

---

## Startup Sequence

```
FastAPI startup event fires
        │
        ▼
Does o2c.db exist?
    No  → run loader.py → create all tables → insert all JSONL data
    Yes → skip (fast startup on redeploy)
        │
        ▼
Build NetworkX graph in memory
(queries SQLite for core entities)
        │
        ▼
App ready to serve requests
```

Loading the data on first run takes ~5–10 seconds. Subsequent starts are instant.

---

## Deployment Architecture

### Render (Primary)

```
GitHub Repo
    │
    ├── Backend Web Service (Python 3.11)
    │   buildCommand: pip install + python db/loader.py
    │   startCommand: uvicorn main:app ...
    │   Persistent Disk: /app/data (holds o2c.db + JSONL files)
    │
    └── Frontend Web Service (Node 20)
        buildCommand: npm ci + npm run build
        startCommand: npm run start
        NEXT_PUBLIC_API_URL → backend URL
```

### Docker (Fallback — one command)

```bash
cp .env.example .env
# add OPENROUTER_API_KEY
docker compose up --build
# App: http://localhost:3000
# API: http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## Performance Notes

| Operation | Latency |
|-----------|---------|
| Initial data load (first run) | 5–10s |
| Graph build from SQLite | < 1s |
| GET /api/graph (serialization) | < 200ms |
| Guardrail LLM check | 1–3s |
| SQL generation LLM call | 2–5s |
| SQLite query execution | < 50ms |
| Answer generation LLM call | 2–4s |
| Total query round-trip | 6–12s |

The two LLM calls (guardrail + generation) are the bottleneck. They run sequentially. If performance is a concern, the guardrail can be skipped for clearly domain-specific questions (though this is a bonus optimization, not required).

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | Free key from openrouter.ai |
| `DATA_DIR` | No | Path to sap-o2c-data folder (default: `./data/sap-o2c-data`) |
| `DB_PATH` | No | SQLite file path (default: `./o2c.db`) |

---

## Security Architecture

Every layer has a specific control. None of them are redundant — they protect against different attack surfaces.

```
THREAT                   LAYER          CONTROL
─────────────────────────────────────────────────────────────────
DDoS / LLM cost abuse    Network        slowapi: 10/min on /api/query
                                        30/min on /api/graph
                                        60/min on /api/status

SQL injection via LLM    Service        run_query() allowlist:
                                        only SELECT/WITH allowed
                                        single-statement enforcement
                                        (no ; stacking)

SQL injection via user   DB             parameterized queries for all
input (non-LLM)                         direct sqlite3 calls

XSS via API responses    HTTP Headers   X-Content-Type-Options: nosniff
                                        X-Frame-Options: DENY
                                        X-XSS-Protection: 1; mode=block
                                        Referrer-Policy: no-referrer

XSS in frontend          React          no dangerouslySetInnerHTML anywhere
                                        React's JSX escaping handles rest

LLM prompt injection     LLM Layer      question max 500 chars
(jailbreak via chat)                    non-printable chars stripped
                                        LLM is not allowed to run code

Config/secret leakage    Config         pydantic-settings reads .env
                                        logging never emits secret values
                                        API key never in HTTP responses

Oversized request body   Middleware     10KB body size limit on POST routes

CORS misconfiguration    CORS           allow_origins reads from env var
                                        not hardcoded, not wildcard in prod
```

---

## Scalability Path

The system is deliberately simple for its current scale (~17K rows, single user). Here's what changes at each growth stage and why:

### Current state
- SQLite handles reads instantly at this data volume
- NetworkX graph fits in ~50MB RAM
- OpenRouter free tier handles ~20 queries/minute
- Single FastAPI process, single Render web service

### 10x scale (thousands of queries/day)
- **First bottleneck**: OpenRouter free tier rate limits hit
- **Fix**: upgrade to paid OpenRouter tier or switch to hosted Llama endpoint (Groq, Together.ai)
- **Second bottleneck**: SQLite write lock during data refreshes (if we add live data)
- **Fix**: move to Postgres on Render's managed DB

### 100x scale (tens of thousands of users)
- SQLite → **Postgres** (connection pooling via pgbouncer, read replicas for analytics queries)
- Single FastAPI process → **multiple uvicorn workers** behind Nginx
- In-memory graph → **cached in Redis** (serialize with networkx's JSON format, rebuild on data change)
- LLM calls → add **semantic response cache**: embed the question, check Redis for a similar past question, return cached answer if similarity > 0.95
- Add **async job queue** (Celery + Redis) for long-running queries so HTTP doesn't block

### Enterprise / global (1B users)
Full re-architecture — the pipeline concept stays, the infrastructure is completely different:

```
Users (global)
    │
    ▼
CDN (Cloudflare) — serves frontend static build from edge
    │
    ▼
API Gateway (Kong / AWS API GW) — auth, rate limiting, routing
    │
    ├──► Graph Service (pods on k8s)
    │         └── Neo4j cluster (graph queries, read replicas per region)
    │
    ├──► Query Service (pods on k8s)
    │         ├── Postgres (Citus distributed) — relational queries
    │         ├── Redis — semantic response cache
    │         └── Inference cluster (vLLM on GPU) — dedicated LLM
    │
    └──► Observability
              ├── Distributed tracing: Jaeger / Tempo
              ├── Metrics: Prometheus + Grafana
              ├── Alerting: PagerDuty
              └── SLOs: p99 query < 5s, availability > 99.9%
```

What stays the same at any scale: the text-to-SQL pipeline, the prompt strategy, the graph model, the two-step LLM pattern. The ideas scale even when the infrastructure doesn't.

---

## docs/ Folder

The `docs/` folder contains deep technical documentation for every part of the system. Each file is written for a senior engineer who wants to understand not just what the code does, but why every decision was made.

| File | Contents |
|------|----------|
| `overview.md` | What this is, the O2C business flow, key decisions at a glance |
| `architecture.md` | System diagram, component responsibilities, data flow |
| `system-design-hld.md` | HLD: components, why this architecture, scalability path to 1B users |
| `system-design-lld.md` | LLD: each module, function signatures, request lifecycle |
| `api-reference.md` | Every endpoint: schema, errors, rate limits, curl examples |
| `database-schema.md` | All tables, columns, ER diagram, index strategy, why SQLite |
| `graph-model.md` | Node types, edge types, ID patterns, why NetworkX |
| `llm-pipeline.md` | Full prompts, few-shot rationale, failure modes, model choice |
| `security.md` | Every control, the threat it stops, what's intentionally missing |
| `scalability.md` | Bottlenecks at current scale, fixes at 10x / 100x / 1B users |
| `frontend.md` | Component tree, state management, react-force-graph-2d choice |
| `deployment.md` | Render + Docker step-by-step, troubleshooting common failures |
| `uml-diagrams.md` | Sequence diagrams, class diagram, ER diagram in Mermaid |
| `future-improvements.md` | Conversation memory, node highlighting, streaming, clustering |
