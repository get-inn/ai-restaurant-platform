#!/bin/bash

# Restaurant Platform Backend Test Runner
# Usage: ./run_tests.sh [options]
#
# This script runs tests for the Restaurant Platform backend with various options
# for filtering and reporting. It supports both local and Docker-based test execution.

set -e

# Default configuration
VERBOSE=""                # Verbose output flag
COVERAGE=""               # Coverage reporting flag
TEST_PATH="src/"          # Base test directory
KEYWORD=""                # Keyword filter for pytest
USE_DOCKER=true           # Whether to run tests in Docker
PORT=5433                 # Port for Docker PostgreSQL

# Default test paths - API tests only
PYTEST_ARGS="src/api"

# Test categories
UNIT_TESTS="src/api"
API_TESTS="src/api src/api/tests/integration"
INTEGRATION_TESTS="src/api/tests/integration"
BOT_TESTS="src/api/tests/integration/test_bots_api.py src/api/tests/integration/test_webhooks_api.py"
ALL_WORKING_TESTS="src/api src/api/tests/integration"

# Display help message
show_help() {
  echo "======================================================="
  echo "Restaurant Platform Backend Test Runner"
  echo "======================================================="
  echo ""
  echo "This script runs tests for the Restaurant Platform backend with various"
  echo "options for filtering and reporting. It supports both local and Docker-"
  echo "based test execution."
  echo ""
  echo "Usage: ./run_tests.sh [options] [path/to/test]"
  echo ""
  echo "Options:"
  echo "  -v, --verbose       Show verbose output"
  echo "  -c, --coverage      Run with coverage report"
  echo "  -u, --unit          Run only unit tests"
  echo "  -a, --api           Run only API tests"
  echo "  -i, --integration   Run only integration tests"
  echo "  -b, --bots          Run only bot-related tests"
  echo "  -w, --working       Run only tests known to be working (default)"
  echo "  -k, --keyword       Run tests matching keyword"
  echo "  -d, --docker        Run tests using Docker (default)"
  echo "  -l, --local         Run tests locally without Docker"
  echo "  --port              Specify custom port for Docker PostgreSQL (default: 5433)"
  echo "  --all               Run all tests, including potentially failing ones"
  echo "  -h, --help          Show this help message"
  echo ""
  echo "Test Categories:"
  echo "  Unit Tests:         Tests individual components in isolation"
  echo "  Integration Tests:  Tests interactions between components"
  echo "  API Tests:          Tests API endpoints and workflows"
  echo "  Bot Tests:          Tests bot conversation scenarios"
  echo ""
  echo "API Test Markers:"
  echo "  auth:               Authentication tests"
  echo "  accounts:           Account management tests"
  echo "  supplier:           Supplier management tests"
  echo "  labor:              Labor management tests"
  echo "  chef:               Chef-related tests"
  echo "  dashboard:          Dashboard tests"
  echo "  integrations:       External integration tests"
  echo "  bots:               Bot management tests"
  echo "  webhooks:           Webhook handler tests"
  echo ""
  echo "Examples:"
  echo "  ./run_tests.sh                  # Run working tests"
  echo "  ./run_tests.sh -u -v            # Run unit tests with verbose output"
  echo "  ./run_tests.sh -i -c            # Run integration tests with coverage"
  echo "  ./run_tests.sh -k auth          # Run tests matching 'auth'"
  echo "  ./run_tests.sh -l               # Run tests locally"
  echo "  ./run_tests.sh --all            # Run all tests"
  echo "  ./run_tests.sh src/api/         # Run specific test directory"
  echo "  ./run_tests.sh -m auth          # Run tests with 'auth' marker"
  echo "======================================================="
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--verbose)
      VERBOSE="-v"
      shift
      ;;
    -c|--coverage)
      COVERAGE="--cov=src --cov-report=term --cov-report=html"
      shift
      ;;
    -u|--unit)
      PYTEST_ARGS="$UNIT_TESTS"
      shift
      ;;
    -a|--api)
      PYTEST_ARGS="$API_TESTS"
      shift
      ;;
    -i|--integration)
      PYTEST_ARGS="$INTEGRATION_TESTS"
      shift
      ;;
    -b|--bots)
      PYTEST_ARGS="$BOT_TESTS"
      shift
      ;;
    -w|--working)
      PYTEST_ARGS="$ALL_WORKING_TESTS"
      shift
      ;;
    -k|--keyword)
      if [[ -z $2 || $2 == -* ]]; then
        echo "Error: Keyword argument requires a value"
        exit 1
      fi
      KEYWORD="-k $2"
      shift 2
      ;;
    -m|--marker)
      if [[ -z $2 || $2 == -* ]]; then
        echo "Error: Marker argument requires a value"
        exit 1
      fi
      KEYWORD="-m $2"
      shift 2
      ;;
    -d|--docker)
      USE_DOCKER=true
      shift
      ;;
    -l|--local)
      USE_DOCKER=false
      shift
      ;;
    --port)
      if [[ -z $2 || $2 == -* ]]; then
        echo "Error: Port argument requires a value"
        exit 1
      fi
      PORT=$2
      shift 2
      ;;
    --all)
      PYTEST_ARGS="$TEST_PATH"
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      # Allow adding specific test paths
      if [[ -d "$1" || -f "$1" ]]; then
        PYTEST_ARGS="$PYTEST_ARGS $1"
      else
        echo "Error: Unknown option or invalid path: $1"
        show_help
        exit 1
      fi
      shift
      ;;
  esac
