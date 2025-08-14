import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import memory_store

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_data():
    """Reset data before each test"""
    memory_store.reset()
    yield
    memory_store.reset()

def test_create_product():
    """Test product creation"""
    product_data = {
        "sku": "TEST-001",
        "name": "Test Product",
        "price": 29.99,
        "stock": 100
    }
    response = client.post("/products", json=product_data)
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "TEST-001"
    assert data["id"] == 1

def test_create_duplicate_sku():
    """Test duplicate SKU error"""
    product_data = {
        "sku": "DUPLICATE",
        "name": "Product 1",
        "price": 10.0,
        "stock": 5
    }
    
    # Create first product
    response = client.post("/products", json=product_data)
    assert response.status_code == 201
    
    # Try to create duplicate
    response = client.post("/products", json=product_data)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

def test_get_products():
    """Test getting all products"""
    # Create a product first
    product_data = {
        "sku": "LIST-001",
        "name": "List Product",
        "price": 15.0,
        "stock": 25
    }
    client.post("/products", json=product_data)
    
    # Get all products
    response = client.get("/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 1
    assert products[0]["sku"] == "LIST-001"

def test_get_product_by_id():
    """Test getting product by ID"""
    # Create a product
    product_data = {
        "sku": "GET-001",
        "name": "Get Product",
        "price": 20.0,
        "stock": 30
    }
    response = client.post("/products", json=product_data)
    product_id = response.json()["id"]
    
    # Get product by ID
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["sku"] == "GET-001"

def test_get_nonexistent_product():
    """Test 404 for nonexistent product"""
    response = client.get("/products/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_update_product():
    """Test product update"""
    # Create a product
    product_data = {
        "sku": "UPDATE-001",
        "name": "Update Product",
        "price": 25.0,
        "stock": 40
    }
    response = client.post("/products", json=product_data)
    product_id = response.json()["id"]
    
    # Update product
    update_data = {"stock": 60, "price": 30.0}
    response = client.put(f"/products/{product_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["stock"] == 60
    assert data["price"] == 30.0
    assert data["name"] == "Update Product"  # Unchanged

def test_delete_product():
    """Test product deletion"""
    # Create a product
    product_data = {
        "sku": "DELETE-001",
        "name": "Delete Product",
        "price": 35.0,
        "stock": 50
    }
    response = client.post("/products", json=product_data)
    product_id = response.json()["id"]
    
    # Delete product
    response = client.delete(f"/products/{product_id}")
    assert response.status_code == 204
    
    # Verify it's gone
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 404

def test_invalid_price():
    """Test validation for invalid price"""
    product_data = {
        "sku": "INVALID-001",
        "name": "Invalid Product",
        "price": -10.0,  # Invalid: negative price
        "stock": 50
    }
    response = client.post("/products", json=product_data)
    assert response.status_code == 422

def test_invalid_stock():
    """Test validation for invalid stock"""
    product_data = {
        "sku": "INVALID-002",
        "name": "Invalid Product",
        "price": 10.0,
        "stock": -5  # Invalid: negative stock
    }
    response = client.post("/products", json=product_data)
    assert response.status_code == 422
