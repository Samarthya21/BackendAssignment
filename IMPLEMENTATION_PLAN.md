# Credit Approval System - Implementation Plan

## Project Overview
Building a Django-based Credit Approval System with REST API endpoints for managing customer loans, credit scoring, and loan eligibility checks.

---

## Technology Stack
- **Framework**: Django 4.2+ with Django Rest Framework (DRF)
- **Database**: PostgreSQL 15+
- **Task Queue**: Celery with Redis
- **Containerization**: Docker & Docker Compose
- **Python**: 3.11+
- **Additional Libraries**:
  - pandas (for Excel data ingestion)
  - openpyxl (Excel file handling)
  - psycopg2-binary (PostgreSQL adapter)
  - celery[redis] (background tasks)
  - django-celery-beat (scheduled tasks)
  - drf-spectacular (API documentation)
  - python-decouple (environment variables)

---

## Project Structure

```
credit_approval_system/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── manage.py
├── config/                      # Django project settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
├── apps/
│   ├── __init__.py
│   ├── customers/               # Customer management
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py          # Business logic
│   │   ├── admin.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_services.py
│   ├── loans/                   # Loan management
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py
│   │   ├── credit_scoring.py    # Credit score calculation
│   │   ├── admin.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       ├── test_services.py
│   │       └── test_credit_scoring.py
│   └── core/                    # Shared utilities
│       ├── __init__.py
│       ├── exceptions.py
│       ├── utils.py
│       └── validators.py
├── tasks/                       # Celery tasks
│   ├── __init__.py
│   └── data_ingestion.py
└── data/                        # Data files
    ├── customerData.csv
    └── loanData.csv
```

---

## Database Schema

### Customer Model
```python
- customer_id (PK, AutoField)
- first_name (CharField, max_length=100)
- last_name (CharField, max_length=100)
- age (PositiveIntegerField)
- phone_number (CharField, max_length=15, unique)
- monthly_salary (DecimalField, max_digits=12, decimal_places=2)
- approved_limit (DecimalField, max_digits=12, decimal_places=2)
- current_debt (DecimalField, max_digits=12, decimal_places=2, default=0)
- created_at (DateTimeField, auto_now_add)
- updated_at (DateTimeField, auto_now)
```

### Loan Model
```python
- loan_id (PK, AutoField)
- customer (ForeignKey to Customer)
- loan_amount (DecimalField, max_digits=12, decimal_places=2)
- tenure (PositiveIntegerField, help_text="Tenure in months")
- interest_rate (DecimalField, max_digits=5, decimal_places=2)
- monthly_repayment (DecimalField, max_digits=12, decimal_places=2)
- emis_paid_on_time (PositiveIntegerField, default=0)
- start_date (DateField)
- end_date (DateField)
- is_active (BooleanField, default=True)
- created_at (DateTimeField, auto_now_add)
- updated_at (DateTimeField, auto_now)
```

**Computed Properties:**
- `repayments_left`: tenure - emis_paid_on_time
- `total_amount`: Calculate total with compound interest

---

## API Endpoints Design

### 1. POST /api/register/
**Purpose**: Register a new customer

**Request Body**:
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "monthly_income": 50000,
    "phone_number": "9876543210"
}
```

**Response** (201 Created):
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

**Business Logic**:
- approved_limit = 36 * monthly_income (rounded to nearest lakh)
- Validation: phone number uniqueness, age > 18, income > 0

---

### 2. POST /api/check-eligibility/
**Purpose**: Check loan eligibility and calculate credit score

**Request Body**:
```json
{
    "customer_id": 1,
    "loan_amount": 500000,
    "interest_rate": 10.5,
    "tenure": 24
}
```

**Response** (200 OK):
```json
{
    "customer_id": 1,
    "approval": true,
    "interest_rate": 10.5,
    "corrected_interest_rate": 12.0,
    "tenure": 24,
    "monthly_installment": 23456.78
}
```

**Credit Scoring Algorithm**:

```python
Components (Total: 100 points):
1. Past Loans Paid on Time (35 points)
   - Percentage of EMIs paid on time across all loans
   - Score = (emis_paid_on_time / total_emis) * 35

