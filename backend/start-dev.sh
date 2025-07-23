#!/bin/bash

# Restaurant Platform Backend Development Script
# This script manages the development environment for the Restaurant Platform backend,
# including running services, migrations, tests, and more.

# Exit on error
set -e

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Show help message
show_help() {
    echo -e "${BLUE}====================================================${NC}"
    echo -e "${GREEN}GET INN Restaurant Platform Backend - Development Script${NC}"
    echo -e "${BLUE}====================================================${NC}"
    echo ""
    echo "Usage: ./start-dev.sh [options]"
    echo ""
    echo -e "${CYAN}Environment Management:${NC}"
    echo "  --build                 Force rebuild of Docker images"
    echo "  --down                  Stop and remove all services (including locally running API)"
    echo "  --restart               Restart services"
    echo "  --logs                  Show logs from running containers"
    echo "  --status                Check status of services"
    echo "  --local-api             Run API server in local Python environment while other components in Docker"
    echo ""
    echo -e "${CYAN}Database Operations:${NC}"
    echo "  --migrate               Run database migrations before starting"
    echo "  --seed                  Apply seed data after migrations"
    echo "  --init-db               Initialize the database with default data"
    echo "  --reset-db              Drop and recreate the database with schema and migrations"
    echo ""
    echo -e "${CYAN}Testing:${NC}"
    echo "  --test [OPTIONS]        Run the test suite (passes options to run_tests.sh)"
    echo "                          e.g. --test -v -u (verbose unit tests)"
    echo ""
    echo -e "${CYAN}Utilities:${NC}"
    echo "  -h, --help              Show this help message"
    echo "  --exec SERVICE COMMAND  Execute command in service container"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./start-dev.sh                   # Start services"
    echo "  ./start-dev.sh --build           # Rebuild and start services"
    echo "  ./start-dev.sh --migrate         # Start services and run migrations"
    echo "  ./start-dev.sh --build --migrate # Rebuild, start, and run migrations"
    echo "  ./start-dev.sh --down            # Stop and remove containers"
    echo "  ./start-dev.sh --logs            # Show logs of running containers"
    echo "  ./start-dev.sh --test            # Run all working tests"
    echo "  ./start-dev.sh --test -u -v      # Run unit tests with verbose output"
    echo "  ./start-dev.sh --exec backend python -c 'print(\"Hello\")' # Run Python code"
    echo "  ./start-dev.sh --local-api        # Run API locally with Docker dependencies"
    echo ""
}

# Check if Docker and Docker Compose are available
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "Error: Docker daemon is not running"
        exit 1
    fi
}

# Default values
BUILD=false
MIGRATE=false
MIGRATIONS_DONE=false
SEED=false
DOWN=false
LOGS=false
EXEC=false
INIT_DB=false
RESET_DB=false
RUN_TESTS=false
STATUS=false
RESTART=false
LOCAL_API=false
EXEC_SERVICE=""
EXEC_COMMAND=""
TEST_ARGS=""

