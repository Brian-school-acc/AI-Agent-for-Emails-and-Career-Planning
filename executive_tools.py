from agent_framework import tool
from random import randint


@tool(
    name="schedule_calendar_event",
    description="Creates a time-blocked event on the student's Outlook calendar for tasks, studying, or meetings.",
    approval_mode="always_require",  # Approving calendar modifications is standard practice
)
def schedule_calendar_event(title: str, start_time: str, duration_minutes: int) -> str:
    """
    Schedule an event on the user's calendar.
    Args:
        title: The name of the event or time-block.
        start_time: ISO 8601 formatted datetime string (e.g., '2026-06-16T14:00:00Z').
        duration_minutes: How long the event should last.
    """
    return f"Successfully scheduled '{title}' for {duration_minutes} minutes starting at {start_time}. Calendar invite sent."


@tool(
    name="create_planner_task",
    description="Adds an actionable task to Microsoft To Do or Planner, complete with due dates and categorized buckets.",
    approval_mode="never_require",
)
def create_planner_task(task_name: str, due_date: str, priority: str = "normal") -> str:
    """
    Create a task in M365 Planner/To Do.
    Args:
        task_name: Description of the task.
        due_date: ISO 8601 formatted date string.
        priority: 'low', 'normal', or 'high'.
    """
    task_id = f"task_{randint(1000, 9999)}"
    return f"Task '{task_name}' created successfully (ID: {task_id}) with priority '{priority}', due on {due_date}."
