#!/bin/bash
#==============================================================================
# upload_bot_media.sh - Bot Media Upload Utility
#==============================================================================
# Uploads media files to the bot media store and registers them for use in
# bot scenarios. Supports image uploads with custom file IDs and descriptions.
#
# This script handles:
# - Authentication with the API
# - Bot selection
# - Media file upload
# - Platform file ID registration
# - Duplicate detection
#
# Author: GetInn Team
#==============================================================================

#==============================================================================
# Configuration
#==============================================================================
API_URL="http://localhost:8000"
IMAGE_PATH=""
MEDIA_FILE_ID=""
DESCRIPTION=""
PLATFORM="telegram"  # Default platform

#==============================================================================
# ANSI color codes
#==============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

#==============================================================================
# Functions
#==============================================================================

# Display help information
show_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Bot Media Upload Utility"
    echo "------------------------"
    echo "Uploads media files to the bot media store and registers them for use in scenarios."
    echo
    echo "Options:"
    echo "  -i, --image PATH        Path to the image file to upload (required)"
    echo "  -f, --file-id ID        File ID to use in the scenario (auto-generated if not provided)"
    echo "  -d, --description DESC  Description of the image (auto-generated if not provided)"
    echo "  -p, --platform NAME     Platform to register the file ID for (default: telegram)"
    echo "  -u, --url URL           API URL (default: http://localhost:8000)"
    echo "  -h, --help              Show this help message"
    echo
    echo "Examples:"
    echo "  $0 --image path/to/image.png"
    echo "  $0 --image path/to/image.png --file-id custom_id --description \"Menu photo\""
    echo
    exit 0
}

# Display error message and exit
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Display warning message
warning() {
    echo -e "${YELLOW}WARNING: $1${NC}" >&2
}

# Display info message
info() {
    echo -e "${BLUE}INFO: $1${NC}"
}

# Display success message
success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

# Get authentication token from API
get_auth_token() {
    info "Getting authentication token..."
    
    TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/v1/api/auth/test-token" \
        -H "Content-Type: application/json" \
        -d '{}')
    
    # Check if curl command succeeded
    if [ $? -ne 0 ]; then
        error_exit "Failed to connect to API at $API_URL"
    fi
    
    TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token // empty')
    
    if [ -z "$TOKEN" ]; then
        error_exit "Failed to get authentication token. API Response: $TOKEN_RESPONSE"
    fi
    
    success "Authentication token obtained successfully"
}

# List available bots and select one
list_bots() {
    info "Listing available bots..."
    
    BOTS_RESPONSE=$(curl -s -X GET "$API_URL/v1/api/accounts/00000000-0000-0000-0000-000000000001/bots" \
        -H "Authorization: Bearer $TOKEN")
    
    # Check if the response is valid JSON
    if ! echo "$BOTS_RESPONSE" | jq empty 2>/dev/null; then
        error_exit "Invalid JSON response from API. Response: $BOTS_RESPONSE"
    fi
    
    # Check if the response is an array
    if ! echo "$BOTS_RESPONSE" | jq 'if type == "array" then true else false end' | grep -q true; then
        # Check if the response contains an error detail
        ERROR=$(echo "$BOTS_RESPONSE" | jq -r '.detail // empty')
        if [ ! -z "$ERROR" ]; then
            error_exit "API Error: $ERROR"
        else
            error_exit "Expected array of bots but got a different response type: $(echo "$BOTS_RESPONSE" | jq type)"
        fi
    fi
    
    # Extract and display bot information
    BOTS_COUNT=$(echo "$BOTS_RESPONSE" | jq length)
    
    if [ "$BOTS_COUNT" -eq 0 ]; then
        error_exit "No bots found. Please create a bot first."
    fi
    
    success "Found $BOTS_COUNT bots:"
    echo "$BOTS_RESPONSE" | jq -r '.[] | "ID: \(.id) | Name: \(.name) | Platform: \(.platform)"'
    
    # Bot selection logic
    if [ "$BOTS_COUNT" -gt 1 ]; then
        # For onboarding bot, try to find the specific one we need
        ONBOARDING_BOT_ID=$(echo "$BOTS_RESPONSE" | jq -r '.[] | select(.name | contains("Onboarding") or contains("onboarding")) | .id')
        
        if [ ! -z "$ONBOARDING_BOT_ID" ]; then
            warning "Found an onboarding bot with ID: $ONBOARDING_BOT_ID"
            info "Using this bot automatically."
            BOT_ID="$ONBOARDING_BOT_ID"
        else
            # Just use the first bot in the array
            BOT_ID=$(echo "$BOTS_RESPONSE" | jq -r '.[0].id')
            BOT_NAME=$(echo "$BOTS_RESPONSE" | jq -r '.[0].name')
            warning "Using first available bot: $BOT_NAME (ID: $BOT_ID)"
        fi
    else
        # Only one bot, use it
        BOT_ID=$(echo "$BOTS_RESPONSE" | jq -r '.[0].id')
        BOT_NAME=$(echo "$BOTS_RESPONSE" | jq -r '.[0].name')
        info "Using bot: $BOT_NAME (ID: $BOT_ID)"
    fi
    
    success "Selected bot with ID: $BOT_ID"
}

