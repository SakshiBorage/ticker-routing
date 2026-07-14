import os

from dotenv import load_dotenv

from app.services.llm_factory import LLMProviderFactory

# Load environment variables
load_dotenv()

# Primary provider, configurable via env vars, defaults to OpenAI
# `or` (not getenv's default arg) so a blank value in .env still falls back,
# since getenv's default only applies when the key is absent entirely.
PRIMARY_PROVIDER = os.getenv("LLM_PROVIDER") or "openai"
MODEL_NAME = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

# Fallback provider used whenever the primary provider's API call fails
FALLBACK_PROVIDER = os.getenv("FALLBACK_LLM_PROVIDER") or "groq"
FALLBACK_MODEL_NAME = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"

SUMMARY_MODEL_NAME = os.getenv("SUMMARY_MODEL") or "gpt-4o-mini"
TOKEN_THRESHOLD = 300  # tickets at or under this token count pass through unchanged

# Bounds how long a single API call can hang before it's treated as a timeout
TIMEOUT_SECONDS = 30

llm = LLMProviderFactory.create(PRIMARY_PROVIDER, MODEL_NAME, temperature=0, timeout=TIMEOUT_SECONDS)

fallback_llm = (
    LLMProviderFactory.create(FALLBACK_PROVIDER, FALLBACK_MODEL_NAME, temperature=0, timeout=TIMEOUT_SECONDS)
    if FALLBACK_PROVIDER
    else None
)

summarizer_llm = LLMProviderFactory.create(
    PRIMARY_PROVIDER, SUMMARY_MODEL_NAME, temperature=0, timeout=TIMEOUT_SECONDS
)
