
import asyncio
import os
from datetime import datetime
from typing import Any

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
from azure.identity import AzureCliCredential  # Uses your az CLI login for credentials
from dotenv import load_dotenv
from pydantic import BaseModel, Field  # Structured outputs for safer parsing
from typing_extensions import Never

# Load environment variables from .env file
load_dotenv()

"""
Sample: Conditional routing with structured outputs

What this sample is:
- A minimal decision workflow that classifies an inbound email as spam or not spam, then routes to the
appropriate handler.

Purpose:
- Show how to attach boolean edge conditions that inspect an AgentExecutorResponse.
- Demonstrate using Pydantic models as response_format so the agent returns JSON we can validate and parse.
- Illustrate how to transform one agent's structured result into a new AgentExecutorRequest for a downstream agent.

Prerequisites:
- FOUNDRY_PROJECT_ENDPOINT must be your Azure AI Foundry Agent Service (V2) project endpoint.
- You understand the basics of WorkflowBuilder, executors, and events in this framework.
- You know the concept of edge conditions and how they gate routes using a predicate function.
- Azure OpenAI access is configured for FoundryChatClient. You should be logged in with Azure CLI (AzureCliCredential)
and have the Foundry V2 Project environment variables set as documented in the getting started chat client README.
- The sample email resource file exists at workflow/resources/email.txt.

High level flow:
1) archivist_agent reads an email and returns TriageResult.
2) If not spam, we transform the detection output into a user message for career_coach_agent, then finish by
yielding the drafted reply as workflow output.
3) If spam, we short circuit to a spam handler that yields a spam notice as workflow output.

Output:
- The final workflow output is printed to stdout, either with a drafted reply or a spam notice.

Notes:
- Conditions read the agent response text and validate it into TriageResult for robust routing.
- Executors are small and single purpose to keep control flow easy to follow.
- The workflow completes when it becomes idle, not via explicit completion events.
"""


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
    """Create a condition callable that routes based on TriageResult.is_spam."""

    # The returned function will be used as an edge predicate.
    # It receives whatever the upstream executor produced.
    def condition(message: Any) -> bool:
        # Defensive guard. If a non AgentExecutorResponse appears, let the edge pass to avoid dead ends.
        if not isinstance(message, AgentExecutorResponse):
            return True

        try:
            # Use your new unified schema here as well!
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
            # Fail closed on parse errors so we do not accidentally route to the wrong path.
            # Returning False prevents this edge from activating.
            return False

    return condition


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


# --- TERMINAL HANDLERS (Receives agent responses and yields output) ---

@executor(id="handle_workflow_output")
async def handle_workflow_output(response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
    """Consolidates output extraction for your specialized agents returning EmailResponses."""
    final_payload = EmailResponse.model_validate_json(response.agent_response.text)
    await ctx.yield_output(f"Processing Complete:\n{final_payload.response}")


# --- AGENT CONSTRUCTORS ---

def create_triage_manager_agent() -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=AzureCliCredential(),
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


def create_archivist_agent() -> Agent:
    """Helper to create a document analyst agent."""
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=AzureCliCredential(),
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

def create_document_executor_agent() -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=AzureCliCredential(),
        ),
        instructions=(
            "You are The Executive. Your role is to handle automated time management, writing documents, "
            "calendar time-blocking, structural task updates, and workflow mapping tracking. "
            "Return JSON with a single field 'response' containing your action blueprint/draft."
        ),
        name="executive_agent",
        default_options={"response_format": EmailResponse},  # type: ignore
    )

def create_career_coach_agent() -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=AzureCliCredential(),
        ),
        instructions=(
            "You are The Career Coach. Your role is to guide professional readiness, academic tracking, "
            "optimize resumes, map workplace simulations, and provide career drafting assistance. "
            "Return JSON with a single field 'response' containing the career development advice."
        ),
        name="career_coach_agent",
        default_options={"response_format": EmailResponse},  # type: ignore
    )


