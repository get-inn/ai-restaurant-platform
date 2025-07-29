#!/bin/bash

# setup_logging.sh
# Script to setup the logging environment for bot conversations

# Function to print colored output
print_colored() {
  local color=$1
  local message=$2
  
  case $color in
    "green") echo -e "\033[0;32m$message\033[0m" ;;
    "yellow") echo -e "\033[0;33m$message\033[0m" ;;
    "red") echo -e "\033[0;31m$message\033[0m" ;;
    "blue") echo -e "\033[0;34m$message\033[0m" ;;
    *) echo "$message" ;;
  esac
}

# Print header
print_colored "blue" "=========================================="
print_colored "blue" "Bot Conversation Logging Setup"
print_colored "blue" "=========================================="
echo

# Determine the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
echo "Project root: $PROJECT_ROOT"

# Create logs directory if it doesn't exist
LOGS_DIR="$PROJECT_ROOT/logs"
if [ ! -d "$LOGS_DIR" ]; then
  print_colored "yellow" "Creating logs directory at $LOGS_DIR"
  mkdir -p "$LOGS_DIR"
  
  if [ $? -eq 0 ]; then
    print_colored "green" "✓ Logs directory created successfully"
  else
    print_colored "red" "✗ Failed to create logs directory"
    exit 1
  fi
else
  print_colored "green" "✓ Logs directory already exists"
fi

# Check permissions on logs directory
if [ ! -w "$LOGS_DIR" ]; then
  print_colored "yellow" "Setting write permissions on logs directory"
  chmod u+w "$LOGS_DIR"
  
  if [ $? -eq 0 ]; then
    print_colored "green" "✓ Write permissions set successfully"
  else
    print_colored "red" "✗ Failed to set write permissions"
    exit 1
  fi
else
  print_colored "green" "✓ Logs directory has write permissions"
fi

# Create .env.logging file with configuration
ENV_FILE="$PROJECT_ROOT/.env.logging"
print_colored "yellow" "Creating environment file at $ENV_FILE"

cat > "$ENV_FILE" << EOF
# Bot conversation logging configuration
# Generated on $(date)

# Log level: DEBUG, INFO, WARNING, ERROR
BOT_LOG_LEVEL=DEBUG

# Log format: json or text
BOT_LOG_FORMAT=json

# Enable file logging
BOT_FILE_LOGGING=true

# Log directory
BOT_LOG_DIR=$LOGS_DIR
EOF

if [ $? -eq 0 ]; then
  print_colored "green" "✓ Environment file created successfully"
else
  print_colored "red" "✗ Failed to create environment file"
  exit 1
fi

# Create a sample log file
SAMPLE_LOG_FILE="$LOGS_DIR/bot_conversations_$(date +%Y%m%d).log"
if [ ! -f "$SAMPLE_LOG_FILE" ]; then
  print_colored "yellow" "Creating sample log file at $SAMPLE_LOG_FILE"
  
  # Generate some sample log entries
  cat > "$SAMPLE_LOG_FILE" << EOF
{"timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")", "level": "INFO", "event_type": "INCOMING", "message": "Received: Hello bot!", "bot_id": "11111111-1111-1111-1111-111111111111", "platform": "telegram", "platform_chat_id": "12345678", "dialog_id": "22222222-2222-2222-2222-222222222222", "user_id": "user123", "message_id": "msg123"}
{"timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.100Z")", "level": "INFO", "event_type": "PROCESSING", "message": "Processing user message", "bot_id": "11111111-1111-1111-1111-111111111111", "platform": "telegram", "platform_chat_id": "12345678", "dialog_id": "22222222-2222-2222-2222-222222222222", "user_id": "user123"}
{"timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.200Z")", "level": "INFO", "event_type": "STATE", "message": "Dialog state changed to step: welcome_step", "bot_id": "11111111-1111-1111-1111-111111111111", "platform": "telegram", "platform_chat_id": "12345678", "dialog_id": "22222222-2222-2222-2222-222222222222", "user_id": "user123", "previous_step": "initial"}
{"timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.300Z")", "level": "INFO", "event_type": "OUTGOING", "message": "Sent: Hello user! How can I help you today?", "bot_id": "11111111-1111-1111-1111-111111111111", "platform": "telegram", "platform_chat_id": "12345678", "dialog_id": "22222222-2222-2222-2222-222222222222", "user_id": "user123", "buttons": ["Option 1", "Option 2"]}
{"timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.400Z")", "level": "WARNING", "event_type": "ERROR", "message": "This is a simulated warning", "bot_id": "11111111-1111-1111-1111-111111111111", "platform": "telegram", "platform_chat_id": "12345678", "dialog_id": "22222222-2222-2222-2222-222222222222", "user_id": "user123"}
{"timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.500Z")", "level": "ERROR", "event_type": "ERROR", "message": "Failed to process message", "bot_id": "11111111-1111-1111-1111-111111111111", "platform": "telegram", "platform_chat_id": "12345678", "dialog_id": "22222222-2222-2222-2222-222222222222", "user_id": "user123", "exception_type": "ValueError", "exception_message": "Invalid input", "traceback": "Traceback (most recent call last):\\n  File \\"<stdin>\\", line 1, in <module>\\nValueError: Invalid input\\n"}
EOF

  if [ $? -eq 0 ]; then
    print_colored "green" "✓ Sample log file created successfully"
  else
    print_colored "red" "✗ Failed to create sample log file"
  fi
fi

# Display summary and usage instructions
echo
print_colored "blue" "=========================================="
print_colored "green" "✓ Bot conversation logging setup complete!"
print_colored "blue" "=========================================="
echo
echo "To activate the logging configuration:"
echo "  source $ENV_FILE"
echo
echo "To view the logs:"
echo "  python -m scripts.bots.utils.view_bot_logs"
echo
echo "To view logs for a specific bot:"
echo "  python -m scripts.bots.utils.view_bot_logs --bot-id 11111111-1111-1111-1111-111111111111"
echo
echo "For more options:"
echo "  python -m scripts.bots.utils.view_bot_logs --help"
echo

exit 0