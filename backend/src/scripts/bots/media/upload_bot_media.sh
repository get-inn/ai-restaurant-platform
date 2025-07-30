#!/bin/bash
# Script to upload any media file to the bot media store and register it for use in scenarios
# New name: upload_bot_media.sh

# Default configuration
API_URL="http://localhost:8000"
IMAGE_PATH=""
MEDIA_FILE_ID=""
DESCRIPTION=""

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    --url|-u)
      API_URL="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -i, --image PATH        Path to the image file to upload"
      echo "  -f, --file-id ID        File ID to use in the scenario"
      echo "  -d, --description DESC  Description of the image"
      echo "  -u, --url URL           API URL (default: http://localhost:8000)"
      echo "  -h, --help              Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help to see available options"
      exit 1
      ;;
  esac
done

# Validate required parameters
if [ -z "$IMAGE_PATH" ]; then
    echo -e "${RED}Error: Image path is required. Use --image or -i option.${NC}"
    echo "Use --help for more information"
    exit 1
fi

if [ ! -f "$IMAGE_PATH" ]; then
    echo -e "${RED}Error: Image file not found at $IMAGE_PATH${NC}"
    exit 1
fi

# Generate file ID from filename if not specified
if [ -z "$MEDIA_FILE_ID" ]; then
    FILENAME=$(basename "$IMAGE_PATH")
    MEDIA_FILE_ID="${FILENAME%.*}_$(date +%s)" # Use filename without extension + timestamp
    echo -e "${YELLOW}Auto-generated file ID: $MEDIA_FILE_ID${NC}"
fi

# Generate description if not specified
if [ -z "$DESCRIPTION" ]; then
    FILENAME=$(basename "$IMAGE_PATH")
    DESCRIPTION="Image: $FILENAME"
    echo -e "${YELLOW}Auto-generated description: $DESCRIPTION${NC}"
fi

# Check if jq is installed (needed for JSON processing)
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed but is required for this script.${NC}"
    echo "Please install jq: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 1
fi

# Function to get authentication token
get_auth_token() {
    echo -e "${BLUE}Getting authentication token...${NC}"
    
    TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/v1/api/auth/test-token" \
        -H "Content-Type: application/json" \
        -d '{}')
    
    TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token // empty')
    
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}Failed to get authentication token${NC}"
        echo "API Response: $TOKEN_RESPONSE"
        exit 1
    fi
    
    echo -e "${GREEN}Authentication token obtained successfully${NC}"
}

# Function to list available bots
list_bots() {
    echo -e "${BLUE}Listing available bots...${NC}"
    
    BOTS_RESPONSE=$(curl -s -X GET "$API_URL/v1/api/accounts/00000000-0000-0000-0000-000000000001/bots" \
        -H "Authorization: Bearer $TOKEN")
    
    # Debugging: Print raw response for analysis
    # echo "Raw API response: $BOTS_RESPONSE"
    
    # Check if the response is valid JSON
    if ! echo "$BOTS_RESPONSE" | jq empty 2>/dev/null; then
        echo -e "${RED}Error: Invalid JSON response from API${NC}"
        echo "Response: $BOTS_RESPONSE"
        exit 1
    fi
    
    # Check if the response is an array
    if ! echo "$BOTS_RESPONSE" | jq 'if type == "array" then true else false end' | grep -q true; then
        echo -e "${RED}Error: Expected array of bots but got a different response${NC}"
        echo "Response type: $(echo "$BOTS_RESPONSE" | jq type)"
        
        # Check if the response contains an error detail
        ERROR=$(echo "$BOTS_RESPONSE" | jq -r '.detail // empty')
        if [ ! -z "$ERROR" ]; then
            echo -e "${RED}Error from API: $ERROR${NC}"
        fi
        exit 1
    fi
    
    # Extract and display bot information
    BOTS_COUNT=$(echo "$BOTS_RESPONSE" | jq length)
    
    if [ "$BOTS_COUNT" -eq 0 ]; then
        echo -e "${YELLOW}No bots found. Please create a bot first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Found $BOTS_COUNT bots:${NC}"
    echo "$BOTS_RESPONSE" | jq -r '.[] | "ID: \(.id) | Name: \(.name) | Platform: \(.platform)"'
    
    # Determine if the response is an array or a single object
    IS_ARRAY=$(echo "$BOTS_RESPONSE" | jq 'if type == "array" then true else false end')
    
    if [ "$IS_ARRAY" = "true" ]; then
        # For onboarding bot, try to find the specific one we need
        ONBOARDING_BOT_ID=$(echo "$BOTS_RESPONSE" | jq -r '.[] | select(.name | contains("Onboarding") or contains("onboarding")) | .id')
        
        if [ ! -z "$ONBOARDING_BOT_ID" ]; then
            echo -e "${YELLOW}Found an onboarding bot with ID: $ONBOARDING_BOT_ID${NC}"
            echo -e "Using this bot automatically."
            BOT_ID="$ONBOARDING_BOT_ID"
        else
            # Just use the first bot in the array
            BOT_ID=$(echo "$BOTS_RESPONSE" | jq -r '.[0].id')
            BOT_NAME=$(echo "$BOTS_RESPONSE" | jq -r '.[0].name')
            echo -e "${YELLOW}Using first available bot: $BOT_NAME (ID: $BOT_ID)${NC}"
        fi
    else
        # Handle single object response
        BOT_ID=$(echo "$BOTS_RESPONSE" | jq -r '.id')
        BOT_NAME=$(echo "$BOTS_RESPONSE" | jq -r '.name')
        echo -e "${YELLOW}Using bot: $BOT_NAME (ID: $BOT_ID)${NC}"
    fi
    
    echo -e "${GREEN}Selected bot with ID: $BOT_ID${NC}"
}

