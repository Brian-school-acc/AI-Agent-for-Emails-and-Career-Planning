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
from docxtpl import DocxTemplate
from pptx import Presentation
from typing import Annotated
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


load_dotenv()

# ==========================================
# TOOL 1: SCHEDULE CALENDAR EVENT
# ==========================================

@tool(
    name="schedule_calendar_event",
    description=(
        "Creates a time-blocked event on the student's Outlook calendar for tasks, studying, "
        "or meetings. Requires the title, start time (in ISO 8601 format), and duration in minutes."
    ),
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
    description=(
        "Adds an actionable task to Microsoft To Do or Planner, complete with due dates and "
        "categorized buckets. Requires the task name, due date (in ISO 8601 format), and priority level."
    ),
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


@tool(
    name="draft_lecturer_email",
    description=(
        "Generates a professionally structured, polished email draft specifically tailored for "
        "academic staff and lecturers. This tool converts a student's raw thoughts and emotional "
        "tone into a high-quality academic passage, ensuring correct structural layout (Subject "
        "line, formal greeting, context, action item, and polite sign-off)."
    ),
    approval_mode="never_require",
)
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


from tools.general_tools import upload_and_link

# 4A - DOCX
@tool(
    name="generate_docx",
    description=(
        "Generates a Microsoft Word document (.docx) from structured text content. "
        "Use this tool when a user explicitly requests a text report, formal summary, or essay download. "
        "The file extension '.docx' is automatically appended if missing."
    ),
    approval_mode="never_require",
)
def generate_docx(filename: str, content: str) -> str:
    """
    Generates a beautifully formatted Word file from text, pushes it to Azure Storage, and outputs a download URL.
    Supports basic Markdown syntax (# Title, ## Heading 1, ### Heading 2, and bullet points) to create professional hierarchies.

    Args:
        filename (str): Desired output name (e.g., 'academic_report.docx').
        content (str): Plain text file data supporting light Markdown for structure.

    Returns:
        str: A Markdown string embedding the functional file download hyperlink.
    """
    if not filename.lower().endswith(".docx"):
        filename += ".docx"

    doc = Document()

    # Parse content line by line to map plain text to native Word styles
    for line in content.split("\n"):
        cleaned_line = line.strip()
        if not cleaned_line:
            continue

        # Map Markdown syntax to python-docx built-in styles
        if cleaned_line.startswith("# "):
            # level=0 automatically applies the 'Title' style
            doc.add_heading(cleaned_line[2:], level=0)

        elif cleaned_line.startswith("## "):
            # level=1 applies 'Heading 1'
            doc.add_heading(cleaned_line[3:], level=1)

        elif cleaned_line.startswith("### "):
            # level=2 applies 'Heading 2'
            doc.add_heading(cleaned_line[4:], level=2)

        elif cleaned_line.startswith("- ") or cleaned_line.startswith("* "):
            # Maps to Word's native bulleted list format
            doc.add_paragraph(cleaned_line[2:], style="List Bullet")

        else:
            # Standard body paragraph
            doc.add_paragraph(cleaned_line)

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
    approval_mode="never_require",
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
    approval_mode="never_require",
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
            slide.shapes.title.text = data.get("title", "Untitled Slide") # type: ignore

            tf = slide.placeholders[1].text_frame # type: ignore
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
    approval_mode="never_require",
)
def generate_pdf(filename: str, content: str) -> str:
    """
    Constructs a structurally sound, beautifully formatted PDF document out of plaintext content.
    Supports basic Markdown syntax (# for Title, ## for H1, ### for H2) to generate professional layouts.

    Args:
        filename (str): Target PDF filename constraint (e.g., 'official_notice.pdf').
        content (str): Plain text asset blocks supporting light Markdown headings.

    Returns:
        str: Hyperlink payload pointing directly to the compiled cloud-hosted PDF.
    """
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    temp_path = os.path.join(tempfile.gettempdir(), filename)
    font_path = os.path.join(
        "tools", "Arial-Unicode-MS.ttf"
    )  # Register a font supporting symbols
    pdfmetrics.registerFont(TTFont("CustomFont", font_path))

    # Initialize document with standard 0.75-inch (54 points) margins
    doc = SimpleDocTemplate(
        temp_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # 1. Define a polished typographic hierarchy with proportional leading
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontName="CustomFont",
        fontSize=24,
        leading=28,
        spaceAfter=18,
        alignment=1,  # Centered
    )
    h1_style = ParagraphStyle(
        "CustomH1",
        parent=styles["Heading1"],
        fontName="CustomFont",
        fontSize=16,
        leading=20,
        spaceBefore=16,
        spaceAfter=6,
        keepWithNext=True,  # Prevents orphan headings at the bottom of pages
    )
    h2_style = ParagraphStyle(
        "CustomH2",
        parent=styles["Heading2"],
        fontName="CustomFont",
        fontSize=12,
        leading=16,
        spaceBefore=12,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontName="CustomFont",
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )

    story = []

    # 2. Parse content line by line to map plain text to proper PDF styles
    for line in content.split("\n"):
        cleaned_line = line.strip()
        if not cleaned_line:
            continue  # Let ParagraphStyle handle vertical spacing instead of blank lines

        # Basic Markdown syntax parsing
        if cleaned_line.startswith("# "):
            p = Paragraph(cleaned_line[2:], title_style)
            story.append(p)
        elif cleaned_line.startswith("## "):
            p = Paragraph(cleaned_line[3:], h1_style)
            story.append(p)
        elif cleaned_line.startswith("### "):
            p = Paragraph(cleaned_line[4:], h2_style)
            story.append(p)
        else:
            p = Paragraph(cleaned_line, body_style)
            story.append(p)

    doc.build(story)

    url = upload_and_link(temp_path, filename)
    return f"PDF Asset generated successfully: [Download {filename}]({url})"