2. Number of Loans Taken (20 points)
   - 1-2 loans: 20 points
   - 3-4 loans: 15 points
   - 5-6 loans: 10 points
   - 7+ loans: 5 points

3. Loan Activity in Current Year (20 points)
   - Active loans in current year
   - 0 loans: 0 points
   - 1 loan: 20 points
   - 2 loans: 15 points
   - 3+ loans: 10 points

4. Loan Approved Volume (15 points)
   - Total approved loan volume vs approved limit
   - <25%: 15 points
   - 25-50%: 10 points
   - 50-75%: 5 points
   - >75%: 0 points

5. Current Debt vs Approved Limit (10 points)
   - current_debt / approved_limit
   - <25%: 10 points
   - 25-50%: 7 points
   - 50-75%: 4 points
   - >75%: 0 points

Special Rules:
- If sum of current loans > approved_limit: credit_score = 0
- If sum of current EMIs > 50% of monthly_salary: reject loan
```

**Approval Logic**:
```python
if credit_score > 50:
    approve with requested interest_rate
elif 30 < credit_score <= 50:
    approve only if interest_rate >= 12%, else correct to 12%
elif 10 < credit_score <= 30:
    approve only if interest_rate >= 16%, else correct to 16%
else:
    reject
```

**Monthly Installment Calculation** (Compound Interest):
```python
P = loan_amount
r = corrected_interest_rate / (12 * 100)
n = tenure

EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
```

---

### 3. POST /api/create-loan/
**Purpose**: Create a new loan after eligibility check

**Request Body**:
```json
{
    "customer_id": 1,
    "loan_amount": 500000,
    "interest_rate": 10.5,
    "tenure": 24
}
```

**Response** (201 Created if approved):
```json
{
    "loan_id": 101,
    "customer_id": 1,
    "loan_approved": true,
    "message": "Loan approved successfully",
    "monthly_installment": 23456.78
}
```

**Response** (400 Bad Request if rejected):
```json
{
    "loan_id": null,
    "customer_id": 1,
    "loan_approved": false,
    "message": "Loan rejected due to low credit score",
    "monthly_installment": 0
}
```

**Business Logic**:
- Reuse credit score calculation from check-eligibility
- If approved, create loan record with corrected_interest_rate
- Update customer's current_debt
- Set start_date to today, end_date to today + tenure months

---

### 4. GET /api/view-loan/{loan_id}/
**Purpose**: View details of a specific loan

**Response** (200 OK):
```json
{
    "loan_id": 101,
    "customer": {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "9876543210",
        "age": 30
    },
    "loan_amount": 500000,
    "interest_rate": 12.0,
    "monthly_installment": 23456.78,
    "tenure": 24
}
```

---

### 5. GET /api/view-loans/{customer_id}/
**Purpose**: View all loans for a customer

**Response** (200 OK):
```json
[
    {
        "loan_id": 101,
        "loan_amount": 500000,
        "interest_rate": 12.0,
        "monthly_installment": 23456.78,
        "repayments_left": 20
    },
    {
        "loan_id": 102,
        "loan_amount": 300000,
        "interest_rate": 14.5,
        "monthly_installment": 15678.90,
        "repayments_left": 15
    }
]
```

---

## Background Tasks (Celery)

### Task 1: Data Ingestion from CSV/Excel
**File**: `tasks/data_ingestion.py`

```python
@shared_task
def ingest_customer_data():
    """
    Read customerData.csv and bulk create Customer records
    - Handle duplicates (phone_number)
    - Log success/failure count
    - Return task status
    """

@shared_task
def ingest_loan_data():
    """
    Read loanData.csv and bulk create Loan records
    - Link to existing customers
    - Calculate current_debt for each customer
    - Handle missing customer references
    - Log success/failure count
    """

