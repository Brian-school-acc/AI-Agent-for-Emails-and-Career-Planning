import asyncio
from msgraph import GraphServiceClient
from azure.identity.aio import DefaultAzureCredential
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient


# 1. Create a function tool that calls the MS Graph API
async def get_unread_emails(top: int = 5) -> str:
    """Fetches the latest unread emails for the authenticated user from Microsoft Graph."""
    scopes = ["https://graph.microsoft.com/.default"]

    # Leverages managed identity or local Azure CLI auth
    credential = DefaultAzureCredential()
    client = GraphServiceClient(credential, scopes)

    try:
        # Call MS Graph API: /me/messages?$filter=isRead eq false
        query_params = {"filter": "isRead eq false", "top": top}
        messages = await client.me.messages.get(
            request_configuration={"query_parameters": query_params}
        )

        if not messages.value:
            return "No unread emails."

        # Format the response so the LLM can easily read it
        formatted_msgs = []
        for msg in messages.value:
            formatted_msgs.append(
                f"- From: {msg.sender.email_address.name}, Subject: {msg.subject}"
            )

        return "\n".join(formatted_msgs)

    except Exception as e:
        return f"Failed to retrieve emails: {str(e)}"


async def main():
    # 2. Attach your Graph API wrapper as a standard tool
    async with DefaultAzureCredential() as credential:
        client = FoundryChatClient(credential=credential)

        async with Agent(
            client=client,
            name="GraphAssistant",
            instructions="You are an assistant that manages the user's emails.",
            tools=[get_unread_emails],  # MS Graph wrapped tool injected here
        ) as agent:

            result = await agent.run("Can you check if I have any unread emails?")
            print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
