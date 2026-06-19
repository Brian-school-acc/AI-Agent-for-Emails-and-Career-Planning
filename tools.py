"""Custom tools for the agents. Each function is decorated with @tool
so the framework exposes it. Import these into server.py and attach via tools=[...]."""

import asyncio
import glob
import os
import tempfile

from datetime import datetime
from dotenv import load_dotenv
from typing import Annotated
from pydantic import Field
from zoneinfo import ZoneInfo

from agent_framework.foundry import FoundryChatClient
import azure.cognitiveservices.speech as speechsdk
from agent_framework import tool
from azure.ai.projects.models import MemorySearchPreviewTool

from constants import CUHK_ABBR


load_dotenv()

@tool(approval_mode="never_require")
def summarize_document(document_id: str) -> str:
    """
    Retrieve a brief summary of a specific document by its ID or title.

    Args:
        document_id: The exact title or ID of the document to summarize.
    """
    return f"Summary of {document_id}: This document outlines the standard operating procedures and academic requirements for the current semester. It includes important dates, grading rubrics, and contact protocols."


@tool(
    name="file_search",
    description=(
        "Search local documents/notes for a keyword or phrase. Use when the user "
        "asks about content that may live in saved files or exports. Returns "
        "matching snippets with their file names."
    ),
)
def file_search(
    query: Annotated[str, Field(description="Keyword or phrase to search for.")],
    folder: Annotated[str, Field(description="Folder to search in.")] = "./docs",
) -> str:
    """Naive local full-text search over .txt/.md files."""
    print(f"🔧 file_search called: {query!r}")   # remove once confirmed working

    hits = []
    for path in glob.glob(os.path.join(folder, "**", "*"), recursive=True):
        if not path.lower().endswith((".txt", ".md")):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        if query.lower() in text.lower():
            idx = text.lower().find(query.lower())
            start, end = max(0, idx - 80), idx + 120
            snippet = text[start:end].replace("\n", " ").strip()
            hits.append(f"[{os.path.basename(path)}] …{snippet}…")
        if len(hits) >= 5:
            break

    if not hits:
        return f'No local files matched "{query}". State "Data insufficient" to the user.'
    return "Found these matches:\n" + "\n".join(hits)


@tool(
    name="inquire_abbreviations",
    description="Call this function whenever there is an abbrieviation for clearer context",
    approval_mode="never_require",
)
def inquire_abbreviations(abbreviation: str) -> str:
    """
    Retrieve the full form of a common or CUHK-specific abbreviation.

    **Usage guidelines for the LLM (conservative approach):**
    1. **ALWAYS call this function** when the token is:
       - a recognised short form in the context (e.g., "sem", "reg"),
       - and clearly used as an abbreviation, not as a regular word.
       - clearly in uppercase (e.g. ART)
       - when you suspect that a word could be an abbreviation

    2. **Do not expand** if:
       - the token is a common English word (e.g., "art" → treat as "art", not "Faculty of Arts"),
       - the token is ambiguous without further context,
       - the token appears in a proper name or quoted text,
       - the user's intent is unclear (e.g., they may have typed a typo).

    3. **When the dictionary returns an empty result**:
       - Do **not** invent an expansion.
       - Return an empty string and treat the token as‑is.

    4. **When the dictionary returns a match but the context suggests otherwise**:
       - Prefer the literal token over the expansion.
       - For example, if the user says "I study art", do not replace "art" with "Faculty of Arts".

    5. **If multiple expansions exist** (e.g., "CSC" could be Career Services or Campus Services),
       - avoid returning a single one; either ask the user for clarification or keep the abbreviation unchanged.

    6. **Fallback**:
       - If you are not certain that the token is an abbreviation intended to be expanded,
         do not use this function. Let the user's original text stand.

    Args:
        abbreviation: a case‑insensitive abbreviation to inquire.
    Returns:
        The full expansion if the abbreviation is found and confidently applicable,
        otherwise an empty string.
    """

    dictionary: dict = CUHK_ABBR
    result = dictionary.get(abbreviation, "")

    # Clean return format
    if result:
        return f"{abbreviation}: {result}"
    else:
        return f"There is probably no cuhk-specific meaning for the word f{abbreviation}"


