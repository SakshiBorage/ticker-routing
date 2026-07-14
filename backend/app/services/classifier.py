import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import ValidationError

from app.prompts.classification_prompt import SYSTEM_MESSAGE
from app.schemas.ticket import FALLBACK_RESULT, parse_and_validate
from app.services.resilience import API_FAILURE_RESULT, PermanentFailure, TemporaryFailure, robust_invoke
from app.services.validation import validate_input


def build_messages(ticket: str):
    print("[build_messages] called")
    result = [
        SystemMessage(content=SYSTEM_MESSAGE),
        HumanMessage(
            content=f'Input: "{ticket}"\nOutput:'
        ),
    ]
    return result


def classify_ticket(ticket: str) -> dict:
    print("[classify_ticket] called")
    clean_ticket = validate_input(ticket)

    messages = build_messages(clean_ticket)

    try:
        response = robust_invoke(messages)
    except (TemporaryFailure, PermanentFailure):
        print("[classify_ticket] output: API_FAILURE_RESULT")
        return dict(API_FAILURE_RESULT)

    result = json.loads(response.content)
    print(f"[classify_ticket] output: {result!r}")
    return result


def robust_classify_ticket(ticket: str) -> dict:
    print("[robust_classify_ticket] called")
    clean_ticket = validate_input(ticket)
    messages = build_messages(clean_ticket)

    # Attempt 1
    try:
        raw_output = robust_invoke(messages).content
    except (TemporaryFailure, PermanentFailure):
        print("[robust_classify_ticket] output: API_FAILURE_RESULT")
        return dict(API_FAILURE_RESULT)

    try:
        result = parse_and_validate(raw_output).model_dump()
        print(f"[robust_classify_ticket] output: {result!r}")
        return result
    except (json.JSONDecodeError, ValidationError) as first_error:
        pass

    # Attempt 2: feed the validation error back and ask the LLM to correct itself
    retry_messages = messages + [
        AIMessage(content=raw_output),
        HumanMessage(
            content=(
                "Your previous response was invalid: "
                f"{first_error}\n"
                "Return ONLY a corrected JSON object with exactly the required "
                "fields, categories, priorities, and team mapping described above."
            )
        ),
    ]
    try:
        raw_output_retry = robust_invoke(retry_messages).content
    except (TemporaryFailure, PermanentFailure):
        print("[robust_classify_ticket] output: API_FAILURE_RESULT")
        return dict(API_FAILURE_RESULT)

    try:
        result = parse_and_validate(raw_output_retry).model_dump()
        print(f"[robust_classify_ticket] output: {result!r}")
        return result
    except (json.JSONDecodeError, ValidationError):
        pass

    # Both attempts failed validation -> safe fallback
    print("[robust_classify_ticket] output: FALLBACK_RESULT")
    return dict(FALLBACK_RESULT)
