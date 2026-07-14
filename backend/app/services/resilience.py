import time

from app.config import fallback_llm, llm

MAX_ATTEMPTS = 3  # 1 initial call + 2 retries for temporary failures
RETRY_DELAY_SECONDS = 1

API_FAILURE_RESULT = {
    "category": "general_inquiry",
    "priority": "Low",
    "assigned_team": "Customer Support Desk",
    "reasoning": "Automated classification unavailable due to a persistent API failure; flagged for human review.",
}


class TemporaryFailure(Exception):
    """LLM call kept failing with a transient error (timeout, network, 429, 500) after all retries."""


class PermanentFailure(Exception):
    """LLM call failed with a non-retryable error (invalid/unauthorized API key)."""


def classify_llm_error(exc: Exception) -> str:
    """
    Classify a provider exception as "temporary", "permanent", or "unknown".

    Matches by exception class name and by `status_code` (rather than
    importing each provider's SDK) since every LangChain chat model
    integration - OpenAI, Groq, etc. - raises errors modeled the same way,
    so this works across whichever provider the factory created.
    """
    print(f"[classify_llm_error] called with exc={exc!r}")
    error_name = type(exc).__name__
    status_code = getattr(exc, "status_code", None)

    if error_name in {"AuthenticationError", "PermissionDeniedError"} or status_code in (401, 403):
        print("[classify_llm_error] output: 'permanent'")
        return "permanent"

    if error_name in {"APITimeoutError", "APIConnectionError", "RateLimitError", "InternalServerError"} \
            or status_code in (429, 500, 502, 503, 504):
        print("[classify_llm_error] output: 'temporary'")
        return "temporary"

    print("[classify_llm_error] output: 'unknown'")
    return "unknown"


def call_with_retries(model, messages):
    """Invoke `model`, retrying temporary failures up to MAX_ATTEMPTS times, 1s apart."""
    print(f"[call_with_retries] called with model={model!r}, messages={messages!r}")
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"[call_with_retries] attempt {attempt}/{MAX_ATTEMPTS}")
        try:
            response = model.invoke(messages)
            print(f"[call_with_retries] output: {response!r}")
            return response
        except Exception as exc:
            error_type = classify_llm_error(exc)
            if error_type == "permanent":
                print(f"[call_with_retries] output: raising PermanentFailure({exc!r})")
                raise PermanentFailure(str(exc)) from exc
            if error_type == "unknown":
                print(f"[call_with_retries] output: re-raising unknown error {exc!r}")
                raise
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)
    print(f"[call_with_retries] output: raising TemporaryFailure({last_error!r})")
    raise TemporaryFailure(str(last_error)) from last_error


def robust_invoke(messages):
    """
    Invoke the primary LLM with retries on temporary failures. On a
    permanent failure, switch to the fallback provider, which gets the
    same retry treatment.
    """
    print(f"[robust_invoke] called with messages={messages!r}")
    try:
        response = call_with_retries(llm, messages)
        print(f"[robust_invoke] output: {response!r}")
        return response
    except PermanentFailure:
        if fallback_llm is None:
            raise
        response = call_with_retries(fallback_llm, messages)
        print(f"[robust_invoke] output (fallback): {response!r}")
        return response
