import asyncio
from agent_framework import ChatAgent, MCPStreamableHTTPTool

from utils import create_openaichat_client


async def http_mcp_example():
    """Example using an HTTP-based MCP server."""
    async with (
        MCPStreamableHTTPTool(
            name="contoso_pizza",
            url="https://ca-pizza-mcp-sc6u2typoxngc.graypond-9d6dd29c.eastus2.azurecontainerapps.io/mcp",
            load_tools=True,
            approval_mode="never_require",
        ) as mcp_server,
        ChatAgent(
            chat_client=create_openaichat_client(),
            name="PizzaBot",
            instructions="You are PizzaBot, an AI assistant that helps users order pizza.",
        ) as agent,
    ):
        result = await agent.run(
            "What is the price for a pizza hawai?",
            tools=mcp_server
        )
        print(result)


if __name__ == "__main__":
    asyncio.run(http_mcp_example())