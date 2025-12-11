"""
Contoso Pizza Bot Agent
A conversational AI agent for pizza ordering and store information.
"""
import asyncio
import os
from pathlib import Path

from agent_framework import HostedFileSearchTool, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIResponsesClient
from dotenv import load_dotenv
from rich import print

from add_data import create_vector_store, load_cached_vector_store
from tools import calculate_pizza_for_people

# Load environment variables once at module level
load_dotenv()

# Constants
INSTRUCTIONS_FILE = "instructions.txt"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.7


def create_openai_client() -> OpenAIResponsesClient:
    """
    Create and configure the OpenAI Responses client.

    Returns:
        OpenAIResponsesClient: Configured client instance

    Raises:
        ValueError: If required environment variables are missing
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_id = os.getenv("OPENAI_MODEL_ID")

    if not all([api_key, base_url, model_id]):
        raise ValueError(
            "Missing required environment variables: "
            "OPENAI_API_KEY, OPENAI_BASE_URL, or OPENAI_MODEL_ID"
        )

    return OpenAIResponsesClient(
        api_key=api_key,
        base_url=base_url,
        model_id=model_id,
    )


async def get_or_create_vector_store(client: OpenAIResponsesClient):
    """
    Get cached vector store or create a new one.

    Args:
        client: OpenAI Responses client instance

    Returns:
        Tuple of (file_ids, vector_store)
    """
    cached = load_cached_vector_store()

    if cached:
        print("\n📦 Using cached vector store...")
        file_ids, vector_store = cached
    else:
        print("\n🔨 Creating new vector store...")
        file_ids, vector_store = await create_vector_store(client)

    print(f"✅ Vector store ready (ID: {vector_store.vector_store_id})\n")
    return file_ids, vector_store


def load_instructions(file_path: str = INSTRUCTIONS_FILE) -> str:
    """
    Load agent instructions from file.

    Args:
        file_path: Path to the instructions file

    Returns:
        Instructions text

    Raises:
        FileNotFoundError: If instructions file doesn't exist
    """
    instructions_path = Path(file_path)
    if not instructions_path.exists():
        raise FileNotFoundError(f"Instructions file not found: {file_path}")

    return instructions_path.read_text(encoding="utf-8")


def create_pizza_agent(
    client: OpenAIResponsesClient,
    vector_store,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P
):
    """
    Create the pizza bot agent with configured tools.

    Args:
        client: OpenAI Responses client instance
        vector_store: Vector store for file search
        temperature: Sampling temperature for responses
        top_p: Nucleus sampling parameter
        use_mcp: Whether to include MCP tool (None=auto-detect from env, True=force enable, False=disable)

    Returns:
        Configured agent instance
    """
    # Start with basic tools
    tools = [
        HostedFileSearchTool(inputs=vector_store),
        calculate_pizza_for_people,
    ]

    return client.create_agent(
        name="pizza-bot",
        instructions=load_instructions(),
        temperature=temperature,
        top_p=top_p,
        tools=tools,
    )


def get_mcp_tool(use_mcp: bool | None)-> MCPStreamableHTTPTool | None:
    # Auto-detect MCP usage from environment if not specified
    if use_mcp is None:
        use_mcp = os.getenv("ENABLE_MCP", "false").lower() in ["true", "1", "yes"]

    # Add MCP tool if enabled
    if use_mcp:
        try:
            print("🔌 Attempting to configure MCP tool...")

            # Get MCP URL from environment or use default
            mcp_url = os.getenv(
                "MCP_URL",
                "https://ca-pizza-mcp-sc6u2typoxngc.graypond-9d6dd29c.eastus2.azurecontainerapps.io/sse"
            )

            # Optionally include an Authorization header from environment variable MCP_API_TOKEN.
            mcp_headers = {}
            mcp_token = os.getenv("MCP_API_TOKEN")
            if mcp_token:
                mcp_headers["Authorization"] = f"Bearer {mcp_token}"

            mcp_tool = MCPStreamableHTTPTool(
                name="contoso_pizza_mcp",
                url=mcp_url,
                headers=mcp_headers if mcp_headers else None,
                allowed_tools=[
                    "get_pizzas",
                    "get_pizza_by_id",
                    "get_toppings",
                    "get_topping_by_id",
                    "get_topping_categories",
                    "get_orders",
                    "get_order_by_id",
                    "place_order",
                    "delete_order_by_id",
                ],
            )
            mcp_tool.approval_mode = "never_require"
            print(f"✅ MCP tool configured successfully (URL: {mcp_url})")

            return mcp_tool

        except Exception as e:
            print(f"⚠️  Warning: Could not configure MCP tool: {e}")
            print("   Continuing with basic tools only (vector search + pizza calculator)")
    return None


async def stream_agent_response(agent, query: str,mcp_tool: MCPStreamableHTTPTool) -> None:
    """
    Stream agent response to console.

    Args:
        agent: Agent instance
        query: User query
        mcp_tool: MCP tool instance
        :param agent:
        :param query:
        :param mcp_tool:
    """
    print(f"User: {query}")
    print("Assistant: ", end="", flush=True)

    async for chunk in agent.run_stream(query,tools=mcp_tool):
        if chunk.text:
            print(chunk.text, end="", flush=True)

    print("\n")


async def run_pizza_bot_demo(use_mcp: bool = None) -> None:
    """
    Run the pizza bot demonstration with test queries.

    Args:
        use_mcp: Whether to enable MCP tools
                 - None (default): Auto-detect from ENABLE_MCP environment variable
                 - True: Force enable MCP
                 - False: Disable MCP
    """
    try:
        print("🍕 Starting Contoso Pizza Bot Demo")
        print("=" * 60)

        # Initialize client and vector store
        client = create_openai_client()
        file_ids, vector_store = await get_or_create_vector_store(client)

        # Create agent with or without MCP
        agent = create_pizza_agent(client, vector_store)

        print("=" * 60)
        print("🤖 Agent ready! Running demo queries...\n")

        # Test queries
        queries = [
            "Show me the available pizzas.",
            "Hi My Name is John, living in New york and my UserId is U123. Show me the available pizzas.",
            "I'm having a party with 10 people who are very hungry. "
            "How much pizza should I order?",
            "Can you give me directions to the nearest Contoso Pizza store from 123 Main St, New York, NY?",
            "What are the most popular pizza toppings at Contoso Pizza?",
            "price of a large pepperoni pizza in Contoso Pizza?",
        ]

        mcp_tool = get_mcp_tool(use_mcp=use_mcp)
        # Process each query
        for query in queries:
            await stream_agent_response(agent, query,mcp_tool)

    except Exception as e:
        print(f"❌ Error running pizza bot: {e}")
        raise


async def interactive_mode(agent) -> None:
    """
    Run interactive chat mode with the agent.

    Args:
        agent: Agent instance
    """
    print("\n💬 Interactive mode (type 'exit' to quit)")
    print("=" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            print("Assistant: ", end="", flush=True)
            async for chunk in agent.run_stream(user_input):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print()

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main() -> None:
    """Main entry point."""
    # Run pizza bot demo with MCP enabled
    await run_pizza_bot_demo(True)


if __name__ == "__main__":
    asyncio.run(main())