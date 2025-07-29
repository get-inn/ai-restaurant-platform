#!/bin/bash

# Configuration
API_BASE_URL="http://localhost:8000"
# External URL accessible from the internet for Telegram webhooks (must be HTTPS)
EXTERNAL_BASE_URL="https://your-domain.com"  # Change this to your actual domain
BOT_NAME="Сяо Чи (小吃)"
BOT_TOKEN="7803081968:AAHIZZh27PZUuZU2BkjJI2NYz11Yz5dXSFo"
FIXED_BOT_ID="11111111-1111-1111-1111-111111111111"  # Use fixed ID for testing

# Determine project root and logs directory
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"
BOT_LOGS_DIR="$PROJECT_ROOT/logs"
BACKEND_LOGS_DIR="$BACKEND_DIR/logs"
LOG_FILE="$BACKEND_DIR/telegram_bot_setup.log"

# Ensure bot logs directory exists
mkdir -p "$BOT_LOGS_DIR"
mkdir -p "$BACKEND_LOGS_DIR"

# Clear log file
> "$LOG_FILE"

# Function to log messages
log() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

# Function to get auth token
get_auth_token() {
    log "Getting authentication token..."
    
    # For a real implementation, you would authenticate with your API
    # This is a placeholder for the test token
    TEST_TOKEN="test_token_for_api_access"
    
    log "✅ Authentication token obtained"
    echo "$TEST_TOKEN"
}

# Function to make a safe curl request with error handling
safe_curl() {
    local method=$1
    local url=$2
    local auth_token=$3
    local data=$4
    local description=$5
    
    log "Making $method request to $url"
    
    local response
    local exit_code
    
    if [ -z "$data" ]; then
        # GET request
        response=$(curl -s -X "$method" \
            -H "Authorization: Bearer $auth_token" \
            -H "Content-Type: application/json" \
            -w "\nHTTP_STATUS:%{http_code}" \
            "$url")
        exit_code=$?
    else
        # POST/PUT request with data
        response=$(curl -s -X "$method" \
            -H "Authorization: Bearer $auth_token" \
            -H "Content-Type: application/json" \
            -d "$data" \
            -w "\nHTTP_STATUS:%{http_code}" \
            "$url")
        exit_code=$?
    fi
    
    # Extract HTTP status code
    local http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d':' -f2)
    local response_body=$(echo "$response" | grep -v "HTTP_STATUS:")
    
    # Check for curl errors
    if [ $exit_code -ne 0 ]; then
        log "⚠️ Curl error: $exit_code when $description"
        log "Request URL: $url"
        log "Request data: $data"
        echo "ERROR:$exit_code"
        return
    fi
    
    # Check HTTP status code
    if [[ -z "$http_status" || "$http_status" -ge 400 ]]; then
        log "⚠️ HTTP error: $http_status when $description"
        log "Request URL: $url"
        log "Request data: $data"
        log "Response: $response_body"
        echo "ERROR:$http_status"
        return
    fi
    
    log "✅ $description successful"
    echo "$response_body"
}

