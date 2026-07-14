from app.services.preprocessing import count_tokens, preprocess_ticket_text

MAX_INPUT_TOKENS = 4000  # tickets over this length are rejected before any processing


def has_readable_text(ticket: str) -> bool:
    """
    Language-agnostic check for actual textual content.

    str.isalpha() is Unicode-aware and recognizes letters from any script
    (Latin, Devanagari, Arabic, CJK, Cyrillic, etc.), so this works
    regardless of the ticket's language. Digits, punctuation/special
    characters, and emojis are not letters, so a ticket made up of only
    those (e.g. "12345", "!!!???", "😀😭🔥") has no alphabetic character
    and is treated as unreadable.
    """
    print(f"[has_readable_text] called with ticket={ticket!r}")
    result = any(ch.isalpha() for ch in ticket)
    print(f"[has_readable_text] output: {result!r}")
    return result


def validate_input(ticket: str) -> str:
    """
    Validate and normalize the incoming support ticket.
    """
    print(f"[validate_input] called with ticket={ticket!r}")

    if ticket is None or not ticket.strip():
        raise ValueError(
            "Input ticket text is blank. Please provide a valid ticket."
        )

    clean_ticket = ticket.strip()

    token_count = count_tokens(clean_ticket)
    if token_count > MAX_INPUT_TOKENS:
        raise ValueError(
            f"Input ticket text is too long ({token_count} tokens). "
            f"Maximum allowed length is {MAX_INPUT_TOKENS} tokens."
        )

    if not has_readable_text(clean_ticket):
        raise ValueError(
            "Input ticket text contains no readable text (only numbers, "
            "special characters, or emojis). Please provide a valid ticket."
        )

    result = preprocess_ticket_text(clean_ticket)
    print(f"[validate_input] output: {result!r}")
    return result
