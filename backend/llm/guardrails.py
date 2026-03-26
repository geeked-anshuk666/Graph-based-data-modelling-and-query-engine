import logging

from llm.client import get_model, settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You classify questions as on-topic or off-topic for an SAP Order-to-Cash (O2C) dataset. "
    "On-topic: sales orders, deliveries, billing documents, payments, journal entries, "
    "customers, products, plants, or SAP business processes. "
    "Answer ONLY 'yes' or 'no'."
)


async def is_on_topic(question: str) -> bool:
    """Short LLM classification call. Returns True if the question is about O2C data."""
    # if no gemini key, we might have a configuration issue
    if not settings.gemini_api_key:
        logger.warning("No GEMINI_API_KEY found, skipping guardrail check")
        return True

    try:
        model = get_model()
        # combine system + user prompt for simplicity in direct SDK
        prompt = f"{SYSTEM_PROMPT}\n\nUser Question: {question}\nAnswer 'yes' or 'no':"
        
        # generate_content_async is the async version of the Google SDK call
        response = await model.generate_content_async(
            prompt,
            generation_config={"temperature": 0.0, "max_output_tokens": 10}
        )
        
        answer = response.text.strip().lower() if response and response.text else "yes"
        return answer.startswith("yes")
    except Exception:
        logger.exception("guardrail check failed, defaulting to on-topic")
        return True
