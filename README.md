## AI-Powered E-Commerce Ticket Routing System

## Overview

This project automates the first level of customer support ticket routing for an e-commerce marketplace using a Large Language Model (LLM).

Given a raw customer support message, the system identifies the most appropriate business category, assigns a priority, maps the ticket to the responsible support team, and provides a concise reasoning for the routing decision.

The objective is to reduce manual triaging effort while maintaining consistent and structured routing decisions.

---

## Goal

For every incoming customer ticket, generate a structured JSON response containing:

- Category
- Priority
- Assigned Team
- Reasoning

The output should be deterministic, schema-valid, and suitable for direct integration into a support workflow.

---

## Workflow

```
Customer Ticket
       │
       ▼
Input Validation
       │
       ▼
Prompt Construction
       │
       ▼
LLM Classification
       │
       ▼
JSON Schema Validation
       │
       ▼
Retry (if validation fails)
       │
       ▼
Fallback Response (if required)
       │
       ▼
Final Routing Decision
```

---

## Assumptions

This project assumes:

- The customer is always a buyer (not a seller or merchant).
- Each ticket belongs to exactly one primary category.
- Every category maps to one predefined support team.
- Priority is limited to **High**, **Medium**, or **Low**.
- The reasoning is always a single concise sentence.
- If insufficient information is provided, the ticket is routed to `general_inquiry`.
- Fraud or security-related issues are always treated as **High** priority.

---

## Output Format

```json
{
  "category": "payments_billing",
  "priority": "High",
  "assigned_team": "Payments & Billing",
  "reasoning": "Customer reports duplicate payment deduction causing financial loss."
}
```

---

## Technology Stack

- Python
- LLM API (Groq/OpenAI/Gemini)
- Pydantic
- dotenv