
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
from prompt import TRIAGE_MANAGER_PROMPT, ARCHIVIST_PROMPT, EXECUTIVE_PROMPT, CAREER_COACH_PROMPT

# Load environment variables from .env file
load_dotenv()

# --- DATA MODELS ---

class TriageResult(BaseModel):
    """Structured routing schema for incoming documents."""
    
    # 1. ALWAYS FORCE THINKING FIRST
    reason: str = Field(description="Analyze the user request step-by-step and explain which category rules it satisfies before picking flags.")
    
    # 2. THEN SET THE FLAGS
    is_exec: bool = Field(description="True if the request mentions scheduling, planning, meetings, timelines, tracking, or task management.")
    is_read: bool = Field(description="True if the text requires analyzing, reading logs, or looking up info.")
    is_career: bool = Field(description="True if the text relates to resumes, job searching, or academic studies.")
    
    doc_content: str = Field(description="The exact unaltered original document text.")

class EmailResponse(BaseModel):
    """Represents the ultimate text response generated from processing agents."""
    response: str


def get_condition(expected_result: bool, agent_flag: str):
    """Create a condition callable that routes based on TriageResult flags."""
    def condition(message: Any) -> bool:
        if not isinstance(message, AgentExecutorResponse):
            return False          # No decision → stay on current node
        try:
            detection = TriageResult.model_validate_json(message.agent_response.text)
            return getattr(detection, agent_flag) == expected_result
        except Exception:
            return False



def is_all_false(message: Any) -> bool:
    """Checks if all routing flags are False."""
    if not isinstance(message, AgentExecutorResponse):
        return False
    try:
        detection = TriageResult.model_validate_json(message.agent_response.text)
        return not (detection.is_exec or detection.is_read or detection.is_career)
    except Exception:
        return False


# --- BRIDGE EXECUTORS (Translates Triage Objects to downstream Agent Requests) ---

@executor(id="to_archivist_request")
async def to_archivist_request(response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
    """Transforms triage content directly into a request packet for the Archivist Agent."""
    detection = TriageResult.model_validate_json(response.agent_response.text)
    user_msg = Message("user", contents=[detection.doc_content])
    await ctx.send_message(AgentExecutorRequest(messages=[user_msg], should_respond=True))

@executor(id="to_executive_request")
async def to_executive_request(response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
    """Transforms triage content directly into a request packet for the Executive Agent."""
    detection = TriageResult.model_validate_json(response.agent_response.text)
    user_msg = Message("user", contents=[detection.doc_content])
    await ctx.send_message(AgentExecutorRequest(messages=[user_msg], should_respond=True))

@executor(id="to_career_request")
async def to_career_request(response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
    """Transforms triage content directly into a request packet for the Career Coach Agent."""
    detection = TriageResult.model_validate_json(response.agent_response.text)
    user_msg = Message("user", contents=[detection.doc_content])
    await ctx.send_message(AgentExecutorRequest(messages=[user_msg], should_respond=True))

@executor(id="handle_fallback")
async def handle_fallback(response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
    await ctx.yield_output("I'm ready to help! Please send me a document, a request for a meeting, or a career question.")

# --- TERMINAL HANDLERS (Receives agent responses and yields output) ---

@executor(id="handle_workflow_output")
async def handle_workflow_output(response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
    """Consolidates output extraction for your specialized agents returning EmailResponses."""
    try:
        final_payload = EmailResponse.model_validate_json(response.agent_response.text)
    except Exception as e:
        # Log the error and return a safe fallback
        await ctx.yield_output(f"Error processing agent response: {e}")
        return
    await ctx.yield_output(f"Processing Complete:\n{final_payload.response}")


# --- AGENT CONSTRUCTORS ---

def create_triage_manager_agent(credential=DefaultAzureCredential()) -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=TRIAGE_MANAGER_PROMPT,
        name="triage_manager_agent",
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
        default_options={"response_format": EmailResponse, "store": False, "reasoning": None},  # type: ignore
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
        default_options={"response_format": EmailResponse, "store": False, "reasoning": None},  # type: ignore
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
        default_options={"response_format": EmailResponse, "store": False, "reasoning": None},  # type: ignore
    )


def main() -> None:
    credential = DefaultAzureCredential()

    # Create agents and session
    triage_manager_agent = create_triage_manager_agent(credential=credential)
    archivist_agent = create_archivist_agent(credential=credential)
    executive_agent = create_executive_agent(credential=credential)
    career_coach_agent = create_career_coach_agent(credential=credential)

    triage_manager_agent_executor = AgentExecutor(triage_manager_agent, id="triage_manager_exec", context_mode="full") # type: ignore
    archivist_agent_executor = AgentExecutor(archivist_agent, id="archivist_exec", context_mode="last_agent") # type: ignore
    executive_agent_executor = AgentExecutor(executive_agent, id="executive_exec", context_mode="last_agent") # type: ignore
    career_coach_agent_executor = AgentExecutor(career_coach_agent, id="career_coach_exec", context_mode="last_agent") # type: ignore


    # Establish conditional DAG execution layout
    workflow = (
        WorkflowBuilder(
            start_executor=triage_manager_agent_executor,
            name="agent-cuhk-workflow")
        
        # Branch 1: Read/Archival Path
        .add_edge(triage_manager_agent_executor, to_archivist_request, condition=get_condition(True, "read"))
        .add_edge(to_archivist_request, archivist_agent_executor)
        .add_edge(archivist_agent_executor, handle_workflow_output)
        
        # Branch 2: Write/Executive Path
        .add_edge(triage_manager_agent_executor, to_executive_request, condition=get_condition(True, "exec"))
        .add_edge(to_executive_request, executive_agent_executor)
        .add_edge(executive_agent_executor, handle_workflow_output)
        
        # Branch 3: Career/Academic Path
        .add_edge(triage_manager_agent_executor, to_career_request, condition=get_condition(True, "career"))
        .add_edge(to_career_request, career_coach_agent_executor)
        .add_edge(career_coach_agent_executor, handle_workflow_output)
        
        # This edge only triggers if no flags are True
        .add_edge(triage_manager_agent_executor, handle_fallback, condition=lambda msg: not isinstance(msg, AgentExecutorResponse) or is_all_false(msg))
        
        .build()
        .as_agent()
    )

    # --- HOSTING INITIALIZATION ---
    print("🚀 Starting local Agent Response Server interface on http://localhost:8088...")
    
    # Notice: The checkpoint_storage kwarg has been completely removed! 
    # The framework manages it internally, and our monkeypatch secures the type whitelist.
    server = ResponsesHostServer(workflow)
    server.run()

if __name__ == "__main__":
    main()