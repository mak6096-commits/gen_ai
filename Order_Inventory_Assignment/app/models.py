from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlmodel import SQLModel, Field as SQLField, create_engine, Session, select


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"


# Database Models (SQLModel)
class ProductBase(SQLModel):
    sku: str = SQLField(unique=True, index=True)
    name: str = SQLField(index=True)
    price: float = SQLField(gt=0)  # price > 0
    stock: int = SQLField(ge=0)    # stock >= 0


class Product(ProductBase, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)


class OrderBase(SQLModel):
    product_id: int = SQLField(foreign_key="product.id", index=True)
    quantity: int = SQLField(gt=0)  # quantity > 0
    status: OrderStatus = SQLField(default=OrderStatus.PENDING, index=True)


class Order(OrderBase, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    created_at: datetime = SQLField(default_factory=datetime.utcnow, index=True)


# API Request/Response Models
class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)


class ProductResponse(ProductBase):
    id: int


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    
    @validator('status')
    def validate_status_transition(cls, v, values):
        # Define allowed status transitions
        # This could be more complex in real scenarios
        return v


class OrderResponse(OrderBase):
    id: int
    created_at: datetime


# Webhook Models
class PaymentWebhook(BaseModel):
    event_type: str
    order_id: int
    payment_id: str
    amount: float
    timestamp: datetime


class ErrorResponse(BaseModel):
    detail: str
