import tiktoken
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import TOKEN_THRESHOLD, summarizer_llm
from app.prompts.summarization_prompt import SUMMARIZE_SYSTEM_MESSAGE

_tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")


def count_tokens(text: str) -> int:
    print("[count_tokens] called")
    result = len(_tokenizer.encode(text))
    print(f"[count_tokens] output: {result!r}")
    return result


def summarize_ticket(ticket_text: str) -> str:
    """Summarize a long ticket using a cheap LLM call before classification."""
    print("[summarize_ticket] called")
    messages = [
        SystemMessage(content=SUMMARIZE_SYSTEM_MESSAGE),
        HumanMessage(content=ticket_text),
    ]
    response = summarizer_llm.invoke(messages)
    result = response.content.strip()
    print(f"[summarize_ticket] output: {result!r}")
    return result


def preprocess_ticket_text(ticket_text: str) -> str:
    """Pass short tickets through unchanged; summarize tickets over TOKEN_THRESHOLD tokens."""
    print("[preprocess_ticket_text] called")
    if count_tokens(ticket_text) <= TOKEN_THRESHOLD:
        print("[preprocess_ticket_text] output: unchanged (under token threshold)")
        return ticket_text
    result = summarize_ticket(ticket_text)
    print(f"[preprocess_ticket_text] output: {result!r}")
    return result
