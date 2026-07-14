from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.ticket import CATEGORY_TEAM_MAP


class TicketRecordOut(BaseModel):
    id: int
    input_ticket: str
    category: str
    priority: str
    assigned_team: str
    reasoning: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TicketRecordUpdate(BaseModel):
    category: Literal[tuple(CATEGORY_TEAM_MAP.keys())]
    priority: Literal["High", "Medium", "Low"]
    assigned_team: str
    reasoning: str
    is_verified: bool