done

# Go to the script directory
cd "$(dirname "$0")"

# Get the project root directory
PROJECT_ROOT="$(cd .. && pwd)"

# Function to run tests with Docker
run_with_docker() {
  echo "Running tests with Docker..."
  
  # Check if we're already inside a Docker container
  if [ -f /.dockerenv ]; then
    echo "Already running in Docker container, switching to local test mode..."
    run_local
    return $?
  fi
  
  echo "Setting up Docker test environment..."
  
  # Use docker compose command with better error detection
  DOCKER_COMPOSE_CMD=""
  
  # First check if Docker is installed
  if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH."
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
  fi
  
  # Check if docker compose (v2) is available
  if docker compose version &> /dev/null; then
    echo "Using Docker Compose V2"
    DOCKER_COMPOSE_CMD="docker compose"
  # Check if docker-compose (v1) is available
  elif command -v docker-compose &> /dev/null; then
    echo "Using legacy Docker Compose V1"
    DOCKER_COMPOSE_CMD="docker-compose"
  else
    echo "ERROR: Docker Compose not found."
    echo "Please install Docker Compose:"
    echo "  - For Docker Desktop: It should be included"
    echo "  - For Linux: https://docs.docker.com/compose/install/linux/"
  echo "  - Note: Test tools are available in src/tools/"
    exit 1
  fi
  
  # Verify Docker is running
  if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon is not running."
    echo "Please start Docker and try again."
    exit 1
  fi

  echo "Starting test containers..."
  
  # Create required directories
  LOG_DIR="$PROJECT_ROOT/logs"
  mkdir -p "$LOG_DIR"
  echo "Created logs directory: $LOG_DIR"
  
  # If requirements-dev.txt doesn't exist in the project root, copy it from backend
  if [ ! -f "$PROJECT_ROOT/requirements-dev.txt" ] && [ -f "requirements-dev.txt" ]; then
    echo "Copying requirements-dev.txt to project root for container access"
    cp "requirements-dev.txt" "$PROJECT_ROOT/"
  fi
  
  # Set required environment variables for testing
  export BOT_LOG_LEVEL=DEBUG
  export BOT_LOG_FORMAT=json
  export BOT_FILE_LOGGING=true
  export BOT_LOG_DIR=/app/logs
  export TEST_ARGS="$PYTEST_ARGS $VERBOSE $COVERAGE $KEYWORD"
  
  # Export these variables for Docker Compose to use
  export PROJECT_ROOT
  export LOG_DIR
  
  # Set docker-compose file path
  DOCKER_COMPOSE_FILE="$PROJECT_ROOT/backend/docker/docker-compose.test.yml"
  
  # Check if the Docker Compose file exists
  if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "ERROR: Docker Compose file not found at: $DOCKER_COMPOSE_FILE"
    echo "Looking for alternative locations..."
    
    # Try alternative location
    ALT_DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.test.yml"
    if [ -f "$ALT_DOCKER_COMPOSE_FILE" ]; then
      echo "Found Docker Compose file at: $ALT_DOCKER_COMPOSE_FILE"
      DOCKER_COMPOSE_FILE="$ALT_DOCKER_COMPOSE_FILE"
    else
      echo "ERROR: Could not find docker-compose.test.yml in common locations."
      echo "Please ensure the file exists in one of these locations:"
      echo "  - $PROJECT_ROOT/backend/docker/docker-compose.test.yml"
      echo "  - $PROJECT_ROOT/docker/docker-compose.test.yml"
      exit 1
    fi
  fi
  
  echo "Using Docker Compose file: $DOCKER_COMPOSE_FILE"
  
  # Run the tests with Docker Compose
  echo "Starting Docker containers and running tests..."
  echo "This may take a few minutes for the first run as images are built..."
  
  # Always run in foreground mode to capture logs properly
  echo "Running tests with Docker Compose..."
  # Ensure the test environment has needed variables
  mkdir -p "$PROJECT_ROOT/logs"
  touch "$PROJECT_ROOT/logs/test_results.log"
  chmod 777 "$PROJECT_ROOT/logs"
  chmod 666 "$PROJECT_ROOT/logs/test_results.log"
  
  # Run the tests - explicitly setting LOG_FILE environment variable for docker-compose
  export LOG_FILE=/app/logs/test_results.log
  $DOCKER_COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" up --build --abort-on-container-exit 2>&1 | tee test_run.log
  exit_code=$?
  
  # Show Docker logs to help with debugging
  echo "\nDisplaying test results summary:"
  if [ -f "$PROJECT_ROOT/logs/test_results.log" ]; then
    echo "\n=== Test Results ===\n"
    grep -E "(FAILED|PASSED|collected|==+>)" "$PROJECT_ROOT/logs/test_results.log" || echo "No test results found in log file"
  else
    echo "\n=== Test Results ===\n"
    echo "Test results log file not found at $PROJECT_ROOT/logs/test_results.log"
    echo "Checking for other log files..."
    find "$PROJECT_ROOT/logs/" -type f -name "*.log" | xargs -I {} echo "Found log file: {}"
  fi
  
  if [ $exit_code -ne 0 ]; then
    echo "\nTests failed with exit code $exit_code"
    echo "Checking container logs for errors:"
    $DOCKER_COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" logs backend | tail -50
  fi

  echo "Test run completed with exit code $exit_code"
  
  # Clean up
  echo "Cleaning up test containers..."
  $DOCKER_COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" down -v

  return $exit_code
}

