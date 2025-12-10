import os
from dotenv import load_dotenv
import asyncio
from agent_framework import HostedVectorStoreContent, HostedFileSearchTool
from agent_framework.openai import OpenAIResponsesClient


# Load environment variables (expects PROJECT_CONNECTION_STRING in .env)
load_dotenv(override=True)


DOCS_DIR = "./documents"


async def create_vector_store(client: OpenAIResponsesClient) -> tuple[list[str], HostedVectorStoreContent]:
    """Upload local Contoso docs and build the vector store."""
    if not os.path.isdir(DOCS_DIR):
        raise FileNotFoundError(
            f"Documents folder not found at {DOCS_DIR}. "
            "Create it and add your Contoso Pizza files (PDF, TXT, MD, etc.)."
        )

    print(f"Uploading files from {DOCS_DIR} ...")
    file_ids: list[str] = []

    # Create vector store first
    vector_store = await client.client.vector_stores.create(
        name="contoso-pizza-store-information",
        expires_after={"anchor": "last_active_at", "days": 1},
    )
    print(f"Created vector store, ID: {vector_store.id}")

    # Upload and add each file to the vector store
    for fname in os.listdir(DOCS_DIR):
        fpath = os.path.join(DOCS_DIR, fname)
        if not os.path.isfile(fpath) or fname.startswith('.'):
            continue

        # Read file content
        with open(fpath, 'rb') as f:
            file_content = f.read()

        # Upload file
        uploaded_file = await client.client.files.create(
            file=(fname, file_content),
            purpose="user_data"
        )
        file_ids.append(uploaded_file.id)
        print(f"Uploaded {fname} with ID: {uploaded_file.id}")

        # Add file to vector store
        result = await client.client.vector_stores.files.create_and_poll(
            vector_store_id=vector_store.id,
            file_id=uploaded_file.id
        )
        if result.last_error is not None:
            raise Exception(f"Vector store file processing failed for {fname}: {result.last_error.message}")

    print(f"Uploaded {len(file_ids)} files.")
    if not file_ids:
        raise RuntimeError("No files uploaded. Put files in ./documents and re-run.")

    vector_store_content=HostedVectorStoreContent(vector_store_id=vector_store.id)
    return file_ids, vector_store_content


async def delete_vector_store(client: OpenAIResponsesClient, file_ids: list[str], vector_store_id: str) -> None:
    """Delete the vector store and uploaded files."""
    await client.client.vector_stores.delete(vector_store_id=vector_store_id)
    for file_id in file_ids:
        await client.client.files.delete(file_id=file_id)


async def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_id = os.getenv("OPENAI_MODEL_ID")


    print(f"Using API endpoint: {base_url}")
    print(f"Note: Vector stores require OpenAI API or Azure OpenAI with Assistants API support")
    print()

    client = OpenAIResponsesClient(
        api_key=api_key,
        base_url=base_url,
        model_id=model_id,
    )

    stream = False

    try:
        file_ids, vector_store = await create_vector_store(client)
        print("Vector store details:")
        print(f" - ID: {vector_store.vector_store_id}")
        print("Vector store created successfully.")

    except Exception as e:
        print(f"\n❌ Error creating vector store: {e}")
        print("\n💡 Solution:")
        print("   Vector stores are an OpenAI Assistants API feature.")
        print("   1. Get a real OpenAI API key from https://platform.openai.com/api-keys")
        print("   2. Update .env file:")
        print("      OPENAI_API_KEY=sk-your-real-openai-key")
        print("      OPENAI_BASE_URL=https://api.openai.com/v1")
        print("      OPENAI_MODEL_ID=gpt-4o-mini")
        print("\n   OR use Azure OpenAI with proper Assistants API configuration")
        return


    agent = client.create_agent(
        name="pizza-bot",
        instructions=open("instructions.txt").read(),
        top_p=0.7,
        temperature=0.7,
        tools=HostedFileSearchTool(vectorStoreIds=[vector_store.vector_store_id]),
    )

    message = "Which Contoso Pizza stores are open after 8pm?"
    print(f"User: {message}")
    if stream:
        print("Assistant: ", end="")
        async for chunk in agent.run_stream(message):
            if chunk.text:
                print(chunk.text, end="")
        print("")
    else:
        response = await agent.run(message)
        print(f"Assistant: {response}")

    #await delete_vector_store(client, file_ids, vector_store.vector_store_id)


if __name__ == "__main__":
    asyncio.run(main())