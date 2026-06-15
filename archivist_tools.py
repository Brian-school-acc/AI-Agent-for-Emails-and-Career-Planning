import json

from agent_framework import tool


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
