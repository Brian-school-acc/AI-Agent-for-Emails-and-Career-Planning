import os
import io
import json

from agent_framework import tool
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas

import pandas as pd
import tempfile
from dotenv import load_dotenv
from pydantic import Field
from random import randint
from datetime import datetime, timedelta, timezone

from docx import Document
from pptx import Presentation
from typing import Annotated
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


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


# ============================================================================================================
# TOOL 4: Generate Documents of Different File Types - Lightweight independent tools + local_2_azure() helper
# ============================================================================================================


# 1. THE HELPER FUNCTION (Not a tool, just reusable code)
def upload_and_link(temp_path: str, filename: str) -> str:
    ACCOUNT_NAME = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    ACCOUNT_KEY = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
    CONTAINER_NAME = os.environ.get("AZURE_BLOB_CONTAINER_NAME")

    # 1. Credential Validation
    err_msg: list[str] = []
    if not ACCOUNT_NAME:
        err_msg.append("ACCOUNT_NAME")
    if not ACCOUNT_KEY:
        err_msg.append("ACCOUNT_KEY")
    if not CONTAINER_NAME:
        err_msg.append("CONTAINER_NAME")

    if err_msg:
        raise EnvironmentError(f"Missing Credentials: {', '.join(err_msg)}")

    # 2. Upload and Link Generation with Safe Cleanup
    try:
        blob_service_client = BlobServiceClient(
            account_url=f"https://{ACCOUNT_NAME}.blob.core.windows.net",
            credential=ACCOUNT_KEY,
        )
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, blob=filename # type: ignore
        )

        # Upload the file
        with open(temp_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        # Generate SAS token
        expiry_time = datetime.now(timezone.utc) + timedelta(hours=1)
        sas_token = generate_blob_sas(
            account_name=ACCOUNT_NAME, # type: ignore
            container_name=CONTAINER_NAME, # type: ignore
            blob_name=filename,
            account_key=ACCOUNT_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
        )

        return f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{filename}?{sas_token}"

    finally:
        # 3. Guaranteed Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)


# 4A - DOCX
@tool(
    name="generate_docx",
    description=(
        "Generates a Microsoft Word document (.docx) from structured text content. "
        "Use this tool when a user explicitly requests a text report, formal summary, or essay download. "
        "The file extension '.docx' is automatically appended if missing."
    ),
)
def generate_docx(filename: str, content: str) -> str:
    """
    Generates a Word file from text, pushes it to Azure Storage, and outputs a download URL.

    Args:
        filename (str): Desired output name (e.g., 'academic_report.docx').
        content (str): Plain text file data. Newlines create individual document paragraphs.

    Returns:
        str: A Markdown string embedding the functional file download hyperlink.
    """
    if not filename.lower().endswith(".docx"):
        filename += ".docx"

    doc = Document()
    for line in content.split("\n"):
        if line.strip():
            doc.add_paragraph(line.strip())

    temp_path = os.path.join(tempfile.gettempdir(), filename)
    doc.save(temp_path)

    url = upload_and_link(temp_path, filename)
    return f"Document ready: [Download {filename}]({url})"


# 4B - XLSX
@tool(
    name="generate_xlsx",
    description=(
        "Generates a professional Microsoft Excel (.xlsx) spreadsheet from a raw CSV text string. "
        "Use this tool whenever structural tabular data, datasets, or grade listings must be compiled "
        "and made downloadable for analysis. The system handles table indexing and auto-formatting."
    ),
)
def generate_xlsx(filename: str, csv_data: str) -> str:
    """
    Parses a CSV data string into a Pandas DataFrame, exports to Excel format, and uploads to cloud storage.

    Args:
        filename (str): Target spreadsheet filename (e.g., 'student_grades.xlsx').
        csv_data (str): Comma-separated or tabular string layout containing rows and headers.

    Returns:
        str: Markdown output link to fetch the target compiled spreadsheet file.
    """
    if not filename.lower().endswith(".xlsx"):
        filename += ".xlsx"

    # Convert the plain text CSV string into a structure Pandas can work with
    df = pd.read_csv(io.StringIO(csv_data.strip()))

    temp_path = os.path.join(tempfile.gettempdir(), filename)
    df.to_excel(temp_path, index=False, engine="openpyxl")

    url = upload_and_link(temp_path, filename)
    return f"Spreadsheet ready: [Download {filename}]({url})"


# 4C - PPTX
@tool(
    name="generate_pptx",
    description=(
        "Generates a Microsoft PowerPoint (.pptx) presentation deck. The 'slides_json' input parameter "
        "MUST be a JSON-formatted string array of objects where each slide configuration explicitly "
        "contains a 'title' string and a 'bullets' list of strings. Use this for presentation summaries."
    ),
)
def generate_pptx(filename: str, slides_json: str) -> str:
    """
    Compiles a structured presentation layout array into a downloadable PowerPoint slide deck.

    Args:
        filename (str): Presentation filename target (e.g., 'lecture_summary.pptx').
        slides_json (str): A serialized JSON array matching the structure:
            '[{"title": "Intro", "bullets": ["Point A", "Point B"]}]'

    Returns:
        str: Hyperlink payload directing users to download the resulting presentation file.
    """
    if not filename.lower().endswith(".pptx"):
        filename += ".pptx"

    prs = Presentation()
    slide_layout = prs.slide_layouts[1]  # Title and Content slide structure template

    try:
        slide_data = json.loads(slides_json)
        for data in slide_data:
            slide = prs.slides.add_slide(slide_layout)
            slide.shapes.title.text = data.get("title", "Untitled Slide")

            tf = slide.placeholders[1].text_frame
            for idx, bullet in enumerate(data.get("bullets", [])):
                p = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
                p.text = bullet
    except Exception as e:
        return f"Error compiling presentation layout parameters: {str(e)}"

    temp_path = os.path.join(tempfile.gettempdir(), filename)
    prs.save(temp_path)

    url = upload_and_link(temp_path, filename)
    return f"Presentation deck ready: [Download {filename}]({url})"


# 4D - PDF
@tool(
    name="generate_pdf",
    description=(
        "Generates an unmodifiable Portable Document Format (.pdf) file. Use this tool specifically "
        "when unalterable or print-ready formal assets like certificate letters, formal transcript text wrappers, "
        "or invoices are requested by the user."
    ),
)
def generate_pdf(filename: str, content: str) -> str:
    """
    Constructs a structurally sound PDF document out of plaintext content, managing layouts elegantly via ReportLab.

    Args:
        filename (str): Target PDF filename constraint (e.g., 'official_notice.pdf').
        content (str): Plain text asset blocks. Newlines represent layout spacers or structural paragraph breaks.

    Returns:
        str: Hyperlink payload pointing directly to the compiled cloud-hosted PDF.
    """
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    temp_path = os.path.join(tempfile.gettempdir(), filename)

    doc = SimpleDocTemplate(temp_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    for line in content.split("\n"):
        if line.strip():
            p = Paragraph(line.strip(), styles["Normal"])
            story.append(p)
            story.append(
                Spacer(1, 12)
            )  # Consistent standard typographic spacing padding

    doc.build(story)

    url = upload_and_link(temp_path, filename)
    return f"PDF Asset generated successfully: [Download {filename}]({url})"
