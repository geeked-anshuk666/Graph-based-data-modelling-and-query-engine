from openai import OpenAI

from config import settings

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if settings.gemini_api_key:
            # use Google AI Studio (Gemini) direct access
            _client = OpenAI(
                api_key=settings.gemini_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
        else:
            # Fallback to OpenRouter (default)
            _client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
    return _client
