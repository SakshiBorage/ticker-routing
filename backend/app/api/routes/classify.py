from fastapi import APIRouter, HTTPException

from app.schemas.ticket import TicketRequest
from app.services.classifier import classify_ticket, robust_classify_ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/classify")
def classify(request: TicketRequest):
    """Raw pipeline: validate -> preprocess -> classify (no output validation/retry)."""
    try:
        return classify_ticket(request.ticket)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/classify/validated")
def classify_validated(request: TicketRequest):
    """Robust pipeline: validate -> preprocess -> classify -> validate output -> retry -> fallback."""
    try:
        return robust_classify_ticket(request.ticket)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
