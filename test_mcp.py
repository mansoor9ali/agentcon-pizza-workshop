import asyncio
from agent_framework import ChatAgent, MCPStreamableHTTPTool

from utils import create_openaichat_client


async def list_mcp_tools():
    """List all available tools from the MCP server."""
    print("🔌 Connecting to MCP server...")
    print("=" * 80)

    async with MCPStreamableHTTPTool(
        name="contoso_pizza",
        url="https://ca-pizza-mcp-sc6u2typoxngc.graypond-9d6dd29c.eastus2.azurecontainerapps.io/mcp",
        load_tools=True,
        approval_mode="never_require",
    ) as mcp_server:
        print(f"✅ Connected to MCP server: {mcp_server.name}\n")

        # Try to get tools through the session
        if hasattr(mcp_server, 'session') and mcp_server.session:
            try:
                tools_result = await mcp_server.session.list_tools()
                tools = tools_result.tools if hasattr(tools_result, 'tools') else []
            except Exception as e:
                print(f"❌ Error listing tools through session: {e}")
                print(f"Session attributes: {dir(mcp_server.session)}")
                return
        elif hasattr(mcp_server, 'functions') and mcp_server.functions:
            # Try the functions attribute
            print(f"📋 Found {len(mcp_server.functions)} function(s) loaded:\n")
            for i, func in enumerate(mcp_server.functions, 1):
                print(f"{i}. Function: {func}")
                print("-" * 80)
            return
        else:
            print("❌ Unable to list tools from MCP server")
            print(f"Available attributes: {dir(mcp_server)}")
            return

        print(f"📋 Found {len(tools)} tool(s):\n")

        for i, tool in enumerate(tools, 1):
            print(f"{i}. Tool Name: {tool.name}")
            print(f"   Description: {tool.description if hasattr(tool, 'description') else 'No description'}")

            # Print input schema if available
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                schema = tool.inputSchema
                print(f"   Input Schema:")

                # Handle both dict and object types
                properties = None
                required_fields = []

                if isinstance(schema, dict):
                    properties = schema.get('properties', {})
                    required_fields = schema.get('required', [])
                elif hasattr(schema, 'properties'):
                    properties = schema.properties
                    required_fields = schema.required if hasattr(schema, 'required') else []

                if properties:
                    print(f"   Properties:")
                    for prop_name, prop_info in properties.items():
                        if isinstance(prop_info, dict):
                            prop_type = prop_info.get('type', 'unknown')
                            prop_desc = prop_info.get('description', 'No description')
                        else:
                            prop_type = getattr(prop_info, 'type', 'unknown')
                            prop_desc = getattr(prop_info, 'description', 'No description')

                        required = prop_name in required_fields
                        req_mark = "* (required)" if required else ""
                        print(f"     - {prop_name} ({prop_type}){req_mark}: {prop_desc}")
                else:
                    print(f"     (No parameters required)")

            print("-" * 80)


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
            "Place an order for 2 large pepperoni pizzas.",
            tools=mcp_server
        )
        print(result)


if __name__ == "__main__":
    # List all available MCP tools
    asyncio.run(list_mcp_tools())

    print("\n" + "=" * 80)
    print("Now running example order...\n")

    # Run the example
    # asyncio.run(http_mcp_example())
