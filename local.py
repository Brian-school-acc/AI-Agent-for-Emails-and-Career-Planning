import asyncio
from agent_framework import (
    AgentExecutor,
    WorkflowBuilder,
)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Ensure your predefined agents are imported correctly
from predefined_agents import (
    triage_and_route,
    create_archivist_agent,
    create_executive_agent,
    create_career_coach_agent,
    create_front_desk_agent,
)

load_dotenv()


async def chat_loop(workflow_agent):
    """
    A simple command-line chat interface to test the workflow locally without streaming.
    """
    print("\n" + "=" * 50)
    print("🚀 Local Student Success Workflow Started.")
    print("Type 'exit' or 'quit' to end the session.")
    print("=" * 50 + "\n")

    while True:
        try:
            user_input = input("\nStudent: ")

            if user_input.strip().lower() in ["exit", "quit"]:
                print("\nShutting down local workflow...")
                break

            if not user_input.strip():
                continue

            print("\nProcessing routing & agent response... (Please wait)\n")

            # Use .run() to wait for the complete response block
            result = await workflow_agent.run(user_input)

            print(f"Assistant:\n{result}")

        except KeyboardInterrupt:
            print("\nShutting down local workflow...")
            break
        except Exception as e:
            print(f"\n[Error during execution]: {e}")


async def main() -> None:
    # 1. Initialize credentials (still needed if your agents call Azure OpenAI/Search)
    credential = DefaultAzureCredential()

    # 2. Create specialized agents
    archivist_agent = await create_archivist_agent(credential=credential)
    executive_agent = await create_executive_agent(credential=credential)
    career_coach_agent = await create_career_coach_agent(credential=credential)
    front_desk_agent = await create_front_desk_agent(credential=credential)

    # 3. Wrap specialist agents inside target Executors
    # type: ignore is kept from your original code if your linter flags it
    archivist_agent_executor = AgentExecutor(archivist_agent, id="archivist_exec", context_mode="full")  # type: ignore
    executive_agent_executor = AgentExecutor(executive_agent, id="executive_exec", context_mode="full")  # type: ignore
    career_coach_agent_executor = AgentExecutor(career_coach_agent, id="career_coach_exec", context_mode="full")  # type: ignore
    front_desk_agent_executor = AgentExecutor(front_desk_agent, id="front_desk_exec", context_mode="full")  # type: ignore

    # 4. Establish clean structural layout using programmatic routing
    workflow = (
        WorkflowBuilder(
            name="agent-cuhk-workflow",
            description="a workflow to take user request and respond accordingly with tools",
            start_executor=triage_and_route,  # Custom routing function as entrypoint
        )
        # Expose topology paths out of your triage function to the specialized executors
        .add_edge(triage_and_route, archivist_agent_executor)
        .add_edge(triage_and_route, executive_agent_executor)
        .add_edge(triage_and_route, career_coach_agent_executor)
        .add_edge(triage_and_route, front_desk_agent_executor)
        .build()
        .as_agent()
    )

    # 5. Start the local chat loop
    await chat_loop(workflow)


if __name__ == "__main__":
    # In a local environment without a web server, we manage the async event loop directly
    asyncio.run(main())
