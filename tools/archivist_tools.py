import datetime
import httpx
import json
import os
import re

from dotenv import load_dotenv
from typing import Annotated, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from nylas import Client

from agent_framework import tool
from agent_framework.foundry import FoundryAgent

from fastapi import FastAPI, HTTPException


load_dotenv()

NYLAS_API_KEY = os.environ.get("NYLAS_API_KEY", "")
NYLAS_GRANT_ID = os.environ.get("NYLAS_GRANT_ID", "")

if not NYLAS_API_KEY or not NYLAS_GRANT_ID:
    raise EnvironmentError("Invalid Nylas Credentials: Nylas API Key or Grant ID.")

nylas_client = Client(api_key=NYLAS_API_KEY)


@tool(
    name="retrieve_student_emails",
    description="Searches and retrieves recent emails from a student's inbox using semantic keywords.",
    approval_mode="never_require",
)
def retrieve_student_emails(
    search_query: Annotated[
        str,
        Field(
            description="Keywords to search for in the email thread (e.g., 'medical leave', 'Dean', 'grades')."
        ),
    ],
) -> dict:  # 🔴 CHANGE 1: Return a dictionary, not a string
    """Queries the connected email inbox via Nylas API and returns structured data for Adaptive Cards."""
    grant_id = NYLAS_GRANT_ID

    if not grant_id:
        return {"error": "Nylas Grant ID missing from environment configuration."}

    try:
        query_params = {
            "search_query_native": search_query,
            "limit": 5,  # 🔴 CHANGE 2: Lower the limit. A card with 30 emails will be too large to render.
        }

        response = nylas_client.messages.list(
            identifier=grant_id,
            query_params=query_params,
        )

        if not response.data:
            return {"search_query": search_query, "count": 0, "emails": []}

        formatted_emails = []
        for msg in response.data:
            # Safely extract attributes
            sender_obj = msg.from_[0] if msg.from_ else None

            # Depending on the Nylas V3 SDK, sender might be an object with .name and .email
            sender_name = getattr(sender_obj, "name", None) or getattr(
                sender_obj, "email", "Unknown Sender"
            )

            subject = msg.subject if msg.subject else "(No Subject)"
            snippet = msg.snippet if msg.snippet else "(Empty Body)"

            # 🔴 CHANGE 3: Append a dictionary to the list
            formatted_emails.append(
                {
                    "message_id": msg.id,  # Useful if you want to add an Action.Submit to "Read Full Email"
                    "sender": sender_name,
                    "subject": subject,
                    "snippet": (
                        snippet[:150] + "..." if len(snippet) > 150 else snippet
                    ),  # Truncate for UI
                }
            )

        # 🔴 CHANGE 4: Return the structured root object
        return {
            "search_query": search_query,
            "count": len(formatted_emails),
            "emails": formatted_emails,
        }

    except Exception as e:
        return {"error": f"Failed to retrieve emails via Nylas: {str(e)}"}




# Initialize the Nylas V3 Client
NYLAS_API_KEY = os.environ.get("NYLAS_API_KEY", "")
NYLAS_GRANT_ID = os.environ.get("NYLAS_GRANT_ID", "")
if not NYLAS_API_KEY or not NYLAS_GRANT_ID:
    raise EnvironmentError("Invalid Nylas Credentials: Nylas API Key or Grant ID.")

nylas_client = Client(api_key=NYLAS_API_KEY)


# ==========================================
# NYLAS EMAIL RETRIEVAL TOOL
# ==========================================


@tool(
    name="retrieve_student_emails",
    description="Searches and retrieves recent emails from a student's inbox using semantic keywords or sender names.",
    approval_mode="never_require",
)
def retrieve_student_emailss(
    search_query: Annotated[
        str,
        Field(
            description="Keywords to search for in the email thread (e.g., 'medical leave', 'Dean', 'grades')."
        ),
    ],
) -> str:
    """Queries the connected email inbox via Nylas API and returns clean text summaries."""
    grant_id = NYLAS_GRANT_ID

    if not grant_id:
        return "Error: Nylas Grant ID missing from environment configuration."

    try:
        # Search messages using query parameters
        query_params = {
            "search_query_native": search_query,
            "limit": 30,  # Keep context small and relevant
        }

        # Fetch messages from the Nylas API
        # Removed tuple unpacking; Nylas V3 Python SDK returns a ListResponse object
        response = nylas_client.messages.list(
            identifier=grant_id,
            query_params=query_params,  # type: ignore
        )

        # Access the list of messages via the `.data` attribute
        if not response.data:
            return f"No recent emails found matching query: '{search_query}'."

        formatted_emails = []
        for msg in response.data:
            # Safely extract sender information using object attributes
            sender = msg.from_[0] if msg.from_ else "Unknown"
            subject = msg.subject if msg.subject else "(No Subject)"
            snippet = msg.snippet if msg.snippet else "(Empty Body)"

            formatted_emails.append(
                f"From: {sender}\n"
                f"Subject: {subject}\n"
                f"Snippet: {snippet}\n"
                f"---"
            )

        return "\n\n".join(formatted_emails)

    except Exception as e:
        return f"Failed to retrieve emails via Nylas: {str(e)}"