# Log a message with optional color
log() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Process command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        --build)
            BUILD=true
            shift
            ;;
        --migrate)
            MIGRATE=true
            shift
            ;;
        --seed)
            SEED=true
            MIGRATE=true  # Seed implies migrate
            shift
            ;;
        --down)
            DOWN=true
            shift
            ;;
        --logs)
            LOGS=true
            shift
            ;;
        --status)
            STATUS=true
            shift
            ;;
        --restart)
            RESTART=true
            shift
            ;;
        --init-db)
            INIT_DB=true
            shift
            ;;
        --reset-db)
            RESET_DB=true
            shift
            ;;
        --local-api)
            LOCAL_API=true
            shift
            ;;
        --test)
            RUN_TESTS=true
            # Collect all test args until next option
            shift
            while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
                TEST_ARGS="$TEST_ARGS $1"
                shift
            done
            ;;
        --exec)
            EXEC=true
            if [[ $# -lt 3 ]]; then
                log $RED "Error: --exec requires SERVICE and COMMAND"
                show_help
                exit 1
            fi
            EXEC_SERVICE="$2"
            shift 2
            EXEC_COMMAND="$*"
            break
            ;;
        *)
            log $RED "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check Docker availability
check_docker

# Try different Docker socket paths
if [ -S "/var/run/docker.sock" ]; then
    export DOCKER_HOST=unix:///var/run/docker.sock
elif [ -S "$HOME/.docker/run/docker.sock" ]; then
    export DOCKER_HOST=unix://$HOME/.docker/run/docker.sock
fi

# Disable credential helper to avoid errors
export DOCKER_CONFIG=/tmp/

# Go to the root directory
cd "$(dirname "$0")"

# Set the Docker Compose file
COMPOSE_FILE="docker/docker-compose.dev.yml"

# For local API development, we'll use a custom service selection
LOCAL_API_SERVICES="db redis adminer"
if $LOCAL_API; then
    log $YELLOW "Using local API development mode (backend will run locally)"
fi

# Check if .env file exists, create from template if not
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Creating .env from template..."
        cp .env.example .env
        echo "Created .env file. Please edit it with your configuration."
    elif [ -f .env.template ]; then
        echo "Creating .env from template..."
        cp .env.template .env
        echo "Created .env file. Please edit it with your configuration."
    else
        echo "Warning: .env template not found. You may need to create .env manually."
    fi
fi

# Function to check service status
check_status() {
    log $BLUE "======================================================="
    log $GREEN "Service Status"
    log $BLUE "======================================================="
    docker compose -f "$COMPOSE_FILE" ps
    log $BLUE "======================================================="
}

# Stop and remove containers if requested
if $DOWN; then
    log $YELLOW "Stopping and removing containers..."
    docker compose -f "$COMPOSE_FILE" down
    
    # Kill any local API processes (uvicorn)
    log $YELLOW "Checking for locally running API processes..."
    
    # Method 1: Find by process command line
    API_PIDS=$(ps -ef | grep "uvicorn" | grep "src.api.main" | grep -v grep | awk '{print $2}')
    if [ -n "$API_PIDS" ]; then
        log $YELLOW "Found locally running API processes. Stopping them..."
        echo $API_PIDS | xargs -r kill -9
        log $GREEN "Local API processes stopped."
    else
        log $GREEN "No locally running API processes found by command name."
    fi
    
    # Method 2: Find by port usage
    log $YELLOW "Checking for processes using port 8000..."
    PORT_PIDS=""
    if command -v lsof >/dev/null 2>&1; then
        PORT_PIDS=$(lsof -i :8000 -t 2>/dev/null)
    elif command -v netstat >/dev/null 2>&1; then
        PORT_PIDS=$(netstat -anp 2>/dev/null | grep ":8000 " | grep "LISTEN" | awk '{print $7}' | cut -d'/' -f1)
    elif command -v ss >/dev/null 2>&1; then
        PORT_PIDS=$(ss -tunlp 2>/dev/null | grep ":8000 " | grep -o "pid=[0-9]*" | cut -d'=' -f2)
    fi
    
    if [ -n "$PORT_PIDS" ]; then
        log $YELLOW "Found processes using port 8000. Stopping them..."
        echo $PORT_PIDS | xargs -r kill -9
        log $GREEN "Processes using port 8000 stopped."
    else
        log $GREEN "No processes found using port 8000."
    fi
    
    # Check if port is still in use after killing processes
    sleep 1
    PORT_CHECK=""
    if command -v lsof >/dev/null 2>&1; then
        PORT_CHECK=$(lsof -i :8000 2>/dev/null)
    elif command -v netstat >/dev/null 2>&1; then
        PORT_CHECK=$(netstat -an 2>/dev/null | grep ":8000 " | grep "LISTEN")
    elif command -v ss >/dev/null 2>&1; then
        PORT_CHECK=$(ss -tunl 2>/dev/null | grep ":8000 ")
    fi
    
    if [ -n "$PORT_CHECK" ]; then
        log $RED "Warning: Port 8000 is still in use after attempting to stop processes."
        log $RED "You may need to manually find and stop the process using this port."
    else
        log $GREEN "Port 8000 is now free."
    fi
    
    log $GREEN "All services have been stopped and containers removed."
    exit 0
fi

# Show logs if requested
if $LOGS; then
    log $BLUE "Showing logs from containers..."
    docker compose -f "$COMPOSE_FILE" logs -f
    exit 0
fi

# Show status if requested
if $STATUS; then
    check_status
    exit 0
fi

# Execute command if requested
if $EXEC; then
    log $BLUE "Executing command in $EXEC_SERVICE container..."
    docker compose -f "$COMPOSE_FILE" exec "$EXEC_SERVICE" $EXEC_COMMAND
    exit $?
fi

# Restart services if requested
if $RESTART; then
    log $YELLOW "Restarting services..."
    docker compose -f "$COMPOSE_FILE" restart
    log $GREEN "Services restarted."
    check_status
    exit 0
fi

# Build images if requested
if $BUILD; then
    log $BLUE "Building Docker images..."
    docker compose -f "$COMPOSE_FILE" build
fi

# Start services
log $BLUE "Starting services..."
if $LOCAL_API; then
    docker compose -f "$COMPOSE_FILE" up -d $LOCAL_API_SERVICES
else
    docker compose -f "$COMPOSE_FILE" up -d
fi

# Wait for database to be ready
if $MIGRATE || $RESET_DB || $INIT_DB; then
    log $YELLOW "Waiting for database to be ready..."
    
    # Wait for database to be ready (more robust method)
    for i in {1..10}; do
        if docker compose -f "$COMPOSE_FILE" exec db pg_isready -U postgres > /dev/null 2>&1; then
            log $GREEN "Database is ready"
            break
        fi
        log $YELLOW "Waiting for database (attempt $i/10)..."
        sleep 2
    done
fi

# Reset database if requested
if $RESET_DB; then
    log $YELLOW "Resetting database..."
    if $LOCAL_API; then
        # Drop database if exists
        export PGPASSWORD="postgres"
        psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS restaurant;"
        # Create database will be handled by alembic in migration step
        MIGRATE=true  # Force migration after reset
        INIT_DB=true  # Force init after reset
    else
        # When in Docker mode, use the container to handle reset
        docker compose -f "$COMPOSE_FILE" exec db psql -U postgres -c "DROP DATABASE IF EXISTS restaurant;"
        MIGRATE=true  # Force migration after reset
        INIT_DB=true  # Force init after reset
    fi
    log $GREEN "Database reset completed"
fi

# Run migrations if requested
if $MIGRATE; then
    log $YELLOW "Running database migrations..."
    if $LOCAL_API; then
        # When in local API mode, run migrations directly
        # Make sure virtual env is activated
        if [ ! -d "venv" ]; then
            log $YELLOW "Creating Python virtual environment..."
            python3 -m venv venv
            log $GREEN "Created Python virtual environment"
        fi
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Set environment variables for migrations
        export PYTHONPATH="$PWD"
        export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/restaurant"
        
        # Run alembic to handle all database operations (creating DB, schema, extensions, and migrations)
        alembic -c alembic.local.ini upgrade head
    else
        # Otherwise run in the backend container with local config
        docker compose -f "$COMPOSE_FILE" exec backend alembic -c alembic.local.ini upgrade head
    fi
    
    # Mark migrations as done
    MIGRATIONS_DONE=true
    log $GREEN "Database migrations completed"
    
    if $SEED; then
        log $YELLOW "Applying seed data..."
        if $LOCAL_API; then
            # When in local API mode, apply seed data directly
            # Make sure virtual env is activated
            source venv/bin/activate
            export PYTHONPATH="$PWD"
            python -m src.seed
        else
            # Otherwise run in the backend container
            docker compose -f "$COMPOSE_FILE" exec backend python -m src.seed
        fi
        log $GREEN "Seed data applied"
    fi
    
    # Set MIGRATE back to false after completing
    MIGRATE=false
fi

# Initialize database if requested
if $INIT_DB; then
    log $YELLOW "Initializing database with default data..."
    
    # Make sure migrations have run before initialization
    if ! $MIGRATE && ! $MIGRATIONS_DONE; then
        log $YELLOW "Running migrations before initialization..."
        
        if $LOCAL_API; then
            # Run migrations locally
            source venv/bin/activate
            export PYTHONPATH="$PWD"
            export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/restaurant"
            alembic -c alembic.local.ini upgrade head
        else
            # Run migrations in Docker
            docker compose -f "$COMPOSE_FILE" exec backend alembic -c alembic.local.ini upgrade head
        fi
        log $GREEN "Database migrations completed for initialization"
    fi
    
    # Run the actual initialization
    if $LOCAL_API; then
        # When in local API mode, run the initialization directly
        # Ensure virtual environment is active
        source venv/bin/activate
        export PYTHONPATH="$PWD"
        export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/restaurant"
        
        # Run initialization command
        python -c "from src.api.dependencies.db import SessionLocal; from src.api.core.init_db import init_db; db = SessionLocal(); init_db(db); db.close()"
    else
        # Otherwise run it in the backend container
        docker compose -f "$COMPOSE_FILE" exec -e INITIALIZE_DB=true backend python -c "from src.api.dependencies.db import SessionLocal; from src.api.core.init_db import init_db; db = SessionLocal(); init_db(db); db.close()"
    fi
    log $GREEN "Database initialization completed"
fi

# Run tests if requested
if $RUN_TESTS; then
    log $BLUE "======================================================="
    log $GREEN "Running Tests"
    log $BLUE "======================================================="
    
    if $LOCAL_API; then
        # When in local API mode, run tests directly
        # Make sure virtual environment is activated
        if [ ! -d "venv" ]; then
            log $YELLOW "Creating Python virtual environment..."
            python3 -m venv venv
            log $GREEN "Created Python virtual environment"
        fi
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Set environment variables for tests
        export PYTHONPATH="$PWD"
        export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/restaurant"
        
        # Run tests
        if [ -f "./run_tests.sh" ]; then
            if [ -z "$TEST_ARGS" ]; then
                # If no specific test args provided, run working tests
                log $YELLOW "Running tests with default settings (working tests only)..."
                ./run_tests.sh --local -v
            else
                # Use provided test args
                log $YELLOW "Running tests with custom arguments: $TEST_ARGS"
                ./run_tests.sh --local $TEST_ARGS
            fi
        else
            log $YELLOW "run_tests.sh not found, running pytest directly..."
            if [ -z "$TEST_ARGS" ]; then
                python -m pytest -v
            else
                python -m pytest $TEST_ARGS
            fi
        fi
    else
        # In Docker mode, use the container
        # Copy run_tests.sh to the container if it doesn't exist there
        if ! docker compose -f "$COMPOSE_FILE" exec backend test -f ./run_tests.sh; then
            log $YELLOW "Copying run_tests.sh to container..."
            docker compose -f "$COMPOSE_FILE" cp run_tests.sh backend:/app/run_tests.sh
            docker compose -f "$COMPOSE_FILE" exec backend chmod +x /app/run_tests.sh
        fi
        
        # Check if the requirements-dev.txt file exists in the container
        if ! docker compose -f "$COMPOSE_FILE" exec backend test -f ./requirements-dev.txt; then
            log $YELLOW "Copying requirements-dev.txt to container..."
            docker compose -f "$COMPOSE_FILE" cp requirements-dev.txt backend:/app/requirements-dev.txt
            log $YELLOW "Installing test dependencies..."
            docker compose -f "$COMPOSE_FILE" exec backend pip install -r requirements-dev.txt
        fi
        
        # Run tests using the improved run_tests.sh
        if [ -z "$TEST_ARGS" ]; then
            # If no specific test args provided, run working tests
            log $YELLOW "Running tests with default settings (working tests only)..."
            docker compose -f "$COMPOSE_FILE" exec backend ./run_tests.sh --local -v
        else
            # Use provided test args
            log $YELLOW "Running tests with custom arguments: $TEST_ARGS"
            docker compose -f "$COMPOSE_FILE" exec backend ./run_tests.sh --local $TEST_ARGS
        fi
    fi
    test_exit_code=$?
    
    # Report test results
    if [ $test_exit_code -eq 0 ]; then
        log $GREEN "All tests passed!"
    else
        log $RED "Some tests failed with exit code $test_exit_code"
    fi
    
    exit $test_exit_code
fi

# Show service status after successful start
check_status

# If using local API mode, start the API server
if $LOCAL_API; then
    # Create a .env.local file with database connection string for local API
    log $YELLOW "Creating .env.local for local API development..."
    echo "# Local environment settings - generated by start-dev.sh" > .env.local
    # Add explicit connection strings for local development
    echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/restaurant" >> .env.local
    echo "DATABASE_SCHEMA=getinn_ops" >> .env.local
    echo "CELERY_BROKER_URL=redis://localhost:6379/0" >> .env.local
    echo "CELERY_RESULT_BACKEND=redis://localhost:6379/0" >> .env.local
    echo "INITIALIZE_DB=false" >> .env.local
    echo "RESET_DB=false" >> .env.local
    echo "BOT_LOG_LEVEL=DEBUG" >> .env.local
    echo "BOT_LOG_FORMAT=json" >> .env.local
    echo "BOT_FILE_LOGGING=false" >> .env.local
    # Copy any additional settings from the original .env file if it exists
    if [ -f .env ]; then
        # Exclude settings we've already explicitly set
        grep -v "DATABASE_URL\|DATABASE_SCHEMA\|CELERY_\|INITIALIZE_DB\|RESET_DB\|BOT_" .env >> .env.local
    fi
    log $GREEN "Created .env.local file"
    
    # Let alembic handle database setup during migration step
    log $GREEN "Database will be set up during migration"
    
    # Check if Python virtual environment exists, create if it doesn't
    if [ ! -d "venv" ]; then
        log $YELLOW "Creating Python virtual environment..."
        python3 -m venv venv
        log $GREEN "Created Python virtual environment"
    fi
    
    # Activate virtual environment and install dependencies
    log $YELLOW "Activating virtual environment and installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    if [ -f requirements-dev.txt ]; then
        pip install -r requirements-dev.txt
    fi
    
    # Start the API server
    log $BLUE "======================================================="
    log $GREEN "Starting local API server (press CTRL+C to stop)..."
    log $BLUE "======================================================="
    # Load environment variables safely
    set -a
    [ -f .env.local ] && . .env.local
    set +a
    
    # Set PYTHONPATH to include the root directory for proper imports
    export PYTHONPATH="$PWD"
    
    # Start uvicorn with INITIALIZE_DB=false to avoid database initialization errors
    echo "Starting API server at http://localhost:8000 - API docs at http://localhost:8000/docs"
    INITIALIZE_DB=false exec python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
    
    # Clean up when API server is stopped
    log $YELLOW "Local API server stopped."
    log $YELLOW "Docker services are still running. Use './start-dev.sh --down' to stop them."
    exit 0
fi

# Display success message
log $BLUE "======================================================="
log $GREEN "Restaurant Platform Development Environment is Ready!"
log $BLUE "======================================================="
log $YELLOW "API Documentation: http://localhost:8000/docs"
log $YELLOW "Database Admin:    http://localhost:8080"
log $BLUE "======================================================="
log $CYAN "Useful commands:"
log $NC "  ./start-dev.sh --status    # Check service status"
log $NC "  ./start-dev.sh --logs      # View logs"
log $NC "  ./start-dev.sh --test      # Run tests"
log $NC "  ./start-dev.sh --down      # Stop services"
log $NC "  ./start-dev.sh --local-api # Start API locally"
log $BLUE "======================================================="
echo ""