# LLM Orchestration & Prompt Inventory

This document tracks the system prompts, few-shot examples, and orchestration logic used by the SAP O2C Graph Query System.

## LLM Strategy (Gemini 2.5 Flash)

As of version 0.2.0, we use the **Gemini 2.5 Flash** model via the native `google-generativeai` SDK. This model provides the best balance of speed, low-latency, and SQL generation accuracy for our dataset.

### 1. Guardrail Prompt (Topic Classification)
**File**: `backend/llm/guardrails.py`

**System Context**:
> You classify questions as on-topic or off-topic for an SAP Order-to-Cash (O2C) dataset. 
> On-topic: sales orders, deliveries, billing documents, payments, journal entries, customers, products, plants, or SAP business processes. 
> Answer ONLY 'yes' or 'no'.

**User Prompt Template**:
```
User Question: {question}
Answer 'yes' or 'no':
```

---

### 2. SQL Generation Prompt (Text-to-SQL)
**File**: `backend/prompts/sql_prompt.py`

**System Context**:
Identifies the core tables (`sales_orders`, `deliveries`, `billing_documents`, `journal_entries`, `partners`, `products`) and their relationships. Explicitly instructs the LLM to use `SELECT` only and join on the technical keys (e.g., `vbeln` for Sales Documents).

**Few-Shot Examples**:
- **Q**: "What are the top 5 sales orders by value?"
- **SQL**: `SELECT Vbeln, Netwr FROM sales_orders ORDER BY Netwr DESC LIMIT 5;`

---

### 3. Natural Language Responder
**File**: `backend/llm/responder.py`

**System Context**:
Instructs the model to take a user question, the SQL executed, and the raw JSON results, then combine them into a concise, business-friendly summary.

---

## Technical Implementation (Resilience)

All LLM calls are orchestrated using the `tenacity` library to handle rate limits (429 errors).

```python
from tenacity import retry, wait_random_exponential, stop_after_attempt
from google.api_core import exceptions

retry_gemini = retry(
    wait=wait_random_exponential(min=4, max=15),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(exceptions.ResourceExhausted)
)

@retry_gemini
async def call_llm(prompt):
    model = genai.GenerativeModel("gemini-2.5-flash")
    return await model.generate_content_async(prompt)
```

## Prompt Evolution Logs
- **v0.1.0**: Used OpenAI-compatible messages (`role: system/user`).
- **v0.2.0**: Migrated to direct `GenerativeModel` calls. Switched to single-string prompts for internal guardrails to minimize token overhead and latency.