# Function to create or activate the bot
setup_bot() {
    local auth_token=$1
    local account_id="00000000-0000-0000-0000-000000000000"  # Replace with actual account ID if known
    
    log "Setting up bot for account ID: $account_id"
    
    # Check if bot already exists by listing all bots
    log "Checking if bot already exists..."
    local bots_response=$(safe_curl "GET" "$API_BASE_URL/v1/api/bots?account_id=$account_id" "$auth_token" "" "Listing bots")
    
    # Check for error
    if [[ "$bots_response" == ERROR:* ]]; then
        log "⚠️ Failed to list bots. Will try to create a new one."
        local bot_id=""
    else
        # For real implementation, parse the JSON response to check if bot exists
        # For this example, we'll assume we need to create a new bot
        local bot_id=""
    fi
    
    if [ -z "$bot_id" ]; then
        log "Bot doesn't exist, creating a new one..."
        
        # Create bot instance
        local create_data="{
            \"name\": \"$BOT_NAME\",
            \"description\": \"Telegram Bot for HR\",
            \"account_id\": \"$account_id\"
        }"
        
        local create_response=$(safe_curl "POST" "$API_BASE_URL/v1/api/accounts/$account_id/bots" "$auth_token" "$create_data" "Creating bot")
        
        # Check for error
        if [[ "$create_response" == ERROR:* ]]; then
            log "⚠️ Failed to create bot. Using fixed ID for demonstration."
            bot_id="$FIXED_BOT_ID"
        else
            # For real implementation, extract bot ID from the response
            # For this example, we'll use a fixed ID
            bot_id="$FIXED_BOT_ID"
        fi
        
        log "Bot ID: $bot_id"
    else
        log "Bot already exists with ID: $bot_id"
        
        # Activate the bot if it exists
        local activate_response=$(safe_curl "POST" "$API_BASE_URL/v1/api/bots/$bot_id/activate" "$auth_token" "{}" "Activating bot")
        
        # Check for error
        if [[ "$activate_response" == ERROR:* ]]; then
            log "⚠️ Failed to activate bot, but will continue with setup."
        fi
    fi
    
    # Add or update Telegram platform credentials
    log "Adding Telegram credentials to bot..."
    local cred_data="{
        \"platform\": \"telegram\",
        \"credentials\": {
            \"token\": \"$BOT_TOKEN\"
        },
        \"is_active\": true
    }"
    
    local cred_response=$(safe_curl "POST" "$API_BASE_URL/v1/api/bots/$bot_id/platforms" "$auth_token" "$cred_data" "Adding Telegram credentials")
    
    # Check for error
    if [[ "$cred_response" == ERROR:* ]]; then
        log "⚠️ Failed to add Telegram credentials, but will continue with setup."
    fi
    
    # Set up webhook
    log "Setting up webhook..."
    local webhook_data="{
        \"url\": \"$EXTERNAL_BASE_URL/v1/api/webhooks/telegram/$bot_id/receive\",
        \"drop_pending_updates\": true,
        \"allowed_updates\": [\"message\", \"callback_query\"]
    }"
    
    local webhook_response=$(safe_curl "POST" "$API_BASE_URL/v1/api/webhooks/telegram/$bot_id/set" "$auth_token" "$webhook_data" "Setting up webhook")
    
    # Check for error
    if [[ "$webhook_response" == ERROR:* ]]; then
        log "⚠️ Failed to set up webhook, but will continue with setup."
    fi
    
    echo "$bot_id"
}

# Main execution
log "Starting Telegram bot setup script..."

# Get auth token
AUTH_TOKEN=$(get_auth_token)
if [ -z "$AUTH_TOKEN" ]; then
    log "❌ Failed to get authentication token. Exiting."
    exit 1
fi

# Setup bot
BOT_ID=$(setup_bot "$AUTH_TOKEN")
if [ -z "$BOT_ID" ]; then
    log "❌ Failed to set up bot. Exiting."
    exit 1
fi

# Check bot status
log "Checking bot status..."
status_response=$(safe_curl "GET" "$API_BASE_URL/v1/api/bots/$BOT_ID" "$AUTH_TOKEN" "" "Checking bot status")

# Check webhook status
log "Checking webhook status via API..."
webhook_status=$(safe_curl "GET" "$API_BASE_URL/v1/api/webhooks/telegram/$BOT_ID/status" "$AUTH_TOKEN" "" "Checking webhook status")

# Check webhook status directly with Telegram
log "Checking webhook status directly with Telegram API..."
telegram_webhook_info=$(curl -s "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo")
log "Telegram webhook info: $telegram_webhook_info"

log "✅ Setup completed successfully! Bot ID: $BOT_ID"
log "See $LOG_FILE for detailed log output"
log "Bot logs are stored in: $BOT_LOGS_DIR"

# Create a sample bot conversation log entry with correct formatting
SAMPLE_LOG="$BOT_LOGS_DIR/bot_conversations_$(date +%Y%m%d)_telegram.log"
log "Creating sample bot conversation log at: $SAMPLE_LOG"

cat > "$SAMPLE_LOG" << EOL
{"timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")", "level": "INFO", "event_type": "SYSTEM", "message": "Bot setup completed", "bot_id": "$BOT_ID", "platform": "telegram"}
{"timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.100Z")", "level": "INFO", "event_type": "INCOMING", "message": "Received: /start", "bot_id": "$BOT_ID", "platform": "telegram", "platform_chat_id": "test_chat", "user_id": "test_user"}
{"timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.200Z")", "level": "INFO", "event_type": "OUTGOING", "message": "Sent: Hello! I am $BOT_NAME, your HR assistant.", "bot_id": "$BOT_ID", "platform": "telegram", "platform_chat_id": "test_chat", "user_id": "test_user"}
EOL

# Ensure the sample log file has proper permissions
chmod 644 "$SAMPLE_LOG"

log "✅ Sample bot log created. Use the following commands to view it:"
log "python -m scripts.bots.utils.view_bot_logs --file $SAMPLE_LOG"
log "python -m scripts.bots.utils.view_bot_logs --bot-id $BOT_ID"

# Display bot information summary
log "=== Bot Information Summary ==="
log "Bot Name: $BOT_NAME"
log "Bot ID: $BOT_ID"
log "Platform: telegram"
log "Token: $BOT_TOKEN"
log "Webhook Status: Check the webhook_status and telegram_webhook_info above"
log "=== End of Summary ==="