from fastapi import FastAPI, HTTPException, Request, Header
from typing import List, Optional, Dict, Any
import os
import hmac
import hashlib
import base64
import json
from datetime import datetime

from app.models import (
    Product, Order, ProductCreate, ProductUpdate, ProductResponse,
    OrderCreate, OrderUpdate, OrderResponse, ErrorResponse, OrderStatus,
    PaymentWebhook
)

# Simple in-memory storage
products_db: Dict[int, Product] = {}
orders_db: Dict[int, Order] = {}
product_counter = 0
order_counter = 0

# Create FastAPI app with metadata
app = FastAPI(
    title="Orders & Inventory Microservice",
    version="1.0.0",
    description="""
    A FastAPI-based microservice for managing products and orders in an online store.
    
    ## Features
    
    * **Products**: Full CRUD operations with stock management
    * **Orders**: Create and manage orders with automatic stock reduction
    * **Webhooks**: Secure payment processing with HMAC verification
    * **Validation**: Comprehensive input validation and error handling
    
    ## Authentication
    
    * Webhook endpoints require HMAC-SHA256 signature verification
    * API endpoints are currently open (add API keys in production)
    """,
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Webhook security
def verify_webhook_signature(signature: str, payload: bytes, secret: str) -> bool:
    """Verify HMAC-SHA256 signature"""
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).digest()
    expected_signature_b64 = base64.b64encode(expected_signature).decode()
    
    provided_signature = signature[7:]  # Remove 'sha256=' prefix
    return hmac.compare_digest(expected_signature_b64, provided_signature)

# Root endpoint
@app.get("/", tags=["General"])
async def root():
    """Welcome message and API information"""
    return {
        "message": "Orders & Inventory Microservice",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {
        "status": "healthy",
        "service": "orders-inventory",
        "timestamp": datetime.utcnow().isoformat(),
        "products_count": len(products_db),
        "orders_count": len(orders_db)
    }

# Product endpoints
@app.post("/products", response_model=ProductResponse, status_code=201, tags=["Products"])
async def create_product(product: ProductCreate):
    """Create a new product with unique SKU validation"""
    global product_counter
    
    # Check for duplicate SKU
    for existing_product in products_db.values():
        if existing_product.sku == product.sku:
            raise HTTPException(status_code=409, detail="Product with this SKU already exists")
    
    product_counter += 1
    new_product = Product(id=product_counter, **product.dict())
    products_db[product_counter] = new_product
    return new_product

@app.get("/products", response_model=List[ProductResponse], tags=["Products"])
async def get_products():
    """List all products"""
    return list(products_db.values())

@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def get_product(product_id: int):
    """Get a specific product by ID"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]

@app.put("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def update_product(product_id: int, product: ProductUpdate):
    """Update a product (partial updates supported)"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    existing_product = products_db[product_id]
    
    # Check for SKU conflicts if updating SKU
    if product.sku and product.sku != existing_product.sku:
        for other_id, other_product in products_db.items():
            if other_id != product_id and other_product.sku == product.sku:
                raise HTTPException(status_code=409, detail="Product with this SKU already exists")
    
    # Update fields
    update_data = product.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_product, field, value)
    
    return existing_product

@app.delete("/products/{product_id}", status_code=204, tags=["Products"])
async def delete_product(product_id: int):
    """Delete a product"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if product has associated orders
    for order in orders_db.values():
        if order.product_id == product_id:
            raise HTTPException(status_code=400, detail="Cannot delete product with existing orders")
    
    del products_db[product_id]
    return None

# Order endpoints
@app.post("/orders", response_model=OrderResponse, status_code=201, tags=["Orders"])
async def create_order(order: OrderCreate):
    """Create a new order with automatic stock reduction"""
    global order_counter
    
    # Check if product exists and has sufficient stock
    if order.product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[order.product_id]
    if product.stock < order.quantity:
        raise HTTPException(
            status_code=409, 
            detail=f"Insufficient stock. Available: {product.stock}, Requested: {order.quantity}"
        )
    
    # Reduce stock atomically
    product.stock -= order.quantity
    
    # Create order
    order_counter += 1
    new_order = Order(
        id=order_counter,
        product_id=order.product_id,
        quantity=order.quantity,
        status=OrderStatus.PENDING,
        created_at=datetime.utcnow()
    )
    orders_db[order_counter] = new_order
    return new_order

@app.get("/orders", response_model=List[OrderResponse], tags=["Orders"])
async def get_orders():
    """List all orders"""
    return list(orders_db.values())

@app.get("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
async def get_order(order_id: int):
    """Get a specific order by ID"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]

@app.put("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
async def update_order(order_id: int, order: OrderUpdate):
    """Update order status with validation"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    existing_order = orders_db[order_id]
    
    # Update fields
    update_data = order.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_order, field, value)
    
    return existing_order

# Webhook endpoints
@app.post("/webhooks/payment", tags=["Webhooks"])
async def process_payment_webhook(
    request: Request, 
    x_webhook_signature: str = Header(..., alias="X-Webhook-Signature")
):
    """Process payment webhook with HMAC verification"""
    webhook_secret = os.getenv("WEBHOOK_SECRET", "webhook-secret-key")
    
    # Get raw payload
    payload = await request.body()
    
    # Verify signature
    if not verify_webhook_signature(x_webhook_signature, payload, webhook_secret):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")
    
    # Parse payload
    try:
        data = json.loads(payload)
        webhook_data = PaymentWebhook(**data)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid payload: {str(e)}")
    
    # Process payment
    if webhook_data.order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[webhook_data.order_id]
    
    if webhook_data.event_type == "payment.succeeded":
        order.status = OrderStatus.PAID
        return {
            "status": "processed",
            "order_id": webhook_data.order_id,
            "new_status": order.status.value
        }
    
    return {"status": "ignored", "reason": f"Unhandled event type: {webhook_data.event_type}"}

# Error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global exception handler for consistent error responses"""
    return {
        "detail": exc.detail,
        "status_code": exc.status_code
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
