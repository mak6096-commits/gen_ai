#!/usr/bin/env python3
"""
Ultra-minimal FastAPI server for maximum compatibility
No advanced Pydantic features, works with any Python version
"""

import os
import sys
import hmac
import hashlib
import base64
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    from fastapi import FastAPI, HTTPException, Request, Header
    from pydantic import BaseModel
    from enum import Enum
    import uvicorn
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Simple models without any validation decorators
class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"

class ProductCreate(BaseModel):
    sku: str
    name: str
    price: float
    stock: int

class Product(BaseModel):
    id: int
    sku: str
    name: str
    price: float
    stock: int

class OrderCreate(BaseModel):
    product_id: int
    quantity: int
    status: str = "PENDING"

class Order(BaseModel):
    id: int
    product_id: int
    quantity: int
    status: str
    created_at: datetime

class PaymentWebhook(BaseModel):
    event_type: str
    order_id: int
    payment_id: str = "pay_123"
    amount: float
    timestamp: Optional[datetime] = None

# Storage
products_db: Dict[int, Product] = {}
orders_db: Dict[int, Order] = {}
product_counter = 0
order_counter = 0

# FastAPI App
app = FastAPI(
    title="Orders & Inventory Microservice",
    version="1.0.0",
    description="A simple microservice for managing products and orders"
)

# Webhook security
def verify_webhook_signature(signature: str, payload: bytes, secret: str) -> bool:
    if not signature.startswith('sha256='):
        return False
    expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    expected_signature_b64 = base64.b64encode(expected_signature).decode()
    provided_signature = signature[7:]
    return hmac.compare_digest(expected_signature_b64, provided_signature)

# Routes
@app.get("/")
async def root():
    return {"message": "Orders & Inventory Microservice", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "orders-inventory",
        "products_count": len(products_db),
        "orders_count": len(orders_db)
    }

@app.post("/products", status_code=201)
async def create_product(product: ProductCreate):
    global product_counter
    
    # Manual validation
    if product.price <= 0:
        raise HTTPException(status_code=422, detail="Price must be greater than 0")
    if product.stock < 0:
        raise HTTPException(status_code=422, detail="Stock cannot be negative")
    
    # Check duplicate SKU
    for existing_product in products_db.values():
        if existing_product.sku == product.sku:
            raise HTTPException(status_code=409, detail="Product with this SKU already exists")
    
    product_counter += 1
    new_product = Product(
        id=product_counter,
        sku=product.sku,
        name=product.name,
        price=product.price,
        stock=product.stock
    )
    products_db[product_counter] = new_product
    return new_product

@app.get("/products")
async def get_products():
    return list(products_db.values())

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]

@app.post("/orders", status_code=201)
async def create_order(order: OrderCreate):
    global order_counter
    
    # Manual validation
    if order.quantity <= 0:
        raise HTTPException(status_code=422, detail="Quantity must be greater than 0")
    
    if order.product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[order.product_id]
    if product.stock < order.quantity:
        raise HTTPException(status_code=409, detail=f"Insufficient stock. Available: {product.stock}")
    
    # Update stock
    product.stock -= order.quantity
    
    order_counter += 1
    new_order = Order(
        id=order_counter,
        product_id=order.product_id,
        quantity=order.quantity,
        status="PENDING",
        created_at=datetime.utcnow()
    )
    orders_db[order_counter] = new_order
    return new_order

@app.get("/orders")
async def get_orders():
    return list(orders_db.values())

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]

@app.post("/webhooks/payment")
async def process_payment_webhook(request: Request, x_webhook_signature: str = Header(..., alias="X-Webhook-Signature")):
    webhook_secret = os.getenv("WEBHOOK_SECRET", "webhook-secret-key")
    payload = await request.body()
    
    if not verify_webhook_signature(x_webhook_signature, payload, webhook_secret):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")
    
    try:
        data = json.loads(payload)
        webhook_data = PaymentWebhook(**data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid payload: {str(e)}")
    
    if webhook_data.order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[webhook_data.order_id]
    if webhook_data.event_type == "payment.succeeded":
        order.status = "PAID"
        return {"status": "processed", "order_id": webhook_data.order_id, "new_status": order.status}
    
    return {"status": "ignored", "reason": f"Unhandled event type: {webhook_data.event_type}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8007))
    print(f"🚀 Starting ultra-compatible FastAPI server on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
