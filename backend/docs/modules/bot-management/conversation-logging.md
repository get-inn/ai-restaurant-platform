# Bot Conversation Logging

This document describes the bot conversation logging system in the GET INN Restaurant Platform.

## Overview

The platform includes a detailed logging system for bot conversations designed to work in both development and production environments. It provides structured logs that help developers debug and trace user interactions with bots across various messaging platforms.

## Key Features

- **Structured JSON Logs**: Easily parseable logs for integration with log aggregators
- **Context-Aware Logging**: Maintains conversation context across log entries
- **Docker-Friendly**: Optimized for containerized environments
- **Multiple Log Types**: Categories for incoming messages, outgoing messages, state changes, and more
- **Sensitive Data Protection**: Automatic redaction of sensitive information
- **Thread-Local Storage**: For maintaining context in asynchronous operations

## Configuration

### Environment Variables

The following environment variables control the logging behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| BOT_LOG_LEVEL | Log level (DEBUG, INFO, WARNING, ERROR) | INFO |
| BOT_LOG_FORMAT | Output format (json, text) | json |
| BOT_FILE_LOGGING | Enable file logging (true, false) | false |
| BOT_LOG_DIR | Directory for log files | /app/logs in Docker, logs in local development |

### Setup

For local development, run the setup script:

```bash
cd backend
./scripts/bots/setup_logging.sh
```

This creates necessary directories and an environment file you can source:

```bash
source .env.logging
```

## Usage

### Basic Usage

Import and use the logger in your bot-related components:

```python
from src.bot_manager.conversation_logger import get_logger, LogEventType

# Create a logger instance
logger = get_logger(bot_id="123", platform="telegram")

# Log incoming messages
logger.incoming_message("Hello bot!", {"user_id": "user123"})

# Log outgoing messages
logger.outgoing_message("Hello user!", {"buttons": ["Option 1", "Option 2"]})

# Log state changes
logger.state_change("welcome_step", {"previous_step": "initial"})

# Log general events with different levels
logger.debug(LogEventType.PROCESSING, "Processing user input")
logger.info(LogEventType.DIALOG, "Dialog flow completed")
logger.warning(LogEventType.ERROR, "Invalid input received")
logger.error(LogEventType.ERROR, "Failed to process message", exc_info=exception)
```

### Context Management

The logger maintains context across log entries using thread-local storage:

```python
# Set or update context values
logger.set_context(
    bot_id="123",
    platform="telegram",
    platform_chat_id="chat456",
    dialog_id="dialog789"
)

# Context will be included in all subsequent logs from this thread
logger.info(LogEventType.PROCESSING, "Processing with context")

# Clear specific context values
logger.clear_context("platform_chat_id")

# Clear all context
logger.clear_context()
```

## Log Event Types

Use the appropriate `LogEventType` for different events:

| Event Type | Description | Example Use |
|------------|-------------|-------------|
| INCOMING | Incoming messages from users | `logger.incoming_message("Hello", {})` |
| OUTGOING | Outgoing messages to users | `logger.outgoing_message("Hi there", {})` |
| PROCESSING | General processing steps | `logger.info(LogEventType.PROCESSING, "Processing user input")` |
| STATE_CHANGE | Dialog state transitions | `logger.state_change("main_menu", {})` |
| ERROR | Error conditions | `logger.error(LogEventType.ERROR, "Failed to process")` |
| WEBHOOK | Webhook events from platforms | `logger.info(LogEventType.WEBHOOK, "Received webhook")` |
| VARIABLE | Variable updates | `logger.debug(LogEventType.VARIABLE, "Updated user name")` |
| CONDITION | Condition evaluation results | `logger.debug(LogEventType.CONDITION, "Evaluated condition")` |
| ADAPTER | Platform adapter operations | `logger.debug(LogEventType.ADAPTER, "Sending to platform")` |

## Log Structure

### JSON Format

```json
{
  "timestamp": "2023-07-13T10:15:30.123Z",
  "level": "INFO",
  "event_type": "INCOMING",
  "message": "Received message from user",
  "context": {
    "bot_id": "11111111-1111-1111-1111-111111111111",
    "platform": "telegram",
    "platform_chat_id": "12345678",
    "dialog_id": "22222222-2222-2222-2222-222222222222",
    "user_id": "user123"
  },
  "data": {
    "message_id": "msg123",
    "text": "Hello bot!",
    "timestamp": "2023-07-13T10:15:29.987Z"
  }
}
```

