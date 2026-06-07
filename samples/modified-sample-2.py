# Copyright (c) Microsoft. All rights reserved.

import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

from agent_framework import Agent, AgentExecutor, WorkflowBuilder
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from agent_framework._workflows._checkpoint import FileCheckpointStorage

# Load environment variables from .env file
load_dotenv()

checkpoint_storage = FileCheckpointStorage(
    "/.checkpoints",
    allowed_checkpoint_types=[
        "azure.ai.agentserver.responses.models._generated.sdk.models.models._enums:MessageRole",
    ],
)

def main():
    # Initialize the Azure AI Foundry Client
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )

    # 1. 🎯 Master Orchestrator Agent
    orchestrator_agent = Agent(
        client=client,
        instructions=(
            "You are the Master Orchestrator for Student Success. "
            "Your job is to greet the student, analyze their intent/demand, and route "
            "tasks to the specialized worker agents (Archivist, Executive, Career Coach). "
            "Summarize what needs to be done for the next agent."
        ),
        name="master_orchestrator",
    )

    # 2. 📚 The Archivist Agent
    archivist_agent = Agent(
        client=client,
        instructions=(
            "You are The Archivist. Your role is to handle tasks related to emails, "
            "college updates, deadlines, and SharePoint data. Extract critical info and "
            "categorize it logically."
        ),
        name="the_archivist",
    )

    # 3. 📅 The Executive Agent
    executive_agent = Agent(
        client=client,
        instructions=(
            "You are The Executive. Your role is to handle automated time management, "
            "calendar time-blocking, task lists, and workflow tracking."
        ),
        name="the_executive",
    )

    # 4. 💼 The Career Coach Agent
    career_agent = Agent(
        client=client,
        instructions=(
            "You are The Career Coach. Your role is to guide professional readiness, "
            "optimize resumes, map workplace simulations, and provide career drafting."
        ),
        name="the_career_coach",
    )

    # EXECUTORS: Switch context_mode to "full" so your workers have 
    # access to what the user originally asked, instead of just the last turn.
    orchestrator_executor = AgentExecutor(orchestrator_agent, context_mode="full")
    archivist_executor = AgentExecutor(archivist_agent, context_mode="full")
    executive_executor = AgentExecutor(executive_agent, context_mode="full")
    career_executor = AgentExecutor(career_agent, context_mode="full")

    # 🏆 Hackathon Winning Workflow Topology
    # Constructing a hub-and-spoke graph routing system matching your pitch example
    workflow_agent = (
        WorkflowBuilder(
            start_executor=orchestrator_executor,
            # We want the orchestrator or final worker response back to the client
            output_executors=[orchestrator_executor, archivist_executor, executive_executor, career_executor],
        )
        # Orchestrator routes out to workers based on detected student intent
        .add_edge(orchestrator_executor, archivist_executor)
        .add_edge(orchestrator_executor, executive_executor)
        .add_edge(orchestrator_executor, career_executor)

        
        # Workers can pass back to Orchestrator or run sequentially if needed
        .add_edge(archivist_executor, orchestrator_executor)  # E.g., Archivist finds deadline -> Executive blocks calendar
        .add_edge(executive_executor, orchestrator_executor)     # E.g., Executive sets timeline -> Career Coach generates draft
        .add_edge(career_executor, orchestrator_executor)
        
        .build()
        .as_agent()
    )

    # Run the hosted response server for Microsoft Teams integration
    server = ResponsesHostServer(workflow_agent)
    server.run()

if __name__ == "__main__":
    main()