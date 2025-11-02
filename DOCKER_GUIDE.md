# Docker Setup Guide

## Quick Start (Single Command)

```bash
docker-compose up --build
```

This command will:
1. Build the Django application image
2. Start PostgreSQL database
3. Start Redis server
4. Run database migrations
5. Start Django web server
6. Start Celery worker
7. Start Celery beat scheduler

The API will be available at: **http://localhost:8000**

---

## Step-by-Step Setup

### 1. Prerequisites

- Docker Desktop installed (includes docker-compose)
- No need for Python, PostgreSQL, or Redis installed locally

### 2. Build and Start Services

```bash
# Build images and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

### 3. Verify Services are Running

```bash
# Check running containers
docker-compose ps

# Expected output:
# credit_approval_web           running   0.0.0.0:8000->8000/tcp
# credit_approval_db            running   0.0.0.0:5432->5432/tcp
# credit_approval_redis         running   0.0.0.0:6379->6379/tcp
# credit_approval_celery_worker running
# credit_approval_celery_beat   running
```

### 4. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f db
```

---

## Data Ingestion

### Method 1: Using Django Management Command

```bash
# Run data ingestion inside the web container
docker-compose exec web python manage.py ingest_data

# With custom file paths
docker-compose exec web python manage.py ingest_data \
  --customer-file=data/customerData.csv \
  --loan-file=data/loanData.csv
```

### Method 2: Async with Celery

```bash
docker-compose exec web python manage.py ingest_data --async
```

---

## Common Docker Commands

### Create Django Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

### Run Database Migrations

```bash
docker-compose exec web python manage.py migrate
```

### Access Django Shell

```bash
docker-compose exec web python manage.py shell
```

### Access PostgreSQL Database

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d credit_approval_db

# Run SQL query
docker-compose exec db psql -U postgres -d credit_approval_db -c "SELECT COUNT(*) FROM customers;"
```

### Access Redis CLI

```bash
docker-compose exec redis redis-cli
```

### Run Tests

```bash
docker-compose exec web pytest
docker-compose exec web pytest --cov
```

### Restart Specific Service

```bash
docker-compose restart web
docker-compose restart celery_worker
```

---

## Stopping Services

```bash
# Stop all services (containers remain)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers, and delete volumes (WARNING: deletes database data)
docker-compose down -v
```

---

## Rebuilding After Code Changes

```bash
# Rebuild and restart
docker-compose up --build

# Force rebuild without cache
docker-compose build --no-cache
docker-compose up
```

---

## Environment Variables

The docker-compose.yml uses environment variables from:
1. `.env.docker` file (for Docker setup)
2. Or system environment variables
3. Or defaults in docker-compose.yml

### Creating .env file for Docker

```bash
# Copy the Docker-specific env file
cp .env.docker .env

# Or create your own .env with these variables:
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=credit_approval_db
DB_USER=postgres
DB_PASSWORD=postgres
```

---

## Service Details

### PostgreSQL (db)
- **Port**: 5432
- **Database**: credit_approval_db
- **User**: postgres
- **Password**: postgres (change in production!)
- **Data**: Persisted in `postgres_data` volume

### Redis (redis)
- **Port**: 6379
- **Purpose**: Celery broker and result backend

### Django Web (web)
- **Port**: 8000
- **Command**: Gunicorn WSGI server with 3 workers
- **Auto-runs**: Migrations and collectstatic on startup

### Celery Worker (celery_worker)
- **Purpose**: Process background tasks (data ingestion)
- **Workers**: 1 (increase for production)

### Celery Beat (celery_beat)
- **Purpose**: Task scheduler (for periodic tasks)

---

## Troubleshooting

### Port Already in Use

```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Database Connection Issues

```bash
# Check if db container is healthy
docker-compose ps

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Rebuild After Changing Dependencies

```bash
# When requirements.txt changes
docker-compose down
docker-compose build --no-cache web celery_worker
docker-compose up
```

### Clear Everything and Start Fresh

```bash
# WARNING: This deletes all data!
docker-compose down -v
docker-compose up --build
```

### View Container Resource Usage

```bash
docker stats
```

---

## Production Deployment Notes

### Changes for Production:

1. **Update .env variables**:
   ```
   DEBUG=False
   SECRET_KEY=<generate-strong-key>
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DB_PASSWORD=<strong-password>
   ```

2. **Use production settings**:
   ```yaml
   environment:
     - DJANGO_SETTINGS_MODULE=config.settings.production
   ```

3. **Add nginx reverse proxy** (recommended):
   ```yaml
   nginx:
     image: nginx:alpine
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - ./nginx.conf:/etc/nginx/nginx.conf
   ```

4. **Enable HTTPS** with Let's Encrypt

5. **Increase Gunicorn workers**:
   ```
   --workers 4
   ```

6. **Set up log aggregation** (e.g., ELK stack)

7. **Configure backup for PostgreSQL**

---

## Health Checks

All services have health checks configured:

- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Web**: Automatic dependency wait

---

## Accessing Services from Host

- **Django API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/api/docs/
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

---

## Docker Volumes

Data is persisted in Docker volumes:

```bash
# List volumes
docker volume ls

# Inspect a volume
docker volume inspect backendassignment_postgres_data

# Backup database volume
docker run --rm -v backendassignment_postgres_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/db_backup.tar.gz /data
```

---

## Development Workflow

1. **Start services**: `docker-compose up -d`
2. **Make code changes**: Edit files normally
3. **View changes**: Django auto-reloads (DEBUG=True)
4. **Run migrations**: `docker-compose exec web python manage.py migrate`
5. **View logs**: `docker-compose logs -f web`
6. **Stop services**: `docker-compose down`

---

## Network Configuration

All services are on the `credit_network` bridge network.

Services can communicate using container names:
- Django connects to `db:5432`
- Django connects to `redis:6379`
- Celery connects to `db:5432` and `redis:6379`

---

## Useful Aliases (Optional)

Add to your `.bashrc` or `.zshrc`:

```bash
alias dc='docker-compose'
alias dcu='docker-compose up'
alias dcd='docker-compose down'
alias dcl='docker-compose logs -f'
alias dce='docker-compose exec'
alias dcr='docker-compose restart'

# Usage examples:
# dcu -d --build
# dce web python manage.py shell
# dcl web
```

---

## Testing the API

Once services are running, test with curl:

```bash
# Register a customer
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "monthly_income": 50000,
    "phone_number": "9876543210"
  }'

# Check eligibility
curl -X POST http://localhost:8000/api/check-eligibility/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "loan_amount": 200000,
    "interest_rate": 10.5,
    "tenure": 24
  }'
```

---

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify services: `docker-compose ps`
3. Check network: `docker network inspect backendassignment_credit_network`
4. Restart services: `docker-compose restart`

---

**Happy Dockerizing! 🐳**