# ==========================================
# TOOL 1: OUTLOOK EMAIL SEARCH (GRAPH API MOCK)
# ==========================================


@tool(
    name="search_outlook_emails",
    description="Searches the student's Outlook mailbox for recent communications, filtering by exact keyword queries and a sliding time window.",
    approval_mode="never_require",
)
def search_outlook_emails(
    query: Annotated[
        str,
        Field(
            description="The primary search term, keyword, or KQL query (e.g., 'registration deadline', 'financial aid')."
        ),
    ],
    days_back: Annotated[
        int,
        Field(description="The lookback window in days to restrict the search scope."),
    ] = 7,
) -> str:
    """
    Simulates a Microsoft Graph /me/messages search query. Filters a dynamic, temporally
    accurate local database based on the requested lookback window and keyword matches.
    """
    # Base reference date: June 16, 2026
    current_date = datetime.date(2026, 6, 16)
    cutoff_date = current_date - datetime.timedelta(days=days_back)

    # Comprehensive mock database
    MOCK_MAILBOX = [
        {
            "subject": "URGENT: Fall 2026 Registration Deadline",
            "sender": "registrar@college.edu",
            "date": "2026-06-15",
            "body": "Please remember to submit your add/drop forms before the portal closes on Friday.",
        },
        {
            "subject": "Weekly Campus Newsletter",
            "sender": "student_affairs@college.edu",
            "date": "2026-06-14",
            "body": "Campus events this week include the tech job fair and alumni mixer.",
        },
        {
            "subject": "Financial Aid Disbursement Update",
            "sender": "finaid@college.edu",
            "date": "2026-06-10",
            "body": "Your pell grant has been applied to your tuition balance for the upcoming semester.",
        },
        {
            "subject": "CS101: Syllabus Update",
            "sender": "prof.davis@college.edu",
            "date": "2026-06-05",
            "body": "I have uploaded the revised syllabus detailing the new midterm weightings.",
        },
        {
            "subject": "Library Overdue Notice",
            "sender": "circulation@library.college.edu",
            "date": "2026-06-12",
            "body": "The book 'Algorithms 4th Ed' is currently 3 days overdue. Please return immediately.",
        },
    ]

    results = []
    query_lower = query.lower()

    for email in MOCK_MAILBOX:
        email_date = datetime.date.fromisoformat(email["date"])

        # 1. Temporal Filter
        if email_date < cutoff_date:
            continue

        # 2. Keyword Filter
        if (
            query_lower in email["subject"].lower()
            or query_lower in email["body"].lower()
        ):
            results.append(
                {
                    "subject": email["subject"],
                    "sender": email["sender"],
                    "date": email["date"],
                    "content_snippet": email["body"][:60] + "...",
                }
            )

    response_payload = {
        "search_parameters": {"query": query, "lookback_days": days_back},
        "total_hits": len(results),
        "results": results,
    }

    return json.dumps(response_payload, indent=4)


# ==========================================
# TOOL 2: REGEX-POWERED DEADLINE EXTRACTOR
# ==========================================


@tool(
    name="extract_deadlines",
    description="Scans a block of raw text or email content and extracts concrete dates, times, and actionable deadlines using heuristic pattern matching.",
    approval_mode="never_require",
)
def extract_deadlines(
    text_content: Annotated[
        str,
        Field(
            description="The raw text body from an email, syllabus, or SharePoint page to be parsed for deadlines."
        ),
    ],
) -> str:
    """
    Uses Regex heuristics to identify temporal commitments.
    Classifies the severity of the deadline based on proximity keywords (e.g., 'urgent', 'required').
    """
    extracted_data = []

    # 1. Regex Patterns for Dates and Times
    # Matches: MM/DD/YYYY, YYYY-MM-DD, Month DD
    date_pattern = re.compile(
        r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?)\b",
        re.IGNORECASE,
    )
    # Matches: HH:MM AM/PM
    time_pattern = re.compile(
        r"\b(?:1[0-2]|0?[1-9])(?::[0-5][0-9])?\s*(?:AM|PM|am|pm)\b"
    )

    # Split text into sentences for contextual extraction
    sentences = re.split(r"(?<=[.!?]) +", text_content.replace("\n", " "))

    for sentence in sentences:
        dates_found = date_pattern.findall(sentence)
        times_found = time_pattern.findall(sentence)

        # Heuristic keywords for actionability
        is_actionable = any(
            kw in sentence.lower()
            for kw in ["due", "submit", "deadline", "by", "required", "rsvp", "closing"]
        )
        is_urgent = any(
            kw in sentence.lower()
            for kw in ["urgent", "immediately", "today", "tomorrow", "asap"]
        )

        if dates_found or is_actionable:
            severity = "High" if is_urgent else ("Medium" if is_actionable else "Low")

            # Synthesize task context by stripping out the raw date text roughly
            context_snippet = sentence.strip()

            extracted_data.append(
                {
                    "context": context_snippet,
                    "extracted_date": (
                        dates_found[0] if dates_found else "Implied/Relative"
                    ),
                    "extracted_time": (
                        times_found[0] if times_found else "EOD (Assumed)"
                    ),
                    "actionable": is_actionable,
                    "severity_tier": severity,
                }
            )

    # Sort by severity purely for structured output
    severity_map = {"High": 1, "Medium": 2, "Low": 3}
    extracted_data.sort(key=lambda x: severity_map.get(x["severity_tier"], 4))

    return json.dumps(
        {
            "status": "success",
            "characters_scanned": len(text_content),
            "deadlines_identified": len(extracted_data),
            "found_deadlines": extracted_data,
        },
        indent=4,
    )


