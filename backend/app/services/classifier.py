import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import ValidationError

from app.config import llm
from app.prompts.classification_prompt import SYSTEM_MESSAGE
from app.schemas.ticket import FALLBACK_RESULT, parse_and_validate
from app.services.validation import validate_input


def build_messages(ticket: str):
    return [
        SystemMessage(content=SYSTEM_MESSAGE),
        HumanMessage(
            content=f'Input: "{ticket}"\nOutput:'
        ),
    ]


def classify_ticket(ticket: str) -> dict:
    clean_ticket = validate_input(ticket)

    messages = build_messages(clean_ticket)

    response = llm.invoke(messages)

    return json.loads(response.content)


def robust_classify_ticket(ticket: str) -> dict:
    clean_ticket = validate_input(ticket)
    messages = build_messages(clean_ticket)

    # Attempt 1
    raw_output = llm.invoke(messages).content
    try:
        return parse_and_validate(raw_output).model_dump()
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
    raw_output_retry = llm.invoke(retry_messages).content
    try:
        return parse_and_validate(raw_output_retry).model_dump()
    except (json.JSONDecodeError, ValidationError):
        pass

    # Both attempts failed validation -> safe fallback
    return dict(FALLBACK_RESULT)
