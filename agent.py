# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from agent_framework import HostedFileSearchTool
from agent_framework.openai import OpenAIResponsesClient
from dotenv import load_dotenv
from rich import print

from add_data import create_vector_store, load_cached_vector_store
from tools import calculate_pizza_for_people

load_dotenv()


async def example_pizza_bot() -> None:
    # Create OpenAI Responses client
    client = OpenAIResponsesClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model_id=os.getenv("OPENAI_MODEL_ID"),
    )

    # Try to load cached vector store first
    cached = load_cached_vector_store()

    if cached:
        print("\n📦 Using cached vector store...")
        file_ids, vector_store = cached
    else:
        print("\n🔨 Creating new vector store...")
        file_ids, vector_store = await create_vector_store(client)

    print("Vector store details:")
    print(f" - ID: {vector_store.vector_store_id}")
    print("Vector store ready for use.")


    agent = client.create_agent(
        name="pizza-bot",
        instructions=open("instructions.txt").read(),
        top_p=0.7,
        temperature=0.7,
        tools=[HostedFileSearchTool(inputs=vector_store), calculate_pizza_for_people],
    )

    query = "Hi My Name is John, living in New york and my UserId is U123. Which Contoso Pizza stores are open after 8pm?"
    print(f"User: {query}")
    print("Assistant: ", end="")

    # Use streaming to see the agent's response as it's generated
    async for chunk in agent.run_stream(query):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print("\n")


async def main() -> None:
    await  example_pizza_bot()



if __name__ == "__main__":
    asyncio.run(main())