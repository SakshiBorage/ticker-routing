from sqlalchemy import Boolean, Column, DateTime, Integer, Text, func

from app.db import Base


class TicketRecord(Base):
    __tablename__ = "ticket_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    input_ticket = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    priority = Column(Text, nullable=False)
    assigned_team = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    is_verified = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Jira sync state: None until verification first triggers ticket creation,
    # then "pending" -> "created"/"failed". Kept independent of is_verified so
    # a Jira outage never blocks or rolls back the verification itself.
    jira_status = Column(Text, nullable=True)
    jira_ticket_key = Column(Text, nullable=True)
    jira_ticket_url = Column(Text, nullable=True)
