
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
            return True

        try:
            detection = TriageResult.model_validate_json(message.agent_response.text)
            
            match agent_flag:
                case "read":
                    return detection.is_read == expected_result
                case "exec":
                    return detection.is_exec == expected_result
                case "career":
                    return detection.is_career == expected_result
                case _:
                    return False
        except Exception:
            return False

    return condition


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
    final_payload = EmailResponse.model_validate_json(response.agent_response.text)
    await ctx.yield_output(f"Processing Complete:\n{final_payload.response}")


# --- AGENT CONSTRUCTORS ---

def create_triage_manager_agent(credential=DefaultAzureCredential()) -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=(
            "You are a triage routing assistant that categorizes incoming user queries and documents.\n\n"
            "CRITICAL OPERATIONAL RULES:\n"
            "1. You must think first! Populate the 'reason' field by detailing exactly what the user wants.\n"
            "2. Evaluate meeting requests, calendar planning, conference logistics, and timeline setups as 'is_exec = true'.\n"
            "3. Evaluate document reads or log reviews as 'is_read = true'.\n"
            "4. Evaluate resume edits, career prep, or academic goals as 'is_career = true'.\n\n"
            "You must match at least one flag if a clear task is present. Preserve the text exactly in 'doc_content'."
        ),
        name="triage_manager_agent",
        default_options={"response_format": TriageResult},  # type: ignore
    )


def create_archivist_agent(credential=DefaultAzureCredential()) -> Agent:
    """Helper to create a document analyst agent."""
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=(
            "You are The Archivist. Your role is to handle tasks related to emails, "
            "college updates, deadlines, and SharePoint data. Extract critical info and "
            "categorize it logically. Return JSON with a single field 'response' "
            "containing the analysis output."
        ),
        name="archivist_agent",
        default_options={"response_format": EmailResponse} # type: ignore
    )

def create_document_executor_agent(credential=DefaultAzureCredential()) -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=(
            "You are The Executive. Your role is to handle automated time management, writing documents, "
            "calendar time-blocking, structural task updates, and workflow mapping tracking. "
            "Return JSON with a single field 'response' containing your action blueprint/draft."
        ),
        name="executive_agent",
        default_options={"response_format": EmailResponse},  # type: ignore
    )

def create_career_coach_agent(credential=DefaultAzureCredential()) -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        instructions=(
            "You are The Career Coach. Your role is to guide professional readiness, academic tracking, "
            "optimize resumes, map workplace simulations, and provide career drafting assistance. "
            "Return JSON with a single field 'response' containing the career development advice."
        ),
        name="career_coach_agent",
        default_options={"response_format": EmailResponse},  # type: ignore
    )


def main() -> None:
    credential = DefaultAzureCredential()

    # Create agents and session
    triage_agent = create_triage_manager_agent(credential=credential)
    
    triage_session = triage_agent.create_session()
    archivist_agent = create_archivist_agent(credential=credential)
    document_executor_agent = create_document_executor_agent(credential=credential)
    career_coach_agent = create_career_coach_agent(credential=credential)

    archivist_session = archivist_agent.create_session()
    document_executor_session = document_executor_agent.create_session()
    career_coach_session = career_coach_agent.create_session()

    triage_agent_executor = AgentExecutor(triage_agent, session=triage_session) # type: ignore
    archivist_agent_executor = AgentExecutor(archivist_agent, session=archivist_session, context_mode="full") # type: ignore
    document_executor_agent_executor = AgentExecutor(document_executor_agent, session=document_executor_session, context_mode="full") # type: ignore
    career_coach_agent_executor = AgentExecutor(career_coach_agent, session=career_coach_session, context_mode="full") # type: ignore


    # Establish conditional DAG execution layout
    workflow = (
        WorkflowBuilder(
            start_executor=triage_agent_executor,
            name="agent-cuhk-workflow")
        
        # Branch 1: Read/Archival Path
        .add_edge(triage_agent_executor, to_archivist_request, condition=get_condition(True, "read"))
        .add_edge(to_archivist_request, archivist_agent_executor)
        .add_edge(archivist_agent_executor, handle_workflow_output)
        
        # Branch 2: Write/Executive Path
        .add_edge(triage_agent_executor, to_executive_request, condition=get_condition(True, "exec"))
        .add_edge(to_executive_request, document_executor_agent_executor)
        .add_edge(document_executor_agent_executor, handle_workflow_output)
        
        # Branch 3: Career/Academic Path
        .add_edge(triage_agent_executor, to_career_request, condition=get_condition(True, "career"))
        .add_edge(to_career_request, career_coach_agent_executor)
        .add_edge(career_coach_agent_executor, handle_workflow_output)
        
        # This edge only triggers if no flags are True
        .add_edge(triage_agent_executor, handle_fallback, condition=lambda msg: not isinstance(msg, AgentExecutorResponse) or is_all_false(msg))
        
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