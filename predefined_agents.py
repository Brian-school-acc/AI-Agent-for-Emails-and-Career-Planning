import asyncio
import os
import json
from dotenv import load_dotenv
from typing import Any, Literal

from agent_framework import (
    Agent,
    AgentExecutorRequest,
    Message,
    WorkflowContext,
    executor,
)
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

from pydantic import BaseModel, Field  # Structured outputs for safer parsing
from prompts import (
    TRIAGE_PROMPT,
    ARCHIVIST_PROMPT,
    SECRETARY_PROMPT,
    CAREER_COACH_PROMPT,
    FRONTDESK_PROMPT,
)
from tools.general_tools import (
    inquire_abbreviations,
    convert_text_to_speech,
    get_memory_search_preview_tool,
    get_file_search_tool,
    upload_sandbox_file_to_azure,
    generate_image,
)
from tools.front_desk_tools import (
    get_weather,
    get_current_time,
    get_general_faq,
)

from tools.archivist_tools import (
    retrieve_student_emails,
    extract_deadlines,
)
from tools.secretary_tools import (
    draft_lecturer_email,
    create_planner_task,
    schedule_calendar_event,
    generate_docx,
    generate_xlsx,
    generate_pptx,
    generate_pdf,
)
from tools.career_coach_tools import (
    analyze_resume_skill_gaps,
    generate_mock_interview_scenario,
    simulate_workplace,
)

load_dotenv()

PROJECT_ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL_NAME = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "")
SCOPE = "user_demo"

# --- 1. DATA MODELS ---


class TriageResult(BaseModel):
    """Structured routing schema for incoming documents."""

    reason: str = Field(description="Analyze the user request step-by-step.")
    route: Literal["read", "secretary", "career", "fallback"] = Field(
        description="Select 'read' for analysis/lookup, 'secretary' for timelines/deadlines/tasks, 'career' for resumes, or 'fallback' if general/unclear."
    )

    doc_content: str = Field(
        default="", description="The exact unaltered original document text."
    )


# --- 2. Helper Function: CLIENT & TOOL FACTORY ---
_client: FoundryChatClient | None = None
_file_search_tool: Any | None = None
_memory_search_preview_tool: Any | None = None

def _get_foundry_client(credential: DefaultAzureCredential, model_choice: str) -> FoundryChatClient:
    """Helper method to construct the centralized inference provider client."""
    # 0. Check and Ensure there is one instance of client
    global _client
    model_choice = os.environ[model_choice]

    # 1. Return the cached client if it already exists
    if _client is not None:
        return _client

    else:
        if not PROJECT_ENDPOINT:
            raise ValueError("Missing environment variable: FOUNDRY_PROJECT_ENDPOINT")

        _client = FoundryChatClient(
            project_endpoint=PROJECT_ENDPOINT,
            model=model_choice,
            credential=credential,
        )
        return _client


async def _get_cached_file_search_tool(client: FoundryChatClient) -> Any:
    """Helper method to construct and cache the file search tool globally."""
    global _file_search_tool

    # 1. Return the cached tool if it already exists
    if _file_search_tool is not None:
        return _file_search_tool

    # 2. Otherwise, await the creation and cache it
    _file_search_tool = await get_file_search_tool(client)
    return _file_search_tool


def _get_cached_memory_search_preview_tool() -> Any:
    """Helper method to construct and cache the memory search tool globally."""
    global _memory_search_preview_tool

    # 1. Return the cached tool if it already exists
    if _memory_search_preview_tool is not None:
        return _memory_search_preview_tool

    # 2. Otherwise, create and cache it (assuming synchronous based on original usage)
    _memory_search_preview_tool = get_memory_search_preview_tool()
    return _memory_search_preview_tool


# --- CENTRALIZED DISPATCHER ROUTER ---


