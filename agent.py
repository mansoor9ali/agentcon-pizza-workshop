# Copyright (c) Microsoft. All rights reserved.

import asyncio

from agent_framework import HostedFileSearchTool
from agent_framework_declarative._models import FileSearchTool
from rich import print

from utils import create_openaichat_client


async def example_pizza_bot() -> None:
    # Create the File Search tool
    vector_store_id = "vs_693a0172458481919d9cb08a21ca0ce7"
    file_search = HostedFileSearchTool(vectorStoreIds=[vector_store_id])

    agent = create_openaichat_client().create_agent(
        name="pizza-bot",
        instructions=open("instructions.txt").read(),
        top_p=0.7,
        temperature=0.7,
        tools=file_search,
    )

    query = "Which Contoso Pizza stores are open after 8pm?"
    print(f"User: {query}")
    result = await agent.run(query)
    print(f"Result: {result}\n")


async def main() -> None:
    await  example_pizza_bot()



if __name__ == "__main__":
    asyncio.run(main())