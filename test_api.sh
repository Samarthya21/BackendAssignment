#!/bin/bash

echo "=== Testing Credit Approval System API ==="
echo ""

# Test 1: Register a customer
echo "1. Testing Customer Registration (POST /api/register/)"
echo "---------------------------------------------------"
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "phone_number": "9876543210",
    "monthly_income": 50000
  }'
echo -e "\n\n"

# Test 2: Register another customer
echo "2. Registering another customer"
echo "---------------------------------------------------"
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "age": 28,
    "phone_number": "9876543211",
    "monthly_income": 75000
  }'
echo -e "\n\n"

# Test 3: Check loan eligibility
echo "3. Testing Loan Eligibility Check (POST /api/check-eligibility/)"
echo "---------------------------------------------------"
curl -X POST http://127.0.0.1:8000/api/check-eligibility/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "loan_amount": 100000,
    "interest_rate": 12.5,
    "tenure": 12
  }'
echo -e "\n\n"

# Test 4: Create a loan
echo "4. Testing Loan Creation (POST /api/create-loan/)"
echo "---------------------------------------------------"
curl -X POST http://127.0.0.1:8000/api/create-loan/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "loan_amount": 100000,
    "interest_rate": 12.5,
    "tenure": 12
  }'
echo -e "\n\n"

# Test 5: View specific loan
echo "5. Testing View Loan (GET /api/view-loan/1/)"
echo "---------------------------------------------------"
curl -X GET http://127.0.0.1:8000/api/view-loan/1/
echo -e "\n\n"

# Test 6: View all loans for customer
echo "6. Testing View Customer Loans (GET /api/view-loans/1/)"
echo "---------------------------------------------------"
curl -X GET http://127.0.0.1:8000/api/view-loans/1/
echo -e "\n\n"

echo "=== All tests completed ==="
