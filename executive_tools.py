import os

from agent_framework import tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas

import datetime
import httpx
import tempfile
from datetime import datetime, timedelta
from docx import Document
from dotenv import load_dotenv
from pydantic import Field
from random import randint
from typing import Annotated, List, Dict, Optional, Any, Literal


load_dotenv()

# ==========================================
# TOOL 1: SCHEDULE CALENDAR EVENT
# ==========================================

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


# ==========================================
# TOOL 1: CREATE PLANNER TASKS
# ==========================================

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


# ==========================================
# TOOL 3: DRAFT EMAILS TO LECTURERS
# ==========================================

@tool(approval_mode="never_require")
def draft_lecturer_email(
    main_idea: Annotated[
        str,
        Field(
            description="The core request or issue the student needs to express (e.g., 'Requesting a 2-day extension on the Python project due to illness')."
        ),
    ],
    tone: Annotated[
        str,
        Field(
            description="The desired psychological/professional tone of the email (e.g., 'respectful', 'apologetic', 'urgent', 'inquisitive')."
        ),
    ],
    length: Annotated[
        str,
        Field(
            description="The preferred length of the email (e.g. 'short', 'moderate', 'long')."
        ),
    ],
) -> str:
    """
    Generates a professionally structured, polished email draft specifically tailored for academic staff and lecturers.

    This tool converts a student's raw thoughts and emotional tone into a high-quality academic passage,
    ensuring correct structural layout (Subject line, formal greeting, context, action item, and polite sign-off).
    """
    # Few-shot templates map based on the requested tone
    templates = {
        "apologetic": (
            "Subject: Extension Request: [Course Name] - [Your Name]\n\n"
            "Dear Professor [Last Name],\n\n"
            "I am writing to sincerely apologize for my upcoming absence/delay. {main_idea}. "
            "I understand the importance of deadlines and truly regret any inconvenience this may cause. "
            "Could we discuss the possibility of an extension, or a time to review what I've missed?\n\n"
            "Thank you for your time and understanding.\n\nSincerely,\n[Your Name]\n[Student ID]"
        ),
        "respectful": (
            "Subject: Inquiry regarding [Topic/Course] - [Your Name]\n\n"
            "Dear Dr. [Last Name],\n\n"
            "I hope this email finds you well. I am reaching out to respectfully ask for your guidance regarding "
            "the current course material. Specifically, {main_idea}. "
            "I have reviewed the syllabus and class notes, but I would greatly appreciate your expert clarification "
            "during your upcoming office hours if possible.\n\n"
            "Thank you for your support and dedication to our learning.\n\nBest regards,\n[Your Name]\n[Student ID]"
        ),
        "urgent": (
            "Subject: URGENT: Academic Conflict / Clarification Needed - [Your Name]\n\n"
            "Dear Professor [Last Name],\n\n"
            "I apologize for the urgent nature of this message, but I am facing an immediate constraint: {main_idea}. "
            "Given the proximity of the deadline, I wanted to bring this to your attention as soon as possible "
            "to explore potential paths forward or alternatives.\n\n"
            "I will follow up with you after our next lecture, or am available to meet sooner if your schedule permits.\n\n"
            "Thank you for your prompt attention to this matter.\n\nRespectfully,\n[Your Name]\n[Student ID]"
        ),
    }

    # Fallback to a standard polite template if the exact tone isn't pre-configured
    selected_template = templates.get(tone.lower(), templates["respectful"])
    return selected_template.format(main_idea=main_idea) + f" Length of email: {length}"


@tool(
    name="generate_and_link_docx",
    description="Generates a report and provides a secure download link.",
)
def generate_and_link_docx(filename: str, content: str) -> str:
    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
    container_name = os.environ.get("AZURE_BLOB_CONTAINER_NAME")

    # 0. Checking storage account credentials
    err_msg: list[str] = []
    if account_name is None:
        err_msg.append(f"ACCOUNT_NAME: {account_name}")
    if account_key is None:
        err_msg.append(f"ACCOUNT_KEY: {account_key}")
    if container_name is None:
        err_msg.append(f"CONTAINER_NAME: {container_name}")
    
    if err_msg:
        raise EnvironmentError(f"Mssing Credentials: {", ".join(err_msg)}")

    # 1. Generate local document
    doc = Document()
    for line in content.split("\n"):
        doc.add_paragraph(line.strip())

    temp_path = os.path.join(tempfile.gettempdir(), filename)
    doc.save(temp_path)

    # 2. Upload to Azure
    blob_service_client = BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=account_key,
    )
    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=filename # type: ignore
    )

    with open(temp_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    # 3. Generate a 1-hour SAS Download URL
    sas_token = generate_blob_sas(
        account_name=account_name, # type: ignore
        container_name=container_name, # type: ignore
        blob_name=filename,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    download_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{filename}?{sas_token}"
    os.remove(temp_path)

    # The agent will output this markdown directly to the Copilot UI
    return f"Document generated successfully. [Click here to download {filename}]({download_url})"