@executor(id="triage_and_route")
async def triage_and_route(
    messages: list[Message], ctx: WorkflowContext[list[Message]]
) -> None:
    if not messages:
        print("❌ No input messages received at entrypoint.")
        return

    # Extract the text string from the last conversation turn safely
    last_message = messages[-1]
    if hasattr(last_message, "contents") and last_message.contents:
        original_prompt = str(last_message.contents[0])
    elif hasattr(last_message, "content"):
        original_prompt = str(last_message.content)  # type: ignore
    else:
        original_prompt = str(last_message)

    # Initialize target_route for the routes
    target_route = None

    # Build the triage agent locally to run SILENTLY (Isolated from the stream)
    credential = DefaultAzureCredential()
    model_choice = "FAST_MINI_MODEL"
    triage_agent = Agent(
        client=_get_foundry_client(credential, model_choice),
        instructions=TRIAGE_PROMPT,
        name="triage_agent",
        default_options={"store": False, "reasoning": None, "allow_multiple_tool_calls": True},  # type: ignore
        require_per_service_call_history_persistence=True,
    )

    print("🔍 Executing silent triage classification...")
    triage_response = await triage_agent.run(original_prompt)
    raw_text = triage_response.text.strip()

    # Clean up markdown code blocks if the model wrapped them
    if raw_text.startswith("```json"):
        raw_text = raw_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text.split("```", 1)[1].rsplit("```", 1)[0].strip()

    try:
        detection = TriageResult.model_validate_json(raw_text)
        target_route = detection.route
    except Exception as e:
        print(f"❌ Dispatcher validation failed: {e}. Defaulting to fallback route.")
        target_route = "fallback"
        detection = TriageResult(
            reason="Fail-safe routing", route="fallback", doc_content=raw_text
        )

    # 3. Package the request bundle for your specialist agents
    user_msg = Message("user", contents=[str(original_prompt)])
    specialist_request = AgentExecutorRequest(messages=[user_msg], should_respond=True)

    # 4. Route directly to the targeted specialist executor matching the IDs in main()
    if target_route == "read":
        print("➡️ Dispatcher: Routing to Archivist Agent.")
        await ctx.send_message(specialist_request, "archivist_exec")  # type: ignore
    elif target_route == "secretary":
        print("➡️ Dispatcher: Routing to Secretary Agent.")
        await ctx.send_message(specialist_request, "secretary_exec")  # type: ignore
    elif target_route == "career":
        print("➡️ Dispatcher: Routing to Career Coach Agent.")
        await ctx.send_message(specialist_request, "career_coach_exec")  # type: ignore
    else:
        print("➡️ Dispatcher: Routing to Front Desk Fallback.")
        await ctx.send_message(specialist_request, "front_desk_exec")  # type: ignore

    target_route = None  # Revert the initial status of target_route


# --- AGENT CONSTRUCTORS ---


async def create_archivist_agent(
    credential=DefaultAzureCredential(), allow_multiple_tool_calls: bool = True,
) -> Agent:
    """Helper to create a document analyst agent."""
    model_choice = "STANDARD_HEAVY_MODEL"
    client: FoundryChatClient = _get_foundry_client(credential, model_choice)
    web_search_tool = client.get_web_search_tool(
        user_location={
            "city": "The Chiense University of Hong Kong",
            "region": "Hong Kong",
        },
        search_context_size="high",
        allowed_domains=["lib.cuhk.edu.hk"],
    )
    memory_search_preview_tool = _get_cached_memory_search_preview_tool()
    file_search_tool = await _get_cached_file_search_tool(client)

    tool_list: list[Any] = [
        web_search_tool,
        memory_search_preview_tool,
        file_search_tool,
        inquire_abbreviations,
        retrieve_student_emails,
        extract_deadlines,
    ]

    return Agent(
        client=client,
        instructions=ARCHIVIST_PROMPT,
        name="archivist_agent",
        tools=tool_list,
        default_options={
            "store": False,
            "reasoning": None,
            "allow_multiple_tool_calls": allow_multiple_tool_calls,
        },  # type: ignore
        require_per_service_call_history_persistence=True,
    )


