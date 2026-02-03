# 🍕 ABC Pizza Bot - AI-Powered Pizza Ordering Agent

An intelligent conversational AI agent for pizza ordering, menu browsing, and store information. Built with the Agent Framework and Model Context Protocol (MCP) for seamless integration with backend services.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [MCP Server](#mcp-server)
- [Available Tools](#available-tools)
- [Testing](#testing)
- [API Reference](#api-reference)
- [Store Locations](#store-locations)

## Overview

ABC PizzaBot is an AI assistant that helps users:
- Browse pizza menus and toppings
- Get pricing information
- Place and track orders
- Find store locations and hours
- Get promotional offers and discounts

The system uses:
- **OpenAI GPT-4o** for natural language understanding
- **Vector Store** for store information retrieval
- **MCP Server** for real-time menu, orders, and location data
- **PostgreSQL** for persistent data storage

## Features

- 🍕 **Menu Browsing** - View available pizzas, sizes, and prices
- 🧀 **Topping Customization** - Browse and add toppings by category
- 🛒 **Order Management** - Place, view, and cancel orders
- 📍 **Store Locator** - Find nearby stores with hours and contact info
- 🎁 **Promotions** - View active offers and discount codes
- 🧮 **Pizza Calculator** - Get recommendations for group orders
- 🔐 **API Key Authentication** - Secure MCP server access

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   ABC PizzaBot  │────▶│   MCP Server     │────▶│   PostgreSQL    │
│   (Agent)       │     │   (FastMCP)      │     │   Database      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │
        │                        │
        ▼                        ▼
┌─────────────────┐     ┌──────────────────┐
│  Vector Store   │     │  Authentication  │
│  (Store Info)   │     │  (API Key/JWT)   │
└─────────────────┘     └──────────────────┘
```

## Project Structure

```
agentcon-pizza-workshop/
├── agent.py                 # Main pizza bot agent
├── tools.py                 # Custom tools (pizza calculator)
├── add_data.py              # Vector store management
├── utils.py                 # Utility functions
├── instructions.txt         # Agent instructions/prompts
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration
├── .env.example             # Example environment file
│
├── mcp_server/              # MCP Server Implementation
│   ├── mcp_abc_pizza_server.py  # FastMCP server with tools
│   ├── database.py          # PostgreSQL database operations
│   ├── config.py            # Server configuration
│   ├── models.py            # Pydantic data models
│   ├── schema.sql           # Database schema
│   └── seed_data.py         # Sample data seeder
│
├── mcp_client/              # MCP Client for testing
│   └── my_client.py         # Test client with demos
│
├── documents/               # Store information documents
│   ├── abc_pizza_amsterdam.md
│   ├── abc_pizza_boston.md
│   ├── abc_pizza_chicago.md
│   └── ... (20 store locations)
│
└── test_mcp.py              # MCP integration tests
```

## Prerequisites

- **Python 3.11+**
- **PostgreSQL 14+** (for MCP server)
- **OpenAI API Key** (for GPT-4o)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd agentcon-pizza-workshop
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database:**
   ```bash
   # Create database
   createdb mcp_abc_pizza_db
   
   # Run schema
   cd mcp_server
   psql -d mcp_abc_pizza_db -f schema.sql
   
   # Seed sample data
   python seed_data.py
   ```

5. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database credentials
   ```

## Configuration

Create a `.env` file with the following settings:

```env
# OpenAI Configuration
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_ID=gpt-4o
OPENAI_API_KEY=sk-your-openai-api-key

# MCP Configuration
ENABLE_MCP=true
MCP_URL=http://localhost:8366/mcp
MCP_API_TOKEN=pizza-api-key-12345

# MCP Server Settings
MCP_SERVER_NAME=ABC Pizza MCP Server
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8366

# Authentication
AUTH_ENABLED=true
AUTH_TYPE=APIKEY
AUTH_API_KEYS=pizza-api-key-12345,pizza-api-key-67890

# PostgreSQL Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=mcp_abc_pizza_db
POSTGRES_USER=your-username
POSTGRES_PASSWORD=your-password
```

## Running the Application

### 1. Start the MCP Server

```bash
python -u mcp_server/mcp_abc_pizza_server.py --http
```

The server will start at `http://localhost:8366/mcp`

### 2. Run the Pizza Bot Agent

In a new terminal:

```bash
python agent.py
```

## MCP Server

The MCP (Model Context Protocol) server provides a standardized interface for the AI agent to interact with backend services.

### Starting the Server

```bash
# HTTP mode (recommended for development)
python -u mcp_server/mcp_abc_pizza_server.py --http

# With custom port
python -u mcp_server/mcp_abc_pizza_server.py --http --port 9000

# Stdio mode (for direct integration)
python -u mcp_server/mcp_abc_pizza_server.py
```

### Authentication

The server supports multiple authentication methods:

- **API Key**: Simple key-based authentication
- **Bearer Token**: Static token validation
- **JWT**: JSON Web Token with JWKS validation

## Available Tools

### Menu & Products

| Tool | Description |
|------|-------------|
| `get_pizzas` | List all available pizzas with sizes and prices |
| `get_pizza_by_id` | Get details for a specific pizza |
| `get_toppings` | List toppings (filter by category: meats, vegetables, cheeses, sauces, premium) |
| `get_topping_by_id` | Get details for a specific topping |
| `get_topping_categories` | List all topping categories |
| `get_popular_toppings` | Get the most popular toppings |

### Orders

| Tool | Description |
|------|-------------|
| `get_orders` | List orders (filter by userId, status, time period) |
| `get_order_by_id` | Get details for a specific order |
| `place_order` | Create a new order |
| `delete_order_by_id` | Cancel a pending order |

### Store Information

| Tool | Description |
|------|-------------|
| `get_store_locations` | List store locations (filter by city) |
| `get_active_offers` | List current promotions and discounts |

### Authentication

| Tool | Description |
|------|-------------|
| `get_auth_info` | Check current authentication status |

### Admin Tools

| Tool | Description |
|------|-------------|
| `notify_menu_update` | Send MCP notifications to clients |
| `refresh_menu_cache` | Refresh menu cache and notify clients |

## Testing

### Test MCP Client

```bash
# Full test suite (in-process)
python mcp_client/my_client.py

# HTTP test with API key
python mcp_client/my_client.py --http --api-key pizza-api-key-12345

# Chatbot demo
python mcp_client/my_client.py --demo

# Admin tools test
python mcp_client/my_client.py --http --api-key pizza-api-key-12345 --admin
```

### Test MCP Tools Listing

```bash
python test_mcp.py --api-key pizza-api-key-12345
```

## API Reference

### Place Order

```json
{
    "userId": "U123",
    "nickname": "John's Order",
    "items": [
        {
            "pizza_id": "uuid-of-pizza",
            "size": "large",
            "quantity": 2,
            "toppings": ["topping-uuid-1", "topping-uuid-2"]
        }
    ]
}
```

### Order Status Values

| Status | Description |
|--------|-------------|
| `pending` | Order placed, awaiting confirmation |
| `confirmed` | Order confirmed by store |
| `preparing` | Order being prepared |
| `ready` | Order ready for pickup |
| `delivered` | Order delivered |
| `cancelled` | Order cancelled |

## Store Locations

ABC Pizza has stores in 20 locations worldwide:

| Region | Cities |
|--------|--------|
| 🇺🇸 **USA** | New York, Boston, Chicago, San Francisco, Seattle, Washington DC, Milwaukee |
| 🇳🇱 **Netherlands** | Amsterdam |
| 🇩🇪 **Germany** | Cologne |
| 🇮🇳 **India** | Delhi, Hyderabad, Pune |
| 🇦🇪 **UAE** | Dubai |
| 🇸🇬 **Singapore** | Singapore |
| 🇻🇳 **Vietnam** | Ho Chi Minh City |
| 🇲🇽 **Mexico** | Mexico City |
| 🇧🇷 **Brazil** | São Paulo |
| 🇦🇺 **Australia** | Perth |
| 🇺🇬 **Uganda** | Kampala, Mukono |

## Bot Guidelines

The ABC PizzaBot follows these guidelines:
- Be friendly, helpful, and concise in responses
- Gather all necessary information for orders (pizza type, options)
- Default to San Francisco store if no location specified
- Convert prices to appropriate currency for store location
- Convert pickup times to local timezone
- List at most 5 menu entries at a time
- Always confirm orders before placing them
- Request UserId and Name if not provided

## License

This project is for educational and demonstration purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

Built with ❤️ using [Agent Framework](https://github.com/microsoft/agent-framework) and [FastMCP](https://github.com/jlowin/fastmcp)