# Function to check if media with this file ID already exists
check_existing_media() {
    echo -e "${BLUE}Checking if media with file ID '$MEDIA_FILE_ID' already exists...${NC}"
    
    # Get all media files for this bot
    MEDIA_RESPONSE=$(curl -s -X GET "$API_URL/v1/api/bots/$BOT_ID/media" \
        -H "Authorization: Bearer $TOKEN")
    
    # Check if the response is valid JSON
    if ! echo "$MEDIA_RESPONSE" | jq empty 2>/dev/null; then
        echo -e "${RED}Error: Invalid JSON response from API${NC}"
        echo "Response: $MEDIA_RESPONSE"
        return 1
    fi
    
    # Check if the response contains an error (handles both object and array responses)
    if echo "$MEDIA_RESPONSE" | jq -e 'if type == "object" then .detail else empty end' > /dev/null 2>&1; then
        ERROR=$(echo "$MEDIA_RESPONSE" | jq -r '.detail')
        echo -e "${RED}Error listing media: $ERROR${NC}"
        return 1
    fi
    
    # Check if any media has our platform file ID
    EXISTING_MEDIA=$(echo "$MEDIA_RESPONSE" | jq -r --arg file_id "$MEDIA_FILE_ID" '.[] | select(.platform_file_ids.telegram==$file_id) | .id')
    
    if [ ! -z "$EXISTING_MEDIA" ]; then
        echo -e "${YELLOW}Media with file ID '$MEDIA_FILE_ID' already exists (ID: $EXISTING_MEDIA)${NC}"
        MEDIA_ID=$EXISTING_MEDIA
        return 0
    fi
    
    echo -e "${BLUE}No existing media found with this file ID${NC}"
    return 1
}

# Function to upload media file
upload_media_file() {
    # First check if media already exists
    if check_existing_media; then
        echo -e "${GREEN}Using existing media file with ID: $MEDIA_ID${NC}"
        echo -e "Media is available for use in scenarios with file_id: ${YELLOW}$MEDIA_FILE_ID${NC}"
        return 0
    fi
    
    echo -e "${BLUE}Uploading image file to bot media store...${NC}"
    echo -e "File: ${YELLOW}$IMAGE_PATH${NC}"
    
    # Using curl's form upload for the file
    UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/v1/api/bots/$BOT_ID/media" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@$IMAGE_PATH")
    
    # Check if the response is valid JSON
    if ! echo "$UPLOAD_RESPONSE" | jq empty 2>/dev/null; then
        echo -e "${RED}Error: Invalid JSON response from API${NC}"
        echo "Response: $UPLOAD_RESPONSE"
        exit 1
    fi
    
    # Check if the response contains an error
    ERROR=$(echo "$UPLOAD_RESPONSE" | jq -r '.detail // empty')
    if [ ! -z "$ERROR" ]; then
        echo -e "${RED}Error uploading media: $ERROR${NC}"
        exit 1
    fi
    
    # Get media ID from the response
    MEDIA_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.media_id // .id // empty')
    
    if [ -z "$MEDIA_ID" ]; then
        echo -e "${RED}Failed to upload media file${NC}"
        echo "API Response: $UPLOAD_RESPONSE"
        exit 1
    fi
    
    echo -e "${GREEN}Media file uploaded successfully with ID: $MEDIA_ID${NC}"
    
    # Register the file ID for the platform
    echo -e "${BLUE}Registering platform file ID...${NC}"
    
    REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/v1/api/media/$MEDIA_ID/platform-id" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"platform\": \"telegram\",
            \"file_id\": \"$MEDIA_FILE_ID\"
        }")
    
    # Check if the response contains an error
    ERROR=$(echo "$REGISTER_RESPONSE" | jq -r '.detail // empty')
    if [ ! -z "$ERROR" ]; then
        echo -e "${RED}Error registering file ID: $ERROR${NC}"
        exit 1
    fi
    
    # Check if response is valid JSON and contains the expected ID
    if ! echo "$REGISTER_RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
        echo -e "${RED}Failed to register platform file ID${NC}"
        echo "API Response: $REGISTER_RESPONSE"
        exit 1
    fi
    
    # All looks good if we reach here
    
    echo -e "${GREEN}Platform file ID registered successfully${NC}"
    echo -e "Media is now available for use in scenarios with file_id: ${YELLOW}$MEDIA_FILE_ID${NC}"
}

# Main execution flow
echo -e "${YELLOW}=== Uploading Media File to Bot Media Store ===${NC}"
echo -e "Image: ${BLUE}$(basename "$IMAGE_PATH")${NC}"
echo -e "File ID: ${BLUE}$MEDIA_FILE_ID${NC}"
echo -e "Description: ${BLUE}$DESCRIPTION${NC}"

get_auth_token
list_bots
upload_media_file

echo -e "${GREEN}=== Process completed successfully ===${NC}"
echo -e "You can now use this image in your scenario by adding:"
echo -e "${BLUE}\"media\": [
  {
    \"type\": \"image\",
    \"description\": \"$DESCRIPTION\",
    \"file_id\": \"$MEDIA_FILE_ID\"
  }
]${NC}"