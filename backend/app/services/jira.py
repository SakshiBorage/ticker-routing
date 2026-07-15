import time

import requests

from app.config import JIRA_API_TOKEN, JIRA_EMAIL, JIRA_PROJECT_KEY, JIRA_URL

MAX_ATTEMPTS = 3  # 1 initial call + 2 retries for temporary failures
RETRY_DELAY_SECONDS = 1

# Adjust this to match an issue type that actually exists in your project -
# Company-managed projects created from different templates have different
# default issue types (e.g. "Task", "Bug", "Story", or for service-desk
# style templates: "Incident", "Service Request"). Check your project's
# issue type scheme if this doesn't match and you get a 400 error.
ISSUE_TYPE_NAME = "Task"


class JiraTemporaryFailure(Exception):
    """Jira call kept failing with a transient error (timeout, network, 429, 5xx) after all retries."""


class JiraPermanentFailure(Exception):
    """Jira call failed with a non-retryable error (bad auth, bad project/issue type, malformed payload)."""


def classify_jira_error(exc: Exception) -> str:
    """Classify a requests exception as "temporary", "permanent", or "unknown"."""
    if isinstance(exc, requests.HTTPError):
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code in (401, 403, 400, 404):
            return "permanent"
        if status_code in (429, 500, 502, 503, 504):
            return "temporary"
        return "unknown"

    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return "temporary"

    return "unknown"


def build_description_adf(reasoning: str, original_message: str) -> dict:
    """
    Jira Cloud REST API v3 requires the description field in Atlassian
    Document Format (ADF), not a plain string. This builds a structured
    description with the AI's reasoning and the original message in
    clearly separated, headed sections - easier for a human agent to scan
    than one concatenated block of text.
    """
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "AI Classification Reasoning"}],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": reasoning}],
            },
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Original Message"}],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": original_message}],
            },
        ],
    }


def _create_jira_ticket_once(
    category: str,
    priority: str,
    assigned_team: str,
    reasoning: str,
    original_message: str,
) -> dict:
    readable_category = category.replace("_", " ").title()
    summary = f"[{priority}] {readable_category}: {original_message[:50]}"

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": build_description_adf(reasoning, original_message),
            "issuetype": {"name": ISSUE_TYPE_NAME},
            "priority": {"name": priority},  # High / Medium / Low - matches Jira's default scheme
            "components": [{"name": assigned_team}],
            "labels": [category],  # e.g. "fraud_security" - extra filter, independent of Component
        }
    }

    response = requests.post(
        f"{JIRA_URL}/rest/api/3/issue",
        json=payload,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={"Content-Type": "application/json"},
    )

    response.raise_for_status()
    result = response.json()
    return {
        "key": result["key"],
        "url": f"{JIRA_URL}/browse/{result['key']}",
    }


def create_jira_ticket(
    category: str,
    priority: str,
    assigned_team: str,
    reasoning: str,
    original_message: str,
) -> dict:
    """
    Creates a Jira issue from a classification result, retrying temporary
    failures up to MAX_ATTEMPTS times.

    Returns {"key": ..., "url": ...} on success.
    Raises JiraPermanentFailure / JiraTemporaryFailure otherwise - the
    caller is expected to record that outcome on the ticket record rather
    than let it propagate to the admin-verify request.
    """
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return _create_jira_ticket_once(category, priority, assigned_team, reasoning, original_message)
        except Exception as exc:
            error_type = classify_jira_error(exc)
            if error_type == "permanent":
                raise JiraPermanentFailure(str(exc)) from exc
            if error_type == "unknown":
                raise
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)
    raise JiraTemporaryFailure(str(last_error)) from last_error
