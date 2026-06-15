import os
import json
import docx
from pptx import Presentation


# --- 📝 DOCUMENT GENERATION: MICROSOFT WORD ---
#  AFTER (Safe for strict OSS gateways)
# def generate_word_document() -> str:
#     """
#     Compiles structured text into a professional Microsoft Word (.docx) file.

#     Args:
#         document_title: The title text printed at the top of the document.
#         sections_json: A JSON string dictionary of your headers and paragraphs.
#         filename: The exact file output string ending in .docx (e.g., 'Report.docx').
#     """
#     doc = docx.Document()
#     doc.add_heading("A Level 0 Heading", level=0)
#     absolute_output_path = r"C:\CUHK\ECA\MSHK AI Agent Lab (Hackathon)\agent-cuhk\generated_document.docx"
#     try:
#         doc.save(absolute_output_path)
#         return f"Successfully compiled Word document at: {absolute_output_path}"
#     except Exception as e:
#         return f"Failed to generate Word document: {str(e)}"

# def generate_powerpoint_presentation() -> str:
#     """
#     Generates structured presentations into a Microsoft PowerPoint (.pptx) deck.

#     Args:
#         presentation_title:  The title text of the first slide.
#         slides_json: A JSON string dictionary of your headers and paragraphs.
#         filename: The exact file output string ending in .pptx (e.g., 'Presentation_Deck.pptx').
#     """

#     prs = Presentation()
#     title_layout = prs.slide_layouts[0]
#     cover_slide = prs.slides.add_slide(title_layout)

#     try:
#         cover_slide.shapes.title.text = "presentation_title"
#         absolute_output_path = r"C:\CUHK\ECA\MSHK AI Agent Lab (Hackathon)\agent-cuhk\generated_document.pptx"
#         prs.save(absolute_output_path)
#         return f"Successfully compiled PowerPoint slides at: {absolute_output_path}"
#     except Exception as e:
#         return f"Failed to generate Word document: {str(e)}"


def generate_word_document(
    document_title: str, sections_json: str, filename: str
) -> str:
    """
    Compiles structured text into a professional Microsoft Word (.docx) file.

    Args:
        document_title: The title text printed at the top of the document.
        sections_json: A JSON string dictionary of your headers and paragraphs.
        filename: The exact file output string ending in .docx (e.g., 'Report.docx').
    """
    doc = docx.Document()
    doc.add_heading(document_title, level=0)

    try:
        sections_dict = json.loads(sections_json)
        for heading, paragraph_text in sections_dict.items():
            doc.add_heading(heading, level=1)
            doc.add_paragraph(paragraph_text)

        absolute_output_path = os.path.abspath(filename)
        doc.save(absolute_output_path)
        return f"Successfully compiled Word document at: {absolute_output_path}"
    except Exception as e:
        return f"Failed to generate Word document: {str(e)}"


# --- 📊 DOCUMENT GENERATION: MICROSOFT POWERPOINT ---
def generate_powerpoint_presentation(
    presentation_title: str, slides_json: str, filename: str
) -> str:
    """
    Generates structured presentations into a Microsoft PowerPoint (.pptx) deck.

    Args:
        presentation_title:  The title text of the first slide.
        slides_json: A JSON string dictionary of your headers and paragraphs.
        filename: The exact file output string ending in .pptx (e.g., 'Presentation_Deck.pptx').
    """

    prs = Presentation()
    title_layout = prs.slide_layouts[0]
    cover_slide = prs.slides.add_slide(title_layout)
    cover_slide.shapes.title.text = presentation_title

    try:
        slides_data = json.loads(slides_json)
        bullet_content_layout = prs.slide_layouts[1]

        for slide_item in slides_data:
            new_slide = prs.slides.add_slide(bullet_content_layout)
            new_slide.shapes.title.text = slide_item.get("title", "Topic Overview")
            text_frame = new_slide.placeholders[1].text_frame
            text_frame.text = ""

            for bullet_point in slide_item.get("bullets", []):
                paragraph = text_frame.add_paragraph()
                paragraph.text = bullet_point
                paragraph.level = 0

        absolute_output_path = os.path.abspath(filename)
        prs.save(absolute_output_path)
        return f"Successfully compiled PowerPoint deck at: {absolute_output_path}"
    except Exception as e:
        return f"Failed to generate PowerPoint: {str(e)}"
