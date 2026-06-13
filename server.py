import os
import asyncio
from typing import Any

# --- 1. THE CRITICAL WORKAROUND (MONKEYPATCH) ---
# We intercept the internal storage creation to inject the MessageRole whitelist
# before the ResponsesHostServer can execute and crash on deserialization.
import agent_framework._workflows._checkpoint as checkpoint_mod
from azure.ai.agentserver.responses.models._generated.sdk.models.models._enums import MessageRole

_original_init = checkpoint_mod.FileCheckpointStorage.__init__

def _patched_init(self, *args, **kwargs):
    allowed = kwargs.get("allowed_checkpoint_types")
    if allowed is None:
        allowed = set()
    elif isinstance(allowed, list):
        allowed = set(allowed)
    else:
        allowed = set(allowed)
    
    # Add the missing OpenAI Streaming Event identifiers here:
    allowed.update([
        "openai.lib.streaming.responses._events:ResponseTextDeltaEvent",
        "openai.lib.streaming.responses._events:ResponseTextDoneEvent"
    ])
    
    # Inject both the class and string identifiers into the secure unpickler
    allowed.add(MessageRole)
    allowed.add("azure.ai.agentserver.responses.models._generated.sdk.models.models._enums:MessageRole")
    
    kwargs["allowed_checkpoint_types"] = allowed
    _original_init(self, *args, **kwargs)

checkpoint_mod.FileCheckpointStorage.__init__ = _patched_init
# ------------------------------------------------

from agent_framework import (  # Core chat primitives used to build requests
    Agent,
    AgentExecutor,
    AgentExecutorRequest,  # Input message bundle for an AgentExecutor
    AgentExecutorResponse,
    Message,
    WorkflowBuilder,  # Fluent builder for wiring executors and edges
    WorkflowContext,  # Per-run context and event bus
    executor,  # Decorator to declare a Python function as a workflow executor
)
from agent_framework.foundry import FoundryChatClient  # Thin client wrapper for Azure OpenAI chat models
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from azure.identity import AzureCliCredential  # Uses your az CLI login for credentials
from dotenv import load_dotenv
from pydantic import BaseModel, Field  # Structured outputs for safer parsing
from typing_extensions import Never
from refined_prompt import TRIAGE_PROMPT, ARCHIVIST_PROMPT, EXECUTIVE_PROMPT, CAREER_COACH_PROMPT, FRONTDESK_PROMPT

# Load environment variables from .env file
load_dotenv()

# --- DATA MODELS ---

from typing import Literal

class TriageResult(BaseModel):
    """Structured routing schema for incoming documents."""
    
    reason: str = Field(description="Analyze the user request step-by-step.")
    
    # Force the model to choose EXACTLY ONE target domain track
    route: Literal["read", "exec", "career", "fallback"] = Field(
        description="Select 'read' for analysis/lookup, 'exec' for timelines/deadlines/tasks, 'career' for resumes, or 'fallback' if general/unclear."
    )
    
    doc_content: str = Field(description="The exact unaltered original document text.")

# --- CENTRALIZED DISPATCHER ROUTER ---

@executor(id="route_to_agent")
async def route_to_agent(response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
    raw_text = response.agent_response.text.strip()
    
    if raw_text.startswith("```json"):
        raw_text = raw_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text.split("```", 1)[1].rsplit("```", 1)[0].strip()

    try:
        detection = TriageResult.model_validate_json(raw_text)
        route_target = detection.route
    except Exception as e:
        print(f"❌ Dispatcher validation failed: {e}. Defaulting to fallback route.")
        route_target = "fallback"
        detection = TriageResult(reason="Fail-safe routing", route="fallback", doc_content=raw_text)
    
    original_prompt = ctx.get_state("input")
    if not original_prompt:
        print("ORIGINAL_PROMPT NOT GET STATE input")
        messages = ctx.get_state("messages", [])
        if messages and isinstance(messages, list):
            original_prompt = messages[-1].get("content", "")
            
    if not original_prompt:
        print("ORIGINAL_PROMPT NOT GET POPULATE")
        original_prompt = detection.doc_content
        
    user_msg = Message("user", contents=[str(original_prompt)])
    request = AgentExecutorRequest(messages=[user_msg], should_respond=True)
    
    # Precise enum evaluation
    if route_target == "read":
        print("➡️ Dispatcher: Routing to Archivist Agent.")
        await ctx.send_message(request, "archivist_exec")
    elif route_target == "exec":
        print("➡️ Dispatcher: Routing to Executive Agent.")
        await ctx.send_message(request, "executive_exec")
    elif route_target == "career":
        print("➡️ Dispatcher: Routing to Career Coach Agent.")
        await ctx.send_message(request, "career_coach_exec")
    else:
        print("➡️ Dispatcher: Routing to Front Desk Fallback.")
        await ctx.send_message(request, "front_desk_exec")

# --- TERMINAL HANDLERS (Receives agent responses and yields output) ---

# @executor(id="handle_workflow_output")
# async def handle_workflow_output(response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
#     """Consolidates output extraction for your specialized agents returning EmailResponses."""
#     try:
#         final_payload = ResponseModel.model_validate_json(response.agent_response.text)
#     except Exception as e:
#         # Log the error and return a safe fallback
#         await ctx.yield_output(f"Error processing agent response: {e}")
#         return
#     await ctx.yield_output(f"RESPONSE: {final_payload.response}")


# --- AGENT CONSTRUCTORS ---

def create_triage_agent(credential=DefaultAzureCredential()) -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=TRIAGE_PROMPT,
        name="triage_agent",
        default_options={"response_format": TriageResult, "store": False},  # type: ignore
    )

