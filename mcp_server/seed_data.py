"""
Seed data script for ABC Pizza MCP Server.
Populates the database with initial pizzas, toppings, locations, and offers.
"""

import asyncio
import asyncpg
from uuid import uuid4
from datetime import datetime, timedelta

# Handle imports for both standalone execution and package import
try:
    from .config import db_config
except ImportError:
    from config import db_config


async def seed_database():
    """Seed the database with initial data."""
    conn = await asyncpg.connect(
        host=db_config.host,
        port=db_config.port,
        database=db_config.database,
        user=db_config.user,
        password=db_config.password,
    )

    try:
        print("🍕 Seeding ABC Pizza database...")

        # ====================================================================
        # SEED TOPPING CATEGORIES
        # ====================================================================
        print("  📦 Creating topping categories...")
        categories = [
            {"name": "Meats", "description": "Premium meat toppings"},
            {"name": "Vegetables", "description": "Fresh vegetable toppings"},
            {"name": "Cheeses", "description": "Artisan cheese selections"},
            {"name": "Sauces", "description": "Signature sauces"},
            {"name": "Premium", "description": "Premium specialty toppings"},
        ]

        category_ids = {}
        for cat in categories:
            cat_id = uuid4()
            await conn.execute("""
                INSERT INTO topping_categories (id, name, description)
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
                RETURNING id
            """, cat_id, cat["name"], cat["description"])

            # Get actual ID (in case of conflict)
            result = await conn.fetchval(
                "SELECT id FROM topping_categories WHERE name = $1", cat["name"]
            )
            category_ids[cat["name"]] = result

        # ====================================================================
        # SEED TOPPINGS
        # ====================================================================
        print("  🧀 Creating toppings...")
        toppings = [
            # Meats
            {"name": "Pepperoni", "category": "Meats", "price": 1.50},
            {"name": "Italian Sausage", "category": "Meats", "price": 1.75},
            {"name": "Bacon", "category": "Meats", "price": 2.00},
            {"name": "Ham", "category": "Meats", "price": 1.50},
            {"name": "Grilled Chicken", "category": "Meats", "price": 2.25},
            {"name": "Anchovies", "category": "Meats", "price": 2.00},
            {"name": "Meatballs", "category": "Meats", "price": 2.00},

            # Vegetables
            {"name": "Mushrooms", "category": "Vegetables", "price": 1.00},
            {"name": "Green Peppers", "category": "Vegetables", "price": 0.75},
            {"name": "Red Onions", "category": "Vegetables", "price": 0.75},
            {"name": "Black Olives", "category": "Vegetables", "price": 1.00},
            {"name": "Fresh Tomatoes", "category": "Vegetables", "price": 1.00},
            {"name": "Spinach", "category": "Vegetables", "price": 1.00},
            {"name": "Jalapeños", "category": "Vegetables", "price": 0.75},
            {"name": "Pineapple", "category": "Vegetables", "price": 1.00},
            {"name": "Roasted Garlic", "category": "Vegetables", "price": 1.00},
            {"name": "Artichoke Hearts", "category": "Vegetables", "price": 1.50},
            {"name": "Sun-dried Tomatoes", "category": "Vegetables", "price": 1.50},

            # Cheeses
            {"name": "Extra Mozzarella", "category": "Cheeses", "price": 1.50},
            {"name": "Parmesan", "category": "Cheeses", "price": 1.25},
            {"name": "Feta Cheese", "category": "Cheeses", "price": 1.50},
            {"name": "Ricotta", "category": "Cheeses", "price": 1.50},
            {"name": "Gorgonzola", "category": "Cheeses", "price": 1.75},
            {"name": "Goat Cheese", "category": "Cheeses", "price": 2.00},

            # Sauces
            {"name": "Extra Marinara", "category": "Sauces", "price": 0.50},
            {"name": "BBQ Sauce", "category": "Sauces", "price": 0.75},
            {"name": "Alfredo Sauce", "category": "Sauces", "price": 1.00},
            {"name": "Pesto", "category": "Sauces", "price": 1.25},
            {"name": "Buffalo Sauce", "category": "Sauces", "price": 0.75},

            # Premium
            {"name": "Truffle Oil", "category": "Premium", "price": 3.00},
            {"name": "Prosciutto", "category": "Premium", "price": 3.50},
            {"name": "Fresh Basil", "category": "Premium", "price": 1.00},
            {"name": "Burrata", "category": "Premium", "price": 4.00},
        ]

        for topping in toppings:
            await conn.execute("""
                INSERT INTO toppings (id, name, category_id, price, is_available)
                VALUES ($1, $2, $3, $4, TRUE)
                ON CONFLICT DO NOTHING
            """, uuid4(), topping["name"], category_ids[topping["category"]], topping["price"])

        # ====================================================================
        # SEED PIZZAS
        # ====================================================================
        print("  🍕 Creating pizzas...")
        pizzas = [
            {
                "name": "Margherita",
                "description": "Classic tomato sauce, fresh mozzarella, and basil",
                "sizes": {"small": 9.99, "medium": 12.99, "large": 15.99, "extra-large": 18.99},
                "popularity": 95
            },
            {
                "name": "Pepperoni",
                "description": "Loaded with premium pepperoni and melted mozzarella",
                "sizes": {"small": 10.99, "medium": 13.99, "large": 16.99, "extra-large": 19.99},
                "popularity": 100
            },
            {
                "name": "Hawaiian",
                "description": "Ham, pineapple, and mozzarella - a tropical delight",
                "sizes": {"small": 11.99, "medium": 14.99, "large": 17.99, "extra-large": 20.99},
                "popularity": 75
            },
            {
                "name": "Supreme",
                "description": "Pepperoni, sausage, mushrooms, peppers, onions, and olives",
                "sizes": {"small": 12.99, "medium": 15.99, "large": 18.99, "extra-large": 21.99},
                "popularity": 90
            },
            {
                "name": "BBQ Chicken",
                "description": "Grilled chicken, BBQ sauce, red onions, and cilantro",
                "sizes": {"small": 12.99, "medium": 15.99, "large": 18.99, "extra-large": 21.99},
                "popularity": 85
            },
            {
                "name": "Meat Lovers",
                "description": "Pepperoni, sausage, bacon, ham, and meatballs",
                "sizes": {"small": 13.99, "medium": 16.99, "large": 19.99, "extra-large": 22.99},
                "popularity": 88
            },
            {
                "name": "Veggie Delight",
                "description": "Mushrooms, peppers, onions, tomatoes, olives, and spinach",
                "sizes": {"small": 11.99, "medium": 14.99, "large": 17.99, "extra-large": 20.99},
                "popularity": 70
            },
            {
                "name": "Four Cheese",
                "description": "Mozzarella, parmesan, ricotta, and gorgonzola",
                "sizes": {"small": 11.99, "medium": 14.99, "large": 17.99, "extra-large": 20.99},
                "popularity": 80
            },
            {
                "name": "Buffalo Chicken",
                "description": "Spicy buffalo chicken, blue cheese crumbles, celery",
                "sizes": {"small": 12.99, "medium": 15.99, "large": 18.99, "extra-large": 21.99},
                "popularity": 78
            },
            {
                "name": "White Pizza",
                "description": "Alfredo sauce, ricotta, mozzarella, garlic, and spinach",
                "sizes": {"small": 11.99, "medium": 14.99, "large": 17.99, "extra-large": 20.99},
                "popularity": 72
            },
            {
                "name": "Truffle Mushroom",
                "description": "Premium mushrooms, truffle oil, parmesan, and fresh herbs",
                "sizes": {"small": 14.99, "medium": 17.99, "large": 20.99, "extra-large": 23.99},
                "popularity": 65
            },
            {
                "name": "Mediterranean",
                "description": "Feta, olives, tomatoes, red onion, and fresh oregano",
                "sizes": {"small": 12.99, "medium": 15.99, "large": 18.99, "extra-large": 21.99},
                "popularity": 68
            },
        ]

        import json
        for pizza in pizzas:
            await conn.execute("""
                INSERT INTO pizzas (id, name, description, sizes, is_available, popularity_score)
                VALUES ($1, $2, $3, $4, TRUE, $5)
                ON CONFLICT DO NOTHING
            """, uuid4(), pizza["name"], pizza["description"],
                json.dumps(pizza["sizes"]), pizza["popularity"])

        # ====================================================================
        # SEED STORE LOCATIONS
        # ====================================================================
        print("  📍 Creating store locations...")
        locations = [
            {
                "name": "ABC Pizza - Times Square",
                "address": "1500 Broadway",
                "city": "New York",
                "state": "NY",
                "zip_code": "10036",
                "latitude": 40.7580,
                "longitude": -73.9855,
                "phone": "(212) 555-0100",
                "hours": {"monday": "10:00-23:00", "tuesday": "10:00-23:00", "wednesday": "10:00-23:00",
                         "thursday": "10:00-23:00", "friday": "10:00-24:00", "saturday": "10:00-24:00", "sunday": "11:00-22:00"}
            },
            {
                "name": "ABC Pizza - Brooklyn Heights",
                "address": "120 Montague Street",
                "city": "New York",
                "state": "NY",
                "zip_code": "11201",
                "latitude": 40.6934,
                "longitude": -73.9917,
                "phone": "(718) 555-0101",
                "hours": {"monday": "11:00-22:00", "tuesday": "11:00-22:00", "wednesday": "11:00-22:00",
                         "thursday": "11:00-22:00", "friday": "11:00-23:00", "saturday": "11:00-23:00", "sunday": "12:00-21:00"}
            },
            {
                "name": "ABC Pizza - Downtown LA",
                "address": "800 S Figueroa St",
                "city": "Los Angeles",
                "state": "CA",
                "zip_code": "90017",
                "latitude": 34.0472,
                "longitude": -118.2618,
                "phone": "(213) 555-0102",
                "hours": {"monday": "10:00-22:00", "tuesday": "10:00-22:00", "wednesday": "10:00-22:00",
                         "thursday": "10:00-22:00", "friday": "10:00-23:00", "saturday": "10:00-23:00", "sunday": "11:00-21:00"}
            },
            {
                "name": "ABC Pizza - Santa Monica",
                "address": "401 Santa Monica Blvd",
                "city": "Los Angeles",
                "state": "CA",
                "zip_code": "90401",
                "latitude": 34.0195,
                "longitude": -118.4912,
                "phone": "(310) 555-0103",
                "hours": {"monday": "10:00-22:00", "tuesday": "10:00-22:00", "wednesday": "10:00-22:00",
                         "thursday": "10:00-22:00", "friday": "10:00-23:00", "saturday": "10:00-23:00", "sunday": "11:00-21:00"}
            },
            {
                "name": "ABC Pizza - Chicago Loop",
                "address": "233 S Wacker Dr",
                "city": "Chicago",
                "state": "IL",
                "zip_code": "60606",
                "latitude": 41.8789,
                "longitude": -87.6359,
                "phone": "(312) 555-0104",
                "hours": {"monday": "10:00-22:00", "tuesday": "10:00-22:00", "wednesday": "10:00-22:00",
                         "thursday": "10:00-22:00", "friday": "10:00-23:00", "saturday": "10:00-23:00", "sunday": "11:00-21:00"}
            },
            {
                "name": "ABC Pizza - San Francisco",
                "address": "1 Market St",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94105",
                "latitude": 37.7941,
                "longitude": -122.3950,
                "phone": "(415) 555-0105",
                "hours": {"monday": "10:00-22:00", "tuesday": "10:00-22:00", "wednesday": "10:00-22:00",
                         "thursday": "10:00-22:00", "friday": "10:00-23:00", "saturday": "10:00-23:00", "sunday": "11:00-21:00"}
            },
        ]

        location_ids = []
        for loc in locations:
            loc_id = uuid4()
            location_ids.append((loc_id, loc["city"]))
            await conn.execute("""
                INSERT INTO store_locations (id, name, address, city, state, zip_code, latitude, longitude, phone, hours, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, TRUE)
                ON CONFLICT DO NOTHING
            """, loc_id, loc["name"], loc["address"], loc["city"], loc["state"],
                loc["zip_code"], loc["latitude"], loc["longitude"], loc["phone"], json.dumps(loc["hours"]))

        # ====================================================================
        # SEED OFFERS
        # ====================================================================
        print("  🎁 Creating offers...")
        now = datetime.now()
        offers = [
            # Global offers
            {
                "title": "Welcome Offer - 20% Off First Order",
                "description": "New customers get 20% off their first pizza order!",
                "discount_type": "percentage",
                "discount_value": 20.0,
                "code": "WELCOME20",
                "valid_until": now + timedelta(days=365),
                "location_id": None
            },
            {
                "title": "Family Deal - $10 Off Orders Over $50",
                "description": "Get $10 off when you order $50 or more",
                "discount_type": "fixed",
                "discount_value": 10.0,
                "min_order_amount": 50.0,
                "code": "FAMILY10",
                "valid_until": now + timedelta(days=90),
                "location_id": None
            },
            {
                "title": "Weekend Special - Buy One Get One Free",
                "description": "Order one large pizza, get the second one free! Valid on weekends only.",
                "discount_type": "buy_one_get_one",
                "discount_value": 100.0,
                "code": "BOGO",
                "valid_until": now + timedelta(days=30),
                "location_id": None
            },
        ]

        # Add location-specific offers
        for loc_id, city in location_ids[:3]:  # First 3 locations get special offers
            offers.append({
                "title": f"{city} Special - 15% Off",
                "description": f"Exclusive offer for our {city} customers!",
                "discount_type": "percentage",
                "discount_value": 15.0,
                "code": f"{city.upper().replace(' ', '')}15",
                "valid_until": now + timedelta(days=60),
                "location_id": loc_id
            })

        for offer in offers:
            await conn.execute("""
                INSERT INTO offers (id, location_id, title, description, discount_type, discount_value, 
                                   min_order_amount, code, valid_from, valid_until, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, TRUE)
                ON CONFLICT DO NOTHING
            """, uuid4(), offer.get("location_id"), offer["title"], offer["description"],
                offer["discount_type"], offer["discount_value"], offer.get("min_order_amount", 0),
                offer.get("code"), now, offer.get("valid_until"))

        # ====================================================================
        # SEED SAMPLE USERS
        # ====================================================================
        print("  👤 Creating sample users...")
        users = [
            {"id": "U123", "name": "John Doe", "email": "john@example.com", "location_city": "New York"},
            {"id": "U456", "name": "Jane Smith", "email": "jane@example.com", "location_city": "Los Angeles"},
            {"id": "U789", "name": "Bob Johnson", "email": "bob@example.com", "location_city": "Chicago"},
        ]

        for user in users:
            await conn.execute("""
                INSERT INTO users (id, name, email, location_city)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, email = EXCLUDED.email, location_city = EXCLUDED.location_city
            """, user["id"], user["name"], user["email"], user["location_city"])

        print("✅ Database seeded successfully!")

    finally:
        await conn.close()


async def run_schema():
    """Run the schema.sql file to create tables."""
    conn = await asyncpg.connect(
        host=db_config.host,
        port=db_config.port,
        database=db_config.database,
        user=db_config.user,
        password=db_config.password,
    )

    try:
        print("📋 Running schema.sql...")
        with open("schema.sql", "r") as f:
            schema_sql = f.read()

        await conn.execute(schema_sql)
        print("✅ Schema created successfully!")

    finally:
        await conn.close()


async def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--schema":
        await run_schema()
    else:
        await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
