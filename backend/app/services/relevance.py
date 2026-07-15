import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import summarizer_llm
from app.prompts.relevance_prompt import RELEVANCE_SYSTEM_MESSAGE, build_relevance_prompt


class IrrelevantTicketError(ValueError):
    """Raised when a message has nothing to do with airline customer support."""


def check_relevance(ticket: str) -> bool:
    """
    Cheap pre-check: is this message even about airline support?

    Runs on the lightweight summarizer model, deliberately kept separate
    from the main classification prompt so a bad interaction here can
    never affect routing/priority accuracy there.

    Fails open (treated as relevant) on any error from this call itself,
    so an outage of this secondary check never blocks a legitimate
    complaint - the main classification call has its own fallback for
    its own failures.
    """
    print("[check_relevance] called")
    messages = [
        SystemMessage(content=RELEVANCE_SYSTEM_MESSAGE),
        HumanMessage(content=build_relevance_prompt(ticket)),
    ]
    try:
        response = summarizer_llm.invoke(messages)
        result = json.loads(response.content)
        output = bool(result["is_relevant"])
        print(f"[check_relevance] output: {output!r}")
        return output
    except Exception as exc:
        print(f"[check_relevance] output: True (fail-open, error={exc!r})")
        return True
