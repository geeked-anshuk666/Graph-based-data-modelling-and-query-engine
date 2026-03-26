import logging

from llm.client import get_client
from prompts.answer_prompt import build_answer_messages

logger = logging.getLogger(__name__)

_MODEL = "gemini-1.5-flash"


async def build_answer(question: str, sql: str, rows: list[dict]) -> str:
    """Turn SQL results into a natural language answer."""
    if not rows:
        return "No matching records found in the dataset."

    client = get_client()
    resp = client.chat.completions.create(
        model=_MODEL,
        messages=build_answer_messages(question, sql, rows),
        temperature=0.3,
        max_tokens=300,
    )

    content = resp.choices[0].message.content or ""
    return content.strip()
