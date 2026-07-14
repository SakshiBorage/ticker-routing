from sqlalchemy.orm import Session

from app.models import TicketRecord


def save_ticket_result(db: Session, input_ticket: str, result: dict) -> TicketRecord:
    """Persist the input ticket and its final classification output."""
    record = TicketRecord(
        input_ticket=input_ticket,
        category=result["category"],
        priority=result["priority"],
        assigned_team=result["assigned_team"],
        reasoning=result["reasoning"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
