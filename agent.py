# Copyright (c) Microsoft. All rights reserved.

import asyncio

from agent_framework import HostedFileSearchTool
from rich import print

from add_data import create_vector_store, load_cached_vector_store
from utils import create_openaichat_client


async def example_pizza_bot() -> None:
    # Try to load cached vector store first

    client=create_openaichat_client()
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
        tools=HostedFileSearchTool(inputs=vector_store),
    )

    query = "Hi My Name is John , living in New york and my UserId is U123. Which Contoso Pizza stores are open after 8pm?"
    print(f"User: {query}")
    result = await agent.run(query)
    print(f"Result: {result}\n")


async def main() -> None:
    await  example_pizza_bot()



if __name__ == "__main__":
    asyncio.run(main())