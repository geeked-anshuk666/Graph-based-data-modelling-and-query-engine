# PRD — SAP Order-to-Cash Graph Query System

**Version 1.0** | **Status: Ready to Build**

---

## 1. What This Is

Business data in SAP is spread across dozens of tables. A sales transaction touches at least six entity types — sales order, delivery, billing document, journal entry, payment, customer — and tracing a complete order flow means stitching together foreign keys across all of them.

This app makes that invisible structure visible. It ingests the SAP O2C dataset, builds an interactive graph of how the entities connect, and lets a user ask plain-English questions and get answers that are backed by actual data — with the SQL shown so nothing is a black box.

---

## 2. Who This Is For

A single evaluator (the hiring team) who will:
- Explore the graph to understand the dataset structure
- Ask the 3 example queries from the assignment brief
- Try off-topic questions to test the guardrails
- Inspect the SQL that backs each answer
- Run the app locally or use the hosted link

No auth required. One user.

---

## 3. Goals

| # | Goal | How We Know It's Met |
|---|------|---------------------|
| G1 | Graph is explorable | User can click any node, see its properties, expand its neighbors |
| G2 | Chat answers are grounded | Every answer includes the SQL used to generate it |
| G3 | All 3 example queries work | Tested before submission |
| G4 | Guardrails work | Off-topic questions return the canned message, not a hallucinated answer |
| G5 | App is live | Public URL accessible without setup |
| G6 | Code looks human-written | A senior engineer reviewing the GitHub repo doesn't immediately think "AI wrote this" |

---

## 4. Non-Goals

- Multi-user support or authentication
- Editing the data through the UI
- Real-time SAP data sync
- Saving chat history between sessions
- Supporting queries in languages other than English

---

## 5. Features

### F1: Graph Visualization

**Description**: An interactive force-directed graph of the O2C entity relationships, rendered in the browser.

