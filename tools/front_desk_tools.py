import json
import random

from agent_framework import tool
from datetime import datetime
from typing import Annotated
from pydantic import Field
from zoneinfo import ZoneInfo


@tool
def show_agent_selection_menu() -> str:
    """
    Presents a rich, interactive visual card containing a menu of specialized
    success agents (Career Coach, Executive Office, Archivist, Front Desk).
    Invoke this tool whenever a student says they want to switch departments,
    is unsure who to talk to, or when their problem could span multiple areas.
    """
    card_schema = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": "🤖 Connect with a Specialized Assistant",
                "weight": "Bolder",
                "size": "Large",
                "color": "Accent",
            },
            {
                "type": "TextBlock",
                "text": "Select the specialized AI coach or department you need to interact with.",
                "isSubtle": True,
                "wrap": True,
            },
            {
                "type": "Container",
                "separator": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "💼 Career Coach",
                        "weight": "Bolder",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Get resume reviews and interview practice.",
                        "isSubtle": True,
                        "size": "Small",
                    },
                ],
            },
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "🏛️ Executive Office",
                        "weight": "Bolder",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Handles formal academic appeals and exceptions.",
                        "isSubtle": True,
                        "size": "Small",
                    },
                ],
            },
            {
                "type": "Container",
                "items": [
                    {"type": "TextBlock", "text": "🗄️ Archivist", "weight": "Bolder"},
                    {
                        "type": "TextBlock",
                        "text": "Retrieve historical student records and transcripts.",
                        "isSubtle": True,
                        "size": "Small",
                    },
                ],
            },
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Launch Career Coach",
                "data": {"actionType": "route_to_agent", "targetAgent": "career_coach"},
            },
            {
                "type": "Action.Submit",
                "title": "Launch Executive Agent",
                "data": {"actionType": "route_to_agent", "targetAgent": "executive"},
            },
            {
                "type": "Action.Submit",
                "title": "Launch Archivist",
                "data": {"actionType": "route_to_agent", "targetAgent": "archivist"},
            },
        ],
    }

    # Returning the schema as a serialized string.
    # M365 Copilot intercepts json matching the AdaptiveCard schema and renders it as UI.
    return json.dumps(card_schema)


@tool
def get_weather(location: Annotated[str, "The city name or location string (e.g., 'Seattle', 'Hong Kong')."],) -> str:
    """
    Get the current weather conditions and temperature for a given location.
    If the user does not specify the location, use "Hong Kong" as the default location,
    and particularly specify it in your response.
    """
    conditions = ["sunny", "cloudy", "rainy", "overcast", "clear"]
    chosen_condition = random.choice(conditions)
    high_temp = random.randint(30, 34)
    low_temp = high_temp - random.randint(6, 8)

    return f"The weather in {location} is currently {chosen_condition} with a high of {high_temp}°C and a low of {low_temp}°C."


@tool
def get_current_time() -> str:
    """
    Get the current local time for a given location to help answer relative time and date questions.
    If the user does not specify the location, use "Hong Kong" as the default location,
    and particularly specify it in your response.
    """

    # M365 Copilot often benefits from highly specific time formatting
    tz_utc8 = ZoneInfo("Asia/Shanghai")   # or "Asia/Singapore", "Australia/Perth", "Etc/GMT-8"
    now_utc8 = datetime.now(tz_utc8)
    return now_utc8.strftime("%I:%M %p on %A, %B %d, %Y in Hong Kong (UTC+8)")


@tool(approval_mode="never_require")
def get_general_faq(
    topic: Annotated[
        str,
        Field(
            description="The exact topic keyword to lookup. Must be one of: wifi, hours, support, parking, address, shuttle, library, graduation, access, tuition."
        ),
    ],
) -> str:
    """Look up standard institutional operational answers such as WiFi details, office hours, or public contacts."""
    faq_db = {
        "wifi": "To connect to the campus WiFi, select 'CUHK1x' (or 'WiFi CUHK1x'). Students, staff, and registered guests can log in with their OnePass credentials. Coverage includes most academic buildings, libraries, and hostels.",
        "hours": "Main administrative front desk: Monday to Friday 8:30 AM – 5:00 PM. University Library: today 8:20 AM – 10 PM. University Gallery: Mon–Wed, Fri, Sat 10 AM – 5 PM; Sun 12 PM – 5 PM; closed Thu & public holidays.",
        "support": "For IT support: use the Online Service Desk (chat during office hours) or call hotline 3943 8845. For general campus security or parking: visit www.scu.cuhk.edu.hk. For SEN services: call 3943 5441 or email sens@cuhk.edu.hk.",
        "parking": "Visitor parking is available at open areas like the front of William M.W. Mong Engineering Building and near University Station Exit D. Parking fees and regulations are posted on the Security Office website.",
        "address": "Central Avenue, The Chinese University of Hong Kong, Shatin, New Territories, Hong Kong.",
        "shuttle": "Campus shuttle buses (No. 1A, 1B, 2, 3) depart from the University bus station near MTR University Station Exits A/C. Night service (N Night) runs from 7 PM to 11 PM.",
        "library": "University Library: over 2,400 study seats, computer terminals, group study rooms, and the Learning Garden (open 24/7 during semesters). Contact: (852) 3943 7306 or library@cuhk.edu.hk.",
        "graduation": "Graduation ceremony registration is online. The ceremony lasts about 1.5 hours and is conducted in English. Certificates are not handed out at the ceremony—refer to the 'Collection of Graduation Certificate' page.",
        "access": "Visitors: pre-registered guests need a person‑specific QR code + HKID. Smartcard holders validate at readers. Alumni Credit Card holders present their card. Others must register HKID at entry points.",
        "tuition": "Finance Office sends email notifications when debit notes are issued. Log into CUSIS to view tuition fee details and payment due dates.",
    }

    key = topic.lower().strip()

    # Fixed: Use 'in' to handle cases where the model passes a whole phrase instead of a single keyword
    for db_key, answer in faq_db.items():
        if db_key in key:
            return answer

    return f"I couldn't find a standard FAQ entry for '{topic}'. Let me know if you need help reaching a human representative."