# Check if media with this file ID already exists
check_existing_media() {
    info "Checking if media with file ID '$MEDIA_FILE_ID' already exists..."
    
    # Get all media files for this bot
    MEDIA_RESPONSE=$(curl -s -X GET "$API_URL/v1/api/bots/$BOT_ID/media" \
        -H "Authorization: Bearer $TOKEN")
    
    # Check if the response is valid JSON
    if ! echo "$MEDIA_RESPONSE" | jq empty 2>/dev/null; then
        warning "Invalid JSON response from API when checking media"
        echo "Response: $MEDIA_RESPONSE"
        return 1
    fi
    
    # Check if the response contains an error (handles both object and array responses)
    if echo "$MEDIA_RESPONSE" | jq -e 'if type == "object" then .detail else empty end' > /dev/null 2>&1; then
        ERROR=$(echo "$MEDIA_RESPONSE" | jq -r '.detail')
        warning "Error listing media: $ERROR"
        return 1
    fi
    
    # Check if any media has our platform file ID
    EXISTING_MEDIA=$(echo "$MEDIA_RESPONSE" | jq -r --arg file_id "$MEDIA_FILE_ID" --arg platform "$PLATFORM" \
        '.[] | select(.platform_file_ids[$platform]==$file_id) | .id')
    
    if [ ! -z "$EXISTING_MEDIA" ]; then
        warning "Media with file ID '$MEDIA_FILE_ID' already exists (ID: $EXISTING_MEDIA)"
        MEDIA_ID=$EXISTING_MEDIA
        return 0
    fi
    
    info "No existing media found with this file ID"
    return 1
}

