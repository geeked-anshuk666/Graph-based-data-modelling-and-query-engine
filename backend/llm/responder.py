import logging

from llm.client import get_model, settings, retry_gemini
from prompts.answer_prompt import build_answer_messages

logger = logging.getLogger(__name__)


@retry_gemini
async def build_answer(question: str, sql: str, rows: list[dict]) -> str:
    """Turn SQL results into a natural language answer."""
    if not rows:
        return "No matching records found in the dataset."

    if not settings.gemini_api_key:
        logger.error("No GEMINI_API_KEY found, cannot build answer")
        return f"Query returned {len(rows)} results, but I cannot summarize them without an LLM."

    try:
        model = get_model()
        
        messages = build_answer_messages(question, sql, rows)
        system_content = messages[0]["content"]
        user_content = messages[1]["content"]
        
        prompt = f"{system_content}\n\n{user_content}"

        response = await model.generate_content_async(
            prompt,
            generation_config={"temperature": 0.3, "max_output_tokens": 1000}
        )

        content = response.text if response and response.text else ""
        return content.strip()
    except Exception:
        logger.exception("answer generation failed")
        return f"I found {len(rows)} matching records, but encountered an error generating the summary."