# Function to run tests locally
run_local() {
  echo "Running tests locally..."
  
  # Check if virtual environment exists, create it if needed
  if [ ! -d "venv" ]; then
      echo "Creating virtual environment..."
      python3 -m venv venv
      echo "Virtual environment created."
  fi
  
  # Activate virtual environment
  echo "Activating virtual environment..."
  source venv/bin/activate
  
  # Check if pytest is installed in the virtual environment
  if ! python -m pip list | grep -q pytest; then
      echo "Installing test dependencies from requirements-dev.txt..."
      
      if [ -f "requirements-dev.txt" ]; then
          echo "Installing test dependencies using pip..."
          python -m pip install -r requirements-dev.txt
      else
          echo "ERROR: requirements-dev.txt not found."
          echo "Installing pytest manually..."
          python -m pip install pytest pytest-asyncio
      fi
  fi

  # Configure environment variables
  export TEST_DATABASE_URL="${TEST_DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/test_restaurant}"
  export DATABASE_SCHEMA="${DATABASE_SCHEMA:-getinn_ops}"
  export JWT_SECRET_KEY="${JWT_SECRET_KEY:-testsecretkey}"
  export JWT_ALGORITHM="${JWT_ALGORITHM:-HS256}"
  export PYTHONPATH=$(pwd)
  
  # Display test configuration
  echo "Test configuration:"
  echo " - Database URL: $TEST_DATABASE_URL"
  echo " - Schema: $DATABASE_SCHEMA"
  echo " - Test paths: $PYTEST_ARGS"
  echo " - Python path: $PYTHONPATH"
  
  # Run the tests
  if [ -n "$COVERAGE" ]; then
    echo "Running with coverage report..."
  fi
  
  python -m pytest $PYTEST_ARGS $VERBOSE $COVERAGE $KEYWORD

  return $?
}

