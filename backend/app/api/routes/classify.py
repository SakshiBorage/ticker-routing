from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.ticket import TicketRequest
from app.services.classifier import classify_ticket, robust_classify_ticket
from app.services.storage import save_ticket_result

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/classify")
def classify(request: TicketRequest, db: Session = Depends(get_db)):
    """Raw pipeline: validate -> preprocess -> classify (no output validation/retry)."""
    print("[classify] called")
    try:
        result = classify_ticket(request.ticket)
    except ValueError as error:
        print(f"[classify] output: raising HTTPException 400: {error!r}")
        raise HTTPException(status_code=400, detail=str(error))
    print(f"[classify] output: {result!r}")
    save_ticket_result(db, request.ticket, result)
    return result


@router.post("/classify/validated")
def classify_validated(request: TicketRequest, db: Session = Depends(get_db)):
    """Robust pipeline: validate -> preprocess -> classify -> validate output -> retry -> fallback."""
    print("[classify_validated] called")
    try:
        result = robust_classify_ticket(request.ticket)
    except ValueError as error:
        print(f"[classify_validated] output: raising HTTPException 400: {error!r}")
        raise HTTPException(status_code=400, detail=str(error))
    print(f"[classify_validated] output: {result!r}")
    save_ticket_result(db, request.ticket, result)
    return result