@shared_task
def calculate_customer_debts():
    """
    Recalculate current_debt for all customers
    based on active loans
    """
```

**Execution Strategy**:
- Run ingestion tasks on first docker-compose up
- Can also be triggered via Django management command
- Idempotent design (can run multiple times safely)

---

## Code Quality Standards

### 1. Code Organization
- **Separation of Concerns**: Models, Serializers, Views, Business Logic (Services)
- **DRY Principle**: Reusable utility functions in `core/utils.py`
- **Service Layer**: All business logic in `services.py` files
- **Clean Controllers**: Views only handle HTTP request/response

### 2. Naming Conventions
- **Classes**: PascalCase (e.g., `CustomerSerializer`)
- **Functions/Methods**: snake_case (e.g., `calculate_credit_score`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_CREDIT_SCORE`)
- **Private methods**: _prefixed (e.g., `_validate_loan_amount`)

### 3. Documentation
- **Docstrings**: All classes, functions, and complex logic
- **Inline Comments**: For non-obvious code sections
- **API Documentation**: Using drf-spectacular (Swagger/OpenAPI)
- **README**: Setup instructions, API usage, architecture

### 4. Error Handling
- **Custom Exceptions**: Define in `core/exceptions.py`
- **Proper HTTP Status Codes**: 200, 201, 400, 404, 500
- **Validation**: Use DRF serializers + custom validators
- **Logging**: Structured logging for all errors and important events

### 5. Testing Strategy
- **Unit Tests**: Models, Serializers, Services (>80% coverage goal)
- **Integration Tests**: API endpoints
- **Test Data**: Fixtures for consistent test scenarios
- **Mock External Dependencies**: Database, Celery tasks

### 6. Security
- **Environment Variables**: Sensitive data in .env
- **Input Validation**: All user inputs sanitized
- **SQL Injection Prevention**: Use Django ORM (no raw SQL)
- **CORS**: Configured for frontend access

### 7. Performance
- **Database Indexing**: On frequently queried fields
- **Query Optimization**: select_related, prefetch_related
- **Pagination**: For list endpoints
- **Caching**: Consider Redis for credit scores (optional)

---

## Git Workflow & Commits Plan

### Branch Strategy
```
main (production-ready code)
└── develop (integration branch)
    ├── feature/project-setup
    ├── feature/customer-model
    ├── feature/loan-model
    ├── feature/register-api
    ├── feature/eligibility-api
    ├── feature/create-loan-api
    ├── feature/view-loan-apis
    ├── feature/data-ingestion
    ├── feature/docker-setup
    └── feature/tests-and-docs
```

### Commit Plan (Detailed)

#### Phase 1: Project Foundation
```bash
# Commit 1
git commit -m "chore: initialize Django project with DRF

- Create Django 4.2 project structure
- Add Django Rest Framework
- Configure settings split (base, dev, prod)
- Add .gitignore for Python/Django
- Create requirements.txt with initial dependencies"

# Commit 2
git commit -m "feat: configure PostgreSQL database

- Add PostgreSQL settings in base.py
- Add psycopg2-binary to requirements
- Create database configuration with environment variables
- Add .env.example file"

# Commit 3
git commit -m "chore: setup project structure and apps

- Create customers app
- Create loans app
- Create core app for utilities
- Create tasks directory for Celery
- Update INSTALLED_APPS in settings"
```

#### Phase 2: Data Models
```bash
# Commit 4
git commit -m "feat: implement Customer model

- Add Customer model with all required fields
- Add model validators for phone, age, salary
- Add __str__ method and Meta options
- Create and run migrations
- Add model tests"

# Commit 5
git commit -m "feat: implement Loan model

- Add Loan model with relationship to Customer
- Add computed properties (repayments_left)
- Add model validators
- Create and run migrations
- Add model tests"

# Commit 6
git commit -m "feat: configure Django admin for models

- Register Customer and Loan in admin
- Customize admin list display and filters
- Add search fields
- Add readonly fields for computed values"
```