# 4E - Resume
@tool(
    name="generate_resume",
    description=(
        "Generates a beautifully formatted, ATS-friendly Word (.docx) resume from a structured JSON dataset. "
        "The JSON must include 'name', 'contact_info', 'summary', 'experience', 'education', and 'skills'."
        "If your resume_data_json contains '%', you MUST replace it with '%%' to fit the Jinja2 format"
    ),
    approval_mode="never_require",
)
def generate_resume(
    filename: Annotated[
        str, Field(description="Target output filename (e.g., 'resume_name.docx').")
    ],
    resume_data_json: Annotated[
        str,
        Field(
            description=(
                "A serialized JSON string containing the resume data. You MUST use these exact keys "
                "to match the Jinja2 template:\n"
                "{\n"
                "  'name': 'string',\n"
                "  'region': 'string',\n"
                "  'contact_info': 'string',\n"
                "  'experience': [{\n"
                "     'title': 'string',\n"
                "     'company': 'string',\n"
                "     'dates': 'string',\n"
                "     'details': ['bullet 1', 'bullet 2']\n"
                "  }],\n"
                "  'education': [{\n"
                "     'institution': 'string',\n"
                "     'degree': 'string',\n"
                "     'dates': 'string',\n"
                "     'details': 'string'\n"
                "  }],\n"
                "  'awards': [{'name': 'string', 'year': 'string'}],\n"
                "  'projects': [{'name': 'string', 'details': 'string'}]\n"
                "}\n"
                "If any section like awards or projects is blank, pass an empty list [] for it."
            )
        ),
    ],
) -> str:
    """
    Injects JSON data into a pre-designed Microsoft Word template to generate a professional CV.
    """
    if not filename.lower().endswith(".docx"):
        filename += ".docx"

    try:
        context = json.loads(resume_data_json)
    except json.JSONDecodeError as e:
        return f"Error parsing resume JSON data: {str(e)}. Please provide a valid, raw JSON schema structure."

    # --- DEFENSIVE DATA PATCHING FOR JINJA2 SAFETY ---
    # Ensure mandatory template loop keys exist as iterable arrays to prevent engine crashes
    for list_key in ["experience", "education", "awards", "projects"]:
        if list_key not in context or not isinstance(context[list_key], list):
            context[list_key] = []

    # Normalize skills to always be an iterable list
    if "skills" in context:
        if isinstance(context["skills"], str):
            context["skills"] = [
                s.strip() for s in context["skills"].split(",") if s.strip()
            ]
    else:
        context["skills"] = []
    # -------------------------------------------------

    # 1. Load your pre-designed Word document template
    template_path = os.path.join("tools", "templates", "resume_template.docx")
    if not os.path.exists(template_path):
        return "Error: Resume template file not found."

    try:
        doc = DocxTemplate(template_path)

        # 2. Render the document (injects the JSON dict into the {{ tags }})
        doc.render(context)

        # 3. Save to temp directory
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        doc.save(temp_path)
    except Exception as e:
        return f"Template compilation failure: {str(e)}. Ensure data formats cleanly match internal variable definitions."

    # 4. Upload and return link
    url = upload_and_link(temp_path, filename)
    return f"Resume generated successfully: [Download {filename}]({url})"


# @tool(
#     name="generate_resume",
#     description=(
#         "Generates a beautifully designed, professional PDF resume/CV from a structured JSON dataset. "
#         "The JSON must include 'name', 'contact' (string or list), 'summary', 'experience' (list of dicts with "
#         "'title', 'company', 'dates', 'details'), 'education' (list of dicts), and 'skills' (list of strings)."
#     ),
#     approval_mode="never_require",
# )
# def generate_resume(
#     filename: Annotated[
#         str, Field(description="Target output filename (e.g., 'john_doe_resume.pdf').")
#     ],
#     resume_data_json: Annotated[
#         str,
#         Field(
#             description="A serialized JSON string containing the structured resume data."
#         ),
#     ],
# ) -> str:
#     """
#     Constructs a visually striking, professionally designed PDF CV using ReportLab.

