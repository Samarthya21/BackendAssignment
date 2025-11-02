# Credit Approval System

A Django-based REST API system for managing customer loans, credit scoring, and loan eligibility checks.

## Features

- **Customer Management**: Register customers with auto-calculated credit limits
- **Credit Scoring**: Intelligent algorithm evaluating payment history, loan count, and credit utilization
- **Loan Eligibility**: Check eligibility with dynamic interest rate adjustment
- **Loan Creation**: Automated loan approval based on credit scores
- **Data Ingestion**: Import customer and loan data from CSV files
- **Background Tasks**: Celery-based async processing
- **API Documentation**: Interactive Swagger UI and ReDoc

## Technology Stack

- **Framework**: Django 4.2.16 with Django Rest Framework 3.15.2
- **Database**: PostgreSQL 15+
- **Task Queue**: Celery 5.5+ with Redis
- **Python**: 3.11+ (tested on 3.13.5)
- **API Documentation**: drf-spectacular (OpenAPI 3.0)

## Requirements

- Python 3.11 or higher
- PostgreSQL 15 or higher
- Redis (for Celery)
- pip and virtualenv

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd BackendAssignment
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=credit_approval_db
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Application Settings
APPROVED_LIMIT_MULTIPLIER=36
MAX_EMI_TO_SALARY_RATIO=0.5
```

### 5. Set Up PostgreSQL Database

```bash
# Create database
createdb credit_approval_db

# Or using psql:
psql -U postgres
CREATE DATABASE credit_approval_db;
\q
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 8. Ingest Sample Data

```bash
# Synchronous ingestion
python manage.py ingest_data

# Or with custom file paths
python manage.py ingest_data --customer-file=data/customerData.csv --loan-file=data/loanData.csv
```

## Running the Application

### 1. Start Redis (in a separate terminal)

```bash
redis-server
```

### 2. Start Celery Worker (in a separate terminal)

```bash
celery -A config worker -l info
```

### 3. Start Django Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000/api/`

## API Endpoints

### Customer Endpoints

#### Register Customer
```http
POST /api/register/
Content-Type: application/json

{
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "monthly_income": 50000,
    "phone_number": "9876543210"
}
```

**Response (201 Created):**
```json
{
    "customer_id": 1,
    "name": "John Doe",
    "age": 30,
    "monthly_income": 50000,
    "approved_limit": 1800000,
    "phone_number": "9876543210"
}
```

### Loan Endpoints

#### Check Eligibility
```http
POST /api/check-eligibility/
Content-Type: application/json

{
    "customer_id": 1,
    "loan_amount": 200000,
    "interest_rate": 10.5,
    "tenure": 24
}
```

**Response (200 OK):**
```json
{
    "customer_id": 1,
    "approval": true,
    "interest_rate": 10.5,
    "corrected_interest_rate": 10.5,
    "tenure": 24,
    "monthly_installment": 9251.48
}
```

#### Create Loan
```http
POST /api/create-loan/
Content-Type: application/json

{
    "customer_id": 1,
    "loan_amount": 200000,
    "interest_rate": 10.5,
    "tenure": 24
}
```

**Response (201 Created):**
```json
{
    "loan_id": 1,
    "customer_id": 1,
    "loan_approved": true,
    "message": "Loan approved successfully",
    "monthly_installment": 9251.48
}
```

#### View Loan Details
```http
GET /api/view-loan/1/
```

#### View Customer's All Loans
```http
GET /api/view-loans/1/
```

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Credit Scoring Algorithm

The credit score (0-100) is calculated based on:

### Components

1. **Payment History** (0-40 points)
   - Percentage of EMIs paid on time across all loans
   - Higher payment rate = higher score

2. **Loan Count** (0-20 points)
   - Number of past loans taken
   - Fewer loans = higher score

3. **Current Year Activity** (0-20 points)
   - Loans taken in current year
   - Fewer recent loans = higher score

4. **Credit Utilization** (0-20 points)
   - Current debt vs approved limit
   - Lower utilization = higher score

### Approval Rules

| Credit Score | Decision | Interest Rate |
|-------------|----------|---------------|
| > 50 | Approve | As requested |
| 30-50 | Approve | Minimum 12% |
| 10-30 | Approve | Minimum 16% |
| ≤ 10 | Reject | N/A |
| Current debt > Approved limit | Reject | N/A |
| EMI > 50% of salary | Reject | N/A |

## Project Structure

```
BackendAssignment/
├── apps/
│   ├── customers/          # Customer app
│   │   ├── models.py       # Customer model
│   │   ├── serializers.py  # API serializers
│   │   ├── views.py        # API views
│   │   ├── admin.py        # Django admin config
│   │   └── urls.py         # URL routing
│   ├── loans/              # Loan app
│   │   ├── models.py       # Loan model
│   │   ├── serializers.py  # API serializers
│   │   ├── views.py        # API views
│   │   ├── admin.py        # Django admin config
│   │   └── urls.py         # URL routing
│   └── core/               # Core utilities
│       ├── utils.py        # Helper functions
│       ├── validators.py   # Custom validators
│       ├── credit_scoring.py  # Credit scoring engine
│       └── management/     # Django commands
│           └── commands/
│               └── ingest_data.py
├── config/                 # Project configuration
│   ├── settings/           # Settings split
│   │   ├── base.py        # Base settings
│   │   ├── development.py # Dev settings
│   │   └── production.py  # Prod settings
│   ├── celery.py          # Celery configuration
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI application
├── tasks/                  # Celery tasks
│   └── ingestion.py       # Data ingestion tasks
├── data/                   # CSV data files
│   ├── customerData.csv
│   └── loanData.csv
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov=tasks

# Run specific test file
pytest apps/customers/tests.py
```

### Code Quality

```bash
# Format code with black
black .

# Check linting with flake8
flake8

# Sort imports
isort .
```

### Django Admin

Access the admin interface at: http://localhost:8000/admin/

Use the superuser credentials created earlier.

## Data Ingestion

### CSV File Format

**customerData.csv:**
```csv
Customer ID,First Name,Last Name,Age,Phone Number,Monthly Salary,Approved Limit
1,John,Doe,30,9876543210,50000,1800000
```

**loanData.csv:**
```csv
Customer ID,Loan ID,Loan Amount,Tenure,Interest Rate,Monthly payment,EMIs paid on Time,Date of Approval,End Date
1,1,200000,24,10.5,9251.48,12,2024-01-01,2026-01-01
```

### Async Ingestion

```bash
# Run ingestion as background task
python manage.py ingest_data --async

# Check Celery worker logs for progress
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -U postgres -d credit_approval_db
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping
# Should respond: PONG
```

### Import Errors

Make sure virtual environment is activated and all dependencies are installed:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Migration Issues

```bash
# Reset migrations (WARNING: deletes all data)
python manage.py migrate --fake-zero
python manage.py migrate
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed host names | `localhost` |
| `DB_NAME` | Database name | `credit_approval_db` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | Required |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `APPROVED_LIMIT_MULTIPLIER` | Credit limit multiplier | `36` |
| `MAX_EMI_TO_SALARY_RATIO` | Max EMI ratio | `0.5` |

## License

This project is developed as part of an internship assignment.

## Support

For issues or questions, please contact the development team.
