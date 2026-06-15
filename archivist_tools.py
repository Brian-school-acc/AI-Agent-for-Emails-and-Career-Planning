from agent_framework import tool
from pydantic import Field

import datetime
import httpx
import json

from typing import Annotated, List, Dict, Optional
from random import randint

@tool(
    name="search_outlook_emails",
    description="Searches the student's Outlook mailbox for recent communications, filtering by categories like college updates or course announcements.",
    approval_mode="never_require",
)
def search_outlook_emails(query: str, days_back: int = 7) -> str:
    """
    Search recent emails using Microsoft Graph.
    Args:
        query: The search term or KQL query (e.g., 'registration deadline').
        days_back: Number of days to look back.
    """
    # Mocking extracted email data
    return json.dumps(
        [
            {
                "subject": f"Update on {query}",
                "sender": "registrar@college.edu",
                "date": "2026-06-12",
                "content_snippet": "Please remember to submit your forms...",
            },
            {
                "subject": "Weekly Newsletter",
                "sender": "student_affairs@college.edu",
                "date": "2026-06-14",
                "content_snippet": "Campus events this week include...",
            },
        ]
    )


@tool(description="Check the active logged-in user's recent unread Outlook emails.")
async def check_my_emails(ctx) -> str:
    """Queries the Microsoft Graph API using the user's active identity token."""

    # 1. Dynamically pull the active user's passed-through M365 token
    # The framework automatically fetches this from the active M365 Copilot session
    try:
        user_token = ctx.get_user_token(
            scopes=["https://graph.microsoft.com/Mail.Read"]
        )
    except Exception:
        return "Authentication error: Could not verify your M365 user token."

    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }

    # 2. Target the official Microsoft Graph endpoint for the active user ('/me')
    graph_url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$top=3&$filter=isRead eq false"

    async with httpx.AsyncClient() as client:
        response = await client.get(graph_url, headers=headers)

        if response.status_code == 200:
            messages = response.json().get("value", [])
            if not messages:
                return "Your inbox is clear! You have no unread emails right now."

            output = "Here are your 3 most recent unread emails:\n"
            for msg in messages:
                sender = (
                    msg.get("from", {})
                    .get("emailAddress", {})
                    .get("name", "Unknown Sender")
                )
                subject = msg.get("subject", "(No Subject)")
                output += f"- **From:** {sender} \n  **Subject:** {subject}\n"
            return output

        elif response.status_code == 403:
            return "Access Denied: Your university's IT policy has restricted Mail.Read access for this application."

        return f"Could not access Outlook. (Graph API Error: {response.status_code})"


@tool(
    name="extract_deadlines",
    description="Scans a block of text or email content and extracts concrete dates, times, and actionable deadlines.",
    approval_mode="never_require",
)
def extract_deadlines(text_content: str) -> str:
    """
    Extract upcoming deadlines from provided text.
    Args:
        text_content: The raw text from an email, document, or SharePoint page.
    """
    # Mocking NLP extraction
    return json.dumps(
        {
            "status": "success",
            "found_deadlines": [
                {
                    "task": "Submit add/drop form",
                    "date": "2026-06-20T17:00:00Z",
                    "severity": "High",
                },
                {
                    "task": "RSVP for networking event",
                    "date": "2026-06-18T12:00:00Z",
                    "severity": "Medium",
                },
            ],
        }
    )


