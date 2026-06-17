from agent_framework import tool
from pydantic import Field

import datetime
import httpx

from typing import Annotated, List, Dict, Optional
from random import randint
import os
from dotenv import load_dotenv
from typing import Any, Literal
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

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

# Helper function
# def upload_to_foundry_agents(file_bytes: bytes, filename: str, client) -> str:
    
#     load_dotenv()

#     PROJECT_ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
#     MODEL_NAME = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "")

#     if not PROJECT_ENDPOINT:
#         raise ValueError("Missing environment variable: FOUNDRY_PROJECT_ENDPOINT")

#     client = FoundryChatClient(
#         project_endpoint=PROJECT_ENDPOINT,
#         model=MODEL_NAME,
#         credential=DefaultAzureCredential()
#     )

#     """
#     Uploads a file to the Azure AI Foundry / OpenAI file storage specifically for Agents/Assistants.
#     """
#     # The SDK expects a tuple of (filename, file_bytes)
#     uploaded_file = client.client.files.create(file=(filename, file_bytes), purpose="assistants")

#     # Returns the Azure AI File ID (e.g., file-xxxxxxx)
#     return uploaded_file.


# # ==========================================
# # TOOL 4: GENERATE WORD DOCUMENTS
# # ==========================================

# import os
# from typing import Annotated, List, Dict, Optional
# from pydantic import Field
# from agent_framework import tool

# # Fallback imports for document generation (requires python-docx and python-pptx)
# try:
#     from docx import Document
#     from docx.shared import Pt, Inches
#     from docx.enum.text import WD_ALIGN_PARAGRAPH
# except ImportError:
#     Document = None

# try:
#     from pptx import Presentation
#     from pptx.util import Inches as PptxInches, Pt as PptxPt
# except ImportError:
#     Presentation = None


# import os
# import io
# from typing import Annotated, List, Dict, Optional
# from pydantic import Field
# from agent_framework import tool

# # Fallback imports for document generation (requires python-docx)
# try:
#     from docx import Document
#     from docx.shared import Pt, Inches
#     from docx.enum.text import WD_ALIGN_PARAGRAPH
# except ImportError:
#     Document = None


# @tool(approval_mode="never_require")
# def generate_word_document(
#     title: Annotated[
#         str, Field(description="The primary title of the academic document.")
#     ],
#     author_details: Annotated[
#         str,
#         Field(
#             description="Student name, ID, Course code, and Date (e.g., 'Jane Doe | CS101 | Fall 2026')."
#         ),
#     ],
#     sections: Annotated[
#         List[Dict[str, str]],
#         Field(
#             description="A list of dictionaries representing the document structure. Each dictionary must have 'heading' (str) and 'content' (str) keys. Example: [{'heading': 'Abstract', 'content': '...'}]"
#         ),
#     ],
#     academic_style: Annotated[
#         str,
#         Field(
#             description="The formatting style required: 'APA', 'MLA', or 'Standard'. Dictates font, spacing, and title page logic."
#         ),
#     ] = "APA",
#     references: Annotated[
#         Optional[List[str]],
#         Field(
#             description="A list of formatted citation strings to be appended to the end of the document."
#         ),
#     ] = None,
# ) -> str:
#     """
#     Generates a highly structured, academically formatted Microsoft Word (.docx) file.

#     The Executive Agent should use this tool when a student needs to compile research, essays,
#     or reports into a final, submission-ready format. It strictly enforces academic typography
#     and structural hierarchy.

#     Few-Shot Template for 'sections' payload:
#     [
#         {"heading": "Introduction", "content": "The advent of multi-agent systems..."},
#         {"heading": "Methodology", "content": "We deployed an architecture based on..."}
#     ]
#     """
#     if Document is None:
#         return "Error: 'python-docx' library is not installed. Please install it to generate Word documents."

#     doc = Document()

#     # 1. Apply Academic Styling Preferences
#     style = doc.styles["Normal"]
#     font = style.font
#     if academic_style.upper() in ["APA", "MLA"]:
#         font.name = "Times New Roman"
#         font.size = Pt(12)
#     else:
#         font.name = "Calibri"
#         font.size = Pt(11)

#     # 2. Title Page / Header Injection
#     if academic_style.upper() == "APA":
#         doc.add_paragraph()  # Spacing
#         doc.add_paragraph()
#         title_para = doc.add_paragraph(title)
#         title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
#         title_para.runs[0].bold = True

