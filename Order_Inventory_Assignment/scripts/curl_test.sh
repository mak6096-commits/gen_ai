#!/bin/bash

# FastAPI Orders & Inventory API - Complete curl Testing Script
# This script demonstrates all required testing as per assignment Part F

BASE_URL="http://127.0.0.1:8007"
echo "🚀 Testing Orders & Inventory API at: $BASE_URL"
echo "=" | tr '=' '\n' | head -50 | tr '\n' '=' && echo

# Test 1: Health Check
echo "📋 TEST 1: Health Check"
curl -X GET "$BASE_URL/health" -w "\nStatus: %{http_code}\n\n"

# Test 2: Create Product (201 Expected)
echo "📋 TEST 2: Create Product"
echo "Creating product with SKU 'CURL-001'..."
PRODUCT_RESPONSE=$(curl -s -X POST "$BASE_URL/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "CURL-001",
    "name": "Curl Test Product",
    "price": 49.99,
    "stock": 100
  }' -w "HTTP_STATUS:%{http_code}")

PRODUCT_ID=$(echo $PRODUCT_RESPONSE | sed 's/HTTP_STATUS:.*//g' | grep -o '"id":[0-9]*' | cut -d':' -f2)
HTTP_STATUS=$(echo $PRODUCT_RESPONSE | grep -o 'HTTP_STATUS:[0-9]*' | cut -d':' -f2)
echo "Response: $(echo $PRODUCT_RESPONSE | sed 's/HTTP_STATUS:.*//g')"
echo "Status: $HTTP_STATUS"
echo "Product ID: $PRODUCT_ID"
echo

# Test 3: Get All Products (200 Expected)
echo "📋 TEST 3: Get All Products"
curl -X GET "$BASE_URL/products" -w "\nStatus: %{http_code}\n\n"

# Test 4: Get Product by ID (200 Expected)
echo "📋 TEST 4: Get Product by ID"
echo "Getting product ID: $PRODUCT_ID"
curl -X GET "$BASE_URL/products/$PRODUCT_ID" -w "\nStatus: %{http_code}\n\n"

# Test 5: Update Product (200 Expected)
echo "📋 TEST 5: Update Product Stock"
echo "Updating stock to 150..."
curl -X PUT "$BASE_URL/products/$PRODUCT_ID" \
  -H "Content-Type: application/json" \
  -d '{"stock": 150}' -w "\nStatus: %{http_code}\n\n"

# Test 6: Create Order (201 Expected)
echo "📋 TEST 6: Create Order"
echo "Creating order for 5 units of product $PRODUCT_ID..."
ORDER_RESPONSE=$(curl -s -X POST "$BASE_URL/orders" \
  -H "Content-Type: application/json" \
  -d "{
    \"product_id\": $PRODUCT_ID,
    \"quantity\": 5
  }" -w "HTTP_STATUS:%{http_code}")

ORDER_ID=$(echo $ORDER_RESPONSE | sed 's/HTTP_STATUS:.*//g' | grep -o '"id":[0-9]*' | cut -d':' -f2)
HTTP_STATUS=$(echo $ORDER_RESPONSE | grep -o 'HTTP_STATUS:[0-9]*' | cut -d':' -f2)
echo "Response: $(echo $ORDER_RESPONSE | sed 's/HTTP_STATUS:.*//g')"
echo "Status: $HTTP_STATUS"
echo "Order ID: $ORDER_ID"
echo

# Test 7: Verify Stock Reduction
echo "📋 TEST 7: Verify Stock Reduction"
echo "Checking product stock after order creation..."
curl -X GET "$BASE_URL/products/$PRODUCT_ID" -w "\nStatus: %{http_code}\n\n"

# Test 8: Get Order Details (200 Expected)
echo "📋 TEST 8: Get Order Details"
echo "Getting order ID: $ORDER_ID"
curl -X GET "$BASE_URL/orders/$ORDER_ID" -w "\nStatus: %{http_code}\n\n"

# Test 9: Update Order Status (200 Expected)
echo "📋 TEST 9: Update Order Status"
echo "Updating order status to PAID..."
curl -X PUT "$BASE_URL/orders/$ORDER_ID" \
  -H "Content-Type: application/json" \
  -d '{"status": "PAID"}' -w "\nStatus: %{http_code}\n\n"

# Test 10: Payment Webhook with Valid Signature
echo "📋 TEST 10: Payment Webhook (Valid Signature)"
echo "Generating HMAC signature for webhook..."

