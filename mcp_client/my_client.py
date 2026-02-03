"""
MCP Client for ABC Pizza Server
====================================
A test client to interact with the Pizza CRM MCP Server.

Usage:
    # Test with direct Python import (in-process)
    python my_client.py

    # Test with HTTP transport (no auth)
    python my_client.py --http

    # Test with HTTP transport + API Key authentication
    python my_client.py --http --api-key pizza-api-key-12345

    # Test with HTTP transport + Bearer token
    python my_client.py --http --token your-bearer-token

    # Test admin notification tools
    python my_client.py --admin
    python my_client.py --http --api-key pizza-api-key-12345 --admin

    # Demo chatbot queries
    python my_client.py --demo
"""

import asyncio
import json
import os
import sys
from fastmcp import Client


def get_sizes_dict(pizza: dict) -> dict:
    """Safely get sizes as a dictionary, parsing JSON string if needed."""
    sizes = pizza.get('sizes', {})
    if isinstance(sizes, str):
        try:
            sizes = json.loads(sizes)
        except (json.JSONDecodeError, TypeError):
            sizes = {}
    return sizes


async def test_pizza_server():
    """Test all Pizza MCP Server tools."""

    # Import the server directly for in-process testing
    from mcp_server.mcp_abc_pizza_server  import mcp

    print("🍕 ABC Pizza MCP Server - Test Client")
    print("=" * 50)

    async with Client(mcp) as client:
        # Test 1: List all tools
        print("\n📋 Available Tools:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:60]}...")

        # Test 2: Get all pizzas
        print("\n🍕 Testing get_pizzas:")
        result = await client.call_tool("get_pizzas", {})
        pizzas = json.loads(result.content[0].text)
        print(f"  Found {len(pizzas)} pizzas")
        if pizzas:
            print(f"  Sample: {pizzas[0]['name']} - {pizzas[0]['description'][:50]}...")
            first_pizza_id = pizzas[0]['id']
        else:
            first_pizza_id = None
            print("  No pizzas found - run seed_data.py first!")

        # Test 3: Get pizza by ID
        if first_pizza_id:
            print(f"\n🔍 Testing get_pizza_by_id (id={first_pizza_id[:8]}...):")
            result = await client.call_tool("get_pizza_by_id", {"id": first_pizza_id})
            pizza = json.loads(result.content[0].text)
            sizes = get_sizes_dict(pizza)
            print(f"  {pizza['name']}: sizes = {list(sizes.keys())}")

        # Test 4: Get topping categories
        print("\n📦 Testing get_topping_categories:")
        result = await client.call_tool("get_topping_categories", {})
        categories = json.loads(result.content[0].text)
        print(f"  Found {len(categories)} categories")
        for cat in categories[:3]:
            print(f"    - {cat['name']}")

        # Test 5: Get toppings (filtered by category)
        print("\n🧀 Testing get_toppings (category='Meats'):")
        result = await client.call_tool("get_toppings", {"category": "Meats"})
        toppings = json.loads(result.content[0].text)
        print(f"  Found {len(toppings)} meat toppings")
        for topping in toppings[:3]:
            print(f"    - {topping['name']}: ${topping['price']}")

        # Test 6: Get store locations
        print("\n📍 Testing get_store_locations:")
        result = await client.call_tool("get_store_locations", {})
        locations = json.loads(result.content[0].text)
        print(f"  Found {len(locations)} store locations")
        for loc in locations[:3]:
            print(f"    - {loc['name']}: {loc['city']}, {loc['state']}")

        # Test 7: Get active offers
        print("\n🎁 Testing get_active_offers:")
        result = await client.call_tool("get_active_offers", {})
        offers = json.loads(result.content[0].text)
        print(f"  Found {len(offers)} active offers")
        for offer in offers[:3]:
            print(f"    - {offer['title']}: {offer['discount_type']} ({offer['discount_value']})")

        # Test 8: Place an order
        if first_pizza_id:
            print("\n🛒 Testing place_order:")
            order_result = await client.call_tool("place_order", {
                "userId": "U123",
                "nickname": "Test Order",
                "items": [
                    {"pizza_id": first_pizza_id, "size": "large", "quantity": 1}
                ]
            })
            order = json.loads(order_result.content[0].text)
            if "error" not in order:
                print(f"  Order placed! ID: {order['id'][:8]}...")
                print(f"  Total: ${order['total_price']}, Status: {order['status']}")
                order_id = order['id']

                # Test 9: Get order by ID
                print(f"\n📄 Testing get_order_by_id:")
                result = await client.call_tool("get_order_by_id", {"id": order_id})
                order_detail = json.loads(result.content[0].text)
                print(f"  Items: {len(order_detail['items'])}")

                # Test 10: Get orders with filters
                print("\n📋 Testing get_orders (userId='U123', status='pending'):")
                result = await client.call_tool("get_orders", {
                    "userId": "U123",
                    "status": "pending"
                })
                orders = json.loads(result.content[0].text)
                print(f"  Found {len(orders)} pending orders for U123")

                # Test 11: Cancel the order
                print(f"\n❌ Testing delete_order_by_id:")
                result = await client.call_tool("delete_order_by_id", {
                    "id": order_id,
                    "userId": "U123"
                })
                cancel_result = json.loads(result.content[0].text)
                print(f"  Result: {cancel_result.get('message', cancel_result.get('error'))}")
            else:
                print(f"  Error: {order['error']}")

        print("\n" + "=" * 50)
        print("✅ All tests completed!")


