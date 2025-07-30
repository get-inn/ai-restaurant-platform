#!/bin/bash
# Common utilities for Telegram bot testing

# Default configuration
BOT_ID="660c1cab-1dc6-46c9-9cab-774c28f0cfe5"
CHAT_ID="397234852"
WEBHOOK_URL="http://localhost:8000/v1/api/webhooks/telegram/$BOT_ID"
LOCAL_API="http://localhost:8000"
TOKEN_FILE="../../../../telegram_token.txt"

# Colors for better readability
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

# Logging function
log() {
  local timestamp=$(date '+[%Y-%m-%d %H:%M:%S]')
  echo -e "$timestamp $1"
}

# Find the correct Python command
get_python_cmd() {
  if command -v python3 &> /dev/null; then
    echo "python3"
  elif command -v python &> /dev/null; then
    echo "python"
  else
    log "${RED}Python executable not found. Please ensure Python is installed.${RESET}"
    exit 1
  fi
}

# Get Telegram token from file
get_telegram_token() {
  if [ -f "$TOKEN_FILE" ]; then
    TOKEN=$(cat $TOKEN_FILE)
    TOKEN_SHORT="${TOKEN:0:10}:****${TOKEN:(-4)}"
    log "Using Telegram bot token: $TOKEN_SHORT"
    echo "$TOKEN"
  else
    log "⚠️ ${YELLOW}WARNING: Token file not found at $TOKEN_FILE, proceeding without token${RESET}"
    echo ""
  fi
}

# Get authentication token from API
get_auth_token() {
  log "Getting authentication token from API..."
  AUTH_RESPONSE=$(curl -s -X POST "$LOCAL_API/v1/api/auth/test-token")
  
  if [ "$(echo "$AUTH_RESPONSE" | grep -c "access_token")" -eq 0 ]; then
    log "❌ ${RED}ERROR: Failed to get authentication token. Response: ${AUTH_RESPONSE}${RESET}"
    log "❌ ${RED}Make sure the API server is running at ${LOCAL_API}${RESET}"
    exit 1
  fi
  
  AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

  if [ -z "$AUTH_TOKEN" ]; then
    log "❌ ${RED}ERROR: Failed to extract authentication token from response${RESET}"
    exit 1
  fi

  log "✅ ${GREEN}Got authentication token${RESET}"
  echo "$AUTH_TOKEN"
}

# Get ngrok URL
get_ngrok_url() {
  log "Checking for ngrok tunnel..."
  NGROK_RESPONSE=$(curl -s -m 3 http://localhost:4040/api/tunnels || echo "")
  
  if [ -z "$NGROK_RESPONSE" ]; then
    log "⚠️ ${YELLOW}Could not connect to ngrok API at http://localhost:4040/api/tunnels${RESET}"
    log "⚠️ ${YELLOW}Make sure ngrok is running with 'ngrok http 8000'${RESET}"
    echo ""
    return
  fi
  
  NGROK_URL=$(echo "$NGROK_RESPONSE" | grep -o '"public_url":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")

  if [ -z "$NGROK_URL" ]; then
    log "⚠️ ${YELLOW}No ngrok tunnel found in response: ${NGROK_RESPONSE}${RESET}"
    log "⚠️ ${YELLOW}Make sure ngrok is properly configured${RESET}"
  else
    log "✅ ${GREEN}Using ngrok URL: $NGROK_URL${RESET}"
  fi
  
  echo "$NGROK_URL"
}

# Send webhook message to bot
send_webhook() {
  local update_id=$1
  local data=$2
  local silent=${3:-false}
  
  if [ "$silent" = true ]; then
    curl -s -X POST $WEBHOOK_URL \
      -H "Content-Type: application/json" \
      -d "$data" > /dev/null
  else
    curl -X POST $WEBHOOK_URL \
      -H "Content-Type: application/json" \
      -d "$data"
  fi
  
  # Small delay to allow webhook processing
  sleep 0.5
}

# Send text message webhook
send_text_message() {
  local update_id=$1
  local message_text=$2
  local silent=${3:-false}
  
  local data='{
    "update_id": '$update_id',
    "message": {
      "message_id": '$((1000 + update_id))',
      "from": {
        "id": '"$CHAT_ID"',
        "is_bot": false,
        "first_name": "Test",
        "username": "testuser" 
      },
      "chat": {
        "id": '"$CHAT_ID"',
        "first_name": "Test",
        "username": "testuser",
        "type": "private"
      },
      "date": 1753856000,
      "text": "'"$message_text"'"
    }
  }'
  
  if [ "$silent" = false ]; then
    log "Sending text message: \"$message_text\""
  fi
  
  send_webhook $update_id "$data" $silent
}

# Send button click webhook (callback query)
send_button_click() {
  local update_id=$1
  local button_data=$2
  local display_text=$3
  local silent=${4:-false}
  
  local data='{
    "update_id": '$update_id',
    "callback_query": {
      "id": "callback_'$update_id'",
      "from": {
        "id": '"$CHAT_ID"',
        "is_bot": false,
        "first_name": "Test",
        "username": "testuser"
      },
      "message": {
        "message_id": '$((1000 + update_id))',
        "from": {
          "id": 987654321,
          "is_bot": true,
          "first_name": "TestBot",
          "username": "test_bot"
        },
        "chat": {
          "id": '"$CHAT_ID"',
          "first_name": "Test",
          "username": "testuser",
          "type": "private"
        },
        "date": 1753856000,
        "text": "'"$display_text"'"
      },
      "chat_instance": "1234567890123456789",
      "data": "'"$button_data"'"
    }
  }'
  
  if [ "$silent" = false ]; then
    log "Clicking button: \"$button_data\""
  fi
  
  send_webhook $update_id "$data" $silent
}