#### Phase 3: Core Utilities
```bash
# Commit 7
git commit -m "feat: add core utilities and validators

- Create custom exceptions in core/exceptions.py
- Add utility functions for rounding, date calculations
- Add custom validators for phone number, age
- Add unit tests for utilities"

# Commit 8
git commit -m "feat: implement credit scoring algorithm

- Create CreditScoreCalculator class
- Implement 5-component scoring logic
- Add approval logic based on credit score
- Add comprehensive docstrings
- Add unit tests for scoring logic"

# Commit 9
git commit -m "feat: add loan calculation utilities

- Implement compound interest EMI calculator
- Add loan eligibility checker
- Add corrected interest rate calculator
- Add unit tests for calculations"
```

#### Phase 4: API - Customer Registration
```bash
# Commit 10
git commit -m "feat: implement customer registration serializer

- Create CustomerRegistrationSerializer
- Add custom validation for input fields
- Implement approved_limit calculation logic
- Add serializer tests"

# Commit 11
git commit -m "feat: implement customer registration API endpoint

- Create RegisterCustomerView (POST /api/register/)
- Add business logic in CustomerService
- Handle duplicate phone number errors
- Add API endpoint tests"
```

#### Phase 5: API - Loan Eligibility
```bash
# Commit 12
git commit -m "feat: implement loan eligibility check serializer

- Create LoanEligibilitySerializer
- Add request/response serializers
- Validate customer_id, loan_amount, tenure
- Add serializer tests"

# Commit 13
git commit -m "feat: implement check eligibility API endpoint

- Create CheckEligibilityView (POST /api/check-eligibility/)
- Integrate credit scoring logic
- Calculate corrected interest rate
- Calculate monthly installment
- Add comprehensive tests"
```

#### Phase 6: API - Loan Creation
```bash
# Commit 14
git commit -m "feat: implement create loan API endpoint

- Create CreateLoanView (POST /api/create-loan/)
- Reuse eligibility check logic
- Create loan record if approved
- Update customer current_debt
- Handle rejection cases
- Add API tests"
```

#### Phase 7: API - Loan Views
```bash
# Commit 15
git commit -m "feat: implement view loan detail API endpoint

- Create ViewLoanView (GET /api/view-loan/<loan_id>/)
- Add nested customer serializer
- Handle loan not found errors
- Add API tests"

# Commit 16
git commit -m "feat: implement view customer loans API endpoint

- Create ViewCustomerLoansView (GET /api/view-loans/<customer_id>/)
- Filter active loans for customer
- Calculate repayments_left dynamically
- Add pagination support
- Add API tests"
```

#### Phase 8: Background Tasks
```bash
# Commit 17
git commit -m "chore: setup Celery with Redis

- Configure Celery in config/celery.py
- Add Redis as broker and backend
- Add celery to requirements.txt
- Configure task autodiscovery"

# Commit 18
git commit -m "feat: implement customer data ingestion task

- Create ingest_customer_data Celery task
- Read customerData.csv using pandas
- Bulk create Customer records
- Handle duplicates and errors
- Add logging"

# Commit 19
git commit -m "feat: implement loan data ingestion task

- Create ingest_loan_data Celery task
- Read loanData.csv using pandas
- Link loans to customers
- Calculate and update current_debt
- Add logging and error handling"

# Commit 20
git commit -m "feat: add management command for data ingestion

- Create 'ingest_data' management command
- Trigger Celery tasks for data import
- Add progress logging
- Add command documentation"
```

