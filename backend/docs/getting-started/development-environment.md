# Development Environment Setup

This guide explains how to set up and work with the local development environment for the GET INN Restaurant Platform backend.

## Prerequisites

- Docker and Docker Compose
- Python 3.11 or later
- Git

## Setup Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-restaurant-platform
```

### 2. Virtual Environment Setup

Create and activate a Python virtual environment for local development:

```bash
# Create a virtual environment
python -m venv backend/venv

# Activate the virtual environment
# On Unix/Linux/macOS
source backend/venv/bin/activate

# On Windows
backend\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Environment Configuration

Create a `.env` or `.env.local` file in the `backend` directory with the necessary configuration:

```bash
# Copy the example environment file
cp backend/.env.example backend/.env.local

# Edit the file with your preferred editor
nano backend/.env.local
```

### 4. Start the Development Environment

The `start-dev.sh` script manages the development environment:

```bash
./backend/start-dev.sh [options]
```

Common options:
- `--build`: Force rebuild of Docker images
- `--migrate`: Run database migrations before starting
- `--seed`: Apply seed data after migrations
- `--down`: Stop and remove containers
- `--local-api`: Run API server locally in Python environment

## Development Workflow

### Local API Development

For local API development, run:

```bash
# First stop any running containers
./backend/start-dev.sh --down

# Then start services with API running locally
./backend/start-dev.sh --local-api

# You may need to apply migrations
./backend/start-dev.sh --local-api --migrate
```

When running with `--local-api`:
- A Python virtual environment will be created in the `backend/venv` directory
- Required dependencies will be installed automatically
- A `.env.local` file will be created with adjusted database connection settings
- The API server will run with hot-reload enabled for faster development
- Other services (database, Redis, etc.) will run in Docker

### Database Management

To apply database migrations:

```bash
# Using Docker
./backend/start-dev.sh --exec backend alembic upgrade head

# Using local virtual environment
source backend/venv/bin/activate
cd backend
python -m alembic upgrade head
```

To create a new migration:

```bash
# Using Docker
./backend/start-dev.sh --exec backend alembic revision -m "description of change"

# Using local virtual environment
source backend/venv/bin/activate
cd backend
python -m alembic revision -m "description of change"
```

### Running Tests

Use the `run_tests.sh` script to execute tests:

```bash
# Run tests in Docker
./backend/run_tests.sh

# Run tests locally using the virtual environment
./backend/run_tests.sh -l

# Run specific test modules
./backend/run_tests.sh -l -k auth_flow
```

## Common Development Tasks

### Viewing Logs

```bash
# View logs from Docker containers
./backend/start-dev.sh --logs

# View specific service logs
./backend/start-dev.sh --logs backend
```

### Running Commands in Docker

```bash
# Execute a command in the backend container
./backend/start-dev.sh --exec backend <command>

# Example: Open a Python shell in the backend container
./backend/start-dev.sh --exec backend python
```

### Viewing Bot Conversation Logs

```bash
# View the latest bot conversation logs
python -m scripts.bots.utils.view_bot_logs --source file --file logs/bot_conversations_latest.log

# Filter by bot ID
python -m scripts.bots.utils.view_bot_logs --bot-id <BOT_ID>
```

## Debugging

### API Debugging

- Access the API documentation at http://localhost:8000/docs
- Enable debug logging by setting `LOG_LEVEL=DEBUG` in your environment file

### Database Debugging

- PostgreSQL is accessible at `localhost:5432`
- Default credentials are in the `.env.example` file
- Use a tool like pgAdmin or DBeaver to connect directly to the database

### Bot Debugging

For debugging bot conversations:

```bash
# Enable detailed bot logs
export BOT_LOG_LEVEL=DEBUG
export BOT_LOG_FORMAT=text
export BOT_FILE_LOGGING=true

# Run the bot setup script
cd backend
./scripts/bots/setup_logging.sh
```

## Troubleshooting

### Container Issues

If containers fail to start:

```bash
# Stop all containers and remove volumes
./backend/start-dev.sh --down -v

# Rebuild and start
./backend/start-dev.sh --build
```

### Database Connection Issues

If you encounter database connection issues:

```bash
# Check that the database container is running
docker ps | grep postgres

# Restart the database container
docker restart ai-restaurant-platform_db_1
```

### Hot Reload Not Working

If changes are not being detected:

```bash
# Restart the API server
./backend/start-dev.sh --down
./backend/start-dev.sh --local-api
```

### Environment Variable Issues

If environment variables are not being picked up:

```bash
# Create a new .env.local file
cp backend/.env.example backend/.env.local

# Restart with the new environment
./backend/start-dev.sh --down
./backend/start-dev.sh --local-api
```