#         author_para = doc.add_paragraph(author_details.replace(" | ", "\n"))
#         author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
#         doc.add_page_break()
#     else:
#         doc.add_paragraph(author_details)
#         doc.add_heading(title, 0)

#     # 3. Content Iteration
#     for section in sections:
#         heading_text = section.get("heading", "")
#         content_text = section.get("content", "")

#         if heading_text:
#             doc.add_heading(heading_text, level=1)

#         if content_text:
#             doc.add_paragraph(content_text)

#     # 4. References Section
#     if references:
#         doc.add_page_break()
#         doc.add_heading(
#             "References" if academic_style.upper() == "APA" else "Works Cited", level=1
#         )
#         for ref in references:
#             ref_para = doc.add_paragraph(ref)
#             ref_para.paragraph_format.left_indent = Inches(0.5)
#             ref_para.paragraph_format.first_line_indent = Inches(-0.5)

#     # ==========================================
#     # 5. CLOUD SERIALIZATION & UPLOAD
#     # ==========================================
#     # Fix 1: Properly define the file name string
#     filename = f"{title.replace(' ', '_').lower()}_final.docx"

#     # Fix 2: Instantiate memory buffer and save doc bytes into it
#     file_stream = io.BytesIO()
#     doc.save(file_stream)

#     # Rewind stream pointer before reading bytes out
#     file_stream.seek(0)
#     file_bytes = file_stream.read()

#     # Fix 3: Handle the Client setup internally for framework isolation
#     from azure.identity import DefaultAzureCredential
#     from azure.ai.projects import AIProjectClient

#     # Target connection string injected automatically by the platform environment
#     PROJECT_ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")

#     if not PROJECT_ENDPOINT:
#         return f"Error: Document successfully compiled in memory ({len(file_bytes)} bytes) but PROJECT_CONNECTION_STRING environment variable is missing."

#     try:
#         # Context-managed client ensures connection pool is safely dismantled after use
#         with AIProjectClient(
#             endpoint=PROJECT_ENDPOINT,
#             credential=DefaultAzureCredential(),
#         ) as client:

#             # File parameters map to a tuple containing metadata and raw bytes
#             uploaded_file = client.agents.create_file(
#                 file=(filename, file_bytes), purpose="agents"
#             )
#             file_id = uploaded_file.id

#         return f"Word document '{title}' successfully generated and uploaded. File ID: {file_id}"

#     except Exception as e:
#         return f"Word document generated successfully in memory, but cloud deployment failed: {str(e)}"


# # ==========================================
# # TOOL 5: GENERATE POEWRPOINT SLIDES
# # ==========================================

# import os
# from typing import Annotated, List, Dict, Any, Optional
# from pydantic import Field
# from agent_framework import tool

# # Fallback imports for document generation (requires python-pptx)
# try:
#     from pptx import Presentation
#     from pptx.util import Inches, Pt
#     from pptx.dml.color import RGBColor
# except ImportError:
#     Presentation = None
#     Inches = None
#     Pt = None
#     RGBColor = None


# @tool(approval_mode="never_require")
# def generate_presentation_slides(
#     presentation_title: Annotated[
#         str,
#         Field(
#             description="The primary headline or topic for the presentation title slide."
#         ),
#     ],
#     slides: Annotated[
#         List[Dict[str, Any]],
#         Field(
#             description="A list of dictionaries defining each slide. Each dictionary must contain 'title' (str) and 'body' (str or List[str]). Optional keys include 'layout' ('content' or 'two_column') and 'speaker_notes' (str)."
#         ),
#     ],
#     subtitle: Annotated[
#         Optional[str],
#         Field(
#             description="The secondary subtitle or corporate/academic presentation credit."
#         ),
#     ] = None,
#     color_theme: Annotated[
#         str,
#         Field(
#             description="The visual theme for slide headers: 'Corporate Blue', 'Academic Charcoal', or 'Crimson Accent'."
#         ),
#     ] = "Corporate Blue",
# ) -> str:
#     """
#     Generates a highly customized PowerPoint presentation (.pptx) slide deck with explicit layout control.

#     The Executive Agent should use this tool when compiling complex educational modules, project proposals,
#     or defense decks that require structural flexibility (e.g., shifting between standard lists and
#     side-by-side visual comparisons) while enforcing a uniform structural schema.