# Display the test plan
echo "======================================================="
echo "Restaurant Platform Backend Test Plan"
echo "======================================================="
echo "Test paths: $PYTEST_ARGS"
echo "Mode: $(if $USE_DOCKER; then echo "Docker"; else echo "Local"; fi)"
if [ -n "$VERBOSE" ]; then echo "Verbose output enabled"; fi
if [ -n "$COVERAGE" ]; then echo "Coverage reporting enabled"; fi
if [ -n "$KEYWORD" ]; then echo "Filtering tests by keyword: $KEYWORD"; fi
echo "======================================================="
echo ""

# Trap Ctrl+C to handle clean exit
trap ctrl_c INT
ctrl_c() {
    echo -e "\n\033[0;31mTest run interrupted by user.\033[0m"
    
    if $USE_DOCKER; then
      echo "Stopping Docker containers..."
      $DOCKER_COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" down -v
    fi
    
    echo "Exiting."
    exit 1
}

# Run tests based on selected mode
start_time=$(date +%s)

if $USE_DOCKER; then
  run_with_docker
  exit_code=$?
else
  run_local
  exit_code=$?
fi

end_time=$(date +%s)
duration=$((end_time - start_time))

# Format time for better readability
format_time() {
  local seconds=$1
  local minutes=$((seconds / 60))
  local remaining_seconds=$((seconds % 60))
  
  if [ $minutes -gt 0 ]; then
    echo "${minutes}m ${remaining_seconds}s"
  else
    echo "${remaining_seconds}s"
  fi
}

# Print results
echo ""
echo "======================================================="
echo "                    Test Run Summary                    "
echo "======================================================="
echo "Test paths:  $PYTEST_ARGS"
echo "Mode:        $(if $USE_DOCKER; then echo "Docker"; else echo "Local"; fi)"
if [ -n "$VERBOSE" ]; then echo "Verbose:     Yes"; fi
if [ -n "$COVERAGE" ]; then echo "Coverage:    Enabled"; fi
if [ -n "$KEYWORD" ]; then echo "Filter:      $KEYWORD"; fi
echo "Duration:    $(format_time $duration)"
echo ""

if [ $exit_code -eq 0 ]; then
  echo -e "\033[0;32m✅ All tests PASSED\033[0m"
else
  echo -e "\033[0;31m❌ Tests FAILED with exit code $exit_code\033[0m"
  echo "Review the output above for details on failures."
fi

if [ -d "$PROJECT_ROOT/logs" ]; then
  BOT_LOGS=$(find "$PROJECT_ROOT/logs" -name "bot_conversations_*.log" 2>/dev/null || echo "")
  if [ -n "$BOT_LOGS" ]; then
    echo ""
    echo "Bot conversation logs are available at:"
    echo "  $(echo "$BOT_LOGS" | sort | tail -1)"
    echo ""
    echo "To view formatted logs, run:"
    echo "  python -m src.tools.utils.view_bot_logs --source file --file $(echo "$BOT_LOGS" | sort | tail -1)"
  fi
  
  # Show a summary of all test logs found
  echo ""
  echo "All log files generated during tests:"
  ls -la "$PROJECT_ROOT/logs/" | grep -v "^total" | grep -v "^d" | head -10
  if [ "$(ls -la "$PROJECT_ROOT/logs/" | grep -v "^total" | grep -v "^d" | wc -l)" -gt 10 ]; then
    echo "... and more (showing 10 of $(ls -la "$PROJECT_ROOT/logs/" | grep -v "^total" | grep -v "^d" | wc -l) files)"
  fi
fi

echo "======================================================="

exit $exit_code