def create_archivist_agent(credential=DefaultAzureCredential()) -> Agent:
    """Helper to create a document analyst agent."""
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=ARCHIVIST_PROMPT,
        name="archivist_agent",
        default_options={"store": False, "reasoning": None},  # type: ignore
    )

def create_executive_agent(credential=DefaultAzureCredential()) -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=EXECUTIVE_PROMPT,
        name="executive_agent",
        default_options={"store": False, "reasoning": None},  # type: ignore
    )

def create_career_coach_agent(credential=DefaultAzureCredential()) -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=CAREER_COACH_PROMPT,
        name="career_coach_agent",
        default_options={"store": False, "reasoning": None},  # type: ignore
    )

def create_front_desk_agent(credential=DefaultAzureCredential()) -> Agent:
    """Handles general chit-chat, greetings, and unsupported requests."""
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=FRONTDESK_PROMPT,
        name="front_desk_agent",
        default_options={"store": False, "reasoning": None},  # type: ignore
    )

def main() -> None:
    credential = DefaultAzureCredential()

    # Create agents
    triage_agent = create_triage_agent(credential=credential)
    archivist_agent = create_archivist_agent(credential=credential)
    executive_agent = create_executive_agent(credential=credential)
    career_coach_agent = create_career_coach_agent(credential=credential)
    front_desk_agent = create_front_desk_agent(credential=credential)

    # Wrap agents inside Executors with corresponding internal string IDs
    triage_agent_executor = AgentExecutor(triage_agent, id="triage_exec", context_mode="last_agent") # type: ignore
    archivist_agent_executor = AgentExecutor(archivist_agent, id="archivist_exec", context_mode="last_agent") # type: ignore
    executive_agent_executor = AgentExecutor(executive_agent, id="executive_exec", context_mode="last_agent") # type: ignore
    career_coach_agent_executor = AgentExecutor(career_coach_agent, id="career_coach_exec", context_mode="last_agent") # type: ignore
    front_desk_agent_executor = AgentExecutor(front_desk_agent, id="front_desk_exec", context_mode="last_agent") # type: ignore

    # Establish clean structural layout using programmatic routing
    workflow = (
        WorkflowBuilder(
            name="agent-cuhk-workflow",
            description="a workflow to take user request and respond accordingly with tools",
            start_executor=triage_agent_executor,
        )
        
        # 1. Unconditionally forward triage evaluation to our dispatcher function
        .add_edge(triage_agent_executor, route_to_agent)
        
        # 2. Expose valid topology paths to the graph compiler 
        .add_edge(route_to_agent, archivist_agent_executor)
        .add_edge(route_to_agent, executive_agent_executor)
        .add_edge(route_to_agent, career_coach_agent_executor)
        .add_edge(route_to_agent, front_desk_agent_executor)
        
        # 3. Connect all execution terminals to the shared payload visualizer
        # .add_edge(archivist_agent_executor, handle_workflow_output)
        # .add_edge(executive_agent_executor, handle_workflow_output)
        # .add_edge(career_coach_agent_executor, handle_workflow_output)
        # .add_edge(front_desk_agent_executor, handle_workflow_output)
        
        .build()
        .as_agent()
    )

    # --- HOSTING INITIALIZATION ---
    print("🚀 Starting local Agent Response Server interface on http://localhost:8088...")
    server = ResponsesHostServer(
        workflow, 
    )
    server.run()

if __name__ == "__main__":
    main()