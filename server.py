# ===================== 1. THE CRITICAL WORKAROUND (MONKEYPATCH) =====================
# ====================================================================================
import agent_framework._workflows._checkpoint as checkpoint_mod
from azure.ai.agentserver.responses.models._generated.sdk.models.models._enums import (
    MessageRole,
)

_original_init = checkpoint_mod.FileCheckpointStorage.__init__


def _patched_init(self, *args, **kwargs):
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
from agent_framework import (
    AgentExecutor,
    WorkflowBuilder,
    WorkflowAgent,
)
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from predefined_agents import (
    triage_and_route,
    create_archivist_agent,
    create_secretary_agent,
    create_career_coach_agent,
    create_front_desk_agent,
)

load_dotenv()


async def setup_workflow() -> WorkflowAgent:
    """Handles all asynchronous agent setup and returns the built workflow."""
    credential = DefaultAzureCredential()

    # Await the creation of specialized agents
    archivist_agent = await create_archivist_agent(credential=credential)
    secretary_agent = await create_secretary_agent(credential=credential)
    career_coach_agent = await create_career_coach_agent(credential=credential)
    front_desk_agent = await create_front_desk_agent(credential=credential)

    # Wrap only specialist agents inside target Executors
    archivist_agent_executor = AgentExecutor(archivist_agent, id="archivist_exec", context_mode="full")  # type: ignore
    secretary_agent_executor = AgentExecutor(secretary_agent, id="secretary_exec", context_mode="full")  # type: ignore
    career_coach_agent_executor = AgentExecutor(career_coach_agent, id="career_coach_exec", context_mode="full")  # type: ignore
    front_desk_agent_executor = AgentExecutor(front_desk_agent, id="front_desk_exec", context_mode="full")  # type: ignore

    # Establish clean structural layout using programmatic routing
    workflow = (
        WorkflowBuilder(
            name="agent-cuhk-workflow",
            description="a workflow to take user request and respond accordingly with tools",
            start_executor=triage_and_route,
        )
        .add_edge(triage_and_route, archivist_agent_executor)
        .add_edge(triage_and_route, secretary_agent_executor)
        .add_edge(triage_and_route, career_coach_agent_executor)
        .add_edge(triage_and_route, front_desk_agent_executor)
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
