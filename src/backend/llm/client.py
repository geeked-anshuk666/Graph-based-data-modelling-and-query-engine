import logging
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import google.generativeai as genai
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
from google.api_core import exceptions

load_dotenv()

class Settings(BaseSettings):
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()

# Configure Google SDK if key is present
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

def get_model(model_name: str = "gemini-2.5-flash"):
    """Return a GenerativeModel instance for Google AI Studio."""
    return genai.GenerativeModel(model_name)

# --- RESILIENCE DECORATOR ---
# Retries up to 3 times with exponential backoff (starts at 4s, caps at 15s)
# Only retries on 429 ResourceExhausted errors
retry_gemini = retry(
    wait=wait_random_exponential(min=4, max=15),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(exceptions.ResourceExhausted),
    before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
        f"Rate limit hit! Retrying in {retry_state.next_action.sleep}s... "
        f"(Attempt {retry_state.attempt_number})"
    )
)
