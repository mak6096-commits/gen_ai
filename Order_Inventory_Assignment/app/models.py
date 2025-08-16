from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

# For older Pydantic compatibility, use simple in-memory storage instead of SQLModel
class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"


# Simple data models for in-memory storage (compatible with Pydantic v1)
class ProductBase(BaseModel):
    sku: str
    name: str
    price: float = Field(..., gt=0)  # price > 0
    stock: int = Field(..., ge=0)    # stock >= 0
    
    class Config:
        schema_extra = {
            "example": {
                "sku": "LAPTOP-001",
                "name": "MacBook Pro 16",
                "price": 2499.99,
                "stock": 25
            }
        }


class Product(ProductBase):
    id: int


class OrderBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)  # quantity > 0
    status: OrderStatus = OrderStatus.PENDING
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": 1,
                "quantity": 2
            }
        }


class Order(OrderBase):
    id: int
    created_at: datetime


# API Request/Response Models
class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)


class ProductResponse(Product):
    pass


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    
    @validator('status')
    def validate_status_transition(cls, v, values):
        # Define allowed status transitions
        # This could be more complex in real scenarios
        return v


class OrderResponse(Order):
    pass


# Webhook Models
class PaymentWebhook(BaseModel):
    event_type: str
    order_id: int
    payment_id: str = "pay_123"
    amount: float
    timestamp: Optional[datetime] = None
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()


class ErrorResponse(BaseModel):
    detail: str
