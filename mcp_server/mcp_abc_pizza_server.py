"""
ABC Pizza MCP Server
========================
A FastMCP 3 server providing tools for pizza ordering, menu browsing,
store locations, and promotional offers.

Supports token-based authentication:
- JWT: Validate tokens using JWKS endpoint (recommended for production)
- BEARER: Simple static bearer token validation (for development/testing)

MCP Tools:
- get_pizzas: List all pizzas
- get_pizza_by_id: Get pizza details
- get_toppings: List toppings (optional category filter)
- get_topping_by_id: Get topping details
- get_topping_categories: List topping categories
- get_orders: List orders with filters
- get_order_by_id: Get order details
- place_order: Create new order
- delete_order_by_id: Cancel pending order
- get_store_locations: List store locations
- get_active_offers: List current promotions
- notify_menu_update: Admin tool to notify clients of menu changes
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional
import json
import sys

from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_access_token, get_context, AccessToken
from pydantic import BaseModel, Field
import mcp.types as mcp_types  # Import MCP types for notifications

# Handle imports for both standalone execution and package import
try:
    from .database import Database
    from .config import server_config, auth_config
except ImportError:
    from database import Database
    from config import server_config, auth_config


# ============================================================================
# SAFE PRINT FUNCTION (handles encoding issues on Windows)
# ============================================================================

def safe_print(*args, **kwargs):
    """Print that handles encoding errors gracefully (for Windows console)."""
    # When running in stdio mode, print to stderr to not interfere with MCP protocol
    file = kwargs.pop('file', sys.stderr)
    try:
        print(*args, file=file, **kwargs)
    except UnicodeEncodeError:
        # Replace problematic characters with ASCII alternatives
        text = " ".join(str(arg) for arg in args)
        # Replace common emoji with ASCII
        text = text.replace("🔐", "[AUTH]")
        text = text.replace("🔓", "[OPEN]")
        text = text.replace("⚠️", "[WARN]")
        text = text.replace("🍕", "[PIZZA]")
        text = text.replace("✅", "[OK]")
        text = text.replace("👋", "[BYE]")
        text = text.replace("🚀", "[START]")
        text = text.replace("📡", "[NET]")
        print(text, file=file, **kwargs)


# ============================================================================
# AUTHENTICATION SETUP
# ============================================================================

def create_auth_provider():
    """Create authentication provider based on configuration."""
    if not auth_config.enabled:
        safe_print("🔓 Authentication: DISABLED")
        return None

    auth_type = auth_config.auth_type.upper()

    if auth_type == "JWT":
        from fastmcp.server.auth.providers.jwt import JWTVerifier

        safe_print(f"🔐 Authentication: JWT")
        safe_print(f"   JWKS URI: {auth_config.jwt_jwks_uri}")
        safe_print(f"   Issuer: {auth_config.jwt_issuer}")
        safe_print(f"   Audience: {auth_config.jwt_audience}")

        return JWTVerifier(
            jwks_uri=auth_config.jwt_jwks_uri,
            issuer=auth_config.jwt_issuer,
            audience=auth_config.jwt_audience,
            required_scopes=auth_config.jwt_required_scopes if auth_config.jwt_required_scopes else None,
        )

    elif auth_type == "BEARER" or auth_type == "APIKEY":
        from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

        # For BEARER auth, use the single bearer token
        # For APIKEY auth, use the list of API keys
        if auth_type == "BEARER":
            if not auth_config.bearer_token:
                safe_print("⚠️  WARNING: BEARER auth enabled but no token configured!")
                return None

            safe_print(f"🔐 Authentication: BEARER (static token)")
            tokens = {
                auth_config.bearer_token: {
                    "client_id": "bearer-client",
                    "scopes": ["pizza:read", "pizza:write", "pizza:admin"]
                }
            }
        else:  # APIKEY
            if not auth_config.api_keys:
                safe_print("⚠️  WARNING: APIKEY auth enabled but no keys configured!")
                return None

            safe_print(f"🔐 Authentication: API Key")
            safe_print(f"   Valid keys configured: {len(auth_config.api_keys)}")

            # Create token map from API keys
            tokens = {}
            for i, key in enumerate(auth_config.api_keys):
                tokens[key] = {
                    "client_id": f"api-key-client-{i+1}",
                    "scopes": ["pizza:read", "pizza:write"]
                }

        return StaticTokenVerifier(tokens=tokens)

    else:
        safe_print(f"🔓 Authentication: NONE (type={auth_type})")
        return None


# Create auth provider
auth_provider = create_auth_provider()


# ============================================================================
# APPLICATION CONTEXT (Lifespan)
# ============================================================================

@dataclass
class AppContext:
    """Application context with typed dependencies."""
    db: Database


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    safe_print("🍕 Starting ABC Pizza MCP Server...")

    # Initialize database connection pool on startup
    db = await Database.connect()
    safe_print("✅ Database connection pool established")

    try:
        yield AppContext(db=db)
    finally:
        # Cleanup on shutdown
        await db.disconnect()
        safe_print("👋 Database connection pool closed")


# ============================================================================
# MCP SERVER INITIALIZATION
# ============================================================================

mcp = FastMCP(
    name=server_config.name,
    lifespan=app_lifespan,
    auth=auth_provider,  # Add authentication if configured
)


# ============================================================================
# INPUT MODELS FOR TOOLS
# ============================================================================

class OrderItemInput(BaseModel):
    """Input model for an order item."""
    pizza_id: str = Field(..., description="ID of the pizza to order")
    size: str = Field(default="medium", description="Size: small, medium, large, extra-large")
    quantity: int = Field(default=1, ge=1, description="Number of pizzas")
    toppings: list[str] = Field(default_factory=list, description="List of additional topping IDs")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db(ctx: Context) -> Database:
    """Get database instance from context parameter."""
    return ctx.request_context.lifespan_context.db


def get_db_from_context() -> Database:
    """
    Get database instance using runtime dependency.

    This is useful for utility functions that don't receive Context as parameter.
    Must be called within a request context (e.g., inside a tool function).
    """
    ctx = get_context()
    return ctx.request_context.lifespan_context.db


def get_authenticated_user() -> Optional[dict]:
    """
    Get authenticated user information from access token.

    Returns dict with user info if authenticated, None otherwise.
    """
    token: AccessToken | None = get_access_token()

    if token is None:
        return None

    return {
        "client_id": token.client_id,
        "scopes": token.scopes,
        "expires_at": str(token.expires_at) if token.expires_at else None,
        "user_id": token.claims.get("sub") if token.claims else None,
        "claims": token.claims,
    }


# ============================================================================
# AUTHENTICATION TOOLS
# ============================================================================

@mcp.tool
async def get_auth_info() -> str:
    """
    Get information about the current authentication status.

    Returns authentication status and user information if authenticated.
    Useful for debugging and verifying token validation.
    """
    user = get_authenticated_user()

    if user is None:
        return json.dumps({
            "authenticated": False,
            "message": "No authentication token provided or authentication is disabled"
        }, indent=2)

    return json.dumps({
        "authenticated": True,
        "client_id": user.get("client_id"),
        "user_id": user.get("user_id"),
        "scopes": user.get("scopes"),
        "expires_at": user.get("expires_at"),
    }, indent=2)


# ============================================================================
# PIZZA TOOLS
# ============================================================================

@mcp.tool
async def get_pizzas(ctx: Context) -> str:
    """
    Get a list of all pizzas in the menu.

    Returns a JSON array of available pizzas with their names, descriptions,
    sizes with prices, and availability status.
    """
    db = get_db(ctx)
    pizzas = await db.get_all_pizzas()
    return json.dumps(pizzas, indent=2)


@mcp.tool
async def get_pizza_by_id(ctx: Context, id: str) -> str:
    """
    Get a specific pizza by its ID.

    Args:
        id: The unique identifier of the pizza to retrieve

    Returns the pizza details including name, description, available sizes
    with prices, and availability status.
    """
    db = get_db(ctx)
    pizza = await db.get_pizza_by_id(id)

    if pizza is None:
        return json.dumps({"error": "Pizza not found", "id": id})

    return json.dumps(pizza, indent=2)


# ============================================================================
# TOPPING TOOLS
# ============================================================================

@mcp.tool
async def get_toppings(ctx: Context, category: Optional[str] = None) -> str:
    """
    Get a list of all toppings in the menu.

    Args:
        category: Optional category name to filter toppings (e.g., 'meats', 'vegetables', 'cheeses')

    Returns a JSON array of toppings with their names, categories, prices,
    and availability status.
    """
    db = get_db(ctx)
    toppings = await db.get_all_toppings(category=category)
    return json.dumps(toppings, indent=2)


@mcp.tool
async def get_topping_by_id(ctx: Context, id: str) -> str:
    """
    Get a specific topping by its ID.

    Args:
        id: The unique identifier of the topping to retrieve

    Returns the topping details including name, category, price,
    and availability status.
    """
    db = get_db(ctx)
    topping = await db.get_topping_by_id(id)

    if topping is None:
        return json.dumps({"error": "Topping not found", "id": id})

    return json.dumps(topping, indent=2)


@mcp.tool
async def get_topping_categories(ctx: Context) -> str:
    """
    Get a list of all topping categories.

    Returns a JSON array of topping categories with their names
    and descriptions.
    """
    db = get_db(ctx)
    categories = await db.get_topping_categories()
    return json.dumps(categories, indent=2)


# ============================================================================
# ORDER TOOLS
# ============================================================================

@mcp.tool
async def get_orders(
    ctx: Context,
    userId: Optional[str] = None,
    status: Optional[str] = None,
    last: Optional[str] = None
) -> str:
    """
    Get a list of orders in the system.

    Args:
        userId: Filter orders by user ID
        status: Filter by order status (pending, confirmed, preparing, ready, delivered, cancelled).
                Comma-separated list allowed (e.g., 'pending,confirmed')
        last: Filter orders created in the last X minutes or hours (e.g., '60m', '2h', '1d')

    Returns a JSON array of orders with their details.
    """
    db = get_db(ctx)
    orders = await db.get_orders(user_id=userId, status=status, last=last)
    return json.dumps(orders, indent=2)


@mcp.tool
async def get_order_by_id(ctx: Context, id: str) -> str:
    """
    Get a specific order by its ID.

    Args:
        id: The unique identifier of the order to retrieve

    Returns the complete order details including all items, status,
    total price, and timestamps.
    """
    db = get_db(ctx)
    order = await db.get_order_by_id(id)

    if order is None:
        return json.dumps({"error": "Order not found", "id": id})

    return json.dumps(order, indent=2)


@mcp.tool
async def place_order(
    ctx: Context,
    userId: str,
    items: list[dict],
    nickname: Optional[str] = None
) -> str:
    """
    Place a new order with pizzas.

    Args:
        userId: ID of the user placing the order (required)
        items: List of order items. Each item should have:
               - pizza_id (required): ID of the pizza
               - size: Pizza size (small, medium, large, extra-large). Default: medium
               - quantity: Number of pizzas. Default: 1
               - toppings: List of additional topping IDs. Default: []
        nickname: Optional nickname for the order (e.g., "John's Birthday Party")

    Returns the created order with all details including order ID, items,
    total price, and status.

    Example items:
    [
        {"pizza_id": "uuid-1", "size": "large", "quantity": 2},
        {"pizza_id": "uuid-2", "size": "medium", "quantity": 1, "toppings": ["topping-uuid-1"]}
    ]
    """
    db = get_db(ctx)

    try:
        order = await db.place_order(
            user_id=userId,
            items=items,
            nickname=nickname
        )
        return json.dumps(order, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e), "success": False})
    except Exception as e:
        return json.dumps({"error": f"Failed to place order: {str(e)}", "success": False})


@mcp.tool
async def delete_order_by_id(ctx: Context, id: str, userId: str) -> str:
    """
    Cancel an order if it has not yet been started.

    The order must be in 'pending' status to be cancelled.
    The userId must match the order owner.

    Args:
        id: ID of the order to cancel (required)
        userId: ID of the user that placed the order (required)

    Returns a success message or an error with the reason for failure.

    Possible errors:
    - ORDER_NOT_FOUND: Order does not exist
    - NOT_AUTHORIZED: User is not the order owner
    - CANNOT_CANCEL: Order is not in pending status
    """
    db = get_db(ctx)
    result = await db.delete_order(order_id=id, user_id=userId)
    return json.dumps(result, indent=2)


# ============================================================================
# STORE LOCATION TOOLS (Additional for chatbot support)
# ============================================================================

@mcp.tool
async def get_store_locations(ctx: Context, city: Optional[str] = None) -> str:
    """
    Get a list of ABC Pizza store locations.

    Args:
        city: Optional city name to filter locations (e.g., 'New York', 'Los Angeles')

    Returns a JSON array of store locations with addresses, coordinates,
    phone numbers, and operating hours. Useful for finding nearby stores
    and getting directions.
    """
    db = get_db(ctx)
    locations = await db.get_store_locations(city=city)
    return json.dumps(locations, indent=2)


@mcp.tool
async def get_active_offers(ctx: Context, location_id: Optional[str] = None) -> str:
    """
    Get a list of currently active offers and discounts.

    Args:
        location_id: Optional location ID to get location-specific offers.
                     If not provided, returns all global offers and promotions.

    Returns a JSON array of active offers including discount details,
    promo codes, and validity periods. Useful for informing customers
    about current deals when ordering.
    """
    db = get_db(ctx)
    offers = await db.get_active_offers(location_id=location_id)
    return json.dumps(offers, indent=2)


@mcp.tool
async def get_popular_toppings(ctx: Context, limit: int = 10) -> str:
    """
    Get the most popular pizza toppings at ABC Pizza.

    Args:
        limit: Maximum number of toppings to return (default: 10)

    Returns a JSON array of the most frequently ordered toppings,
    ranked by popularity based on customer orders.
    """
    db = get_db(ctx)
    try:
        toppings = await db.get_popular_toppings(limit=limit)
        return json.dumps(toppings, indent=2)
    except Exception:
        # Fallback if no orders exist yet
        toppings = await db.get_all_toppings()
        return json.dumps(toppings[:limit], indent=2)


# ============================================================================
# ADMIN NOTIFICATION TOOLS
# ============================================================================

@mcp.tool
async def notify_menu_update(ctx: Context, notification_type: str = "all") -> str:
    """
    Send MCP notifications to clients about capability changes.

    This is useful when the server's capabilities change dynamically,
    such as when menu items are added/removed, new promotions are created,
    or store hours change.

    Args:
        notification_type: Type of notification to send:
            - "tools": Notify that available tools have changed
            - "resources": Notify that available resources have changed
            - "prompts": Notify that available prompts have changed
            - "all": Send all notification types (default)

    Returns success status with notifications sent.

    Use Cases:
    - After adding new pizza types dynamically
    - After enabling/disabling seasonal menu items
    - After updating store operating hours
    - After creating new promotional offers
    """
    notifications_sent = []

    try:
        if notification_type in ("tools", "all"):
            # Notify clients that the tool list has changed
            # (e.g., new pizza customization tools added)
            await ctx.send_notification(mcp_types.ToolListChangedNotification())
            notifications_sent.append("ToolListChangedNotification")

        if notification_type in ("resources", "all"):
            # Notify clients that resources have changed
            # (e.g., new menu PDFs, images available)
            await ctx.send_notification(mcp_types.ResourceListChangedNotification())
            notifications_sent.append("ResourceListChangedNotification")

        if notification_type in ("prompts", "all"):
            # Notify clients that prompts have changed
            # (e.g., new order templates, greeting prompts)
            await ctx.send_notification(mcp_types.PromptListChangedNotification())
            notifications_sent.append("PromptListChangedNotification")

        return json.dumps({
            "success": True,
            "message": "MCP notifications sent to connected clients",
            "notifications_sent": notifications_sent,
            "notification_type": notification_type
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Failed to send notifications"
        }, indent=2)


@mcp.tool
async def refresh_menu_cache(ctx: Context) -> str:
    """
    Refresh the menu cache and notify clients of changes.

    This tool:
    1. Reloads pizza, topping, and offer data from the database
    2. Sends MCP notifications to inform clients that data has changed

    Useful for admin operations when menu items have been updated
    directly in the database.

    Returns the refreshed menu summary and notification status.
    """
    db = get_db(ctx)

    try:
        # Reload data from database
        pizzas = await db.get_all_pizzas()
        toppings = await db.get_all_toppings()
        categories = await db.get_topping_categories()
        offers = await db.get_active_offers()
        locations = await db.get_store_locations()

        # Send notification that resources have changed
        await ctx.send_notification(mcp_types.ResourceListChangedNotification())

        return json.dumps({
            "success": True,
            "message": "Menu cache refreshed and clients notified",
            "summary": {
                "pizzas_count": len(pizzas),
                "toppings_count": len(toppings),
                "categories_count": len(categories),
                "active_offers_count": len(offers),
                "locations_count": len(locations)
            },
            "notification_sent": "ResourceListChangedNotification"
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Failed to refresh menu cache"
        }, indent=2)


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Check for command line arguments
    transport = "stdio"
    host = server_config.host
    port = server_config.port

    if "--http" in sys.argv or "-h" in sys.argv:
        transport = "http"

    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    safe_print(f"🚀 Starting server with transport={transport}")

    if transport == "http":
        safe_print(f"📡 Listening on http://{host}:{port}")
        mcp.run(transport="http", host=host, port=port)
    else:
        mcp.run()