# ==========================================
# TOOL 3: EXECUTIVE INBOX TRIAGE PIPELINE
# ==========================================


@tool(
    name="screen_and_categorize_emails",
    description="Evaluates incoming inbox payloads, processes metadata, applies behavioral tags, and returns a clean actionable brief for executive multi-agent triage.",
    approval_mode="never_require",
)
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
) -> (
    str
):  # Returning str (JSON dumped List[Dict]) for standard agent passing, though signature allowed List[Dict]
    """
    Acts as the primary sensory interface for the Executive agent before transferring complex requests
    downwards to the Archivist, Career Coach, or Front Desk agents.
    """
    # 1. Expanded, Temporally Contextualized Mock Inbox
    mock_inbox = [
        {
            "id": "MSG-001",
            "from": "Registrar Office",
            "subject": "Tuition Balance Reminder",
            "body": "Your account shows a pending balance of $200 due by Friday. Failure to pay will result in a hold.",
            "unread": True,
            "flagged": False,
            "received_hours_ago": 2,
        },
        {
            "id": "MSG-002",
            "from": "Prof. Davis (CS101)",
            "subject": "Assignment 3 Extension Granted",
            "body": "Hi team, I am moving the deadline to Sunday night due to the AWS outage.",
            "unread": True,
            "flagged": True,
            "received_hours_ago": 5,
        },
        {
            "id": "MSG-003",
            "from": "Career Services",
            "subject": "Mock Interview Sign-ups",
            "body": "Slots are now open for the upcoming tech mock interviews. First come, first served.",
            "unread": False,
            "flagged": True,
            "received_hours_ago": 26,
        },
        {
            "id": "MSG-004",
            "from": "Student Housing",
            "subject": "Room Inspection Notice",
            "body": "Inspections will occur next Tuesday morning starting at 9 AM. Ensure rooms are clean.",
            "unread": False,
            "flagged": False,
            "received_hours_ago": 48,
        },
        {
            "id": "MSG-005",
            "from": "IT Helpdesk",
            "subject": "Action Required: Password Expiry",
            "body": "Your university single sign-on password will expire in 24 hours. Update it immediately.",
            "unread": True,
            "flagged": True,
            "received_hours_ago": 1,
        },
    ]

    screened_results = []

    # 2. Filtering Logic
    for email in mock_inbox:
        match = False
        if filter_type.lower() == "unread" and email["unread"]:
            match = True
        elif filter_type.lower() == "flagged" and email["flagged"]:
            match = True
        elif filter_type.lower() == "category-related" and category_keyword:
            kw = category_keyword.lower()
            if kw in email["subject"].lower() or kw in email["body"].lower():
                match = True
        elif filter_type.lower() == "time-specific":
            if email["received_hours_ago"] <= (time_window_hours or 24):
                match = True

        # 3. Automatic Heuristic Categorization
        if match:
            category = "General Administrative"
            subj_body = (email["subject"] + " " + email["body"]).lower()

            if any(
                k in subj_body
                for k in ["assignment", "grade", "syllabus", "midterm", "prof"]
            ):
                category = "Academic / Faculty"
            elif any(k in subj_body for k in ["tuition", "balance", "finaid", "grant"]):
                category = "Financial Services"
            elif any(k in subj_body for k in ["interview", "career", "resume", "job"]):
                category = "Career Development"
            elif any(k in subj_body for k in ["password", "it", "outage", "sso"]):
                category = "IT / Security"

            # 4. Triage Brief Generation
            one_liner = f"[{category}] From {email['from']}: Actionable requirement regarding '{email['subject']}' received {email['received_hours_ago']}h ago."

            screened_results.append(
                {
                    "email_id": email["id"],
                    "triage_category": category,
                    "executive_summary": one_liner,
                    "urgency_flag": email["flagged"] or ("urgent" in subj_body),
                }
            )

    # Return as structured JSON for reliable LLM ingestion
    return json.dumps(
        {
            "triage_filter_applied": filter_type,
            "total_screened": len(screened_results),
            "actionable_triage_list": screened_results,
        },
        indent=4,
    )
