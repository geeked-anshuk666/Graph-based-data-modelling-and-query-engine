import logging
import re

from llm.client import get_client
from prompts.sql_prompt import build_sql_messages

logger = logging.getLogger(__name__)

_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

# strip markdown code fences the LLM sometimes wraps SQL in
_FENCE_RE = re.compile(r"^```(?:sql)?\s*\n?", re.MULTILINE)
_FENCE_END = re.compile(r"\n?```\s*$", re.MULTILINE)


async def generate_sql(question: str) -> str:
    """Call the LLM to generate SQL from a natural language question."""
    client = get_client()
    resp = client.chat.completions.create(
        model=_MODEL,
        messages=build_sql_messages(question),
        temperature=0.0,
        max_tokens=500,
    )

    raw = resp.choices[0].message.content.strip()

    # strip code fences if present
    sql = _FENCE_RE.sub("", raw)
    sql = _FENCE_END.sub("", sql).strip()

    # basic sanity — the query_runner does the real validation,
    # but catch obvious garbage early
    if not sql.upper().startswith(("SELECT", "WITH")):
        logger.warning("LLM returned non-SELECT SQL: %.80s", sql)
        raise ValueError("LLM generated non-SELECT query")

    return sql
