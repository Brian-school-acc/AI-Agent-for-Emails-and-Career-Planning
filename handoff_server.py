# ===================== 1. THE CRITICAL WORKAROUND (MONKEYPATCH) =====================
# ====================================================================================
import agent_framework._workflows._checkpoint as checkpoint_mod
from azure.ai.agentserver.responses.models._generated.sdk.models.models._enums import (
    MessageRole,
)

_original_init = checkpoint_mod.FileCheckpointStorage.__init__


def _patched_init(self, *args, **kwargs):
    print("✅ Patched FileCheckpointStorage.__init__ called")

    allowed = kwargs.get("allowed_checkpoint_types")
    if allowed is None:
        allowed = set()
    elif isinstance(allowed, list):
        allowed = set(allowed)
    else:
        allowed = set(allowed)

    allowed.update(
        [
            "openai.lib.streaming.responses._events:ResponseTextDeltaEvent",
            "openai.lib.streaming.responses._events:ResponseTextDoneEvent",
            "agent_framework_orchestrations._handoff:HandoffAgentUserRequest",
            "types:GenericAlias",
        ]
    )

    allowed.add(MessageRole)
    allowed.add(
        "azure.ai.agentserver.responses.models._generated.sdk.models.models._enums:MessageRole"
    )

    kwargs["allowed_checkpoint_types"] = allowed
    _original_init(self, *args, **kwargs)


checkpoint_mod.FileCheckpointStorage.__init__ = _patched_init
# ====================================================================================

import asyncio
import os
from dotenv import load_dotenv

from agent_framework import WorkflowAgent
from agent_framework.orchestrations import HandoffBuilder
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from agent_framework.foundry import FoundryChatClient

from predefined_agents import (
    create_archivist_agent,
    create_secretary_agent,
    create_career_coach_agent,
    create_front_desk_agent,
)

load_dotenv()


async def setup_workflow() -> WorkflowAgent:
    """Handles all asynchronous agent setup and returns the built workflow."""
    credential = DefaultAzureCredential()
    chat_client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["FAST_MINI_MODEL"],
        credential=DefaultAzureCredential(),
    )
    # Create triage/coordinator agent
    triage_agent = chat_client.as_agent(
        instructions=(
            "You are frontline support triage. Route customer issues to the appropriate specialist agents "
            "based on the problem described."
        ),
        description="Triage agent that handles general inquiries.",
        name="triage_agent",
        default_options={"store": False, "reasoning": None, "allow_multiple_tool_calls": False},  # type: ignore
        require_per_service_call_history_persistence=True,
    )

    # Await the creation of specialized agents
    archivist_agent = await create_archivist_agent(credential=credential, allow_multiple_tool_calls=False)
    secretary_agent = await create_secretary_agent(credential=credential, allow_multiple_tool_calls=False)
    career_coach_agent = await create_career_coach_agent(credential=credential, allow_multiple_tool_calls=False)
    front_desk_agent = await create_front_desk_agent(credential=credential, allow_multiple_tool_calls=False)

    # Build the handoff workflow
    workflow = (
        HandoffBuilder(
            name="Student Support Handoff",
            participants=[
                triage_agent,
                archivist_agent,
                secretary_agent,
                career_coach_agent,
                front_desk_agent,
            ],
        )
        .with_start_agent(triage_agent)  # Triage receives initial user input
        # Triage cannot route directly to refund agent
        .add_handoff(
            triage_agent,
            [archivist_agent, secretary_agent, career_coach_agent, front_desk_agent],
        )
        .add_handoff(
            archivist_agent,
            [
                triage_agent,
                archivist_agent,
                secretary_agent,
                career_coach_agent,
                front_desk_agent,
            ],
        )
        .add_handoff(
            secretary_agent,
            [
                triage_agent,
                archivist_agent,
                secretary_agent,
                career_coach_agent,
                front_desk_agent,
            ],
        )
        .add_handoff(
            career_coach_agent,
            [
                triage_agent,
                archivist_agent,
                secretary_agent,
                career_coach_agent,
                front_desk_agent,
            ],
        )
        .add_handoff(
            front_desk_agent,
            [
                triage_agent,
                archivist_agent,
                secretary_agent,
                career_coach_agent,
                front_desk_agent,
            ],
        )
        .build()
        .as_agent()
    )
    return workflow


def main() -> None:
    # 1. Run the async setup inside an isolated event loop
    print("⏳ Initializing agents and connecting to Azure Vector Stores...")
    workflow = asyncio.run(setup_workflow())

    # 2. Start the synchronous hosting server in the main thread
    print(
        "🚀 Starting local Agent Response Server interface on http://localhost:8088..."
    )
    server = ResponsesHostServer(workflow)
    server.run()


if __name__ == "__main__":
    main()
