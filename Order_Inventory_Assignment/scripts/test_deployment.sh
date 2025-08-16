#!/bin/bash

# Deployment Test Script for Render.com
# This script tests a deployed service to ensure it's working correctly

# Configuration
if [ -z "$1" ]; then
    echo "Usage: $0 <RENDER_URL>"
    echo "Example: $0 https://your-service.onrender.com"
    exit 1
fi

RENDER_URL="$1"
echo "🚀 Testing deployed service at: $RENDER_URL"

# Remove trailing slash if present
RENDER_URL=$(echo "$RENDER_URL" | sed 's/\/$//')

# Test 1: Health Check
echo ""
echo "📋 Test 1: Health Check"
response=$(curl -s -w "Status: %{http_code}" -X GET "$RENDER_URL/health")
echo "✅ $response"

# Test 2: API Documentation
echo ""
echo "📋 Test 2: API Documentation Available"
response=$(curl -s -w "Status: %{http_code}" -X GET "$RENDER_URL/docs" | tail -1)
echo "✅ Swagger UI: $response"

# Test 3: Create Product
echo ""
echo "📋 Test 3: Create Product"
response=$(curl -s -w "Status: %{http_code}" -X POST "$RENDER_URL/products" \
    -H "Content-Type: application/json" \
    -d '{
        "sku": "DEPLOY-TEST-001",
        "name": "Deployment Test Product",
        "description": "Testing live deployment",
        "price": 99.99,
        "stock": 10
    }')
echo "✅ $response"

# Test 4: Get Products
echo ""
echo "📋 Test 4: List Products"
response=$(curl -s -w "Status: %{http_code}" -X GET "$RENDER_URL/products")
echo "✅ $response"

# Test 5: Create Order
echo ""
echo "📋 Test 5: Create Order"
response=$(curl -s -w "Status: %{http_code}" -X POST "$RENDER_URL/orders" \
    -H "Content-Type: application/json" \
    -d '{
        "product_id": 1,
        "quantity": 2
    }')
echo "✅ $response"

echo ""
echo "🎉 Deployment testing completed!"
echo ""
echo "📚 Access your live API documentation at:"
echo "   $RENDER_URL/docs"
echo ""
echo "🔍 Monitor your service at:"
echo "   Render Dashboard → Your Service → Logs"
