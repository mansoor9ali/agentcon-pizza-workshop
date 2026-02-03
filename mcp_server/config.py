"""
Configuration module for Contoso Pizza MCP Server.
Loads environment variables for database and server configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""
    host: str
    port: int
    database: str
    user: str
    password: str
    min_pool_size: int = 5
    max_pool_size: int = 20

    @property
    def dsn(self) -> str:
        """Get the database connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class ServerConfig:
    """MCP Server configuration."""
    name: str = "Contoso Pizza MCP Server"
    transport: str = "stdio"
    host: str = "0.0.0.0"
    port: int = 8366


@dataclass
class AuthConfig:
    """Authentication configuration."""
    enabled: bool = False
    auth_type: str = "NONE"  # JWT, BEARER, APIKEY, or NONE

    # JWT settings
    jwt_jwks_uri: Optional[str] = None
    jwt_issuer: Optional[str] = None
    jwt_audience: Optional[str] = None
    jwt_required_scopes: list[str] = field(default_factory=list)

    # Bearer token settings
    bearer_token: Optional[str] = None

    # API key settings
    api_keys: list[str] = field(default_factory=list)
    api_key_header: str = "X-API-Key"  # Header name for API key


def get_database_config() -> DatabaseConfig:
    """Get database configuration from environment variables."""
    return DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DATABASE", "mcp_abc_pizza_db"),
        user=os.getenv("POSTGRES_USER", "user-name"),
        password=os.getenv("POSTGRES_PASSWORD", "strong-password"),
        min_pool_size=int(os.getenv("DB_MIN_POOL_SIZE", "5")),
        max_pool_size=int(os.getenv("DB_MAX_POOL_SIZE", "20")),
    )


def get_server_config() -> ServerConfig:
    """Get server configuration from environment variables."""
    return ServerConfig(
        name=os.getenv("MCP_SERVER_NAME", "Contoso Pizza MCP Server"),
        transport=os.getenv("MCP_TRANSPORT", "stdio"),
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "8366")),
    )


def get_auth_config() -> AuthConfig:
    """Get authentication configuration from environment variables."""
    # Parse required scopes from comma-separated string
    scopes_str = os.getenv("AUTH_JWT_REQUIRED_SCOPES", "")
    scopes = [s.strip() for s in scopes_str.split(",") if s.strip()]

    # Parse API keys from comma-separated string
    api_keys_str = os.getenv("AUTH_API_KEYS", "")
    api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]

    return AuthConfig(
        enabled=os.getenv("AUTH_ENABLED", "false").lower() == "true",
        auth_type=os.getenv("AUTH_TYPE", "NONE").upper(),
        jwt_jwks_uri=os.getenv("AUTH_JWT_JWKS_URI"),
        jwt_issuer=os.getenv("AUTH_JWT_ISSUER"),
        jwt_audience=os.getenv("AUTH_JWT_AUDIENCE"),
        jwt_required_scopes=scopes,
        bearer_token=os.getenv("AUTH_BEARER_TOKEN"),
        api_keys=api_keys,
        api_key_header=os.getenv("AUTH_API_KEY_HEADER", "X-API-Key"),
    )


# Export singleton configs
db_config = get_database_config()
server_config = get_server_config()
auth_config = get_auth_config()
