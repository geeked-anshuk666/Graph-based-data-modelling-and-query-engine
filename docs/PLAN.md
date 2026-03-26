# Master Plan: SAP O2C Graph Query System (Evaluation Ready)

## Goal Description
Build a full-stack SAP Order-to-Cash (O2C) Graph Query System with a focus on high-quality AI interaction, grounded SQL generation, and interactive visualization. This plan specifically incorporates the **Evaluation Compliance Strategy** for the Dodge AI FDE assignment.

## Evaluation Compliance Strategy (MANDATORY)
To ensure high scores in **Prompt Quality**, **Debugging Workflow**, and **Iteration Patterns**:
- **Atomic Commits**: Every change will have a descriptive commit message following `AI_rules.md` Section 9.
- **Prompt Log (`PROMPTS_USED.md`)**: Every significant LLM prompt used during development will be recorded.
- **Debugging Log (`CHANGELOG.md`)**: Root cause analysis and "Fixed" sections for every bug found during development.
- **Walkthrough Artifact**: A living `walkthrough.md` in the artifacts directory to document iteration steps and reasoning.

---

## Proposed Changes

### Component 1: Project Foundation & Ingestion
- [NEW] `.env.example`
- [NEW] `backend/requirements.txt`
- [NEW] `backend/db/schema.sql` (19 entity tables)
- [NEW] `backend/db/loader.py` (JSONL to SQLite)

### Component 2: Backend Core (FastAPI)
- [NEW] `backend/main.py` (FastAPI setup + Middleware)
- [NEW] `backend/config.py` (Pydantic Settings)
- [NEW] `backend/llm/sql_generator.py` (Few-shot prompting logic)
- [NEW] `backend/graph/builder.py` (NetworkX integration)

### Component 3: Frontend (Next.js)
- [NEW] `frontend/components/GraphView.tsx` (react-force-graph-2d)
- [NEW] `frontend/components/ChatPanel.tsx` (Chat UI + SQL blocks)

### Component 4: Documentation & Submission
- [NEW] `docs/*.md` (All 14 required technical docs)
- [NEW] `CHANGELOG.md` (Iteration log)
- [NEW] `PROMPTS_USED.md` (Prompt tracker)
- [NEW] `AI_NOTES.md` (Human vs AI breakdown)

---

## Verification Plan

### Automated Tests
- `pytest` for backend query runner and guardrails.

### Manual Verification
- Testing all 3 example queries:
  1. Products in most billing docs
  2. Full flow of billing doc 90504259
  3. Delivered but not billed orders
- Testing guardrails with "What is the capital of France?".

### ⏸️ CHECKPOINT: User Approval Required
**Do you approve of this consolidated plan? (Y/N)**
- **Y**: Proceed to Implementation Phase.
- **N**: Provide feedback for revision.
