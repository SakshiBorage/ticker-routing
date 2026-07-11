from app.services.preprocessing import preprocess_ticket_text


def validate_input(ticket: str) -> str:
    """
    Validate and normalize the incoming support ticket.
    """

    if ticket is None or not ticket.strip():
        raise ValueError(
            "Input ticket text is blank. Please provide a valid ticket."
        )

    clean_ticket = ticket.strip()
    return preprocess_ticket_text(clean_ticket)
