# Copyright (c) Microsoft. All rights reserved.

import logging
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

import asyncio
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential


async def multi_tool_mcp_example():
    """Example using multiple hosted MCP tools."""
    async with AzureCliCredential() as credential:
        client = FoundryChatClient(credential=credential)
        # Create multiple MCP tools using the client method
        learn_mcp = client.get_mcp_tool(
            name="Microsoft Learn MCP",
            url="https://learn.microsoft.com/api/mcp",
            approval_mode="never_require",  # Auto-approve documentation searches
        )
        github_mcp = client.get_mcp_tool(
            name="GitHub MCP",
            url="https://api.githubcopilot.com/mcp/",
            approval_mode="always_require",  # Require approval for GitHub operations
            headers={"Authorization": "Bearer github-token"},
        )

        # Create agent with multiple MCP tools
        async with Agent(
            client=client,
            name="MultiToolAgent",
            instructions="You can search documentation and access GitHub repositories.",
            tools=[learn_mcp, github_mcp],
        ) as agent:
            result = await agent.run(
                "Find Azure documentation and also check the latest commits in microsoft/semantic-kernel"
            )
            print(result.text)


if __name__ == "__main__":
    asyncio.run(multi_tool_mcp_example())











async def basic_foundry_mcp_example():
    """Basic example of Foundry agent with hosted MCP tools."""
    async with AzureCliCredential() as credential:
        client = FoundryChatClient(credential=credential)
        # Create a hosted MCP tool using the client method
        learn_mcp = client.get_mcp_tool(
            name="Microsoft Learn MCP",
            url="https://learn.microsoft.com/api/mcp",
        )

        # Create agent with hosted MCP tool
        async with Agent(
            client=client,
            name="MicrosoftLearnAgent",
            instructions="You answer questions by searching Microsoft Learn content only.",
            tools=[learn_mcp],
        ) as agent:
            # Simple query without approval workflow
            result = await agent.run(
                "Please summarize the Azure AI Agent documentation related to MCP tool calling?"
            )
            print(result.text)


if __name__ == "__main__":
    asyncio.run(basic_foundry_mcp_example())
