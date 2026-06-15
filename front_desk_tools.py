import os, glob
import random
import re

from agent_framework import tool
from datetime import datetime, timedelta
from typing import Annotated
from pydantic import Field
from zoneinfo import ZoneInfo

# IMPORTANT
# Note that modifying tools need to update prompt as well
# IMPORTANT

# @tool(approval_mode="never_require")
# def get_weather(location: Annotated[str,Field(description="The city name or location string (e.g., 'Seattle', 'Hong Kong')."),],) -> str:
#     """Get the current weather conditions and temperature for a given location."""
#     conditions = ["sunny", "cloudy", "rainy", "overcast", "clear"]
#     chosen_condition = random.choice(conditions)
#     high_temp = random.randint(15, 32)
#     low_temp = high_temp - random.randint(5, 10)

#     return f"The weather in {location} is currently {chosen_condition} with a high of {high_temp}°C and a low of {low_temp}°C."


# @tool(approval_mode="never_require")
# def get_weather(location: str) -> str:
#     """
#     Get the current weather conditions and temperature for a given location.

#     Args:
#         location: The city name or location string (e.g., 'Seattle', 'Hong Kong').
#     """
#     conditions = ["sunny", "cloudy", "rainy", "overcast", "clear"]
#     chosen_condition = random.choice(conditions)
#     high_temp = random.randint(15, 32)
#     low_temp = high_temp - random.randint(5, 10)

#     return f"The weather in {location} is currently {chosen_condition} with a high of {high_temp}°C and a low of {low_temp}°C."


@tool
def get_weather(location: Annotated[str, "The city name or location string (e.g., 'Seattle', 'Hong Kong')."],) -> str:
    """Get the current weather conditions and temperature for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "overcast", "clear"]
    chosen_condition = random.choice(conditions)
    high_temp = random.randint(15, 32)
    low_temp = high_temp - random.randint(5, 10)

    return f"The weather in {location} is currently {chosen_condition} with a high of {high_temp}°C and a low of {low_temp}°C."


@tool
def get_current_time() -> str:
    """Get the current local time to help answer relative time and date questions."""
    # M365 Copilot often benefits from highly specific time formatting
    return datetime.now().strftime("%I:%M %p on %A, %B %d, %Y")


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
