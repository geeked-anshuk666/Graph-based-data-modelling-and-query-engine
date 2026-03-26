import logging

from llm.client import get_client

logger = logging.getLogger(__name__)

_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

SYSTEM_PROMPT = (
    "You classify questions as on-topic or off-topic for an SAP Order-to-Cash dataset. "
    "On-topic questions ask about sales orders, deliveries, billing documents, payments, "
    "journal entries, customers, products, plants, or anything related to SAP business processes. "
    "Questions about what terms mean in the O2C context are on-topic. "
    "Off-topic: general knowledge, coding, creative writing, other companies. "
    "Answer only 'yes' or 'no'."
)


async def is_on_topic(question: str) -> bool:
    """Short LLM classification call. Returns True if the question is about O2C data."""
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0.0,
            max_tokens=10,
        )
        answer = resp.choices[0].message.content.strip().lower()
        return answer.startswith("yes")
    except Exception:
        logger.exception("guardrail check failed, defaulting to on-topic")
        # fail open — if guardrail is down, let the query through
        # rather than blocking legitimate questions
        return True
