import google.generativeai as genai
from openai import OpenAI

from config import settings

# Configure Google SDK
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

_openai_client = None


def get_openai_client() -> OpenAI:
    """Return an OpenAI client for OpenRouter fallback."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _openai_client


def get_model(model_name: str = "gemini-2.5-flash"):
    """Return a GenerativeModel instance for Google AI Studio."""
    return genai.GenerativeModel(model_name)
