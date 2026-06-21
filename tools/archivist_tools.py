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


load_dotenv()

NYLAS_API_KEY = os.environ.get("NYLAS_API_KEY", "")
NYLAS_GRANT_ID = os.environ.get("NYLAS_GRANT_ID", "")

if not NYLAS_API_KEY or not NYLAS_GRANT_ID:
    raise EnvironmentError("Invalid Nylas Credentials: Nylas API Key or Grant ID.")

nylas_client = Client(api_key=NYLAS_API_KEY)


@tool(
    name="retrieve_student_emails",
    description=(
        "Searches and retrieves recent emails from a student's inbox using semantic keywords "
        "via the Nylas API, returning structured data. If the user does not specify a particular "
        "topic or keyword (e.g., generally asking 'check my emails' or 'are there any recent messages'), "
        "you MUST use a broad, default search query such as 'in:inbox', 'is:unread', or 'newer_than:1d' "
        "to ensure general recent emails are successfully retrieved."
    ),
    approval_mode="never_require",
)
def retrieve_student_emails(
    search_query: Annotated[
        str,
        Field(
            description="Keywords to search for in the email thread (e.g., 'medical leave', 'Dean', 'grades')."
        ),
    ],
) -> dict:  # Return a dictionary, not a string
    """Queries the connected email inbox via Nylas API and returns structured data for Adaptive Cards."""
    grant_id = NYLAS_GRANT_ID

    if not grant_id:
        return {"error": "Nylas Grant ID missing from environment configuration."}

    try:
        query_params = {
            "search_query_native": search_query,
            "limit": 30,
        }

        response = nylas_client.messages.list(
            identifier=grant_id,
            query_params=query_params, # type: ignore
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

            # 3. Append a dictionary to the list
            formatted_emails.append(
                {
                    "message_id": msg.id,  # Useful if you want to add an Action.Submit to "Read Full Email"
                    "sender": sender_name,
                    "subject": subject,
                    "snippet": (
                        snippet[:500] + "..." if len(snippet) > 500 else snippet
                    ),  # Truncate for UI
                }
            )

        # 4. Return the structured root object
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
            "limit": 15,  # Keep context small and relevant
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


def screen_n_categorize(sentence: str) -> dict | None:
    """
    Helper function to screen a sentence for dates/times and categorize its urgency.
    Returns a structured dictionary if a temporal commitment or action is found, else None.
    """
    # 1. Regex Patterns for Dates, Times, and Days
    date_pattern = re.compile(
        r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?)\b",
        re.IGNORECASE,
    )
    time_pattern = re.compile(
        r"\b(?:1[0-2]|0?[1-9])(?::[0-5][0-9])?\s*(?:AM|PM|am|pm)\b", re.IGNORECASE
    )
    day_pattern = re.compile(
        r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b",
        re.IGNORECASE,
    )

    dates_found = date_pattern.findall(sentence)
    times_found = time_pattern.findall(sentence)
    days_found = day_pattern.findall(sentence)

    sentence_lower = sentence.lower()

    # 2. Heuristic keywords for actionability
    is_actionable = any(
        kw in sentence_lower
        for kw in [
            "due",
            "submit",
            "deadline",
            "by",
            "required",
            "rsvp",
            "closing",
            "assignment",
        ]
    )
    is_urgent = any(
        kw in sentence_lower
        for kw in ["urgent", "immediately", "today", "tomorrow", "asap"]
    )

    # 3. Categorize and build the dictionary if conditions are met
    if dates_found or days_found or is_actionable or is_urgent:
        severity = "High" if is_urgent else ("Medium" if is_actionable else "Low")

        # Determine the best date string to show
        best_date = "Implied/Relative"
        if dates_found:
            best_date = dates_found[0]
        elif days_found:
            best_date = f"Coming {days_found[0]}"

        return {
            "context": sentence.strip(),
            "extracted_date": best_date,
            "extracted_time": times_found[0] if times_found else "EOD (Assumed)",
            "actionable": is_actionable,
            "severity_tier": severity,
        }

    return None


@tool(
    name="extract_deadlines",
    description=(
        "Scans a block of raw text OR a JSON payload of emails (from retrieve_student_emails) "
        "and extracts concrete dates, times, and actionable deadlines using heuristic pattern matching."
    ),
    approval_mode="never_require",
)
def extract_deadlines(
    text_content: Annotated[
        str,
        Field(
            description="The raw text body, or JSON string of emails, to be parsed for deadlines."
        ),
    ],
) -> str:
    """
    Uses Regex heuristics to identify temporal commitments. Smartly handles JSON email payloads
    to preserve sender/subject context, or falls back to raw text processing.
    """
    extracted_data = []
    severity_map = {"High": 1, "Medium": 2, "Low": 3}

    # 1. Try parsing as JSON (integration with retrieve_student_emails)
    try:
        data = json.loads(text_content)
        if isinstance(data, dict) and "emails" in data:
            for email in data["emails"]:
                # Combine subject and snippet for scanning
                combined_text = (
                    f"{email.get('subject', '')}. {email.get('snippet', '')}"
                )
                sentences = re.split(r"(?<=[.!?]) +", combined_text.replace("\n", " "))

                for sentence in sentences:
                    categorized = screen_n_categorize(sentence)
                    if categorized:
                        # Append email-specific metadata to the extracted deadline
                        categorized["source"] = (
                            f"Email from {email.get('sender', 'Unknown')}"
                        )
                        categorized["subject"] = email.get("subject", "No Subject")
                        extracted_data.append(categorized)

            extracted_data.sort(key=lambda x: severity_map.get(x["severity_tier"], 4))
            return json.dumps(
                {
                    "status": "success",
                    "emails_scanned": len(data["emails"]),
                    "deadlines_identified": len(extracted_data),
                    "found_deadlines": extracted_data,
                },
                indent=4,
            )

    except json.JSONDecodeError:
        pass  # Not a JSON payload, proceed to raw text parsing

    # 2. Fallback: Parse as raw text
    sentences = re.split(r"(?<=[.!?]) +", text_content.replace("\n", " "))
    for sentence in sentences:
        categorized_data = screen_n_categorize(sentence)
        if categorized_data:
            categorized_data["source"] = "Raw Text Document"
            extracted_data.append(categorized_data)

    # Sort by severity
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
