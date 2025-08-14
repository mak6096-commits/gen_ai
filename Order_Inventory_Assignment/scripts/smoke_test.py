#!/usr/bin/env python3
"""
Smoke test script for Orders & Inventory API
Tests basic functionality and validates responses
"""

import requests
import os
import json
import hmac
import hashlib
from datetime import datetime

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your-webhook-secret-key")

def test_api():
    """Run comprehensive smoke tests"""
    print(f"🚀 Starting smoke tests against: {BASE_URL}")
    
    try:
        # Test 1: Health check
        print("\n📋 Test 1: Health Check")
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print(f"✅ Health check passed: {response.json()}")
        
        # Test 2: Create product
        print("\n📋 Test 2: Create Product")
        product_data = {
            "sku": "TEST-001",
            "name": "Test Product",
            "price": 29.99,
            "stock": 100
        }
        response = requests.post(f"{BASE_URL}/products", json=product_data)
        assert response.status_code == 201, f"Product creation failed: {response.status_code}"
        product = response.json()
        product_id = product["id"]
        print(f"✅ Product created: ID {product_id}, SKU {product['sku']}")
        
        # Test 3: Get product
        print("\n📋 Test 3: Get Product")
        response = requests.get(f"{BASE_URL}/products/{product_id}")
        assert response.status_code == 200, f"Get product failed: {response.status_code}"
        retrieved_product = response.json()
        assert retrieved_product["sku"] == "TEST-001"
        print(f"✅ Product retrieved: {retrieved_product['name']}")
        
        # Test 4: Create order
        print("\n📋 Test 4: Create Order")
        order_data = {
            "product_id": product_id,
            "quantity": 2
        }
        response = requests.post(f"{BASE_URL}/orders", json=order_data)
        assert response.status_code == 201, f"Order creation failed: {response.status_code}"
        order = response.json()
        order_id = order["id"]
        print(f"✅ Order created: ID {order_id}, Status {order['status']}")
        
        # Test 5: Verify stock reduction
        print("\n📋 Test 5: Verify Stock Reduction")
        response = requests.get(f"{BASE_URL}/products/{product_id}")
        updated_product = response.json()
        expected_stock = 100 - 2  # Original stock minus order quantity
        assert updated_product["stock"] == expected_stock, f"Stock not reduced: {updated_product['stock']}"
        print(f"✅ Stock correctly reduced to: {updated_product['stock']}")
        
        # Test 6: Test webhook (payment processing)
        print("\n📋 Test 6: Test Payment Webhook")
        webhook_payload = {
            "event_type": "payment.succeeded",
            "order_id": order_id,
            "payment_id": f"pay_{datetime.now().timestamp()}",
            "amount": 59.98,  # 2 * 29.99
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Generate HMAC signature
        payload_bytes = json.dumps(webhook_payload).encode()
        signature = hmac.new(
            WEBHOOK_SECRET.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}"
        }
        
        response = requests.post(
            f"{BASE_URL}/webhooks/payment",
            data=payload_bytes,
            headers=headers
        )
        assert response.status_code == 200, f"Webhook failed: {response.status_code}"
        webhook_result = response.json()
        print(f"✅ Webhook processed: {webhook_result}")
        
        # Test 7: Verify order status updated
        print("\n📋 Test 7: Verify Order Status Updated")
        response = requests.get(f"{BASE_URL}/orders/{order_id}")
        updated_order = response.json()
        assert updated_order["status"] == "PAID", f"Order status not updated: {updated_order['status']}"
        print(f"✅ Order status updated to: {updated_order['status']}")
        
        # Test 8: Test error cases
        print("\n📋 Test 8: Error Cases")
        
        # Try to create order with insufficient stock
        large_order = {
            "product_id": product_id,
            "quantity": 200  # More than available stock
        }
        response = requests.post(f"{BASE_URL}/orders", json=large_order)
        assert response.status_code == 409, f"Should fail with insufficient stock: {response.status_code}"
        print(f"✅ Insufficient stock error handled correctly")
        
        # Try to get non-existent product
        response = requests.get(f"{BASE_URL}/products/99999")
        assert response.status_code == 404, f"Should return 404 for non-existent product: {response.status_code}"
        print(f"✅ 404 error handled correctly")
        
        # Test 9: List all resources
        print("\n📋 Test 9: List Resources")
        
        # List products
        response = requests.get(f"{BASE_URL}/products")
        assert response.status_code == 200
        products = response.json()
        assert len(products) >= 1
        print(f"✅ Listed {len(products)} products")
        
        # List orders
        response = requests.get(f"{BASE_URL}/orders")
        assert response.status_code == 200
        orders = response.json()
        assert len(orders) >= 1
        print(f"✅ Listed {len(orders)} orders")
        
        print("\n🎉 All smoke tests passed successfully!")
        print(f"📊 Final order status: {updated_order}")
        
        return True
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_api()
    exit(0 if success else 1)
