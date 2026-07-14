from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TicketRecord
from app.schemas.admin import TicketRecordOut, TicketRecordUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tickets", response_model=list[TicketRecordOut])
def list_tickets(db: Session = Depends(get_db)):
    return db.query(TicketRecord).order_by(desc(TicketRecord.created_at)).all()


@router.patch("/tickets/{ticket_id}", response_model=TicketRecordOut)
def update_ticket(ticket_id: int, payload: TicketRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(TicketRecord).filter(TicketRecord.id == ticket_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if record.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Ticket has already been verified and can no longer be modified.",
        )

    record.category = payload.category
    record.priority = payload.priority
    record.assigned_team = payload.assigned_team
    record.reasoning = payload.reasoning
    record.is_verified = payload.is_verified
    db.commit()
    db.refresh(record)
    return record
