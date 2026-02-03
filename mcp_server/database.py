"""
Database module for ABC Pizza MCP Server.
Provides async PostgreSQL operations using asyncpg with connection pooling.
"""

import asyncpg
from asyncpg import Pool
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID
import json
import re

# Handle imports for both standalone execution and package import
try:
    from .config import db_config
except ImportError:
    from config import db_config


class Database:
    """Async PostgreSQL database operations."""

    def __init__(self, pool: Pool):
        """Initialize with a connection pool."""
        self._pool = pool

    @classmethod
    async def create_pool(cls) -> Pool:
        """Create a connection pool."""
        return await asyncpg.create_pool(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password,
            min_size=db_config.min_pool_size,
            max_size=db_config.max_pool_size,
        )

    @classmethod
    async def connect(cls) -> "Database":
        """Create a new Database instance with a connection pool."""
        pool = await cls.create_pool()
        return cls(pool)

    async def disconnect(self) -> None:
        """Close the connection pool."""
        await self._pool.close()

    # ========================================================================
    # PIZZA OPERATIONS
    # ========================================================================

    async def get_all_pizzas(self) -> list[dict]:
        """Get all available pizzas."""
        query = """
            SELECT id, name, description, sizes, image_url, is_available, popularity_score
            FROM pizzas
            WHERE is_available = TRUE
            ORDER BY popularity_score DESC, name ASC
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [self._row_to_dict(row) for row in rows]

    async def get_pizza_by_id(self, pizza_id: str) -> Optional[dict]:
        """Get a specific pizza by ID."""
        query = """
            SELECT id, name, description, sizes, image_url, is_available, popularity_score
            FROM pizzas
            WHERE id = $1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, UUID(pizza_id))
            return self._row_to_dict(row) if row else None

    # ========================================================================
    # TOPPING OPERATIONS
    # ========================================================================

    async def get_all_toppings(self, category: Optional[str] = None) -> list[dict]:
        """Get all toppings, optionally filtered by category."""
        if category:
            query = """
                SELECT t.id, t.name, t.category_id, tc.name as category_name, t.price, t.is_available
                FROM toppings t
                LEFT JOIN topping_categories tc ON t.category_id = tc.id
                WHERE t.is_available = TRUE AND LOWER(tc.name) = LOWER($1)
                ORDER BY tc.name, t.name
            """
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, category)
        else:
            query = """
                SELECT t.id, t.name, t.category_id, tc.name as category_name, t.price, t.is_available
                FROM toppings t
                LEFT JOIN topping_categories tc ON t.category_id = tc.id
                WHERE t.is_available = TRUE
                ORDER BY tc.name, t.name
            """
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query)

        return [self._row_to_dict(row) for row in rows]

    async def get_topping_by_id(self, topping_id: str) -> Optional[dict]:
        """Get a specific topping by ID."""
        query = """
            SELECT t.id, t.name, t.category_id, tc.name as category_name, t.price, t.is_available
            FROM toppings t
            LEFT JOIN topping_categories tc ON t.category_id = tc.id
            WHERE t.id = $1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, UUID(topping_id))
            return self._row_to_dict(row) if row else None

    async def get_topping_categories(self) -> list[dict]:
        """Get all topping categories."""
        query = """
            SELECT id, name, description
            FROM topping_categories
            ORDER BY name
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [self._row_to_dict(row) for row in rows]

    async def get_popular_toppings(self, limit: int = 10) -> list[dict]:
        """Get most popular toppings based on order frequency."""
        query = """
            SELECT t.id, t.name, t.price, tc.name as category_name, COUNT(*) as order_count
            FROM toppings t
            LEFT JOIN topping_categories tc ON t.category_id = tc.id
            JOIN order_items oi ON oi.toppings ? t.id::text
            WHERE t.is_available = TRUE
            GROUP BY t.id, t.name, t.price, tc.name
            ORDER BY order_count DESC
            LIMIT $1
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            return [self._row_to_dict(row) for row in rows]

    # ========================================================================
    # ORDER OPERATIONS
    # ========================================================================

    async def get_orders(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        last: Optional[str] = None
    ) -> list[dict]:
        """Get orders with optional filters."""
        conditions = []
        params = []
        param_count = 0

        if user_id:
            param_count += 1
            conditions.append(f"user_id = ${param_count}")
            params.append(user_id)

        if status:
            # Support comma-separated status values
            statuses = [s.strip().lower() for s in status.split(",")]
            param_count += 1
            conditions.append(f"status = ANY(${param_count})")
            params.append(statuses)

        if last:
            # Parse time filter like '60m', '2h', '1d'
            time_delta = self._parse_time_filter(last)
            if time_delta:
                param_count += 1
                conditions.append(f"created_at >= ${param_count}")
                params.append(datetime.now() - time_delta)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"""
            SELECT id, user_id, nickname, status, total_price, created_at, updated_at
            FROM orders
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT 100
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_dict(row) for row in rows]

    async def get_order_by_id(self, order_id: str) -> Optional[dict]:
        """Get a specific order with items."""
        order_query = """
            SELECT id, user_id, nickname, status, total_price, created_at, updated_at
            FROM orders
            WHERE id = $1
        """
        items_query = """
            SELECT id, order_id, pizza_id, pizza_name, size, quantity, toppings, item_price
            FROM order_items
            WHERE order_id = $1
            ORDER BY id
        """

        async with self._pool.acquire() as conn:
            order_row = await conn.fetchrow(order_query, UUID(order_id))
            if not order_row:
                return None

            item_rows = await conn.fetch(items_query, UUID(order_id))

            order = self._row_to_dict(order_row)
            order["items"] = [self._row_to_dict(row) for row in item_rows]
            return order

    async def place_order(
        self,
        user_id: str,
        items: list[dict],
        nickname: Optional[str] = None
    ) -> dict:
        """Place a new order."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Calculate total price and prepare items
                total_price = 0.0
                order_items = []

                for item in items:
                    pizza = await self.get_pizza_by_id(item["pizza_id"])
                    if not pizza:
                        raise ValueError(f"Pizza not found: {item['pizza_id']}")

                    size = item.get("size", "medium")
                    if size not in pizza["sizes"]:
                        raise ValueError(f"Invalid size '{size}' for pizza {pizza['name']}")

                    quantity = item.get("quantity", 1)
                    base_price = float(pizza["sizes"][size])

                    # Add topping prices
                    topping_ids = item.get("toppings", [])
                    topping_total = 0.0
                    for topping_id in topping_ids:
                        topping = await self.get_topping_by_id(topping_id)
                        if topping:
                            topping_total += float(topping["price"])

                    item_price = (base_price + topping_total) * quantity
                    total_price += item_price

                    order_items.append({
                        "pizza_id": item["pizza_id"],
                        "pizza_name": pizza["name"],
                        "size": size,
                        "quantity": quantity,
                        "toppings": topping_ids,
                        "item_price": item_price
                    })

                # Create order
                order_id = await conn.fetchval("""
                    INSERT INTO orders (user_id, nickname, status, total_price)
                    VALUES ($1, $2, 'pending', $3)
                    RETURNING id
                """, user_id, nickname, total_price)

                # Create order items
                for oi in order_items:
                    await conn.execute("""
                        INSERT INTO order_items (order_id, pizza_id, pizza_name, size, quantity, toppings, item_price)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, order_id, UUID(oi["pizza_id"]), oi["pizza_name"], oi["size"],
                        oi["quantity"], json.dumps(oi["toppings"]), oi["item_price"])

                # Update pizza popularity
                for oi in order_items:
                    await conn.execute("""
                        UPDATE pizzas SET popularity_score = popularity_score + $1 WHERE id = $2
                    """, oi["quantity"], UUID(oi["pizza_id"]))

                # Ensure user exists
                await conn.execute("""
                    INSERT INTO users (id) VALUES ($1)
                    ON CONFLICT (id) DO NOTHING
                """, user_id)

                return await self.get_order_by_id(str(order_id))

    async def delete_order(self, order_id: str, user_id: str) -> dict:
        """Cancel/delete an order (only if pending)."""
        async with self._pool.acquire() as conn:
            # Check order exists and belongs to user
            order = await conn.fetchrow("""
                SELECT id, user_id, status FROM orders WHERE id = $1
            """, UUID(order_id))

            if not order:
                return {"success": False, "error": "Order not found", "code": "ORDER_NOT_FOUND"}

            if order["user_id"] != user_id:
                return {"success": False, "error": "User not authorized to cancel this order", "code": "NOT_AUTHORIZED"}

            if order["status"] != "pending":
                return {"success": False, "error": f"Order cannot be cancelled (status: {order['status']})", "code": "CANNOT_CANCEL"}

            # Update to cancelled
            await conn.execute("""
                UPDATE orders SET status = 'cancelled', updated_at = NOW() WHERE id = $1
            """, UUID(order_id))

            return {"success": True, "message": f"Order {order_id} has been cancelled"}

    # ========================================================================
    # STORE LOCATION OPERATIONS
    # ========================================================================

    async def get_store_locations(self, city: Optional[str] = None) -> list[dict]:
        """Get store locations, optionally filtered by city."""
        if city:
            query = """
                SELECT id, name, address, city, state, zip_code, country, latitude, longitude, phone, hours, is_active
                FROM store_locations
                WHERE is_active = TRUE AND LOWER(city) LIKE LOWER($1)
                ORDER BY name
            """
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, f"%{city}%")
        else:
            query = """
                SELECT id, name, address, city, state, zip_code, country, latitude, longitude, phone, hours, is_active
                FROM store_locations
                WHERE is_active = TRUE
                ORDER BY city, name
            """
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query)

        return [self._row_to_dict(row) for row in rows]

    # ========================================================================
    # OFFER OPERATIONS
    # ========================================================================

    async def get_active_offers(self, location_id: Optional[str] = None) -> list[dict]:
        """Get active offers, optionally for a specific location."""
        now = datetime.now()

        if location_id:
            query = """
                SELECT id, location_id, title, description, discount_type, discount_value, 
                       min_order_amount, code, valid_from, valid_until, is_active
                FROM offers
                WHERE is_active = TRUE 
                  AND (location_id = $1 OR location_id IS NULL)
                  AND valid_from <= $2
                  AND (valid_until IS NULL OR valid_until >= $2)
                ORDER BY discount_value DESC
            """
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, UUID(location_id), now)
        else:
            query = """
                SELECT id, location_id, title, description, discount_type, discount_value,
                       min_order_amount, code, valid_from, valid_until, is_active
                FROM offers
                WHERE is_active = TRUE
                  AND valid_from <= $1
                  AND (valid_until IS NULL OR valid_until >= $1)
                ORDER BY discount_value DESC
            """
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, now)

        return [self._row_to_dict(row) for row in rows]

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _row_to_dict(self, row: asyncpg.Record) -> Optional[dict]:
        """Convert an asyncpg Record to a dictionary."""
        if row is None:
            return None
        result = dict(row)
        # Convert special types
        for key, value in result.items():
            if isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                # Convert Decimal to float for JSON serialization
                result[key] = float(value)
            elif isinstance(value, str) and key in ('sizes', 'hours', 'toppings', 'preferences'):
                # Parse JSON string fields
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass  # Keep original value if not valid JSON
        return result

    def _parse_time_filter(self, time_str: str) -> Optional[timedelta]:
        """Parse time filter string like '60m', '2h', '1d'."""
        match = re.match(r"^(\d+)([mhd])$", time_str.lower())
        if not match:
            return None

        value = int(match.group(1))
        unit = match.group(2)

        if unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        return None