**Requirements**:
- FR1.1: Render nodes for: SalesOrders, Deliveries, BillingDocuments, Customers, Products, Plants, JournalEntries, Payments
- FR1.2: Color-code nodes by type (each type gets a distinct color with a visible legend)
- FR1.3: Draw directed edges between related nodes, labeled by relationship type
- FR1.4: Click a node → open a metadata panel showing all properties of that entity
- FR1.5: "Expand" a node → fetch and render its immediate neighbors (those not already visible)
- FR1.6: Graph supports pan and zoom
- FR1.7: Show node label (e.g., "SO 740506", "Customer: Cardenas, Parker and Avila") on or near the node
- FR1.8: Initial graph loads within 3 seconds — do not dump all 16K product_storage_location rows into the view
- FR1.9: Graph state persists within the session (expanding nodes adds to the view, doesn't reset it)

---

### F2: Node Metadata Panel

**Description**: A sidebar or overlay showing the full details of a clicked node.

**Requirements**:
- FR2.1: Show entity type as a badge (e.g., "Sales Order", "Customer")
- FR2.2: Show all meaningful properties in a clean key-value layout
  - SalesOrder: order number, creation date, total amount, currency, delivery status, billing status, customer
  - Delivery: delivery doc number, creation date, shipping point, picking status, goods movement status
  - BillingDocument: doc number, type, date, amount, cancelled flag, sold-to party
  - Customer: name, city, country, business partner ID
  - Product: product ID, type, weight, base unit, description
  - Plant: plant code, name, sales organization
- FR2.3: "Expand in graph" button that adds neighbors to the graph
- FR2.4: Close / dismiss button
- FR2.5: Panel updates when a different node is clicked without needing to close first

---

### F3: Chat Query Interface

**Description**: A conversational interface where users ask natural language questions about the dataset and receive grounded, SQL-backed answers.

**Requirements**:
- FR3.1: Text input + send button at the bottom of the chat panel
- FR3.2: Message history scrolls upward as conversation grows
- FR3.3: User messages displayed right-aligned; assistant messages left-aligned
- FR3.4: Each assistant response includes a collapsible SQL block showing the query used
  - Collapsed by default, expandable with a click
  - SQL is syntax-highlighted or shown in a monospace block
- FR3.5: Loading state shown while query is processing (~6–12 seconds expected)
- FR3.6: The system answers all 3 example queries from the assignment:
  - "Which products are associated with the highest number of billing documents?"
  - "Trace the full flow of billing document 90504259 (Sales Order → Delivery → Billing → Journal Entry)"
  - "Identify sales orders that have incomplete flows (delivered but not billed, billed without delivery)"
- FR3.7: Answers are specific, reference actual IDs/amounts from the data, and are not generic
- FR3.8: If the generated SQL returns no rows, response says "No matching records found" — does not hallucinate data

---

### F4: Guardrails

**Description**: The system must refuse to answer questions outside the domain of the dataset.

**Requirements**:
- FR4.1: Off-topic questions return this exact message (or close variant):
  > "This system is set up to answer questions about the SAP Order-to-Cash dataset only. Try asking about sales orders, deliveries, billing documents, or payments."
- FR4.2: Guardrail triggers on:
  - General knowledge questions ("What is the capital of France?")
  - Creative writing requests ("Write me a poem")
  - Coding questions ("How do I sort a list in Python?")
  - Questions about other companies' data or systems
- FR4.3: Guardrail must NOT trigger on legitimate O2C questions, including edge cases like:
  - "What does a billing document cancellation mean?" (domain explanation — allow it)
  - "How many customers are there?" (simple count — allow it)
- FR4.4: Guardrail is LLM-based (classification call), not a keyword blocklist
- FR4.5: Off-topic responses are visually distinct from normal answers (e.g., gray/muted styling)

---

### F5: Status Page

**Description**: A simple health check page at `/status`.

**Requirements**:
- FR5.1: Three cards: Backend (FastAPI), Database (SQLite), LLM (OpenRouter)
- FR5.2: Each card shows: status indicator (green/red), service name, latency in ms
- FR5.3: Auto-refreshes every 30 seconds
- FR5.4: Manual refresh button
- FR5.5: If LLM is down: shows advisory "Chat queries unavailable. Graph exploration still works."

---

### F6: Required Submission Files

- FR6.1: `README.md` — must explain: architecture decisions, DB choice rationale, LLM prompting strategy, guardrail implementation, how to run locally, what's done, what's not done
- FR6.2: `AI_NOTES.md` — what was AI-assisted vs. manually written/verified
- FR6.3: `ABOUTME.md` — name + resume
- FR6.4: `PROMPTS_USED.md` — development prompt log (this is an explicit evaluation criterion)
- FR6.5: `.env.example` — all env vars with placeholder values

---

## 6. User Stories

```
As an evaluator, I want to explore the graph visually
so that I can understand how SAP O2C entities connect
without reading documentation.

As an evaluator, I want to click on a sales order node
so that I can see its amount, customer, and status at a glance.

As an evaluator, I want to ask "trace the full flow of billing document X"
so that I can see the complete Sales Order → Delivery → Billing → Journal chain.

As an evaluator, I want to ask an off-topic question
so that I can verify the guardrails work as described.

As an evaluator, I want to see the SQL behind each answer
so that I can verify the response is grounded in real data.

As an evaluator, I want to open the app on the provided link
without cloning a repo or installing anything.
```

---

## 7. Example Queries — Required Coverage

These must all work correctly at demo time:

| Query | Expected Output Type |
|-------|---------------------|
| "Which products appear in the most billing documents?" | Ranked list with product IDs and counts |
| "Trace the full flow of billing document 90504259" | Multi-stage result: SO → Delivery → Billing → Journal |
| "Find sales orders delivered but not billed" | List of sales order IDs with delivery but no billing |
| "Find orders billed without a delivery" | List of billing docs with no matching delivery |
| "Which customer has the highest total billed amount?" | Customer name + total amount |
| "Show me cancelled billing documents" | List of cancelled doc IDs |
| "What is the total payment amount for customer 320000083?" | Sum from payments table |

Guardrail test cases (must return the canned message):

| Query | Should Return |
|-------|--------------|
| "What is the capital of France?" | Guardrail message |
| "Write me a haiku about shipping" | Guardrail message |
| "How do I use Python pandas?" | Guardrail message |

---

## 8. UX Notes

### Layout
- Main page: two-column split — graph left, chat right
- Graph panel: full height, pan/zoom enabled, legend at top or bottom
- Chat panel: fixed-height scrollable message area, input pinned to bottom

### Loading States
- Graph initial load: skeleton or spinner with "Loading graph..."
- Node expand: spinner on the node being expanded
- Chat response: typing indicator / spinner with "Thinking..."

### Empty States
- Chat with no messages: "Ask a question about the dataset to get started. For example: 'Which products appear in the most billing documents?'"

### Error States
- SQL execution error: "Couldn't run that query — try rephrasing the question."
- LLM timeout: "The AI took too long to respond. Please try again."
- Graph load failure: "Failed to load graph. Check the status page."

---

## 9. Edge Cases

| Scenario | Expected Behavior |
|----------|-----------------|
| User asks about a billing document ID that doesn't exist | "No records found for billing document [X] in the dataset." |
| LLM generates INSERT/UPDATE SQL | Blocked server-side — only SELECT allowed |
| Graph node has no neighbors | NodePanel opens, "No connected nodes found" in expand section |
| OpenRouter returns rate limit (429) | Retry once after 2s, then show "AI is temporarily rate-limited. Try again in a moment." |
| User asks a borderline question ("What does O2C mean?") | Guardrail allows it — it's domain-related |
| Very long query result (100+ rows) | Truncate to 50 rows in the answer, note "showing first 50 of N results" |

---

## 10. Design Direction

**Aesthetic**: Dark, data-dense, professional. Like a Bloomberg terminal met a modern SaaS product. Not playful, not a demo toy — it should feel like a real internal tool.

**Color Palette**:
- Background: `#0f1117`
- Surface: `#1a1d27`
- Border: `#2d3748`
- Graph node colors:
  - SalesOrder: `#3b82f6` (blue)
  - Delivery: `#10b981` (emerald)
  - BillingDoc: `#f59e0b` (amber)
  - Customer: `#8b5cf6` (violet)
  - Product: `#06b6d4` (cyan)
  - Plant: `#6b7280` (gray)
  - JournalEntry: `#f97316` (orange)
  - Payment: `#ef4444` (red)
- Chat user messages: `#3b82f6` bg
- Chat assistant messages: `#1a1d27` bg
- Text: `#f1f5f9`
- Muted text: `#94a3b8`
- SQL block: monospace, `#0f172a` bg, `#a3e635` text

**Key interaction moments:**
- Clicking a node should feel instant — no delay in opening the panel
- The "expand" animation (new nodes flying in) is the most memorable UI moment — make it feel good
- SQL block reveal on click should be smooth (CSS transition, not a jarring pop)

---

## 11. Security Requirements (Non-Functional)

These are mandatory. They must be implemented before demo, not as a cleanup pass.

| Requirement | Implementation | Why It Matters |
|-------------|---------------|----------------|
| Rate limiting | slowapi: 10/min on `/api/query`, 30/min on graph routes | LLM calls cost money; without this a single bad actor can drain the API quota |
| DDoS protection | Rate limiter + 10KB body size cap on POST | Prevents volumetric abuse and oversized payload attacks |
| SQL injection (LLM) | `run_query()` SELECT-only allowlist, single-statement enforcement | A jailbroken LLM prompt could generate `DROP TABLE`; this is the last line of defense |
| SQL injection (direct) | Parameterized queries everywhere sqlite3 is called directly | Classic injection vector; `?` placeholders prevent it entirely |
| XSS via headers | `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` on every response | Stops MIME sniffing, clickjacking, and reflected XSS |
| XSS in frontend | No `dangerouslySetInnerHTML` anywhere; SQL shown in `<pre><code>`, not innerHTML | React's JSX escaping handles the rest |
| Input sanitization | Pydantic `QueryRequest`: 500-char max, non-printable chars stripped | Prevents LLM prompt manipulation via unusual Unicode or control characters |
| CORS | `ALLOWED_ORIGINS` from env var, not hardcoded or wildcard | Wildcard CORS in production allows any site to make credentialed requests |
| Config security | `pydantic-settings` reads `.env`; no `os.environ` scattered in code; API key never logged | One place to audit secret access |

---

## 12. Documentation Requirements

The `docs/` folder is a first-class deliverable, not an afterthought. It must contain 14 files covering every architectural decision, concept, and system design aspect of the codebase.

| File | Must Cover |
|------|-----------|
| `overview.md` | What this is, the O2C business flow, key decisions |
| `architecture.md` | System diagram, component responsibilities, data flow |
| `system-design-hld.md` | HLD: architecture choices, alternatives rejected, scalability path to 1B users |
| `system-design-lld.md` | LLD: module interfaces, request lifecycle, example inputs/outputs at each step |
| `api-reference.md` | Every endpoint with schema, errors, rate limits, and curl examples |
| `database-schema.md` | All tables, ER diagram in Mermaid, index strategy, why SQLite |
| `graph-model.md` | Node types, edge types, ID patterns, why NetworkX |
| `llm-pipeline.md` | Full prompts, few-shot rationale, failure modes, model choice |
| `security.md` | Every control with the specific threat it stops |
| `scalability.md` | Bottlenecks at current scale and the re-architecture path at 10x / 100x / 1B users |
| `frontend.md` | Component tree, state management, react-force-graph-2d rationale |
| `deployment.md` | Render + Docker step-by-step, troubleshooting |
| `uml-diagrams.md` | Sequence diagrams, class diagram, ER diagram — all in Mermaid syntax |
| `future-improvements.md` | Conversation memory, node highlighting, streaming, clustering — with implementation notes |

**Standard for all docs files:** Written for a senior engineer joining the project. Plain prose with code examples. Honest about tradeoffs. No marketing language.

---

## 13. CHANGELOG Requirements

`CHANGELOG.md` must be updated after every commit — not once at the end.

Each entry must include:
- Version number and date
- What was added, changed, or fixed
- For bugs: what was wrong, what caused it, and how it was found

This is explicitly evaluated. A CHANGELOG with 2 entries at the end of the project is worse than no changelog. The evaluators want to see the work happen in real time.

---

## 14. Acceptance Criteria

Done when:

1. **[ ] Live URL** — accessible at a public Render URL, no setup required for the evaluator
2. **[ ] GitHub repo** — public, complete code, all required files
3. **[ ] Graph renders** — 100+ nodes visible, colored by type, edges drawn, legend shown
4. **[ ] Node click** — metadata panel opens with correct entity data
5. **[ ] Node expand** — neighbors are fetched and merged into the graph
6. **[ ] All 3 assignment queries answered** — with correct, SQL-backed, specific responses
7. **[ ] SQL visible** — every chat response has a collapsible SQL block
8. **[ ] Guardrails work** — "What is the capital of France?" returns the canned message, not a hallucinated answer
9. **[ ] Status page works** — all 3 services show real health with latency
10. **[ ] Rate limiting works** — 11th `/api/query` request in a minute returns HTTP 429
11. **[ ] SQL injection blocked** — LLM-generated `DROP TABLE` attempt is rejected by `run_query()`
12. **[ ] Docker works** — `docker compose up --build` after filling `.env` starts both services
13. **[ ] README comprehensive** — covers all 18 sections listed in AI_rules.md Section 14
14. **[ ] docs/ complete** — all 14 files exist and are substantive (not placeholder stubs)
15. **[ ] CHANGELOG up to date** — entry for every meaningful commit, including bugs found and fixed
16. **[ ] Code looks human-written** — variable names, comments, error handling, and structure pass the "would a senior engineer think an AI wrote this?" test