#     Args:
#         filename (str): The desired output filename.
#         resume_data_json (str): JSON string containing the resume content payload.

#     Returns:
#         str: Hyperlink payload pointing directly to the compiled cloud-hosted PDF CV.
#     """
#     if not filename.lower().endswith(".pdf"):
#         filename += ".pdf"

#     try:
#         data = json.loads(resume_data_json)
#     except json.JSONDecodeError as e:
#         return f"Error parsing resume JSON data: {str(e)}"

#     temp_path = os.path.join(tempfile.gettempdir(), filename)

#     # Initialize document with standard 0.5-inch margins for optimal page usage
#     doc = SimpleDocTemplate(
#         temp_path,
#         pagesize=letter,
#         rightMargin=36,
#         leftMargin=36,
#         topMargin=36,
#         bottomMargin=36,
#     )

#     styles = getSampleStyleSheet()

#     # Define polished typography tailored for a CV
#     name_style = ParagraphStyle(
#         "NameStyle",
#         parent=styles["Heading1"],
#         fontName="Helvetica-Bold",
#         fontSize=24,
#         leading=28,
#         spaceAfter=6,
#         alignment=TA_CENTER,
#         textColor=colors.HexColor("#2C3E50"),
#     )

#     contact_style = ParagraphStyle(
#         "ContactStyle",
#         parent=styles["Normal"],
#         fontName="Helvetica",
#         fontSize=10,
#         alignment=TA_CENTER,
#         textColor=colors.HexColor("#7F8C8D"),
#         spaceAfter=12,
#     )

#     section_header_style = ParagraphStyle(
#         "SectionHeader",
#         parent=styles["Heading2"],
#         fontName="Helvetica-Bold",
#         fontSize=14,
#         textColor=colors.HexColor("#2980B9"),
#         spaceBefore=16,
#         spaceAfter=4,
#         textTransform="uppercase",
#     )

#     job_title_style = ParagraphStyle(
#         "JobTitle",
#         parent=styles["Heading3"],
#         fontName="Helvetica-Bold",
#         fontSize=11,
#         spaceBefore=8,
#         spaceAfter=2,
#         textColor=colors.black,
#     )

#     body_style = ParagraphStyle(
#         "ResumeBody",
#         parent=styles["Normal"],
#         fontName="Helvetica",
#         fontSize=10,
#         leading=14,
#         spaceAfter=4,
#     )

#     bullet_style = ParagraphStyle(
#         "ResumeBullet", parent=body_style, leftIndent=15, bulletIndent=5
#     )

#     story = []

#     # 1. Header Section (Name & Contact)
#     story.append(Paragraph(data.get("name", "Name Not Provided"), name_style))
#     contact_info = data.get("contact", "")
#     if isinstance(contact_info, list):
#         contact_info = " | ".join(contact_info)
#     story.append(Paragraph(contact_info, contact_style))
#     story.append(
#         HRFlowable(
#             width="100%", thickness=1, color=colors.HexColor("#BDC3C7"), spaceAfter=12
#         )
#     )

#     # 2. Professional Summary
#     if "summary" in data:
#         story.append(Paragraph("Professional Summary", section_header_style))
#         story.append(Paragraph(data["summary"], body_style))

#     # 3. Experience
#     if "experience" in data and isinstance(data["experience"], list):
#         story.append(Paragraph("Experience", section_header_style))
#         for job in data["experience"]:
#             # Format: Title - Company (Right aligned dates via tables or simple text)
#             title_text = f"<b>{job.get('title', '')}</b> | {job.get('company', '')} <font color='#7F8C8D'>({job.get('dates', '')})</font>"
#             story.append(Paragraph(title_text, job_title_style))

#             details = job.get("details", [])
#             if isinstance(details, str):
#                 details = [details]

#             for detail in details:
#                 story.append(Paragraph(f"• {detail}", bullet_style))

#     # 4. Education
#     if "education" in data and isinstance(data["education"], list):
#         story.append(Paragraph("Education", section_header_style))
#         for edu in data["education"]:
#             edu_text = f"<b>{edu.get('degree', '')}</b> — {edu.get('institution', '')} <font color='#7F8C8D'>({edu.get('dates', '')})</font>"
#             story.append(Paragraph(edu_text, job_title_style))
#             if "details" in edu:
#                 story.append(Paragraph(edu["details"], body_style))

#     # 5. Skills
#     if "skills" in data:
#         story.append(Paragraph("Skills & Expertise", section_header_style))
#         skills = data["skills"]
#         if isinstance(skills, list):
#             skills = ", ".join(skills)
#         story.append(Paragraph(skills, body_style))

#     # Build PDF
#     doc.build(story)

#     # Upload and return Markdown link
#     url = upload_and_link(temp_path, filename)
#     return f"CV Asset generated successfully: [Download {filename}]({url})"
