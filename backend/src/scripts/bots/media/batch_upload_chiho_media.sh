#!/bin/bash
#==============================================================================
# batch_upload_chiho_media.sh - Batch Bot Media Upload Utility
#==============================================================================
# Uploads all images from a directory to the bot media store using the
# upload_bot_media.sh script. This is a specialized script for batch uploading
# Chiho images, but can be modified for other batch upload needs.
#
# Author: GetInn Team
#==============================================================================

#==============================================================================
# Configuration
#==============================================================================
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
UPLOAD_SCRIPT="$SCRIPT_DIR/upload_bot_media.sh"
IMAGES_DIR="/Users/antonkorchagin/Documents/GetInn/Dev/ai-restaurant-platform/backend/docs/modules/bot-management/chiho"
API_URL="http://localhost:8000"
PLATFORM="telegram"
FILE_EXTENSION="png"
DELAY_SECONDS=1

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
    echo "Batch Bot Media Upload Utility"
    echo "-----------------------------"
    echo "Uploads all images from a directory to the bot media store."
    echo
    echo "Options:"
    echo "  -d, --dir PATH         Directory containing images to upload (default: $IMAGES_DIR)"
    echo "  -e, --ext EXTENSION    File extension to upload (default: $FILE_EXTENSION)"
    echo "  -p, --platform NAME    Platform to register IDs for (default: $PLATFORM)"
    echo "  -u, --url URL          API URL (default: $API_URL)"
    echo "  -s, --script PATH      Path to upload script (default: auto-detected)"
    echo "  --delay SECONDS        Delay between uploads in seconds (default: $DELAY_SECONDS)"
    echo "  -h, --help             Show this help message"
    echo
    echo "Examples:"
    echo "  $0"
    echo "  $0 --dir /path/to/images --ext jpg"
    echo "  $0 --platform telegram --delay 2"
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

# Check prerequisites
check_prerequisites() {
    # Check if the upload script exists
    if [ ! -f "$UPLOAD_SCRIPT" ]; then
        error_exit "Upload script not found at $UPLOAD_SCRIPT"
    fi
    
    # Check if the images directory exists
    if [ ! -d "$IMAGES_DIR" ]; then
        error_exit "Images directory not found at $IMAGES_DIR"
    fi
    
    # Make the upload script executable
    chmod +x "$UPLOAD_SCRIPT"
    
    # Check if there are images with the specified extension
    IMAGE_COUNT=$(find "$IMAGES_DIR" -type f -name "*.$FILE_EXTENSION" | wc -l)
    if [ "$IMAGE_COUNT" -eq 0 ]; then
        error_exit "No *.$FILE_EXTENSION files found in $IMAGES_DIR"
    fi
    
    success "Found $IMAGE_COUNT images to upload"
    return 0
}

# Upload all images in the directory
upload_all_images() {
    local counter=0
    local successful=0
    local failed=0
    local failed_files=""
    
    info "Starting batch upload process..."
    
    # Process each image file
    for IMAGE_PATH in "$IMAGES_DIR"/*."$FILE_EXTENSION"; do
        # Skip if not a file
        if [ ! -f "$IMAGE_PATH" ]; then
            continue
        fi
        
        counter=$((counter + 1))
        FILENAME=$(basename "$IMAGE_PATH")
        FILE_ID="${FILENAME%.*}"  # Use filename without extension as file_id
        
        echo
        info "[$counter/$IMAGE_COUNT] Processing $FILENAME"
        echo -e "-----------------------------------"
        
        # Run the upload script with parameters
        if "$UPLOAD_SCRIPT" --image "$IMAGE_PATH" --file-id "$FILE_ID" --url "$API_URL" --platform "$PLATFORM"; then
            successful=$((successful + 1))
            success "Successfully uploaded $FILENAME"
        else
            failed=$((failed + 1))
            failed_files="$failed_files\n- $FILENAME"
            warning "Failed to upload $FILENAME"
        fi
        
        echo -e "-----------------------------------"
        
        # Add a delay between uploads to avoid overwhelming the API
        if [ $counter -lt $IMAGE_COUNT ] && [ $DELAY_SECONDS -gt 0 ]; then
            info "Waiting $DELAY_SECONDS second(s) before next upload..."
            sleep $DELAY_SECONDS
        fi
    done
    
    echo
    success "Batch upload completed: $successful/$IMAGE_COUNT images uploaded successfully"
    
    # Report failures if any
    if [ $failed -gt 0 ]; then
        warning "$failed files failed to upload:$failed_files"
    fi
}

#==============================================================================
# Main script
#==============================================================================

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir|-d)
            IMAGES_DIR="$2"
            shift 2
            ;;
        --ext|-e)
            FILE_EXTENSION="$2"
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
        --script|-s)
            UPLOAD_SCRIPT="$2"
            shift 2
            ;;
        --delay)
            DELAY_SECONDS="$2"
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

# Main execution flow
echo -e "${YELLOW}=== Batch Bot Media Upload Utility ===${NC}"
echo -e "Images directory: ${BLUE}$IMAGES_DIR${NC}"
echo -e "File extension: ${BLUE}$FILE_EXTENSION${NC}"
echo -e "Platform: ${BLUE}$PLATFORM${NC}"
echo -e "API URL: ${BLUE}$API_URL${NC}"
echo -e "Upload script: ${BLUE}$UPLOAD_SCRIPT${NC}"
echo -e "Delay between uploads: ${BLUE}$DELAY_SECONDS second(s)${NC}"

check_prerequisites
upload_all_images

echo -e "${GREEN}=== Batch upload process complete ===${NC}"