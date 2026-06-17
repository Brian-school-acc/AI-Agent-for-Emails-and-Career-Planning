"""Custom tools for the agents. Each function is decorated with @tool
so the framework exposes it. Import these into server.py and attach via tools=[...]."""

import os
import glob

from dotenv import load_dotenv
from typing import Annotated
from pydantic import Field
from random import randint
from datetime import datetime
from zoneinfo import ZoneInfo

import azure.cognitiveservices.speech as speechsdk
from agent_framework import tool

from constants import COMMON_ABBR, CUHK_ABBR


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
    name="inquire_abbrieviations",
    description="Call this function whenever there is an abbrieviation for clearer context",
    approval_mode="never_require"
)
def inquire_abbrieviations(abbreviation: str) -> str:
    """
    Retrieve a dictionary of common abbreviations and
    a dictionary of CUHK-specific abbreviations

    Args:
        abbrieviation: a case-insensitive abbreviation to inquire
    """

    dictionary: dict = COMMON_ABBR.fromkeys(CUHK_ABBR)
    result = dictionary.get(abbreviation, "")

    # Clean return format
    if result:
        return f"{abbreviation} means {result}"
    else:
        return ""


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

    # Define output audio file path (can be routed to a local cache or blob storage)
    output_filename = f"output_speech_{hash(text)}.wav"
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filename)

    # Synthesize the speech
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )
    result = synthesizer.speak_text_async(text).get()

    if result is None:
        return "Speech Recognition Failed."

    else:
        # Checks result.
        try:
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return f"Recognized: {result.text}"
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return f"No speech could be recognized: {result.no_match_details}"
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                return f"Speech Recognition canceled: {cancellation_details.reason}"
            else:
                return f"Speech Recognition Fallback: none of the above reasons"
        
        except Exception as e:
            return f"Error details: {e}"
