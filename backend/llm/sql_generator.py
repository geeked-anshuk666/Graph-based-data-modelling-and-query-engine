import logging
import re

from llm.client import get_model, settings
from prompts.sql_prompt import build_sql_messages

logger = logging.getLogger(__name__)

# strip markdown code fences the LLM sometimes wraps SQL in
_FENCE_RE = re.compile(r"^```(?:sql)?\s*\n?", re.MULTILINE)
_FENCE_END = re.compile(r"\n?```\s*$", re.MULTILINE)


async def generate_sql(question: str) -> str:
    """Call the LLM to generate SQL from a natural language question."""
    if not settings.gemini_api_key:
        logger.error("No GEMINI_API_KEY found, cannot generate SQL")
        raise ValueError("LLM configuration missing")

    try:
        model = get_model()
        
        # convert OpenAI messages to a single prompt for simplicity
        messages = build_sql_messages(question)
        # system prompt is first message, user prompt is second
        system_content = messages[0]["content"]
        user_content = messages[1]["content"]
        
        prompt = f"{system_content}\n\n{user_content}"

        response = await model.generate_content_async(
            prompt,
            generation_config={"temperature": 0.0, "max_output_tokens": 1000}
        )

        content = response.text if response and response.text else ""
        raw = content.strip()

        # strip code fences if present
        sql = _FENCE_RE.sub("", raw)
        sql = _FENCE_END.sub("", sql).strip()

        # basic sanity — catch obvious garbage early
        if not sql.upper().startswith(("SELECT", "WITH", "EXPLAIN")):
            logger.warning("LLM returned non-SELECT SQL: %.80s", sql)
            # if it's empty or garbage, we might want to retry or fail
            if not sql:
                raise ValueError("LLM generated empty SQL")
        
        return sql
    except Exception as e:
        logger.exception("sql generation failed | q=%s", question)
        raise e