#### Phase 9: Docker & Deployment
```bash
# Commit 21
git commit -m "chore: create Dockerfile for Django app

- Create multi-stage Dockerfile
- Install system dependencies
- Configure Python environment
- Add health check endpoint
- Optimize image layers"

# Commit 22
git commit -m "chore: create docker-compose.yml

- Add PostgreSQL service
- Add Redis service
- Add Django web service
- Add Celery worker service
- Configure networking and volumes
- Add environment variables"

# Commit 23
git commit -m "docs: add comprehensive setup instructions

- Create detailed README.md
- Add Docker setup instructions
- Document API endpoints with examples
- Add architecture diagram
- Add troubleshooting section"
```

#### Phase 10: Testing & Documentation
```bash
# Commit 24
git commit -m "test: add comprehensive test coverage

- Add missing unit tests
- Add integration tests for all endpoints
- Add test fixtures
- Achieve >80% code coverage
- Add pytest configuration"

# Commit 25
git commit -m "feat: add API documentation with drf-spectacular

- Configure Swagger UI
- Add schema annotations to views
- Generate OpenAPI 3.0 schema
- Add API documentation endpoint"

# Commit 26
git commit -m "chore: add code quality tools

- Add flake8 configuration
- Add black formatter
- Add pre-commit hooks
- Add isort for import sorting
- Document code style guide"

# Commit 27
git commit -m "docs: finalize documentation and polish

- Update README with final instructions
- Add CONTRIBUTING.md
- Add example .env file
- Add data file samples
- Add architecture documentation"
```

#### Final Phase: Polish & Submission
```bash
# Commit 28
git commit -m "fix: address edge cases and error handling

- Handle division by zero in calculations
- Add validation for negative amounts
- Improve error messages
- Add transaction atomicity for loan creation"

# Commit 29
git commit -m "perf: optimize database queries

- Add database indexes
- Use select_related for customer queries
- Add prefetch_related for loan queries
- Optimize credit score calculation"

# Commit 30
git commit -m "chore: final cleanup and submission prep

- Remove debug code
- Update requirements.txt
- Verify Docker build
- Final documentation review
- Add submission checklist"
```

### Commit Message Convention
```
Format: <type>: <subject>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- chore: Build/config changes
- test: Adding/updating tests
- refactor: Code refactoring
- perf: Performance improvements
- style: Code style changes (formatting)

Examples:
✅ feat: add customer registration API endpoint
✅ fix: correct EMI calculation for edge cases
✅ docs: update API documentation with examples
✅ test: add unit tests for credit scoring
❌ updated files
❌ changes
```

---

## Implementation Timeline

### Day 1 (Hours 0-12)
- [x] Project setup and configuration (Commits 1-3)
- [x] Data models implementation (Commits 4-6)
- [x] Core utilities and validators (Commits 7-9)
- [x] Customer registration API (Commits 10-11)

### Day 2 (Hours 12-24)
- [x] Loan eligibility API (Commits 12-13)
- [x] Create loan API (Commit 14)
- [x] View loan APIs (Commits 15-16)
- [x] Background tasks setup (Commits 17-20)

### Day 3 (Hours 24-36)
- [x] Docker configuration (Commits 21-23)
- [x] Testing and documentation (Commits 24-27)
- [x] Final polish and submission (Commits 28-30)

---

## Testing Strategy

### Unit Tests
```python
# customers/tests/test_models.py
- Test approved_limit calculation
- Test phone number uniqueness
- Test age validation

# customers/tests/test_serializers.py
- Test valid data serialization
- Test validation errors

# customers/tests/test_services.py
- Test customer creation logic
- Test duplicate handling

# loans/tests/test_credit_scoring.py
- Test credit score calculation for various scenarios
- Test approval logic for different credit ranges
- Test EMI calculation accuracy

# loans/tests/test_models.py
- Test loan model creation
- Test repayments_left calculation

# loans/tests/test_views.py
- Test all API endpoints
- Test error responses
- Test edge cases
```

### Integration Tests
```python
# Test complete workflows
- Register customer → Check eligibility → Create loan → View loan
- Test with various credit scores
- Test rejection scenarios
- Test data ingestion flow
```

