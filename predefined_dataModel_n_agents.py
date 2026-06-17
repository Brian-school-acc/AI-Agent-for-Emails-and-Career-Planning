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
    EXECUTIVE_PROMPT,
    CAREER_COACH_PROMPT,
    FRONTDESK_PROMPT
)
from tools import (
    summarize_document,
    inquire_abbreviations,
    convert_text_to_speech,
)
from front_desk_tools import (
    show_agent_selection_menu,
    get_weather,
    get_current_time,
    get_general_faq,
)

# from archivist_tools import (

# )
from executive_tools import (
    draft_lecturer_email,
    create_planner_task,
    schedule_calendar_event,
    generate_and_link_docx,
    # generate_word_document,
    # generate_presentation_slides,
)
from career_coach_tools import (
    analyze_resume_skill_gaps,
    generate_mock_interview_scenario,
    simulate_workplace,
)

load_dotenv()

PROJECT_ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL_NAME = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "")

# --- 1. DATA MODELS ---


class TriageResult(BaseModel):
    """Structured routing schema for incoming documents."""

    reason: str = Field(description="Analyze the user request step-by-step.")
    route: Literal["read", "exec", "career", "fallback"] = Field(
        description="Select 'read' for analysis/lookup, 'exec' for timelines/deadlines/tasks, 'career' for resumes, or 'fallback' if general/unclear."
    )
    
    doc_content: str = Field(
        default="", description="The exact unaltered original document text."
    )


# --- 2. Helper Function: CLIENT FACTORY ---
def _get_foundry_client(credential: DefaultAzureCredential) -> FoundryChatClient:
    """Helper method to construct the centralized inference provider client."""
    if not PROJECT_ENDPOINT:
        raise ValueError("Missing environment variable: FOUNDRY_PROJECT_ENDPOINT")

    return FoundryChatClient(
        project_endpoint=PROJECT_ENDPOINT,
        model=MODEL_NAME,
        credential=credential
    )


# --- CENTRALIZED DISPATCHER ROUTER ---