#     Few-Shot Template for 'slides' payload:
#     [
#         {
#             "title": "Core Architecture",
#             "body": "• Decentralized orchestrator execution\n• Dynamic tool-binding runtime\n• Stateful conversation history memory",
#             "layout": "content",
#             "speaker_notes": "Emphasize to the review board that the runtime handles state binding dynamically."
#         },
#         {
#             "title": "Monolithic vs. Multi-Agent Systems",
#             "body": ["Monolithic Architecture:\\n• Single point of failure\\n• High regression risk", "Multi-Agent System:\\n• Isolate operational scopes\\n• Fault-tolerant fallbacks"],
#             "layout": "two_column",
#             "speaker_notes": "This side-by-side comparison directly addresses the scalability constraints noted in our abstract."
#         }
#     ]
#     """
#     if Presentation is None:
#         return "Error: 'python-pptx' library is not installed. Please install it to generate presentation slides."

#     prs = Presentation()

#     # 1. Map Hex/RGB Visual Themes
#     themes = {
#         "Corporate Blue": RGBColor(10, 34, 64),
#         "Academic Charcoal": RGBColor(45, 45, 45),
#         "Crimson Accent": RGBColor(140, 15, 15),
#     }
#     primary_color = themes.get(color_theme, RGBColor(0, 0, 0))

#     # 2. Generate Title Slide (Layout Index 0)
#     title_layout = prs.slide_layouts[0]
#     title_slide = prs.slides.add_slide(title_layout)
#     title_slide.shapes.title.text = presentation_title

#     if subtitle and len(title_slide.placeholders) > 1:
#         title_slide.placeholders[1].text = subtitle

#     # Paint title with theme color
#     if title_slide.shapes.title.text_frame:
#         for paragraph in title_slide.shapes.title.text_frame.paragraphs:
#             for run in paragraph.runs:
#                 run.font.color.rgb = primary_color

#     # Standard python-pptx presentation template layouts
#     LAYOUT_CONTENT = prs.slide_layouts[1]  # Title and Content
#     LAYOUT_TWO_COLUMN = prs.slide_layouts[4]  # Two Content (Side-by-side)

#     # 3. Content Iteration & Layout Logic
#     for slide_idx, slide_data in enumerate(slides):
#         layout_type = str(slide_data.get("layout", "content")).lower()

#         # Select appropriate layout variant
#         if layout_type == "two_column":
#             slide = prs.slides.add_slide(LAYOUT_TWO_COLUMN)
#         else:
#             slide = prs.slides.add_slide(LAYOUT_CONTENT)

#         # Enforce header text formatting and color theme
#         slide.shapes.title.text = slide_data.get("title", f"Slide {slide_idx + 1}")
#         for paragraph in slide.shapes.title.text_frame.paragraphs:
#             for run in paragraph.runs:
#                 run.font.color.rgb = primary_color

#         # Parse content body text
#         body_data = slide_data.get("body", "")

#         if layout_type == "two_column":
#             # Safe unpacking of array content or single string split for side-by-side columns
#             column_contents = (
#                 body_data if isinstance(body_data, list) else [body_data, ""]
#             )

#             if len(slide.placeholders) > 1:
#                 slide.placeholders[1].text_frame.text = (
#                     str(column_contents[0]) if len(column_contents) > 0 else ""
#                 )
#             if len(slide.placeholders) > 2:
#                 slide.placeholders[2].text_frame.text = (
#                     str(column_contents[1]) if len(column_contents) > 1 else ""
#                 )
#         else:
#             # Handle standard single column list layout
#             if len(slide.placeholders) > 1:
#                 text_payload = (
#                     "\n".join(body_data)
#                     if isinstance(body_data, list)
#                     else str(body_data)
#                 )
#                 slide.placeholders[1].text_frame.text = text_payload

#         # 4. Inject Speaker Notes for Oral Defense Prep
#         speaker_notes = slide_data.get("speaker_notes", "")
#         if speaker_notes:
#             notes_slide = slide.notes_slide
#             notes_slide.notes_text_frame.text = str(speaker_notes)

#     # 5. Serialization and File Generation
#     filename = f"{presentation_title.replace(' ', '_').lower()}_slides.pptx"
#     safe_path = os.path.join(os.getcwd(), filename)
#     prs.save(safe_path)

#     return f"Presentation slides '{presentation_title}' successfully generated with {len(slides)} slides. Safe file path: {safe_path}. Design configuration theme: {color_theme}."
