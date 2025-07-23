# Installation Guide

This guide provides instructions for installing and configuring the GET INN Restaurant Platform backend.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Docker** and **Docker Compose** (latest stable version)
- **Git** (2.25.0 or higher)
- **Python** (3.11 or higher)
- **PostgreSQL** client tools (optional, for direct database access)

## System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: At least 10GB free space
- **CPU**: 4+ cores recommended for development

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ai-restaurant-platform.git
cd ai-restaurant-platform
```

### 2. Environment Setup

#### Create Environment Files

```bash
# Copy example environment files
cp backend/.env.example backend/.env
```

Edit the `.env` file to configure your environment:

```bash
# Required settings
DATABASE_URL=postgresql://postgres:postgres@db:5432/restaurant
DATABASE_SCHEMA=getinn_ops
SECRET_KEY=your-secret-key-here
API_V1_STR=/v1/api

# Optional settings
LOG_LEVEL=INFO
ENVIRONMENT=development
```

#### Environment Variables for Integrations

For Azure OpenAI integration:

```bash
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-05-01-preview
AZURE_OPENAI_GPT41_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_ENABLED=true
```

For iiko integration:

```bash
CREDENTIAL_ENCRYPTION_KEY=your-32-byte-encryption-key
CREDENTIAL_ENCRYPTION_NONCE=your-12-byte-nonce
```

For Telegram bot integration:

```bash
USE_NGROK=false
WEBHOOK_DOMAIN=https://api.example.com
```

### 3. Docker-based Installation

The simplest way to get started is using Docker:

```bash
# Build and start all services
./backend/start-dev.sh --build --migrate --seed

# Check logs to ensure everything started correctly
./backend/start-dev.sh --logs
```

### 4. Local Development Setup

For local development with the API server running directly on your host:

```bash
# Create Python virtual environment
python -m venv backend/venv

# Activate virtual environment (Unix/macOS)
source backend/venv/bin/activate

# Activate virtual environment (Windows)
backend\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start supporting services in Docker
./backend/start-dev.sh --down
./backend/start-dev.sh --local-api

# Apply migrations if needed
cd backend
python -m alembic upgrade head
```

## Verification

Verify your installation:

1. Access the API documentation at http://localhost:8000/docs
2. Try some basic API endpoints
3. Check that database migrations have been applied
4. Verify integration configurations if enabled

## Common Installation Issues

### Docker Issues

#### Error: "Bind for 0.0.0.0:5432 failed: port is already in use"

Solution: You may already have PostgreSQL running locally. Either:
- Stop your local PostgreSQL service
- Change the PostgreSQL port in the Docker configuration

```bash
# Edit docker-compose.dev.yml to change the PostgreSQL port
nano docker/docker-compose.dev.yml

# Look for this section and change 5432:5432 to 5433:5432
# services:
#   db:
#     ports:
#       - "5432:5432"  # Change to "5433:5432"
```

#### Error: "Cannot connect to the Docker daemon"

Solution:
- Ensure Docker is running
- For Linux users, ensure your user is in the `docker` group:
  ```bash
  sudo usermod -aG docker $USER
  # You'll need to log out and log back in
  ```

### Database Issues

#### Error: "Connection refused to PostgreSQL"

Solutions:
- Ensure the database container is running
- Verify database credentials in .env file
- Check that ports are correctly mapped in Docker

#### Error with Migrations: "Target database is not up to date"

Solution:
```bash
./backend/start-dev.sh --exec backend alembic stamp head
./backend/start-dev.sh --exec backend alembic upgrade head
```

### Python Environment Issues

#### Error: "ModuleNotFoundError: No module named 'xyz'"

Solution:
- Ensure your virtual environment is activated
- Reinstall dependencies:
  ```bash
  pip install -r backend/requirements.txt
  ```

#### Error: "ImportError: libpq.so.5: cannot open shared object file"

Solution:
- Install PostgreSQL client libraries:
  ```bash
  # Ubuntu/Debian
  sudo apt install libpq-dev
  
  # CentOS/RHEL
  sudo yum install postgresql-devel
  
  # macOS
  brew install postgresql
  ```

## Next Steps

After installation:

- Explore the [Development Environment Guide](development-environment.md) for daily workflow
- Review the [Project Structure](../architecture/project-structure.md) to understand the codebase
- Check out the [Testing Guide](testing.md) to learn about running tests