@executor(id="triage_and_route")
async def triage_and_route(messages: list[Message], ctx: WorkflowContext[list[Message]]) -> None:
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

    # Initialize target_route for the following 2 routes: A, B
    target_route = None

    # --- ROUTE A (ACTION CARD): INTERCEPT ADAPTIVE CARD SUBMISSIONS ---
    is_card_click = False

    try:
        # If it's a card submission, original_prompt will be a stringified JSON object
        card_data = json.loads(original_prompt.strip())
        if (
            isinstance(card_data, dict)
            and card_data.get("actionType") == "route_to_agent"
        ):
            is_card_click = True
            target_route = card_data.get("targetAgent")
            print(f"🎯 Intercepted Card Click! Direct routing to: {target_route}")
    except (json.JSONDecodeError, TypeError):
        # Not a JSON payload; it's regular student text. Proceed to LLM triage.
        pass

    # 2. Package request bundle for specialists
    user_msg = Message("user", contents=[str(original_prompt)])
    specialist_request = AgentExecutorRequest(messages=[user_msg], should_respond=True)

    # 3. Execution Path Logic
    if is_card_click:
        # Bypasses LLM entirely, saving latency and money
        if target_route == "career_coach":
            print("➡️ Dispatcher: Routing to Archivist Agent.")
            await ctx.send_message(specialist_request, "archivist_exec") # type: ignore
        elif target_route == "executive":
            print("➡️ Dispatcher: Routing to Executive Agent.")
            await ctx.send_message(specialist_request, "executive_exec") # type: ignore
        elif target_route == "archivist":
            print("➡️ Dispatcher: Routing to Career Coach Agent.")
            await ctx.send_message(specialist_request, "career_coach_exec") # type: ignore
        else:
            print("➡️ Dispatcher: Routing to Front Desk Fallback.")
            await ctx.send_message(specialist_request, "front_desk_exec") # type: ignore
    else:
        target_route = None  # Revert the initial status of target_route

    # --- ROUTE B (LLM TRIAGE): FALLBACK TO ORIGINAL SILENT LLM TRIAGE ---

    # 2. Build the triage agent locally to run SILENTLY (Isolated from the stream)
    credential = DefaultAzureCredential()
    triage_agent = Agent(
        client=_get_foundry_client(credential),
        instructions=TRIAGE_PROMPT,
        name="triage_agent",
        default_options={"store": False, "reasoning": None, "allow_multiple_tool_calls": True},  # type: ignore
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
        detection = TriageResult(reason="Fail-safe routing", route="fallback", doc_content=raw_text)

    # 3. Package the request bundle for your specialist agents
    user_msg = Message("user", contents=[str(original_prompt)])
    specialist_request = AgentExecutorRequest(messages=[user_msg], should_respond=True)

    # 4. Route directly to the targeted specialist executor matching the IDs in main()
    if target_route == "read":
        print("➡️ Dispatcher: Routing to Archivist Agent.")
        await ctx.send_message(specialist_request, "archivist_exec")  # type: ignore
    elif target_route == "exec":
        print("➡️ Dispatcher: Routing to Executive Agent.")
        await ctx.send_message(specialist_request, "executive_exec")  # type: ignore
    elif target_route == "career":
        print("➡️ Dispatcher: Routing to Career Coach Agent.")
        await ctx.send_message(specialist_request, "career_coach_exec")  # type: ignore
    else:
        print("➡️ Dispatcher: Routing to Front Desk Fallback.")
        await ctx.send_message(specialist_request, "front_desk_exec")  # type: ignore

    target_route = None  # Revert the initial status of target_route

# --- AGENT CONSTRUCTORS ---


def create_archivist_agent(credential=DefaultAzureCredential()) -> Agent:
    """Helper to create a document analyst agent."""
    client: FoundryChatClient = _get_foundry_client(credential)
    web_search_tool = client.get_web_search_tool(
        user_location={
            "city": "The Chiense University of Hong Kong",
            "region": "Hong Kong",
        },
        search_context_size="high",
        allowed_domains=["https://www.lib.cuhk.edu.hk/en/"],
    )

    tool_list: list[Any] = [
        inquire_abbreviations,
        summarize_document,
        web_search_tool,
    ]

    return Agent(
            client=client,
            instructions=ARCHIVIST_PROMPT,
            name="archivist_agent",
            tools=tool_list,
            default_options={"store": False, "reasoning": None, "allow_multiple_tool_calls": True}, # type: ignore
        )


def create_executive_agent(credential=DefaultAzureCredential()) -> Agent:
    client = _get_foundry_client(credential)

    code_interpreter_tool = client.get_code_interpreter_tool()

    tool_list: list[Any] = [
        inquire_abbreviations,
        draft_lecturer_email,
        create_planner_task,
        schedule_calendar_event,
        code_interpreter_tool,
        generate_and_link_docx,
        # generate_word_document,
        # generate_presentation_slides,
    ]

    return Agent(
        client=client,
        instructions=EXECUTIVE_PROMPT,
        name="executive_agent",
        tools=tool_list,
        default_options={"store": False, "reasoning": None, "allow_multiple_tool_calls": True}, # type: ignore
    )

def create_career_coach_agent(credential=DefaultAzureCredential()) -> Agent:
    client = _get_foundry_client(credential)
    web_search_tool = client.get_web_search_tool(
        search_context_size="high",
    )
    code_interpreter_tool = client.get_code_interpreter_tool()

    tool_list: list[Any] = [
        inquire_abbreviations,
        web_search_tool,
        code_interpreter_tool,
        analyze_resume_skill_gaps,
        generate_mock_interview_scenario,
        simulate_workplace,
        convert_text_to_speech,
    ]

    return Agent(
        client=client,
        instructions=CAREER_COACH_PROMPT,
        name="career_coach_agent",
        tools=tool_list,
        default_options={"store": False, "reasoning": None, "allow_multiple_tool_calls": True}, # type: ignore
    )

def create_front_desk_agent(credential=DefaultAzureCredential()) -> Agent:
    """Handles general chit-chat, greetings, and unsupported requests."""
    client = _get_foundry_client(credential)
    # Configure the web search tool with explicit CUHK location properties
    web_search_tool = client.get_web_search_tool(
        user_location={
            "region": "Hong Kong",
        }
    )

    tool_list: list[Any] = [
        inquire_abbreviations,
        show_agent_selection_menu,
        get_weather,
        get_current_time,
        get_general_faq,
        web_search_tool,
    ]

    return Agent(
        client=client,
        instructions=FRONTDESK_PROMPT,
        name="front_desk_agent",
        tools=tool_list,
        default_options={"store": False, "reasoning": None, "allow_multiple_tool_calls": True}, # type: ignore
    )