async def test_http_client(api_key: str = None, bearer_token: str = None):
    """Test with HTTP transport, optionally with authentication."""
    print("🌐 Testing with HTTP transport...")
    print("Make sure server is running: python mcp_abc_pizza_server.py --http")

    server_url = "http://localhost:8366/mcp"

    # Configure authentication
    # Note: FastMCP's StaticTokenVerifier expects Bearer tokens in Authorization header
    # So both api_key and bearer_token are sent as Bearer tokens
    if api_key:
        print(f"🔐 Using API Key as Bearer token (key: {api_key[:8]}...)")
        client = Client(server_url, auth=api_key)
    elif bearer_token:
        print(f"🔐 Using Bearer token authentication")
        client = Client(server_url, auth=bearer_token)
    else:
        print("🔓 No authentication configured")
        client = Client(server_url)

    async with client:
        tools = await client.list_tools()
        print(f"\n📋 Found {len(tools)} tools via HTTP")

        # Test get_auth_info to verify authentication
        try:
            result = await client.call_tool("get_auth_info", {})
            auth_info = json.loads(result.content[0].text)
            if auth_info.get("authenticated"):
                print(f"✅ Authenticated as: {auth_info.get('client_id', 'unknown')}")
            else:
                print(f"ℹ️  {auth_info.get('message', 'Not authenticated')}")
        except Exception as e:
            print(f"⚠️  Auth check failed: {e}")

        result = await client.call_tool("get_pizzas", {})
        pizzas = json.loads(result.content[0].text)
        print(f"🍕 Found {len(pizzas)} pizzas")


async def demo_chatbot_queries():
    """Demo showing how chatbot queries can be answered."""
    from mcp_server.mcp_abc_pizza_server import mcp

    print("\n" + "=" * 60)
    print("🤖 CHATBOT QUERY DEMOS")
    print("=" * 60)

    async with Client(mcp) as client:
        # Query 1: "Show me the available pizzas"
        print("\n💬 User: 'Show me the available pizzas.'")
        result = await client.call_tool("get_pizzas", {})
        pizzas = json.loads(result.content[0].text)
        print("🤖 Bot: Here are our available pizzas:")
        for p in pizzas[:5]:
            sizes = get_sizes_dict(p)
            sizes_str = ", ".join([f"{k}: ${v}" for k, v in sizes.items()])
            print(f"   • {p['name']} - {p['description'][:40]}...")
            print(f"     Sizes: {sizes_str}")

        # Query 2: "What is the price for a pizza Hawaiian?"
        print("\n💬 User: 'What is the price for a pizza Hawaiian?'")
        result = await client.call_tool("get_pizzas", {})
        pizzas = json.loads(result.content[0].text)
        hawaiian = next((p for p in pizzas if 'hawaiian' in p['name'].lower()), None)
        if hawaiian:
            print(f"🤖 Bot: The Hawaiian pizza is available in these sizes:")
            sizes = get_sizes_dict(hawaiian)
            for size, price in sizes.items():
                print(f"   • {size.capitalize()}: ${price}")

        # Query 3: "Directions to nearest store from New York"
        print("\n💬 User: 'Find stores near New York'")
        result = await client.call_tool("get_store_locations", {"city": "New York"})
        locations = json.loads(result.content[0].text)
        print(f"🤖 Bot: I found {len(locations)} ABC Pizza locations in New York:")
        for loc in locations:
            print(f"   • {loc['name']}")
            print(f"     {loc['address']}, {loc['city']}, {loc['state']} {loc['zip_code']}")
            print(f"     Phone: {loc['phone']}")

        # Query 4: "What are the current offers?"
        print("\n💬 User: 'What offers do you have?'")
        result = await client.call_tool("get_active_offers", {})
        offers = json.loads(result.content[0].text)
        print(f"🤖 Bot: Here are our current promotions:")
        for offer in offers[:4]:
            print(f"   🎁 {offer['title']}")
            print(f"      {offer['description']}")
            if offer.get('code'):
                print(f"      Use code: {offer['code']}")

        # Query 5: "What are the most popular toppings?"
        print("\n💬 User: 'What are the most popular pizza toppings?'")
        result = await client.call_tool("get_popular_toppings", {"limit": 5})
        toppings = json.loads(result.content[0].text)
        print("🤖 Bot: Our most popular toppings are:")
        for i, t in enumerate(toppings[:5], 1):
            print(f"   {i}. {t['name']} (${t['price']})")