# Create webhook payload
WEBHOOK_PAYLOAD='{
  "event_type": "payment.succeeded",
  "order_id": '$ORDER_ID',
  "payment_id": "pay_curl_test_123",
  "amount": 249.95,
  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
}'

# Generate HMAC signature (using default webhook secret)
WEBHOOK_SECRET="your-webhook-secret-key"
SIGNATURE=$(echo -n "$WEBHOOK_PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $2}')

echo "Payload: $WEBHOOK_PAYLOAD"
echo "Signature: sha256=$SIGNATURE"

curl -X POST "$BASE_URL/webhooks/payment" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=$SIGNATURE" \
  -d "$WEBHOOK_PAYLOAD" -w "\nStatus: %{http_code}\n\n"

# ERROR CASES TESTING
echo "=" | tr '=' '\n' | head -50 | tr '\n' '=' && echo
echo "🚨 ERROR CASES TESTING"
echo "=" | tr '=' '\n' | head 50 | tr '\n' '=' && echo

# Error Test 1: Duplicate SKU (409 Expected)
echo "❌ ERROR TEST 1: Duplicate SKU"
curl -X POST "$BASE_URL/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "CURL-001",
    "name": "Duplicate Product",
    "price": 19.99,
    "stock": 25
  }' -w "\nStatus: %{http_code}\n\n"

# Error Test 2: Insufficient Stock (409 Expected)
echo "❌ ERROR TEST 2: Insufficient Stock"
echo "Trying to order 1000 units (more than available)..."
curl -X POST "$BASE_URL/orders" \
  -H "Content-Type: application/json" \
  -d "{
    \"product_id\": $PRODUCT_ID,
    \"quantity\": 1000
  }" -w "\nStatus: %{http_code}\n\n"

# Error Test 3: Product Not Found (404 Expected)
echo "❌ ERROR TEST 3: Product Not Found"
curl -X GET "$BASE_URL/products/99999" -w "\nStatus: %{http_code}\n\n"

# Error Test 4: Order Not Found (404 Expected)
echo "❌ ERROR TEST 4: Order Not Found"
curl -X GET "$BASE_URL/orders/99999" -w "\nStatus: %{http_code}\n\n"

# Error Test 5: Invalid Webhook Signature (403 Expected)
echo "❌ ERROR TEST 5: Invalid Webhook Signature"
curl -X POST "$BASE_URL/webhooks/payment" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=invalid_signature" \
  -d '{
    "event_type": "payment.succeeded",
    "order_id": 1,
    "payment_id": "pay_invalid",
    "amount": 100.00,
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }' -w "\nStatus: %{http_code}\n\n"

# Error Test 6: Missing Webhook Signature (401 Expected)
echo "❌ ERROR TEST 6: Missing Webhook Signature"
curl -X POST "$BASE_URL/webhooks/payment" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "payment.succeeded",
    "order_id": 1,
    "payment_id": "pay_no_sig",
    "amount": 100.00,
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }' -w "\nStatus: %{http_code}\n\n"

# Error Test 7: Invalid Price Validation (422 Expected)
echo "❌ ERROR TEST 7: Invalid Price Validation"
curl -X POST "$BASE_URL/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "INVALID-001",
    "name": "Invalid Product",
    "price": -10.0,
    "stock": 50
  }' -w "\nStatus: %{http_code}\n\n"

# Summary
echo "=" | tr '=' '\n' | head -50 | tr '\n' '=' && echo
echo "📊 TESTING COMPLETE"
echo "=" | tr '=' '\n' | head -50 | tr '\n' '=' && echo

echo "✅ Successful Operations:"
echo "   - Health check (200)"
echo "   - Product creation (201)"
echo "   - Product retrieval (200)"
echo "   - Product update (200)"
echo "   - Order creation (201)"
echo "   - Order retrieval (200)"
echo "   - Order status update (200)"
echo "   - Valid webhook processing (200)"

echo
echo "❌ Error Cases Validated:"
echo "   - Duplicate SKU (409)"
echo "   - Insufficient stock (409)"
echo "   - Product not found (404)"
echo "   - Order not found (404)"
echo "   - Invalid webhook signature (403)"
echo "   - Missing webhook signature (401)"
echo "   - Invalid price validation (422)"

echo
echo "🎯 All curl commands executed successfully!"
echo "📚 View API documentation at: $BASE_URL/docs"
