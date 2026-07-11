import tiktoken
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import TOKEN_THRESHOLD, summarizer_llm
from app.prompts.summarization_prompt import SUMMARIZE_SYSTEM_MESSAGE

_tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")


def count_tokens(text: str) -> int:
    return len(_tokenizer.encode(text))


def summarize_ticket(ticket_text: str) -> str:
    """Summarize a long ticket using a cheap LLM call before classification."""
    messages = [
        SystemMessage(content=SUMMARIZE_SYSTEM_MESSAGE),
        HumanMessage(content=ticket_text),
    ]
    response = summarizer_llm.invoke(messages)
    return response.content.strip()


def preprocess_ticket_text(ticket_text: str) -> str:
    """Pass short tickets through unchanged; summarize tickets over TOKEN_THRESHOLD tokens."""
    if count_tokens(ticket_text) <= TOKEN_THRESHOLD:
        return ticket_text
    return summarize_ticket(ticket_text)