async def test_admin_tools(client):
    """Test admin notification tools."""
    print("\n" + "=" * 60)
    print("🔧 ADMIN TOOLS TEST")
    print("=" * 60)

    # Test 1: Get auth info
    print("\n🔐 Testing get_auth_info:")
    try:
        result = await client.call_tool("get_auth_info", {})
        auth_info = json.loads(result.content[0].text)
        if auth_info.get("authenticated"):
            print(f"  ✅ Authenticated as: {auth_info.get('client_id')}")
            print(f"     Scopes: {auth_info.get('scopes')}")
        else:
            print(f"  ℹ️  {auth_info.get('message')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Test 2: Refresh menu cache
    print("\n🔄 Testing refresh_menu_cache:")
    try:
        result = await client.call_tool("refresh_menu_cache", {})
        cache_result = json.loads(result.content[0].text)
        if cache_result.get("success"):
            print(f"  ✅ {cache_result.get('message')}")
            summary = cache_result.get("summary", {})
            print(f"     Pizzas: {summary.get('pizzas_count', 0)}")
            print(f"     Toppings: {summary.get('toppings_count', 0)}")
            print(f"     Categories: {summary.get('categories_count', 0)}")
            print(f"     Offers: {summary.get('active_offers_count', 0)}")
            print(f"     Locations: {summary.get('locations_count', 0)}")
            print(f"     Notification: {cache_result.get('notification_sent')}")
        else:
            print(f"  ❌ Failed: {cache_result.get('error')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Test 3: Notify menu update (tools only)
    print("\n📢 Testing notify_menu_update (notification_type='tools'):")
    try:
        result = await client.call_tool("notify_menu_update", {"notification_type": "tools"})
        notify_result = json.loads(result.content[0].text)
        if notify_result.get("success"):
            print(f"  ✅ {notify_result.get('message')}")
            print(f"     Notifications sent: {notify_result.get('notifications_sent')}")
        else:
            print(f"  ❌ Failed: {notify_result.get('error')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Test 4: Notify menu update (resources only)
    print("\n📢 Testing notify_menu_update (notification_type='resources'):")
    try:
        result = await client.call_tool("notify_menu_update", {"notification_type": "resources"})
        notify_result = json.loads(result.content[0].text)
        if notify_result.get("success"):
            print(f"  ✅ {notify_result.get('message')}")
            print(f"     Notifications sent: {notify_result.get('notifications_sent')}")
        else:
            print(f"  ❌ Failed: {notify_result.get('error')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Test 5: Notify menu update (all notifications)
    print("\n📢 Testing notify_menu_update (notification_type='all'):")
    try:
        result = await client.call_tool("notify_menu_update", {"notification_type": "all"})
        notify_result = json.loads(result.content[0].text)
        if notify_result.get("success"):
            print(f"  ✅ {notify_result.get('message')}")
            print(f"     Notifications sent: {notify_result.get('notifications_sent')}")
        else:
            print(f"  ❌ Failed: {notify_result.get('error')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ Admin tools test completed!")


async def test_admin_inprocess():
    """Test admin tools with in-process server."""
    from mcp_server.mcp_abc_pizza_server import mcp

    print("🍕 ABC Pizza MCP Server - Admin Tools Test (In-Process)")

    async with Client(mcp) as client:
        await test_admin_tools(client)


async def test_admin_http(api_key: str = None, bearer_token: str = None):
    """Test admin tools with HTTP transport."""
    print("🌐 Testing admin tools with HTTP transport...")
    print("Make sure server is running: python mcp_abc_pizza_server.py --http")

    server_url = "http://localhost:8366/mcp"

    if api_key:
        print(f"🔐 Using API Key as Bearer token (key: {api_key[:8]}...)")
        client = Client(server_url, auth=api_key)
    elif bearer_token:
        print(f"🔐 Using Bearer token authentication")
        client = Client(server_url, auth=bearer_token)
    else:
        print("🔓 No authentication configured")
        client = Client(server_url)

    async with client:
        await test_admin_tools(client)


if __name__ == "__main__":
    # Parse command line arguments
    api_key = None
    bearer_token = None

    for i, arg in enumerate(sys.argv):
        if arg == "--api-key" and i + 1 < len(sys.argv):
            api_key = sys.argv[i + 1]
        elif arg == "--token" and i + 1 < len(sys.argv):
            bearer_token = sys.argv[i + 1]

    # Also check environment variables
    if not api_key:
        api_key = os.getenv("MCP_API_KEY")
    if not bearer_token:
        bearer_token = os.getenv("MCP_BEARER_TOKEN")

    # Determine which test to run
    if "--admin" in sys.argv:
        if "--http" in sys.argv:
            asyncio.run(test_admin_http(api_key=api_key, bearer_token=bearer_token))
        else:
            asyncio.run(test_admin_inprocess())
    elif "--http" in sys.argv:
        asyncio.run(test_http_client(api_key=api_key, bearer_token=bearer_token))
    elif "--demo" in sys.argv:
        asyncio.run(demo_chatbot_queries())
    else:
        asyncio.run(test_pizza_server())
        asyncio.run(demo_chatbot_queries())
