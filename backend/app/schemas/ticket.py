import json
from typing import Literal

from pydantic import BaseModel, field_validator

CATEGORY_TEAM_MAP = {
    "order_issue": "Order Management",
    "delivery_logistics": "Logistics & Delivery Ops",
    "returns_refunds": "Returns & Refunds Team",
    "payments_billing": "Payments & Billing",
    "product_issue": "Product Quality Support",
    "account_access": "Account & Identity Support",
    "wallet_offers": "Rewards & Promotions",
    "seller_related": "Marketplace Trust",
    "warranty_installation": "Warranty & Installation",
    "technical_platform": "Platform Engineering",
    "fraud_security": "Trust & Security",
    "feedback_complaints": "Customer Experience",
    "general_inquiry": "Customer Support Desk",
}

FALLBACK_RESULT = {
    "category": "general_inquiry",
    "priority": "Medium",
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
