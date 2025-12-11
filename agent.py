"""
Contoso Pizza Bot Agent
A conversational AI agent for pizza ordering and store information.
"""
import asyncio
import os
from pathlib import Path

from agent_framework import HostedFileSearchTool
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

    Returns:
        Configured agent instance
    """
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


async def stream_agent_response(agent, query: str) -> None:
    """
    Stream agent response to console.

    Args:
        agent: Agent instance
        query: User query
    """
    print(f"User: {query}")
    print("Assistant: ", end="", flush=True)

    async for chunk in agent.run_stream(query):
        if chunk.text:
            print(chunk.text, end="", flush=True)

    print("\n")


async def run_pizza_bot_demo() -> None:
    """
    Run the pizza bot demonstration with test queries.
    """
    try:
        # Initialize client and vector store
        client = create_openai_client()
        file_ids, vector_store = await get_or_create_vector_store(client)

        # Create agent
        agent = create_pizza_agent(client, vector_store)

        # Test queries
        queries = [
            "Hi My Name is John, living in New york and my UserId is U123. "
            "Which Contoso Pizza stores are open after 8pm?",

            "I'm having a party with 10 people who are very hungry. "
            "How much pizza should I order?",
        ]

        # Process each query
        for query in queries:
            await stream_agent_response(agent, query)

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
    await run_pizza_bot_demo()


if __name__ == "__main__":
    asyncio.run(main())