async def create_secretary_agent(
    credential=DefaultAzureCredential(), allow_multiple_tool_calls: bool = True,
) -> Agent:
    model_choice = "STANDARD_HEAVY_MODEL"
    client: FoundryChatClient = _get_foundry_client(credential, model_choice)
    memory_search_preview_tool = _get_cached_memory_search_preview_tool()
    # file_search_tool = await _get_cached_file_search_tool(client)
    # code_interpreter_tool = client.get_code_interpreter_tool()

    tool_list: list[Any] = [
        memory_search_preview_tool,
        # file_search_tool,
        # code_interpreter_tool,
        # upload_sandbox_file_to_azure,
        inquire_abbreviations,
        draft_lecturer_email,
        create_planner_task,
        schedule_calendar_event,
        generate_docx,
        generate_xlsx,
        generate_pptx,
        generate_pdf,
        generate_image,
    ]

    return Agent(
        client=client,
        instructions=SECRETARY_PROMPT,
        name="secretary_agent",
        tools=tool_list,
        default_options={
            "store": False,
            "reasoning": None,
            "allow_multiple_tool_calls": allow_multiple_tool_calls,
        },  # type: ignore
        require_per_service_call_history_persistence=True,
    )


async def create_career_coach_agent(
    credential=DefaultAzureCredential(), allow_multiple_tool_calls: bool = True,
) -> Agent:
    model_choice = "STANDARD_HEAVY_MODEL"
    client: FoundryChatClient = _get_foundry_client(credential, model_choice)
    web_search_tool = client.get_web_search_tool(
        search_context_size="high",
    )
    memory_search_preview_tool = _get_cached_memory_search_preview_tool()
    file_search_tool = await _get_cached_file_search_tool(client)
    # code_interpreter_tool = client.get_code_interpreter_tool()

    tool_list: list[Any] = [
        web_search_tool,
        memory_search_preview_tool,
        file_search_tool,
        # code_interpreter_tool,
        # upload_sandbox_file_to_azure,
        inquire_abbreviations,
        analyze_resume_skill_gaps,
        generate_mock_interview_scenario,
        simulate_workplace,
        convert_text_to_speech,
        generate_image,
    ]

    return Agent(
        client=client,
        instructions=CAREER_COACH_PROMPT,
        name="career_coach_agent",
        tools=tool_list,
        default_options={
            "store": False,
            "reasoning": None,
            "allow_multiple_tool_calls": allow_multiple_tool_calls,
        },  # type: ignore
        require_per_service_call_history_persistence=True,
    )


async def create_front_desk_agent(
    credential=DefaultAzureCredential(), allow_multiple_tool_calls: bool = True,
) -> Agent:
    """Handles general chit-chat, greetings, and unsupported requests."""
    model_choice = "FAST_MINI_MODEL"
    client: FoundryChatClient = _get_foundry_client(credential, model_choice)
    # openai_client = ChatClient

    web_search_tool = client.get_web_search_tool(
        user_location={
            "region": "Hong Kong",
        }
    )
    memory_search_preview_tool = _get_cached_memory_search_preview_tool()
    # file_search_tool = await _get_cached_file_search_tool(client)
    # code_interpreter_tool = client.get_code_interpreter_tool()

    tool_list: list[Any] = [
        web_search_tool,
        memory_search_preview_tool,
        # file_search_tool,
        # code_interpreter_tool,
        # upload_sandbox_file_to_azure,
        inquire_abbreviations,
        get_weather,
        get_current_time,
        get_general_faq,
    ]

    return Agent(
        client=client,
        instructions=FRONTDESK_PROMPT,
        name="front_desk_agent",
        tools=tool_list,
        default_options={
            "store": False,
            "reasoning": None,
            "allow_multiple_tool_calls": allow_multiple_tool_calls,
        },  # type: ignore
        require_per_service_call_history_persistence=True,
    )
