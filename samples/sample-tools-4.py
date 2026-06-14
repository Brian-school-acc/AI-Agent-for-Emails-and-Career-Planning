# Copyright (c) Microsoft. All rights reserved.

import asyncio

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

"""
OpenAI Responses Client with Web Search Example

This sample demonstrates using get_web_search_tool() with OpenAI Responses Client
for direct real-time information retrieval and current data access.
"""


async def main() -> None:
    client = OpenAIChatClient(
        model="gpt-4o",
        api_key="CL4c9QN20wWinNW625aMG8rIW7sy8VA9mQk5r0USKds3mNGtvEzEJQQJ99CFACrIdLPXJ3w3AAAAACOGQGUg",
        base_url="https://1155236599-1444-resource.openai.azure.com/openai/v1"
    )

    # Create web search tool with location context
    web_search_tool = client.get_web_search_tool(
        user_location={"city": "Seattle", "region": "US"},
    )

    agent = Agent(
        client=client,
        instructions="You are a helpful assistant that can search the web for current information.",
        tools=[web_search_tool],
    )

    message = "What is the current weather? Do not ask for my current location."
    stream = False
    print(f"User: {message}")

    if stream:
        print("Assistant: ", end="")
        async for chunk in agent.run(message, stream=True):
            if chunk.text:
                print(chunk.text, end="")
        print("")
    else:
        response = await agent.run(message)
        print(f"Assistant: {response}")


if __name__ == "__main__":
    asyncio.run(main())
