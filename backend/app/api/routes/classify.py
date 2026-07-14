from fastapi import APIRouter, HTTPException

from app.schemas.ticket import TicketRequest
from app.services.classifier import classify_ticket, robust_classify_ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/classify")
def classify(request: TicketRequest):
    """Raw pipeline: validate -> preprocess -> classify (no output validation/retry)."""
    print(f"[classify] called with request={request!r}")
    try:
        result = classify_ticket(request.ticket)
    except ValueError as error:
        print(f"[classify] output: raising HTTPException 400: {error!r}")
        raise HTTPException(status_code=400, detail=str(error))
    print(f"[classify] output: {result!r}")
    return result


@router.post("/classify/validated")
def classify_validated(request: TicketRequest):
    """Robust pipeline: validate -> preprocess -> classify -> validate output -> retry -> fallback."""
    print(f"[classify_validated] called with request={request!r}")
    try:
        result = robust_classify_ticket(request.ticket)
    except ValueError as error:
        print(f"[classify_validated] output: raising HTTPException 400: {error!r}")
        raise HTTPException(status_code=400, detail=str(error))
    print(f"[classify_validated] output: {result!r}")
    return result
