"""
Pydantic models for ABC Pizza MCP Server.
Defines all data structures for pizzas, toppings, orders, locations, and offers.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class OrderStatus(str, Enum):
    """Order status states."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DiscountType(str, Enum):
    """Discount types for offers."""
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    BUY_ONE_GET_ONE = "buy_one_get_one"


class PizzaSize(str, Enum):
    """Standard pizza sizes."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra-large"


# ============================================================================
# TOPPING MODELS
# ============================================================================

class ToppingCategory(BaseModel):
    """Topping category model."""
    id: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class Topping(BaseModel):
    """Topping model."""
    id: str
    name: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    price: float
    is_available: bool = True

    class Config:
        from_attributes = True


# ============================================================================
# PIZZA MODELS
# ============================================================================

class PizzaSizes(BaseModel):
    """Pizza sizes with prices."""
    small: Optional[float] = None
    medium: Optional[float] = None
    large: Optional[float] = None
    extra_large: Optional[float] = Field(None, alias="extra-large")

    class Config:
        populate_by_name = True


class Pizza(BaseModel):
    """Pizza model."""
    id: str
    name: str
    description: Optional[str] = None
    sizes: dict[str, float]
    image_url: Optional[str] = None
    is_available: bool = True
    popularity_score: int = 0

    class Config:
        from_attributes = True


# ============================================================================
# USER MODELS
# ============================================================================

class User(BaseModel):
    """User model."""
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    location_city: Optional[str] = None
    preferences: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ============================================================================
# ORDER MODELS
# ============================================================================

class OrderItemInput(BaseModel):
    """Input model for order item."""
    pizza_id: str
    size: str = "medium"
    quantity: int = Field(default=1, ge=1)
    toppings: list[str] = Field(default_factory=list)


class OrderItem(BaseModel):
    """Order item model."""
    id: str
    order_id: str
    pizza_id: str
    pizza_name: str
    size: str
    quantity: int
    toppings: list[str] = Field(default_factory=list)
    item_price: float

    class Config:
        from_attributes = True


class Order(BaseModel):
    """Order model."""
    id: str
    user_id: str
    nickname: Optional[str] = None
    status: str = OrderStatus.PENDING.value
    total_price: float
    created_at: datetime
    updated_at: datetime
    items: list[OrderItem] = Field(default_factory=list)

    class Config:
        from_attributes = True


class OrderSummary(BaseModel):
    """Order summary model (without items)."""
    id: str
    user_id: str
    nickname: Optional[str] = None
    status: str
    total_price: float
    created_at: datetime

    class Config:
        from_attributes = True


class PlaceOrderInput(BaseModel):
    """Input model for placing an order."""
    userId: str = Field(..., description="ID of the user placing the order")
    nickname: Optional[str] = Field(None, description="Optional nickname for the order")
    items: list[OrderItemInput] = Field(..., description="List of items in the order")


class DeleteOrderInput(BaseModel):
    """Input model for deleting/cancelling an order."""
    id: str = Field(..., description="ID of the order to cancel")
    userId: str = Field(..., description="ID of the user that placed the order")


# ============================================================================
# STORE LOCATION MODELS
# ============================================================================

class StoreHours(BaseModel):
    """Store operating hours."""
    monday: Optional[str] = None
    tuesday: Optional[str] = None
    wednesday: Optional[str] = None
    thursday: Optional[str] = None
    friday: Optional[str] = None
    saturday: Optional[str] = None
    sunday: Optional[str] = None


class StoreLocation(BaseModel):
    """Store location model."""
    id: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    hours: dict = Field(default_factory=dict)
    is_active: bool = True

    class Config:
        from_attributes = True


# ============================================================================
# OFFER MODELS
# ============================================================================

class Offer(BaseModel):
    """Offer/discount model."""
    id: str
    location_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    min_order_amount: float = 0.0
    code: Optional[str] = None
    valid_from: datetime
    valid_until: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    code: str
