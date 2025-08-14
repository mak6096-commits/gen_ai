from locust import HttpUser, task, between
import random
import json


class OrdersInventoryUser(HttpUser):
    """
    Locust user behavior for load testing the Orders & Inventory API
    
    Simulates realistic user behavior:
    - 70% reads (get products, get orders)
    - 30% writes (create orders, update products)
    """
    
    wait_time = between(0.1, 0.5)  # 100-500ms between requests
    
    def on_start(self):
        """Create test products for this user"""
        self.products = []
        
        # Create 3 test products
        for i in range(3):
            product_data = {
                "sku": f"LOAD-{random.randint(10000, 99999)}-{i}",
                "name": f"Load Test Product {i}",
                "price": round(random.uniform(10, 100), 2),
                "stock": random.randint(50, 200)
            }
            
            with self.client.post("/products", json=product_data, catch_response=True) as response:
                if response.status_code == 201:
                    product = response.json()
                    self.products.append(product)
                    response.success()
                else:
                    response.failure(f"Failed to create product: {response.status_code}")
    
    @task(40)  # 40% of requests
    def get_products(self):
        """Get list of all products"""
        with self.client.get("/products", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get products: {response.status_code}")
    
    @task(30)  # 30% of requests
    def get_random_product(self):
        """Get a specific product"""
        if self.products:
            product = random.choice(self.products)
            with self.client.get(f"/products/{product['id']}", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # Expected for deleted products
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(20)  # 20% of requests
    def create_order(self):
        """Create an order for a random product"""
        if self.products:
            product = random.choice(self.products)
            order_data = {
                "product_id": product["id"],
                "quantity": random.randint(1, 5)
            }
            
            with self.client.post("/orders", json=order_data, catch_response=True) as response:
                if response.status_code == 201:
                    response.success()
                elif response.status_code == 409:
                    # Insufficient stock - expected behavior
                    response.success()
                elif response.status_code == 404:
                    # Product not found - possible if deleted
                    response.success()
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(5)  # 5% of requests
    def get_orders(self):
        """Get list of orders"""
        with self.client.get("/orders", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get orders: {response.status_code}")
    
    @task(3)  # 3% of requests
    def update_product_stock(self):
        """Update product stock"""
        if self.products:
            product = random.choice(self.products)
            update_data = {
                "stock": random.randint(10, 100)
            }
            
            with self.client.put(f"/products/{product['id']}", json=update_data, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # Product might have been deleted
                else:
                    response.failure(f"Failed to update product: {response.status_code}")
    
    @task(2)  # 2% of requests
    def health_check(self):
        """Health check endpoint"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class HeavyUser(HttpUser):
    """
    Heavy user that creates more orders and stress-tests stock management
    """
    
    wait_time = between(0.05, 0.2)  # Faster requests
    
    def on_start(self):
        """Create products with limited stock for stress testing"""
        self.products = []
        
        for i in range(2):
            product_data = {
                "sku": f"STRESS-{random.randint(10000, 99999)}-{i}",
                "name": f"Stress Test Product {i}",
                "price": round(random.uniform(5, 50), 2),
                "stock": random.randint(5, 20)  # Lower stock for stress testing
            }
            
            with self.client.post("/products", json=product_data, catch_response=True) as response:
                if response.status_code == 201:
                    product = response.json()
                    self.products.append(product)
    
    @task(60)
    def rapid_order_creation(self):
        """Rapidly create orders to test concurrency"""
        if self.products:
            product = random.choice(self.products)
            order_data = {
                "product_id": product["id"],
                "quantity": random.randint(1, 3)
            }
            
            with self.client.post("/orders", json=order_data, catch_response=True) as response:
                if response.status_code in [201, 409, 404]:
                    response.success()
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(40)
    def check_product_stock(self):
        """Check product stock frequently"""
        if self.products:
            product = random.choice(self.products)
            with self.client.get(f"/products/{product['id']}", catch_response=True) as response:
                if response.status_code in [200, 404]:
                    response.success()
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")


# Usage instructions:
# 
# Light load test:
# locust -f scripts/locust_test.py --users 25 --spawn-rate 5 --host http://localhost:8000
#
# Heavy load test:
# locust -f scripts/locust_test.py OrdersInventoryUser HeavyUser --users 200 --spawn-rate 20 --host http://localhost:8000