# Upload media file and register platform ID
upload_media_file() {
    # First check if media already exists
    if check_existing_media; then
        success "Using existing media file with ID: $MEDIA_ID"
        echo -e "Media is available for use in scenarios with file_id: ${YELLOW}$MEDIA_FILE_ID${NC}"
        return 0
    fi
    
    info "Uploading image file to bot media store..."
    info "File: $IMAGE_PATH"
    
    # Using curl's form upload for the file
    UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/v1/api/bots/$BOT_ID/media" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@$IMAGE_PATH")
    
    # Check if the response is valid JSON
    if ! echo "$UPLOAD_RESPONSE" | jq empty 2>/dev/null; then
        error_exit "Invalid JSON response from API during upload. Response: $UPLOAD_RESPONSE"
    fi
    
    # Check if the response contains an error
    ERROR=$(echo "$UPLOAD_RESPONSE" | jq -r '.detail // empty')
    if [ ! -z "$ERROR" ]; then
        error_exit "Error uploading media: $ERROR"
    fi
    
    # Get media ID from the response
    MEDIA_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.media_id // .id // empty')
    
    if [ -z "$MEDIA_ID" ]; then
        error_exit "Failed to upload media file. API Response: $UPLOAD_RESPONSE"
    fi
    
    success "Media file uploaded successfully with ID: $MEDIA_ID"
    
    # Register the file ID for the platform
    info "Registering $PLATFORM file ID..."
    
    REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/v1/api/media/$MEDIA_ID/platform-id" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"platform\": \"$PLATFORM\",
            \"file_id\": \"$MEDIA_FILE_ID\"
        }")
    
    # Check if the response contains an error
    ERROR=$(echo "$REGISTER_RESPONSE" | jq -r '.detail // empty')
    if [ ! -z "$ERROR" ]; then
        error_exit "Error registering file ID: $ERROR"
    fi
    
    # Check if response is valid JSON and contains the expected ID
    if ! echo "$REGISTER_RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
        error_exit "Failed to register platform file ID. API Response: $REGISTER_RESPONSE"
    fi
    
    success "Platform file ID registered successfully"
    echo -e "Media is now available for use in scenarios with file_id: ${YELLOW}$MEDIA_FILE_ID${NC}"
}

# Show usage example for scenario
show_usage_example() {
    cat << EOF

You can now use this image in your scenario by adding:
${BLUE}"media": [
  {
    "type": "image",
    "description": "$DESCRIPTION",
    "file_id": "$MEDIA_FILE_ID"
  }
]${NC}
EOF
}

#==============================================================================
# Main script
#==============================================================================

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --image|-i)
            IMAGE_PATH="$2"
            shift 2
            ;;
        --file-id|-f)
            MEDIA_FILE_ID="$2"
            shift 2
            ;;
        --description|-d)
            DESCRIPTION="$2"
            shift 2
            ;;
        --platform|-p)
            PLATFORM="$2"
            shift 2
            ;;
        --url|-u)
            API_URL="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            ;;
        *)
            error_exit "Unknown option: $1. Use --help to see available options."
            ;;
    esac
done

# Validate required parameters
if [ -z "$IMAGE_PATH" ]; then
    error_exit "Image path is required. Use --image or -i option."
fi

if [ ! -f "$IMAGE_PATH" ]; then
    error_exit "Image file not found at $IMAGE_PATH"
fi

# Validate platform
if [ -z "$PLATFORM" ]; then
    PLATFORM="telegram"
    warning "Platform not specified, defaulting to: $PLATFORM"
fi

# Check if jq is installed (needed for JSON processing)
if ! command -v jq &> /dev/null; then
    error_exit "jq is not installed but is required for this script.\nPlease install jq: brew install jq (macOS) or apt-get install jq (Linux)"
fi

# Generate file ID from filename if not specified
if [ -z "$MEDIA_FILE_ID" ]; then
    FILENAME=$(basename "$IMAGE_PATH")
    MEDIA_FILE_ID="${FILENAME%.*}_$(date +%s)" # Use filename without extension + timestamp
    warning "Auto-generated file ID: $MEDIA_FILE_ID"
fi

# Generate description if not specified
if [ -z "$DESCRIPTION" ]; then
    FILENAME=$(basename "$IMAGE_PATH")
    DESCRIPTION="Image: $FILENAME"
    warning "Auto-generated description: $DESCRIPTION"
fi

# Main execution flow
echo -e "${YELLOW}=== Bot Media Upload Utility ===${NC}"
echo -e "Image: ${BLUE}$(basename "$IMAGE_PATH")${NC}"
echo -e "File ID: ${BLUE}$MEDIA_FILE_ID${NC}"
echo -e "Description: ${BLUE}$DESCRIPTION${NC}"
echo -e "Platform: ${BLUE}$PLATFORM${NC}"
echo -e "API URL: ${BLUE}$API_URL${NC}"

get_auth_token
list_bots
upload_media_file

echo -e "${GREEN}=== Process completed successfully ===${NC}"
show_usage_example