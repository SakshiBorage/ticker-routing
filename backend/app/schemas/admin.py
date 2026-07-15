from datetime import datetime
from typing import Literal, Optional

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
    jira_status: Optional[str] = None
    jira_ticket_key: Optional[str] = None
    jira_ticket_url: Optional[str] = None

    class Config:
        from_attributes = True


class TicketRecordUpdate(BaseModel):
    category: Literal[tuple(CATEGORY_TEAM_MAP.keys())]
    priority: Literal["High", "Medium", "Low"]
    assigned_team: str
    reasoning: str
    is_verified: bool
