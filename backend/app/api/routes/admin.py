from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.models import TicketRecord
from app.schemas.admin import TicketRecordOut, TicketRecordUpdate
from app.services.jira import JiraPermanentFailure, JiraTemporaryFailure, create_jira_ticket

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tickets", response_model=list[TicketRecordOut])
def list_tickets(db: Session = Depends(get_db)):
    return db.query(TicketRecord).order_by(desc(TicketRecord.created_at)).all()


@router.patch("/tickets/{ticket_id}", response_model=TicketRecordOut)
def update_ticket(
    ticket_id: int,
    payload: TicketRecordUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
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

    # Verification and Jira sync are independent: the verify commit below
    # always goes through regardless of what happens to the Jira call, so a
    # Jira outage never blocks or reverts the admin's decision. jira_status
    # starting out empty (None) is what gates ticket creation, so re-saving
    # an already-verified record (rejected above) can't double-create one.
    if record.is_verified and not record.jira_status:
        record.jira_status = "pending"
        background_tasks.add_task(_create_jira_ticket_task, ticket_id)

    db.commit()
    db.refresh(record)
    return record


@router.post("/tickets/{ticket_id}/jira/retry", response_model=TicketRecordOut)
def retry_jira_ticket(
    ticket_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    record = db.query(TicketRecord).filter(TicketRecord.id == ticket_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if record.jira_status == "created":
        raise HTTPException(
            status_code=400,
            detail="This ticket already has a Jira ticket created.",
        )

    record.jira_status = "pending"
    background_tasks.add_task(_create_jira_ticket_task, ticket_id)

    db.commit()
    db.refresh(record)
    return record


def _create_jira_ticket_task(ticket_id: int):
    """
    Runs after the verify response has already been sent. Opens its own DB
    session since the request-scoped one from `get_db` is closed by then.
    """
    db = SessionLocal()
    try:
        record = db.query(TicketRecord).filter(TicketRecord.id == ticket_id).first()
        if record is None:
            return

        try:
            result = create_jira_ticket(
                category=record.category,
                priority=record.priority,
                assigned_team=record.assigned_team,
                reasoning=record.reasoning,
                original_message=record.input_ticket,
            )
        except (JiraPermanentFailure, JiraTemporaryFailure):
            record.jira_status = "failed"
            db.commit()
            return

        record.jira_status = "created"
        record.jira_ticket_key = result["key"]
        record.jira_ticket_url = result["url"]
        db.commit()
    finally:
        db.close()