# Reload bot scenario
reload_scenario() {
  log "${YELLOW}Reloading the onboarding scenario with force_reload=True...${RESET}"
  
  PYTHON_CMD=$(get_python_cmd)
  
  # Get the path to the backend directory (4 levels up from current script)
  BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
  
  # Change to backend directory first so Python module imports work correctly
  pushd "$BACKEND_DIR" > /dev/null
  
  $PYTHON_CMD -m src.scripts.bots.setup.telegram_bot_setup --debug
  RESULT=$?
  
  # Return to original directory
  popd > /dev/null
  
  if [ $RESULT -ne 0 ]; then
    log "${RED}Failed to reload scenario. Aborting test.${RESET}"
    exit 1
  fi
  
  log "${GREEN}Scenario reloaded successfully!${RESET}"
}

# View bot logs
view_bot_logs() {
  local bot_id=${1:-$BOT_ID}
  local chat_id=${2:-$CHAT_ID}
  
  PYTHON_CMD=$(get_python_cmd)
  
  # Get the path to the backend directory (4 levels up from current script)
  BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
  
  # Change to backend directory first so Python module imports work correctly
  pushd "$BACKEND_DIR" > /dev/null
  
  log "${GREEN}Viewing logs for bot ID: $bot_id, chat ID: $chat_id${RESET}"
  $PYTHON_CMD -m src.scripts.bots.utils.view_bot_logs --platform telegram --chat-id $chat_id
  
  # Return to original directory
  popd > /dev/null
}

# Check webhook status
check_webhook_status() {
  local auth_token=$1
  local bot_id=${2:-$BOT_ID}
  
  log "Testing webhook status via API..."
  STATUS_URL="$LOCAL_API/v1/api/webhooks/telegram/$bot_id/status"
  STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $auth_token" "$STATUS_URL")
  
  log "Webhook status response:"
  if [ -z "$STATUS_RESPONSE" ]; then
    log "${RED}Empty response from webhook status endpoint${RESET}"
  elif echo "$STATUS_RESPONSE" | grep -q "Invalid HTTP request"; then
    log "${RED}Invalid HTTP request: $STATUS_RESPONSE${RESET}"
    log "${YELLOW}This might be due to API server configuration issues${RESET}"
  else
    # Try to format as JSON if possible
    if echo "$STATUS_RESPONSE" | jq -e . >/dev/null 2>&1; then
      echo "$STATUS_RESPONSE" | jq .
    else
      echo "$STATUS_RESPONSE"
    fi
  fi
}

# Send full onboarding flow up to the specified step
run_onboarding_flow_to() {
  local target_step=$1
  local silent=${2:-true}
  local update_id=733686851
  
  # Start with /start command
  if [ "$silent" = false ]; then log "${CYAN}Starting onboarding flow...${RESET}"; fi
  send_text_message $update_id "/start" $silent
  update_id=$((update_id + 1))
  
  # Send first name
  send_text_message $update_id "Ivan" $silent
  update_id=$((update_id + 1))
  
  # Send last name
  send_text_message $update_id "Petrov" $silent
  update_id=$((update_id + 1))
  
  # Break if we've reached the target step
  if [ "$target_step" = "ask_position" ]; then return; fi
  
  # Select position
  send_button_click $update_id "food-guide" "Кем ты работаешь в ЧиХо?" $silent
  update_id=$((update_id + 1))
  
  # Break if we've reached the target step
  if [ "$target_step" = "ask_project" ]; then return; fi
  
  # Select project
  send_button_click $update_id "pyatnitskaya" "На каком проекте ты будешь работать?" $silent
  update_id=$((update_id + 1))
  
  # Break if we've reached the target step
  if [ "$target_step" = "ask_first_shift" ]; then return; fi
  
  # Send first shift datetime
  send_text_message $update_id "10.08 10:00" $silent
  update_id=$((update_id + 1))
  
  # Break if we've reached the target step
  if [ "$target_step" = "ask_citizenship" ]; then return; fi
  
  # Select citizenship
  send_button_click $update_id "rf" "И еще: укажи своё гражданство" $silent
  update_id=$((update_id + 1))
  
  # Break if we've reached the target step
  if [ "$target_step" = "confirm_data" ]; then return; fi
  
  # Confirm data
  send_button_click $update_id "yes" "Се-се, давай зафиналим:" $silent
  update_id=$((update_id + 1))
  
  # Break if we've reached the target step
  if [ "$target_step" = "first_day_instructions" ]; then return; fi
  
  # Continue through first_day_instructions to documents_button
  send_button_click $update_id "next" "Прежде чем начать погружение..." $silent
  update_id=$((update_id + 1))
  
  # Break if we've reached the target step
  if [ "$target_step" = "documents_button" ]; then return; fi
  
  # Click the "Оки-доки! 👌" button
  send_button_click $update_id "ok" "Список необходимых документов..." $silent
  update_id=$((update_id + 1))
  
  # Break if we've reached the target step
  if [ "$target_step" = "company_history" ]; then return; fi
  
  # Continue through company_history to company_ideology
  # Note: This step now includes an image with file_id "company_history_image"
  send_button_click $update_id "next" "Отлично! Тогда давай погружаться в ЧиХо with image: company_history_image" $silent
  update_id=$((update_id + 1))
  
  # Break if we've reached the target step
  if [ "$target_step" = "company_ideology" ]; then return; fi
  
  # Continue through company_ideology to company_values
  send_button_click $update_id "next" "ЧиХо – это не просто сеть китайских закусочных..." $silent
  update_id=$((update_id + 1))
  
  # Return the next update_id for further interactions
  echo $update_id
}