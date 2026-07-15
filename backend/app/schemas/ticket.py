import json
from typing import Literal

from pydantic import BaseModel, field_validator

CATEGORY_TEAM_MAP = {
    "flight_disruption": "Flight Operations & Rebooking",
    "baggage": "Baggage Services",
    "reservations_ticketing": "Reservations & Ticketing",
    "refunds_compensation": "Refunds & Compensation",
    "payments_billing": "Payments & Billing",
    "loyalty_program": "Loyalty Program Team",
    "account_access": "Account & Identity Support",
    "special_assistance": "Accessibility & Special Services",
    "discrimination_complaint": "Legal & Compliance",
    "fraud_security": "Trust & Security",
    "safety_incident": "Safety & Compliance",
    "technical_platform": "Platform Engineering",
    "feedback_complaints": "Customer Relations",
    "general_inquiry": "Customer Support Desk",
}

FALLBACK_RESULT = {
    "category": "general_inquiry",
    "priority": "Low",
    "assigned_team": "Customer Support Desk",
    "reasoning": "Automated classification failed validation; routed to general queue for manual review.",
}


class TicketClassification(BaseModel):
    category: Literal[tuple(CATEGORY_TEAM_MAP.keys())]
    priority: Literal["High", "Medium", "Low"]
    assigned_team: str
    reasoning: str

    @field_validator("assigned_team")
    @classmethod
    def team_matches_category(cls, assigned_team, info):
        category = info.data.get("category")
        expected_team = CATEGORY_TEAM_MAP.get(category)
        if expected_team is not None and assigned_team != expected_team:
            raise ValueError(
                f"assigned_team '{assigned_team}' does not match the required team "
                f"'{expected_team}' for category '{category}'"
            )
        return assigned_team


def parse_and_validate(raw_output: str) -> TicketClassification:
    data = json.loads(raw_output)
    return TicketClassification(**data)


class TicketRequest(BaseModel):
    ticket: str
    persist: bool = True