### Text Format

```
2023-07-13 10:15:30.123 | INFO | INCOMING | bot_id=11111111-1111-1111-1111-111111111111 platform=telegram | Received message from user | text="Hello bot!" message_id="msg123"
```

## Viewing Logs

### Command Line Utility

Use the provided utility script to filter and view logs:

```bash
# View logs for a specific bot
python -m scripts.bots.utils.view_bot_logs --bot-id BOT_ID

# Filter by platform and chat ID
python -m scripts.bots.utils.view_bot_logs --platform telegram --chat-id CHAT_ID

# Show raw JSON logs
python -m scripts.bots.utils.view_bot_logs --raw

# Get help with additional options
python -m scripts.bots.utils.view_bot_logs --help
```

### Common Filtering Options

| Option | Description | Example |
|--------|-------------|---------|
| --bot-id | Filter by bot ID | `--bot-id 11111111-1111-1111-1111-111111111111` |
| --platform | Filter by platform | `--platform telegram` |
| --chat-id | Filter by chat ID | `--chat-id 12345678` |
| --dialog-id | Filter by dialog ID | `--dialog-id 22222222-2222-2222-2222-222222222222` |
| --level | Filter by log level | `--level ERROR` |
| --event-type | Filter by event type | `--event-type INCOMING` |
| --from-date | Filter from date | `--from-date 2023-07-13` |
| --to-date | Filter to date | `--to-date 2023-07-14` |
| --contains | Filter by text content | `--contains "error"` |
| --tail | Show only the last N logs | `--tail 50` |

## Implementation Details

### Logger Architecture

The conversation logger is implemented with these components:

1. **ConversationLogger**: Main logger class with methods for logging different event types
2. **LoggingContext**: Thread-local storage for maintaining context between log calls
3. **LogFormatter**: Formats log records based on configuration
4. **LogEventType**: Enum defining different types of log events
5. **get_logger**: Factory function to create and configure logger instances

### File Rotation

When file logging is enabled, logs are rotated with these settings:

- Maximum file size: 10MB
- Backup count: 5 files
- Encoding: UTF-8
- File naming: `bot_conversations_{timestamp}.log`

## Best Practices

### When to Log

1. **Always log**:
   - All incoming user messages
   - All outgoing bot responses
   - State changes in the dialog flow
   - Errors and exceptions

2. **Consider logging**:
   - Variable updates that affect flow
   - Condition evaluations for complex logic
   - External service interactions
   - Performance metrics for long-running operations

### Log Levels

- **DEBUG**: Detailed information for development and debugging
- **INFO**: General information about normal operation
- **WARNING**: Potential issues that don't prevent operation
- **ERROR**: Errors that prevented an operation from completing

### Sensitive Data

Avoid logging sensitive information:

```python
# DON'T: Log sensitive data directly
logger.info(LogEventType.PROCESSING, f"Processing payment with card {card_number}")

# DO: Mask sensitive data
masked_card = f"****{card_number[-4:]}"
logger.info(LogEventType.PROCESSING, f"Processing payment with card {masked_card}")
```

## Troubleshooting

### Common Issues

1. **Missing Logs**
   - Check that BOT_LOG_LEVEL is not set too high
   - Verify BOT_FILE_LOGGING is enabled if checking files
   - Ensure BOT_LOG_DIR exists and is writable

2. **Context Not Appearing in Logs**
   - Ensure context is set before logging
   - Check for context clearing in the code
   - Be aware of thread boundaries (context is thread-local)

3. **Performance Issues**
   - Use appropriate log levels to reduce volume
   - Consider disabling file logging in development if not needed
   - Use structured logging to make filtering more efficient

### Debugging the Logger

If you suspect issues with the logging system itself:

```python
# Set Python's root logger to debug
import logging
logging.basicConfig(level=logging.DEBUG)

# Check if logs are being generated
from src.bot_manager.conversation_logger import get_logger
logger = get_logger(bot_id="debug", platform="debug")
logger.info(LogEventType.PROCESSING, "Test log entry")
```

## Integration with Other Systems

### Log Aggregation

The JSON format makes it easy to integrate with log aggregation systems:

- **ELK Stack**: Use Filebeat to ship logs to Elasticsearch
- **Graylog**: Configure GELF input to process JSON logs
- **CloudWatch**: Use CloudWatch agent to stream logs
- **Datadog**: Configure the Datadog agent to collect logs