### Test Coverage Goals
- Overall: >80%
- Models: >90%
- Services: >85%
- Views: >80%
- Utilities: >90%

---

## Environment Variables (.env)

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=credit_approval_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Application
APPROVED_LIMIT_MULTIPLIER=36
MAX_EMI_TO_SALARY_RATIO=0.5
```

---

## Docker Services Configuration

### Services Overview
1. **db**: PostgreSQL 15 database
2. **redis**: Redis for Celery broker
3. **web**: Django application
4. **celery_worker**: Celery worker for background tasks

### Volume Mounts
- `./data:/app/data` - For CSV files
- `postgres_data:/var/lib/postgresql/data` - Database persistence

---

## API Documentation Structure

### Using drf-spectacular
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **OpenAPI Schema**: `/api/schema/`

### Documentation Includes
- Request/Response examples
- Error responses
- Authentication (if needed)
- Rate limiting (if implemented)

---

## Submission Checklist

### Code Quality
- [ ] All API endpoints working correctly
- [ ] Credit scoring algorithm implemented accurately
- [ ] Error handling for all edge cases
- [ ] Code follows PEP 8 standards
- [ ] Meaningful variable and function names
- [ ] Comprehensive docstrings

### Testing
- [ ] Unit tests for models
- [ ] Unit tests for services
- [ ] Integration tests for APIs
- [ ] Test coverage >80%
- [ ] All tests passing

### Documentation
- [ ] README.md with setup instructions
- [ ] API documentation (Swagger)
- [ ] Code comments for complex logic
- [ ] Architecture documentation
- [ ] .env.example file

### Docker
- [ ] Dockerfile builds successfully
- [ ] docker-compose.yml configured
- [ ] All services start with single command
- [ ] Database migrations run automatically
- [ ] Data ingestion works on startup

### Data
- [ ] customerData.csv ingested correctly
- [ ] loanData.csv ingested correctly
- [ ] Current debt calculated accurately
- [ ] No data integrity issues

### Git
- [ ] Clean commit history
- [ ] Meaningful commit messages
- [ ] No sensitive data in repository
- [ ] .gitignore configured properly
- [ ] README has GitHub repo link

### Final Steps
- [ ] Test complete workflow end-to-end
- [ ] Verify all endpoints with Postman/curl
- [ ] Check Docker logs for errors
- [ ] Review code one final time
- [ ] Push to GitHub
- [ ] Submit repository link

---

## Notes & Considerations

### Assumptions
1. Phone numbers are unique identifiers for customers
2. All monetary values in INR
3. EMI calculations use compound interest
4. Loans are monthly repayment only
5. Current year = year of execution

### Edge Cases to Handle
1. Customer with no loan history (new customer)
2. Loan amount = 0 or negative
3. Tenure = 0 or > 60 months
4. Interest rate < 0 or > 100%
5. Division by zero in calculations
6. Customer not found
7. Loan not found
8. Duplicate phone numbers
9. Invalid date ranges
10. CSV file parsing errors

### Performance Optimizations
1. Database indexing on foreign keys
2. Bulk create for data ingestion
3. Query optimization with select_related
4. Cache credit scores (optional)
5. Pagination for list endpoints

### Security Considerations
1. No authentication required (as per assignment)
2. Input validation on all fields
3. SQL injection prevention via ORM
4. Environment variables for secrets
5. CORS configuration if needed

---

## Contact & Support
For questions during implementation:
- Review this document
- Check Django/DRF documentation
- Review similar projects on GitHub
- Debug systematically with logs

---

**Document Version**: 1.0  
**Last Updated**: 2 November 2025  
**Author**: Implementation Team  

---

## Quick Start Commands (Reference)

```bash
# Setup (after Docker is available)
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Ingest data
docker-compose exec web python manage.py ingest_data

# Run tests
docker-compose exec web python manage.py test

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

---

**Ready to implement! Follow the commit plan systematically for best results.**
