import logging
import time

from fastapi import APIRouter, Request
from google.api_core.exceptions import ResourceExhausted

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

RATE_LIMIT_RESPONSE = QueryResponse(
    answer=(
        "The AI is currently busy handling many requests (Rate Limit). "
        "Please wait 15-20 seconds and try again."
    ),
    sql=None,
    rows=[],
    on_topic=True,
)


@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query(req: QueryRequest, request: Request):
    """Natural language → SQL → answer pipeline with resilience."""
    start = time.time()

    try:
        # step 1: guardrail
        logger.info("checking guardrails for q=%.40s", req.question)
        on_topic = await guardrails.is_on_topic(req.question)
        if not on_topic:
            logger.info("off-topic question rejected | q=%.40s", req.question)
            return OFF_TOPIC_RESPONSE

        # step 2: generate SQL
        logger.info("generating SQL for q=%.40s", req.question)
        sql = await sql_generator.generate_sql(req.question)

        # step 3: execute SQL
        logger.info("executing SQL: %.100s", sql)
        conn = get_db()
        try:
            rows = run_query(sql, conn)
            logger.info("SQL executed, found %d rows", len(rows))
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
        logger.info("generating natural language answer...")
        answer = await responder.build_answer(req.question, sql, rows)

        elapsed = time.time() - start
        logger.info("query done in %.2fs | rows=%d | q=%.40s", elapsed, len(rows), req.question)
        return QueryResponse(answer=answer, sql=sql, rows=rows, on_topic=True)

    except ResourceExhausted:
        logger.warning("Gemini rate limit exhausted after all retries | q=%.40s", req.question)
        return RATE_LIMIT_RESPONSE
    except Exception:
        logger.exception("backend query pipeline failed | q=%.40s", req.question)
        return QueryResponse(
            answer="Something went wrong on our end. Please try again in a moment.",
            sql=None,
            rows=[],
        )
