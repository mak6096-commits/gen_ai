from typing import List, Optional
from fastapi import HTTPException
from sqlmodel import Session, select
from app.models import Product, Order, ProductCreate, ProductUpdate, OrderCreate, OrderUpdate, OrderStatus
from app.database import memory_store
from datetime import datetime


class ProductCRUD:
    """CRUD operations for Products"""
    
    @staticmethod
    def create_product(product_data: ProductCreate) -> Product:
        """Create a new product"""
        # Check for duplicate SKU
        if any(p.sku == product_data.sku for p in memory_store.products.values()):
            raise HTTPException(status_code=409, detail="Product with this SKU already exists")
        
        product = Product(
            id=memory_store.product_counter,
            **product_data.dict()
        )
        memory_store.products[product.id] = product
        memory_store.product_counter += 1
        return product
    
    @staticmethod
    def get_products() -> List[Product]:
        """Get all products"""
        return list(memory_store.products.values())
    
    @staticmethod
    def get_product(product_id: int) -> Product:
        """Get product by ID"""
        product = memory_store.products.get(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    
    @staticmethod
    def update_product(product_id: int, product_data: ProductUpdate) -> Product:
        """Update product"""
        product = ProductCRUD.get_product(product_id)
        
        # Check for duplicate SKU if updating SKU
        if product_data.sku and product_data.sku != product.sku:
            if any(p.sku == product_data.sku for p in memory_store.products.values()):
                raise HTTPException(status_code=409, detail="Product with this SKU already exists")
        
        # Update fields that are provided
        update_data = product_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        return product
    
    @staticmethod
    def delete_product(product_id: int) -> bool:
        """Delete product"""
        if product_id not in memory_store.products:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Check if product has pending orders
        pending_orders = [
            order for order in memory_store.orders.values()
            if order.product_id == product_id and order.status in [OrderStatus.PENDING, OrderStatus.PAID]
        ]
        if pending_orders:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete product with pending or paid orders"
            )
        
        del memory_store.products[product_id]
        return True


class OrderCRUD:
    """CRUD operations for Orders"""
    
    @staticmethod
    def create_order(order_data: OrderCreate) -> Order:
        """Create a new order and reduce stock atomically"""
        # Get product and check availability
        product = ProductCRUD.get_product(order_data.product_id)
        
        if product.stock < order_data.quantity:
            raise HTTPException(
                status_code=409, 
                detail=f"Insufficient stock. Available: {product.stock}, Requested: {order_data.quantity}"
            )
        
        # Atomically reduce stock and create order
        product.stock -= order_data.quantity
        
        order = Order(
            id=memory_store.order_counter,
            **order_data.dict(),
            created_at=datetime.utcnow()
        )
        memory_store.orders[order.id] = order
        memory_store.order_counter += 1
        
        return order
    
    @staticmethod
    def get_orders() -> List[Order]:
        """Get all orders"""
        return list(memory_store.orders.values())
    
    @staticmethod
    def get_order(order_id: int) -> Order:
        """Get order by ID"""
        order = memory_store.orders.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    
    @staticmethod
    def update_order(order_id: int, order_data: OrderUpdate) -> Order:
        """Update order (mainly status)"""
        order = OrderCRUD.get_order(order_id)
        
        # Validate status transitions
        if order_data.status:
            valid_transitions = {
                OrderStatus.PENDING: [OrderStatus.PAID, OrderStatus.CANCELED],
                OrderStatus.PAID: [OrderStatus.SHIPPED, OrderStatus.CANCELED],
                OrderStatus.SHIPPED: [],  # Final state
                OrderStatus.CANCELED: []  # Final state
            }
            
            if order_data.status not in valid_transitions.get(order.status, []):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status transition from {order.status} to {order_data.status}"
                )
        
        # Update fields
        update_data = order_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        
        return order
    
    @staticmethod
    def cancel_order(order_id: int) -> bool:
        """Cancel order and restore stock if not yet paid"""
        order = OrderCRUD.get_order(order_id)
        
        if order.status in [OrderStatus.SHIPPED, OrderStatus.CANCELED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel order with status: {order.status}"
            )
        
        # Restore stock if order is being canceled and not yet shipped
        if order.status != OrderStatus.SHIPPED:
            product = ProductCRUD.get_product(order.product_id)
            product.stock += order.quantity
        
        # Set order status to canceled
        order.status = OrderStatus.CANCELED
        return True
    
    @staticmethod
    def delete_order(order_id: int) -> bool:
        """Delete order (only if canceled)"""
        order = OrderCRUD.get_order(order_id)
        
        if order.status != OrderStatus.CANCELED:
            raise HTTPException(
                status_code=400,
                detail="Can only delete canceled orders. Use cancel operation instead."
            )
        
        del memory_store.orders[order_id]
        return True
