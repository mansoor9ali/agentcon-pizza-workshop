import os
import sys

from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv
from foundry_local import FoundryLocalManager
from foundry_local.models import DeviceType

if sys.version_info >= (3, 11):
    from enum import StrEnum

#create enum for modal types
class ModelAlias(StrEnum):
    """Enumeration of devices supported by the model."""
    DEEPSEEK_R1_14B = "deepseek-r1-14b"
    PHi_4_MINI="phi-4-mini"
    QWEN25_14B= "qwen2.5-14b"

# Load environment variables from .env file
load_dotenv()


# python
def create_foundrylocal_client() -> OpenAIChatClient:
    """
    Create and return an OpenAIChatClient instance for Foundry Local.

    Returns:
        OpenAIChatClient: Configured OpenAI chat client for Foundry Local
    """
    manager = FoundryLocalManager(device=DeviceType.CPU)

    # Set Foundry Local environment variables
    os.environ["FOUNDARYLOCAL_API_KEY"] = manager.api_key
    os.environ["FOUNDARYLOCAL_BASE_URL"] = manager.endpoint
    model_info = manager.get_model_info(os.getenv("FOUNDARYLOCAL_MODEL_ID"), device=DeviceType.CPU)
    os.environ["FOUNDARYLOCAL_MODEL_ID"] = model_info.id

    print("✅ Foundry Local client configured:")
    print(f"   - Endpoint: {manager.endpoint}")
    print(f"   - Model ID: {model_info.id}")

    # Return the project's OpenAIChatClient wrapper configured for Foundry Local
    return OpenAIChatClient(
        api_key=manager.api_key,
        base_url=manager.endpoint,
        model_id=model_info.id,
    )

def create_synthetic_client() -> OpenAIChatClient:
    """
    Create and return an OpenAIChatClient instance with environment variables.

    Returns:
        OpenAIChatClient: Configured OpenAI chat client
    """
    return OpenAIChatClient(
        api_key=os.getenv("SYNTHETIC_API_KEY"),
        base_url=os.getenv("SYNTHETIC_BASE_URL"),
        model_id=os.getenv("SYNTHETIC_MODEL_ID"),
    )

def create_openaichat_client() -> OpenAIChatClient:
    """
    Create and return an OpenAIChatClient instance with environment variables.

    Returns:
        OpenAIChatClient: Configured OpenAI chat client
    """
    return OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model_id=os.getenv("OPENAI_MODEL_ID"),
    )

def create_deepseek_client() -> OpenAIChatClient:
    """
    Create and return an OpenAIChatClient instance with environment variables.

    Returns:
        OpenAIChatClient: Configured OpenAI chat client
    """
    return OpenAIChatClient(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        model_id=os.getenv("DEEPSEEK_MODEL_ID"),
    )
