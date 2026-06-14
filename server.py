
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
# ------------------------------------------------------------------------------------------------

# Import packages

from agent_framework import (
    AgentExecutor,
    WorkflowBuilder,
)

from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from predefined_dataModel_n_agents import (
    triage_and_route,
    create_archivist_agent,
    create_executive_agent,
    create_career_coach_agent,
    create_front_desk_agent,
)

load_dotenv()

def main() -> None:
    credential = DefaultAzureCredential()

    # Create specialized agents (We don't need triage wrapped in an Executor anymore)
    archivist_agent = create_archivist_agent(credential=credential)
    executive_agent = create_executive_agent(credential=credential)
    career_coach_agent = create_career_coach_agent(credential=credential)
    front_desk_agent = create_front_desk_agent(credential=credential)

    # Wrap only specialist agents inside target Executors
    archivist_agent_executor = AgentExecutor(archivist_agent, id="archivist_exec", context_mode="last_agent") # type: ignore
    executive_agent_executor = AgentExecutor(executive_agent, id="executive_exec", context_mode="last_agent") # type: ignore
    career_coach_agent_executor = AgentExecutor(career_coach_agent, id="career_coach_exec", context_mode="last_agent") # type: ignore
    front_desk_agent_executor = AgentExecutor(front_desk_agent, id="front_desk_exec", context_mode="last_agent") # type: ignore

    # Establish clean structural layout using programmatic routing
    workflow = (
        WorkflowBuilder(
            name="agent-cuhk-workflow",
            description="a workflow to take user request and respond accordingly with tools",
            start_executor=triage_and_route,  # Set your custom routing function as entrypoint!
        )
        
        # Expose topology paths out of your triage function to the specialized executors
        .add_edge(triage_and_route, archivist_agent_executor)
        .add_edge(triage_and_route, executive_agent_executor)
        .add_edge(triage_and_route, career_coach_agent_executor)
        .add_edge(triage_and_route, front_desk_agent_executor)
        
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
