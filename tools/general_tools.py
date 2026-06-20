"""Custom tools for the agents. Each function is decorated with @tool
so the framework exposes it. Import these into server.py and attach via tools=[...]."""

import asyncio
import base64
import os
import requests
import tempfile
import uuid

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from typing import Annotated
from pydantic import Field
from zoneinfo import ZoneInfo

import azure.cognitiveservices.speech as speechsdk
from openai import OpenAI
from agent_framework.foundry import FoundryChatClient
from agent_framework import tool
from azure.ai.projects.models import MemorySearchPreviewTool

from tools.constants import CUHK_ABBR

from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas


load_dotenv()

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
    ALWAYS use this when a real-life scenario is related, e.g. workplace simulation, interview, etc.
    Also, ALWAYS use this when the user requests an audio read-out or spoken delivery of a student milestone.
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

            # === CRITICAL WINDOWS FIX ===
            # Explicitly delete the SDK objects to flush and release the file handle lock
            del synthesizer
            del audio_config
            # ============================

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

# ======================================================================================================
# TOOL 5: Generate Documents of Different File Types - code_interpreter + sandbox_2_azure() helper
# ======================================================================================================


@tool(
    name="upload_sandbox_file_to_azure",
    description=(
        "MANDATORY POST-EXECUTION HOOK FOR code_interpreter_tool: You must call this tool immediately after"
        "saving ANY file to '/mnt/data/' using the code_interpreter. Do not reply to the user until you have"
        "passed the local filepath to this tool and received the secure Azure URL in return."
        "If retrying code_interpreter fails, switch to other lightweight tools OR return a failure message"
    ),
)
def upload_sandbox_file_to_azure(
    sandbox_file_path: str, destination_filename: str
) -> str:
    if not os.path.exists(sandbox_file_path):
        return f"Error: Cannot find file at {sandbox_file_path}. Are you sure the code_interpreter saved it there?"

    ACCOUNT_NAME = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    ACCOUNT_KEY = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
    CONTAINER_NAME = os.environ.get("AZURE_BLOB_CONTAINER_NAME")

    # 0. Check all three credentials
    err_msg: list[str] = []
    if ACCOUNT_NAME is None:
        err_msg.append("ACCOUNT_NAME")
    if ACCOUNT_KEY is None:
        err_msg.append("ACCOUNT_KEY")
    if CONTAINER_NAME is None:
        err_msg.append("CONTAINER_NAME")

    if err_msg:
        raise EnvironmentError(f"Missing Credentials: {', '.join(err_msg)}")

    blob_service_client = BlobServiceClient(
        account_url=f"https://{ACCOUNT_NAME}.blob.core.windows.net",
        credential=ACCOUNT_KEY,
    )
    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME, blob=destination_filename  # type: ignore
    )

    with open(sandbox_file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    expiry_time = datetime.now(timezone.utc) + timedelta(hours=1)
    sas_token = generate_blob_sas(
        account_name=ACCOUNT_NAME,  # type: ignore
        container_name=CONTAINER_NAME,  # type: ignore
        blob_name=destination_filename,
        account_key=ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=expiry_time,
    )

    os.remove(destination_filename)  # Clean up
    download_url = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{destination_filename}?{sas_token}"
    return f"Success! [Download {sandbox_file_path}]({download_url})"


@tool(
    name="generate_image",
    description=(
        "Generates a high-quality image from a text prompt using FLUX.2-pro. "
        "Use this tool whenever a student requests a visual model, roadmap diagram, or illustration."
    ),
)
def generate_image(
    prompt: Annotated[
        str,
        Field(description="A highly detailed description of the image to generate."),
    ],
    filename: Annotated[
        str,
        Field(
            description="A short, relevant filename for the output image ending in .png."
        ),
    ],
) -> str:
    """
    Invokes the FLUX.2-pro provider API directly via HTTP, processes the byte stream,
    and returns a Copilot-compliant markdown image link.
    """
    # 1. Retrieve environment configurations
    # Note: For FLUX.2-pro, the endpoint should be the base URL up to '.azure.com'
    base_endpoint = os.environ.get("IMAGE_GEN_URL")
    deployment_name = os.environ.get("IMAGE_GEN_MODEL")
    api_key = os.environ.get("IMAGE_GEN_API_KEY")

    if not base_endpoint or not api_key:
        return "Error: Missing Azure AI Foundry credentials."

    # Ensure correct file extension
    if not filename.lower().endswith(".png"):
        filename += ".png"

    # Prevent filename collisions in your Azure Blob storage
    unique_filename = f"{filename.split('.png')[0]}_{uuid.uuid4().hex[:8]}.png"

    # 2. Build Payload matching the Black Forest Labs specifications
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    payload = {
        "prompt": prompt,
        "model": deployment_name,
        "width": 1024,
        "height": 1024,
        "n": 1,
        "output_format": "png",
    }

    try:
        # 3. Execute HTTP Post
        response = requests.post(base_endpoint, json=payload, headers=headers)
        response.raise_for_status()  # Catch HTTP codes like 400, 401, 500

        response_data = response.json()

        # 4. Extract and decode the base64 payload
        b64_json = response_data["data"][0]["b64_json"]
        image_bytes = base64.b64decode(b64_json)

        # 5. Drop bytes into local temp directory for the Azure Blob helper to grab
        temp_path = os.path.join(tempfile.gettempdir(), unique_filename)
        with open(temp_path, "wb") as f:
            f.write(image_bytes)

        # 6. Hand off to your existing helper to push to Azure Storage and generate a SAS link
        sas_url = upload_and_link(temp_path, unique_filename)

        # 7. Deliver directly as markdown for M365 Copilot rendering
        return f"![{prompt}]({sas_url})"

    except requests.exceptions.RequestException as http_err:
        return f"Network error calling {deployment_name} API: {http_err}"
    except Exception as e:
        return f"Error processing generated image: {str(e)}"