async def main() -> None:
    # Build the workflow graph.
    # Start at the spam detector.
    # If not spam, hop to a transformer that creates a new AgentExecutorRequest,
    # then call the email assistant, then finalize.
    # If spam, go directly to the spam handler and finalize.
    triage_manager_agent = AgentExecutor(create_triage_manager_agent())
    archivist_agent = AgentExecutor(create_archivist_agent())
    document_executor_agent = AgentExecutor(create_document_executor_agent())
    career_coach_agent = AgentExecutor(create_career_coach_agent())

    # Establish conditional DAG execution layout
    workflow = (
        WorkflowBuilder(start_executor=triage_manager_agent)
        
        # Branch 1: Read/Archival Path
        .add_edge(triage_manager_agent, to_archivist_request, condition=get_condition(True, "read"))
        .add_edge(to_archivist_request, archivist_agent)
        .add_edge(archivist_agent, handle_workflow_output)
        
        # Branch 2: Write/Executive Path
        .add_edge(triage_manager_agent, to_executive_request, condition=get_condition(True, "exec"))
        .add_edge(to_executive_request, document_executor_agent)
        .add_edge(document_executor_agent, handle_workflow_output)
        
        # Branch 3: Career/Academic Path
        .add_edge(triage_manager_agent, to_career_request, condition=get_condition(True, "career"))
        .add_edge(to_career_request, career_coach_agent)
        .add_edge(career_coach_agent, handle_workflow_output)
        
        .build()
    )


    # Fallback to local script relative folder structural reads to preserve your data pipeline setup
    input_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"user_input.txt")

    if not os.path.exists(input_path):
        # Graceful fallback mock data injection if local files are missing during testing
        email = "I would like to have a Resume Check for the Academic Research Submission. Can you verify my timeline updates?"
    else:
        with open(input_path) as f:
            email = f.read()

    # Execute the workflow
    request = AgentExecutorRequest(messages=[Message("user", contents=[email])], should_respond=True)
    events = await workflow.run(request)
    
    print("\n=================== FULL WORKFLOW EXECUTION TRACE ===================")
    # WorkflowRunResult is an iterable list of raw data-plane events!
    for event in events:
        print(f"\n[Event Type]: {event.type}")
        # Look inside the event data package
        if hasattr(event, "data") and event.data:
            print(f"Payload: {event.data}")
            
    print("\n=================== SEPARATED OUTPUT GROUPS ===================")
    # Fetch terminal answers explicitly
    final_outputs = events.get_outputs()
    print(f"Terminal Outputs Count: {len(final_outputs)}")
    
    if final_outputs:
        for i, out in enumerate(final_outputs):
            print(f"  -> Output [{i}]: {out}")
        
        print(f"\n=================== FINAL WORKFLOW OUTPUT ===================")
        print(final_outputs[-1])
        track_output(final_outputs)
    
def track_output(final_outputs):
        output_filepath_1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), "samples", "output-main-final-msg.txt")
        output_filepath_2 = os.path.join(os.path.dirname(os.path.realpath(__file__)), "samples", "output-main-full-traces.txt")

        to_write = {
            output_filepath_1: final_outputs[-1],
            output_filepath_2: final_outputs
        }
        
        for fp, payload in to_write.items():

            with open(fp, "a", encoding="utf-8") as f:
                # 1. Generate a clean timestamp for context
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 2. Write structural padding barriers around the payload
                f.write("\n" + "=" * 60 + "\n")
                f.write(f" RUN TIME: {timestamp}\n")
                f.write("=" * 60 + "\n\n")
                
                # 3. Append the actual agent response payload
                if isinstance(payload, str):
                    f.write(payload)
                elif isinstance(payload, list):
                    string_payloads = [str(item) if not hasattr(item, "text") else item.text for item in payload]
                    f.write('\n'.join(string_payloads))
                
                # 4. Add trailing padding space for the next run
                f.write("\n\n")

if __name__ == "__main__":
    asyncio.run(main())