import logging
import time

from fastapi import APIRouter, Request

from db.connection import get_db
from db.query_runner import run_query
from llm import guardrails, sql_generator, responder
from middleware.rate_limit import limiter
from models.schemas import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])

OFF_TOPIC_RESPONSE = QueryResponse(
    answer=(
        "This system is set up to answer questions about the SAP Order-to-Cash "
        "dataset only. Try asking about sales orders, deliveries, billing documents, "
        "or payments."
    ),
    sql=None,
    rows=[],
    on_topic=False,
)


@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query(req: QueryRequest, request: Request):
    """Natural language → SQL → answer pipeline.

    1. Guardrail: is the question about O2C data?
    2. Generate SQL from the question
    3. Execute the SQL safely (SELECT only)
    4. Generate a natural language answer from the results
    """
    start = time.time()

    # step 1: guardrail
    on_topic = await guardrails.is_on_topic(req.question)
    if not on_topic:
        logger.info("off-topic question rejected | q=%.40s", req.question)
        return OFF_TOPIC_RESPONSE

    # step 2: generate SQL
    try:
        sql = await sql_generator.generate_sql(req.question)
    except Exception:
        logger.exception("sql generation failed | q=%.40s", req.question)
        return QueryResponse(
            answer="Couldn't generate a query for that question — try rephrasing it.",
            sql=None,
            rows=[],
        )

    # step 3: execute SQL
    conn = get_db()
    try:
        rows = run_query(sql, conn)
    except ValueError as e:
        # run_query rejected it (not SELECT, multiple statements)
        logger.warning("query blocked | reason=%s | sql=%.80s", e, sql)
        return QueryResponse(
            answer="That query was blocked for safety reasons. Try a different question.",
            sql=sql,
            rows=[],
        )
    except Exception:
        logger.exception("query execution failed | sql=%.100s", sql)
        return QueryResponse(
            answer="Couldn't run that query — try rephrasing the question.",
            sql=sql,
            rows=[],
        )

    # step 4: generate answer
    try:
        answer = await responder.build_answer(req.question, sql, rows)
    except Exception:
        logger.exception("answer generation failed")
        answer = f"Query returned {len(rows)} rows but answer generation failed. See the SQL and data below."

    elapsed = time.time() - start
    logger.info("query done in %.2fs | rows=%d | q=%.40s", elapsed, len(rows), req.question)

    return QueryResponse(answer=answer, sql=sql, rows=rows, on_topic=True)
