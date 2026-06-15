from agent_framework import tool  # Ensure you import the tool decorator
from datetime import datetime


@tool
def get_current_time() -> str:
    """Retrieves the current date and time. Use this when the user asks for the time."""
    # Using the timezone from your system context
    return datetime.now().strftime("%A, %B %d, %Y at %I:%M:%S %p")
