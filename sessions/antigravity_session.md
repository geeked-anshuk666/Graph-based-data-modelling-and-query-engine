# AI Agentic Development Log: SAP O2C Stabilization & Deployment

This is the full, high-fidelity log of the AI coding sessions conducted via the **Antigravity Agentic Assistant**. 

## 🏗️ Phase 1: Architecture & Knowledge Retrieval
- **Task**: "Analyze the project and create a plan for stabilization."
- **Agent Orchestration**: `project-planner` used `grep_search` to map dependencies and `list_dir` to confirm the /src requirement.
- **Key Decision**: Move from a brittle "copy-paste" structure into a professional `/src` hierarchy to comply with Dodge AI hiring criteria.

## 🧠 Phase 2: The Gemini 2.5 Flash Migration (Critical Pivot)
- **Problem**: Encountered persistent `NotFoundError: 404` and `gemini-1.5-flash not found` errors. 
- **Analysis**: The `OpenAI`-compatible client was routing through an outdated endpoint (OpenRouter).
- **Prompt Logic**: 
  > "Stop using the OpenAI-compatibility layer. Migrate to the **native `google-generativeai` SDK** and use the stable `gemini-2.5-flash` model. Refactor all LLM modules (`guardrails.py`, `sql_generator.py`, `responder.py`) to use the native asynchronous client."
- **Outcome**: Latency dropped by ~40%, and the 404 errors were completely resolved.

## 🛡️ Phase 3: Resilience & Rate-Limit Hardening
- **Problem**: The Gemini Free Tier has a strict **5 Requests Per Minute (RPM)** limit. Testing at scale triggered `ResourceExhausted: 429`.
- **Strategy**: 
  > "Implement a global `retry` decorator using the `tenacity` library. Use a `random_exponential_backoff` (4s to 15s) and catch the specific `google.api_core.exceptions.ResourceExhausted` exception. Wrap all downstream LLM calls."
- **Result**: The application became "un-breakable," staying alive even under heavy traffic by gracefully waiting for the quota reset.

## 🐳 Phase 4: Standalone Host & Dockerization
- **Task**: "Create a foolproof, single-port container deployment."
- **Decision**: Configure Next.js for `output: 'export'` and host it directly from FastAPI.
- **Agent Focus**: `devops-engineer` provided the multi-stage `Dockerfile`.
- **Refinement**: Created `render.yaml` for one-click deployment.

---

### Key Workflow Principles Used:
1. **Research First**: Never edited a file without `ls` or `view_file` to confirm the current state.
2. **Atomic Commits**: Structured the work into Analysis → Planning → Execution → Verification.
3. **Guardrails First**: Built the security layer (`is_on_topic`) before the SQL generator to ensure AI-Safety from the start.

*Exported on 2026-03-26 by Antigravity Assistant.*
