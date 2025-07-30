#!/bin/bash
# Telegram Bot Setup Script
# -------------------------
# Sets up a Telegram bot instance with the GetInn platform:
# - Checks and starts ngrok if needed
# - Runs the Python setup script
# - Handles output and error reporting

# Colors for better readability
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

# Configuration
LOG_FILE="telegram_bot_setup.log"
PYTHON_SCRIPT="$(dirname $0)/telegram_bot_setup.py"
# Get the backend directory (4 levels up from this script)
BACKEND_DIR="$(cd "$(dirname "$0")/../../../../" && pwd)"
TOKEN_FILE="$BACKEND_DIR/telegram_token.txt"
DEBUG=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --debug)
      DEBUG=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--debug]"
      exit 1
      ;;
  esac
done

# Logging function
log() {
  local timestamp=$(date '+[%Y-%m-%d %H:%M:%S]')
  echo -e "$timestamp $1" | tee -a "$LOG_FILE"
}

# Error handling function
handle_error() {
  log "❌ ${RED}ERROR: $1${RESET}"
  exit 1
}

# Start logging
log "Starting Telegram bot setup script..."

# Check for Python and venv
if command -v pyenv &>/dev/null; then
  log "ℹ️ INFO: Using pyenv for Python environment"
  PYTHON_CMD=$(pyenv which python)
  PIP_CMD=$(pyenv which pip)
  log "🔍 DEBUG: Python command: $PYTHON_CMD"
  log "🔍 DEBUG: Pip command: $PIP_CMD"
else
  log "ℹ️ INFO: Using system Python"
  PYTHON_CMD="python3"
  PIP_CMD="pip3"
fi

# Check if token file exists
if [ ! -f "$TOKEN_FILE" ]; then
  handle_error "Token file not found: $TOKEN_FILE"
fi

# Read token from file
TOKEN=$(cat $TOKEN_FILE)
if [ -z "$TOKEN" ]; then
  handle_error "Token file is empty"
fi

TOKEN_SHORT="${TOKEN:0:10}:****${TOKEN:(-4)}"
log "Using Telegram bot token: $TOKEN_SHORT"

# Check if ngrok is running
log "Setting up ngrok tunnel for local webhook development..."
log "Checking for existing ngrok tunnels or creating a new one..."

# Retry logic for ngrok
NGROK_URL=""
MAX_RETRIES=3
RETRY_COUNT=0
RETRY_DELAY=2

while [ -z "$NGROK_URL" ] && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  # Try to get existing ngrok tunnels
  NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
  
  if [ -z "$NGROK_URL" ]; then
    # Start ngrok if not already running (in background)
    if [ $RETRY_COUNT -gt 0 ]; then
      log "${YELLOW}Attempt $((RETRY_COUNT+1))/$MAX_RETRIES to start ngrok...${RESET}"
    fi
    
    nohup ngrok http 8000 > /dev/null 2>&1 &
    sleep $RETRY_DELAY
    
    RETRY_COUNT=$((RETRY_COUNT+1))
    RETRY_DELAY=$((RETRY_DELAY*2))  # Exponential backoff
  fi
done

if [ -z "$NGROK_URL" ]; then
  handle_error "Failed to start ngrok or get tunnel URL after $MAX_RETRIES attempts"
fi

log "✅ SUCCESS: Ngrok tunnel established: $NGROK_URL"

# Run the Python script
log "Getting authentication token from API..."
log "🔍 DEBUG: Attempting to get test token from http://localhost:8000/v1/api/auth/test-token"

# Make sure the Python script is executable
chmod +x "$PYTHON_SCRIPT"

# Build command with debug flag if needed
PYTHON_ARGS=""
if [ "$DEBUG" = true ]; then
  PYTHON_ARGS="--debug"
fi

# Run the Python script and capture its output
"$PYTHON_CMD" "$PYTHON_SCRIPT" $PYTHON_ARGS | tee /tmp/bot_setup_output.txt
exit_code=$?

if [ $exit_code -ne 0 ]; then
  # Check for common error patterns
  if grep -q "telegram_token.txt not found" /tmp/bot_setup_output.txt; then
    handle_error "Token file not found or inaccessible. Create a token file with your Telegram bot token"
  elif grep -q "Connection refused" /tmp/bot_setup_output.txt; then
    handle_error "API server connection refused. Make sure the API server is running at http://localhost:8000"
  elif grep -q "Authentication error" /tmp/bot_setup_output.txt; then
    handle_error "API authentication failed. Check your API credentials"
  else
    handle_error "Python script failed with exit code $exit_code. Check the output for details"
  fi
else
  # Extract webhook status and error from the Python script output
  WEBHOOK_STATUS=$(grep "Webhook Status:" /tmp/bot_setup_output.txt | tail -1 | cut -d':' -f2- | tr -d ' ')
  WEBHOOK_URL=$(grep "Webhook URL:" /tmp/bot_setup_output.txt | tail -1 | cut -d':' -f2- | sed 's/^[ \t]*//')
  ERROR_MESSAGE=$(grep -A 2 "Direct Telegram API call failed" /tmp/bot_setup_output.txt 2>/dev/null || \
                  grep -A 2 "Failed to set webhook" /tmp/bot_setup_output.txt 2>/dev/null || \
                  grep -A 2 "Error setting webhook" /tmp/bot_setup_output.txt 2>/dev/null || echo "")

  if [ "$WEBHOOK_STATUS" = "error" ]; then
    log "⚠️ WARNING: Bot setup completed but webhook setup failed"
    log "Webhook is available at: $NGROK_URL/v1/api/webhook/telegram"
    if [ -n "$ERROR_MESSAGE" ]; then
      log "Error details:"
      echo "$ERROR_MESSAGE" | while read -r line; do
        log "  $line"
      done
    fi
  else
    log "✅ SUCCESS: Bot setup completed successfully!"
    log "Webhook is available at: $NGROK_URL/v1/api/webhook/telegram"
  fi
  
  log "Use this URL for testing your Telegram bot."
fi

log "To view the bot logs, run: python -m src.scripts.bots.utils.view_bot_logs"
log "  Filter options: --event-type INCOMING|OUTGOING, --contains \"text\", --raw"