@tool(approval_mode="never_require")
async def convert_text_to_speech(
    text: Annotated[
        str,
        Field(description="The formal text or response to convert into spoken audio."),
    ],
    voice_name: Annotated[
        str,
        Field(
            description="The neural voice to use, e.g., 'en-US-AvaNeural' or 'en-US-AndrewNeural'."
        ),
    ] = "en-US-AvaNeural",
) -> str:
    """
    Converts a given text block into synthesized speech and saves it as an audio file.
    Use this when the user requests an audio read-out or spoken delivery of a student milestone.
    """
    # Grab configuration from your Foundry environment variables
    speech_key = os.environ.get("AZURE_SPEECH_KEY")
    speech_region = os.environ.get("AZURE_SPEECH_REGION")

    if not speech_key or not speech_region:
        return "Error: Speech credentials are not configured in the environment."

    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=speech_region
    )
    speech_config.speech_synthesis_voice_name = voice_name

    # Explicitly set the output to MP3 for better web playback compatibility
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    )

    # Use tempfile to securely create a local file path that we will pass to the helper
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        temp_filename = temp_audio_file.name

    audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_filename)

    # Synthesize the speech
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )
    result = synthesizer.speak_text_async(text).get()

    if result is None:
        return "Speech Synthesis Failed."

    # Handle the result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        try:
            # Generate a unique blob name
            blob_name = (
                f"speech_{hash(text)}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
            )

            # Delegate upload, SAS generation, and cleanup to your helper
            audio_url = upload_and_link(temp_filename, blob_name)

            # Return the Markdown link for Copilot
            return f"Audio generated successfully. [Click here to listen or download the audio]({audio_url})"

        except Exception as e:
            return f"Audio was synthesized, but processing/uploading failed. Error: {str(e)}"

    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        return f"Speech synthesis canceled: {cancellation_details.reason}"

    else:
        return "Speech synthesis fallback: unknown error occurred."


def get_memory_search_preview_tool() -> MemorySearchPreviewTool:
    # Set scope to associate the memories with
    scope = "{{$userId}}"

    # Create memory search tool
    memory_search_preview_tool = MemorySearchPreviewTool(
        memory_store_name=os.environ.get("MEMORY_STORE_NAME", "default_memory_store"),
        scope=scope,
        update_delay=2,  # Wait 5 seconds of inactivity before updating memories
        # In a real application, set this to a higher value like 300 (5 minutes, default)
    )

    return memory_search_preview_tool


async def get_file_search_tool(client: FoundryChatClient):
    # 1. Define the target
    user_id = "{{$userId}}"  # Assuming this is injected by your framework later
    vector_store_name = f"Student Success Knowledge Base - {user_id}"

    # 2. Fetch existing vector stores to check for a match
    vector_stores = await client.client.vector_stores.list()
    vector_store_candidates = [
        vs for vs in vector_stores.data if vs.name == vector_store_name
    ]

    # 3. Handle creation vs. retrieval cleanly
    if vector_store_candidates:
        # It exists! Grab the first match.
        vector_store = vector_store_candidates[0]
        print(
            f"✅ Found existing Vector Store: {vector_store.id} (Status: {vector_store.status})"
        )

        # We assume the file was already uploaded and indexed during creation.
        # Skipping the upload and polling process to save time and API calls.
    else:
        # It doesn't exist. Create it, upload the file, and index it.
        print(f"⚙️ Creating new Vector Store: {vector_store_name}")
        vector_store = await client.client.vector_stores.create(name=vector_store_name)

        # Read the raw file ONLY if we are creating a new store
        file_path = "OUTLINE.md"
        with open(file_path, "rb") as f:
            file_content = f.read()

        # Upload the file to Foundry
        uploaded_file = await client.client.files.create(
            file=("OUTLINE.md", file_content), purpose="assistants"
        )

        # Add to Vector Store and poll until indexing is complete
        print("⏳ Indexing file into Vector Store... (This may take a moment)")
        processing_result = await client.client.vector_stores.files.create_and_poll(
            vector_store_id=vector_store.id, file_id=uploaded_file.id
        )

        if processing_result.last_error is not None:
            raise Exception(
                f"File indexing failed: {processing_result.last_error.message}"
            )

        print("✅ Indexing complete!")

    # 4. Retrieve the Hosted File Search Tool bound to the ready Vector Store
    file_search_tool = client.get_file_search_tool(vector_store_ids=[vector_store.id])

    return file_search_tool
