#!/bin/bash

# Credit Approval System - Setup Verification Script
# This script checks if all components are properly set up

echo "========================================"
echo "Credit Approval System - Setup Check"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -n "Checking Python version... "
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python not found"
fi

# Check Virtual Environment
echo -n "Checking virtual environment... "
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} venv directory exists"
else
    echo -e "${RED}✗${NC} venv directory not found"
fi

# Check PostgreSQL
echo -n "Checking PostgreSQL... "
if command -v psql &> /dev/null; then
    PG_VERSION=$(psql --version | cut -d' ' -f3)
    echo -e "${GREEN}✓${NC} PostgreSQL $PG_VERSION"
else
    echo -e "${YELLOW}!${NC} PostgreSQL not found (required for production)"
fi

# Check Redis
echo -n "Checking Redis... "
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓${NC} Redis is running"
    else
        echo -e "${YELLOW}!${NC} Redis installed but not running"
    fi
else
    echo -e "${YELLOW}!${NC} Redis not found (required for Celery)"
fi

# Check .env file
echo -n "Checking .env file... "
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
else
    echo -e "${YELLOW}!${NC} .env file not found (copy from .env.example)"
fi

# Check data files
echo -n "Checking data files... "
if [ -f "data/customerData.csv" ] && [ -f "data/loanData.csv" ]; then
    echo -e "${GREEN}✓${NC} CSV data files found"
else
    echo -e "${YELLOW}!${NC} CSV data files not found in data/ directory"
fi

# Check Django
echo -n "Checking Django installation... "
if [ -d "venv" ]; then
    source venv/bin/activate
    if python -c "import django" &> /dev/null; then
        DJANGO_VERSION=$(python -c "import django; print(django.get_version())")
        echo -e "${GREEN}✓${NC} Django $DJANGO_VERSION"
    else
        echo -e "${RED}✗${NC} Django not installed in venv"
    fi
else
    echo -e "${YELLOW}!${NC} Cannot check without venv"
fi

# Check migrations
echo -n "Checking migrations... "
if [ -f "apps/customers/migrations/0001_initial.py" ]; then
    echo -e "${GREEN}✓${NC} Migrations created"
else
    echo -e "${YELLOW}!${NC} Migrations not found"
fi

echo ""
echo "========================================"
echo "Setup Status Summary"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Install PostgreSQL (if not installed)"
echo "2. Install Redis (if not installed)"
echo "3. Copy .env.example to .env and configure"
echo "4. Create PostgreSQL database: createdb credit_approval_db"
echo "5. Run migrations: python manage.py migrate"
echo "6. Ingest data: python manage.py ingest_data"
echo "7. Start Redis: redis-server"
echo "8. Start Celery: celery -A config worker -l info"
echo "9. Start Django: python manage.py runserver"
echo ""
