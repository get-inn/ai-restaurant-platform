#!/bin/bash
# Script to check if all prerequisites are met for running the tests

# Source the common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

log "${CYAN}Checking prerequisites for Telegram bot tests...${RESET}"

# Check 1: API Server
log "Checking API server connectivity..."
API_RESPONSE=$(curl -s -m 3 $LOCAL_API/health || echo "")
if [ -z "$API_RESPONSE" ] || [ "$(echo $API_RESPONSE | grep -c "ok")" -eq 0 ]; then
    log "${RED}❌ API server not available at $LOCAL_API${RESET}"
    log "${YELLOW}Please ensure the API server is running.${RESET}"
    log "${YELLOW}Run:${RESET} ./start-dev.sh --local-api"
    API_OK=false
else
    log "${GREEN}✓ API server is running${RESET}"
    API_OK=true
fi

# Check 2: Telegram Token
log "Checking Telegram token..."
TOKEN=$(get_telegram_token)
if [ -z "$TOKEN" ]; then
    log "${RED}❌ Telegram token not found${RESET}"
    log "${YELLOW}Please create a telegram_token.txt file with your bot token${RESET}"
    TOKEN_OK=false
else
    log "${GREEN}✓ Telegram token is available${RESET}"
    TOKEN_OK=true
fi

# Check 3: Authentication
if [ "$API_OK" = true ]; then
    log "Checking API authentication..."
    AUTH_RESPONSE=$(curl -s -X POST "$LOCAL_API/v1/api/auth/test-token")
    if [ "$(echo "$AUTH_RESPONSE" | grep -c "access_token")" -eq 0 ]; then
        log "${RED}❌ API authentication failed${RESET}"
        log "${YELLOW}API server returned: ${AUTH_RESPONSE}${RESET}"
        AUTH_OK=false
    else
        log "${GREEN}✓ API authentication is working${RESET}"
        AUTH_OK=true
    fi
else
    log "${YELLOW}Skipping authentication check since API server is not available${RESET}"
    AUTH_OK=false
fi

# Check 4: ngrok
log "Checking ngrok..."
NGROK_URL=$(get_ngrok_url)
if [ -z "$NGROK_URL" ]; then
    log "${YELLOW}⚠️ ngrok tunnel not found${RESET}"
    log "${YELLOW}Some webhook tests may not work without ngrok${RESET}"
    log "${YELLOW}Run:${RESET} ngrok http 8000"
    NGROK_OK=false
else
    log "${GREEN}✓ ngrok tunnel is active: $NGROK_URL${RESET}"
    NGROK_OK=true
fi

# Check 5: Bot instance
if [ "$API_OK" = true ] && [ "$AUTH_OK" = true ]; then
    log "Checking bot instance..."
    AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    BOT_RESPONSE=$(curl -s -H "Authorization: Bearer $AUTH_TOKEN" "$LOCAL_API/v1/api/bots/$BOT_ID")
    
    if [ "$(echo "$BOT_RESPONSE" | grep -c "name")" -eq 0 ]; then
        log "${RED}❌ Bot instance not found with ID: $BOT_ID${RESET}"
        
        # Get the path to the backend directory
        BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
        
        log "${YELLOW}Please run:${RESET} cd $BACKEND_DIR && python -m src.scripts.bots.setup.telegram_bot_setup"
        BOT_OK=false
    else
        log "${GREEN}✓ Bot instance is available${RESET}"
        BOT_OK=true
    fi
else
    log "${YELLOW}Skipping bot instance check since API/auth is not working${RESET}"
    BOT_OK=false
fi

# Summary
echo ""
log "${CYAN}=== Test Prerequisites Summary ===${RESET}"
[ "$API_OK" = true ] && log "${GREEN}✓ API server${RESET}" || log "${RED}❌ API server${RESET}"
[ "$TOKEN_OK" = true ] && log "${GREEN}✓ Telegram token${RESET}" || log "${RED}❌ Telegram token${RESET}"
[ "$AUTH_OK" = true ] && log "${GREEN}✓ API authentication${RESET}" || log "${RED}❌ API authentication${RESET}" 
[ "$NGROK_OK" = true ] && log "${GREEN}✓ ngrok tunnel${RESET}" || log "${YELLOW}⚠️ ngrok tunnel${RESET}"
[ "$BOT_OK" = true ] && log "${GREEN}✓ Bot instance${RESET}" || log "${RED}❌ Bot instance${RESET}"

if [ "$API_OK" = true ] && [ "$TOKEN_OK" = true ] && [ "$AUTH_OK" = true ] && [ "$BOT_OK" = true ]; then
    log "${GREEN}✓✓✓ All critical prerequisites met! Tests can run successfully.${RESET}"
    exit 0
else
    if [ "$NGROK_OK" = false ] && [ "$API_OK" = true ] && [ "$TOKEN_OK" = true ] && [ "$AUTH_OK" = true ] && [ "$BOT_OK" = true ]; then
        log "${YELLOW}⚠️ Most prerequisites met, but webhook tests may not work fully without ngrok.${RESET}"
        exit 0
    else
        log "${RED}❌ Some critical prerequisites are missing. Please fix the issues above.${RESET}"
        exit 1
    fi
fi