@tool(approval_mode="never_require")
def screen_and_categorize_emails(
    filter_type: Annotated[
        str,
        Field(
            description="The targeted evaluation filter. Must be one of: 'unread', 'flagged', 'category-related', or 'time-specific'."
        ),
    ],
    category_keyword: Annotated[
        Optional[str],
        Field(
            description="The theme or keyword required if filter_type is set to 'category-related' (e.g., 'assignment', 'financial', 'admissions')."
        ),
    ] = None,
    time_window_hours: Annotated[
        Optional[int],
        Field(
            description="The sliding lookback window in hours if filter_type is 'time-specific'. Default is 24."
        ),
    ] = 24,
) -> List[Dict[str, str]]:
    """
        Evaluates incoming inbox payloads, processes their metadata and content strings, applies behavioral tags,
        and returns a clean payload featuring a single-line actionable brief for executive multi-agent triage.

        This acts as the primary sensory interface for the Executive agent before transferring complex requests
        downwards to the Archivist, Career Coach, or Front Desk agents.

        Few shot examples for this tool:
        ### TASK: Inbox Presentation Block
        Transform raw filtered arrays into clean, visually separated triage lists for routing downstream.

        ---

        **Example 1 (Input: Unread + Flagged Triage):**
        [
        {"email_id": "1", "category": "Financial Services", "summary": "[Financial Services] From Registrar Office: Actionable requirement regarding 'Tuition Balance Reminder' within 2h."},
        {"email_id": "2", "category": "Academic / Faculty", "summary": "[Academic / Faculty] From Prof. Davis (CS101): Actionable requirement regarding 'Assignment 3 Extension Granted' within 5h."}
        ]

        **Output Visual Component:**

        | ID | Triage Category | System Executive Actionable Summary |
        |---|---|---|
        | **#01** | 💰 Financial Services | **From Registrar Office:** Actionable requirement regarding 'Tuition Balance Reminder' within 2h. |
        | **#02** | 🎓 Academic / Faculty | **From Prof. Davis (CS101):** Actionable requirement regarding 'Assignment 3 Extension Granted' within 5h. |
    """

    # In production, this block calls `patched_msgraph_client.get_inbox()`
    # Mimicking real inbox processing based on the parameters passed by the LLM:
    mock_inbox = [
        {
            "id": "1",
            "from": "Registrar Office",
            "subject": "Tuition Balance Reminder",
            "body": "Your account shows a pending balance of $200 due by Friday.",
            "unread": True,
            "flagged": False,
            "received_hours_ago": 2,
        },
        {
            "id": "2",
            "from": "Prof. Davis (CS101)",
            "subject": "Assignment 3 Extension Granted",
            "body": "Hi team, I am moving the deadline to Sunday night.",
            "unread": True,
            "flagged": True,
            "received_hours_ago": 5,
        },
        {
            "id": "3",
            "from": "Career Services",
            "subject": "Mock Interview Sign-ups",
            "body": "Slots are now open for the upcoming tech mock interviews.",
            "unread": False,
            "flagged": True,
            "received_hours_ago": 26,
        },
        {
            "id": "4",
            "from": "Student Housing",
            "subject": "Room Inspection Notice",
            "body": "Inspections will occur next Tuesday morning starting at 9 AM.",
            "unread": False,
            "flagged": False,
            "received_hours_ago": 48,
        },
    ]

    screened_results = []

    for email in mock_inbox:
        # Match filters
        match = False
        if filter_type == "unread" and email["unread"]:
            match = True
        elif filter_type == "flagged" and email["flagged"]:
            match = True
        elif filter_type == "category-related" and category_keyword:
            kw = category_keyword.lower()
            if kw in email["subject"].lower() or kw in email["body"].lower():
                match = True
        elif filter_type == "time-specific":
            if email["received_hours_ago"] <= (time_window_hours or 24):
                match = True

        if match:
            # Automatic categorization heuristics
            category = "General Administrative"
            if (
                "assignment" in email["subject"].lower()
                or "grade" in email["body"].lower()
            ):
                category = "Academic / Faculty"
            elif (
                "tuition" in email["subject"].lower()
                or "balance" in email["body"].lower()
            ):
                category = "Financial Services"
            elif (
                "interview" in email["subject"].lower()
                or "career" in email["from"].lower()
            ):
                category = "Career Development"

            # Build the clean, tight one-liner summary requested
            one_liner = f"[{category}] From {email['from']}: Actionable requirement regarding '{email['subject']}' within {email['received_hours_ago']}h."

            screened_results.append(
                {"email_id": email["id"], "category": category, "summary": one_liner}
            )

    return screened_results
