import json
import random

from agent_framework import tool
from datetime import datetime
from typing import Annotated
from pydantic import Field
from zoneinfo import ZoneInfo


@tool(
    name="get_weather",
    description=(
        "Get the current weather conditions and temperature for a given location. "
        "If the user does not specify the location, use 'Hong Kong' "
        "as the default location, and explicitly state it in your response."
    ),
    approval_mode="never_require"
)
def get_weather(
    location: Annotated[
        str,
        Field(
            description=(
                "Get the current weather conditions and temperature for a given location. "
                "If the location is not explicitly specified by the user, default to 'Hong Kong'. "
                "Always include the location in your final response."
            )
        ),
    ],
) -> str:
    """
    Get the current weather conditions and temperature for a given location.
    If the user does not specify the location, it means "Hong Kong".
    Also, specify the location in your response.
    """
    conditions = ["sunny", "cloudy", "rainy", "overcast", "clear"]
    chosen_condition = random.choice(conditions)
    high_temp = random.randint(30, 34)
    low_temp = high_temp - random.randint(6, 8)

    return f"The weather in {location} is currently {chosen_condition} with a high of {high_temp}°C and a low of {low_temp}°C."


@tool(
    name="get_current_time",
    description=(
        "Get the current local time for a given location to help answer relative time "
        "and date questions. If the user does not specify the location, use 'Hong Kong' "
        "as the default location, and explicitly state it in your response."
    ),
    approval_mode="never_require"
)
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


@tool(
    name="get_general_faq",
    description=(
        "Look up standard institutional operational answers such as WiFi details, "
        "office hours, or public contacts. You must provide an exact topic keyword "
        "to lookup. Valid keywords are: wifi, hours, support, parking, address, "
        "shuttle, library, graduation, access, tuition."
    ),
    approval_mode="never_require")
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
