# Bot Management System

This module provides a comprehensive system for managing conversational bots across multiple messaging platforms according to the architecture specified in `bots/bot_management_architecture.md`.

## Components

### Core Components

1. **Dialog Manager**
   - Manages conversation flow and coordinates between components
   - Processes incoming messages and generates appropriate responses
   - Routes messages through platform adapters
   - Handles command processing

2. **Scenario Processor**
   - Evaluates dialog scenario steps
   - Processes user inputs against scenario definitions
   - Determines the next step in a conversation flow
   - Resolves conditional logic in scenarios
   - Validates user input against scenario rules

3. **State Repository**
   - Manages persistence of dialog state
   - Provides access to dialog history
   - Synchronizes state across different components
   - Optimizes state access with caching

4. **Conversation Logger**
   - Provides detailed, structured logs for debugging and monitoring
   - Supports context-aware logging across conversation steps
   - Handles sensitive data redaction automatically
   - Works in both development and production environments

### Platform Integration

1. **Platform Adapters**
   - Implement the `PlatformAdapter` interface for different messaging platforms
   - Currently supported platforms:
     - Telegram

2. **Webhook Controllers**
   - Handle incoming webhook requests from messaging platforms
   - Route updates to the Dialog Manager

## Database Schema

The system uses the following database models:

1. **BotInstance**
   - Represents a bot instance in the system
   - Connected to an account
   - Can have multiple platform credentials

2. **BotPlatformCredential**
   - Platform-specific credentials for a bot
   - Stored securely with access control

3. **BotScenario**
   - Defines the conversation flow for a bot
   - Contains step definitions, conditions, and messages

4. **BotDialogState**
   - Represents the current state of a conversation
   - Tracks current step and collected data

5. **BotDialogHistory**
   - Records the history of messages in a conversation
   - Used for analytics and debugging

## Usage

### Initialization

```python
from sqlalchemy.ext.asyncio import AsyncSession
from src.bot_manager import DialogManager
from src.integrations.platforms import get_platform_adapter

# Create a dialog manager with a database session
dialog_manager = DialogManager(db_session)

# Register platform adapters
telegram_adapter = get_platform_adapter("telegram")
await telegram_adapter.initialize({"token": "YOUR_TELEGRAM_TOKEN"})
await dialog_manager.register_platform_adapter("telegram", telegram_adapter)
```

### Processing Messages

```python
# Process an incoming message
response = await dialog_manager.process_incoming_message(
    bot_id=bot_id,
    platform="telegram",
    platform_chat_id=chat_id,
    update_data=update_data
)
```

### Sending Messages

```python
# Send a text message
success = await dialog_manager.send_message(
    bot_id=bot_id,
    platform="telegram",
    platform_chat_id=chat_id,
    message="Hello, world!"
)

# Send a message with buttons
success = await dialog_manager.send_message(
    bot_id=bot_id,
    platform="telegram",
    platform_chat_id=chat_id,
    message="Please select an option:",
    buttons=[
        {"text": "Option 1", "value": "opt1"},
        {"text": "Option 2", "value": "opt2"}
    ]
)
```

## Conversation Logging

The conversation logging system provides detailed, structured logs for bot conversations to facilitate debugging and monitoring in both development and production environments.

### Features

- **Structured JSON Logs**: Easily parseable logs for integration with log aggregators
- **Context-Aware Logging**: Maintains conversation context across log entries
- **Docker-Friendly**: Optimized for containerized environments
- **Multiple Log Types**: Categories for incoming messages, outgoing messages, state changes, and more
- **Sensitive Data Protection**: Automatic redaction of sensitive information
- **Thread-Local Storage**: For maintaining context in asynchronous operations

### Configuration

The logging system can be configured through environment variables:

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
./src/scripts/bots/setup_logging.sh
```

This creates necessary directories and an environment file you can source:

```bash
source .env.logging
```

### Logging Usage

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

### Log Event Types

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

### Viewing Logs

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

### Log Filtering Options

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

## Scenario Format

Scenarios are defined in JSON format with the following structure:

```json
{
  "name": "Bot Name",
  "version": "1.0",
  "start_step": "welcome",
  "steps": {
    "welcome": {
      "type": "message",
      "message": {
        "text": "Welcome to our bot!"
      },
      "next_step": "ask_name"
    },
    "ask_name": {
      "type": "message",
      "message": {
        "text": "What's your name?"
      },
      "expected_input": {
        "type": "text",
        "variable": "name"
      },
      "next_step": "greet_with_name"
    },
    "greet_with_name": {
      "type": "message",
      "message": {
        "text": "Nice to meet you, {{name}}!"
      },
      "buttons": [
        {"text": "Tell me more", "value": "more_info"},
        {"text": "Goodbye", "value": "end"}
      ],
      "expected_input": {
        "type": "button",
        "variable": "choice"
      },
      "next_step": {
        "type": "conditional",
        "conditions": [
          {
            "if": "choice == more_info",
            "then": "provide_info"
          },
          {
            "if": "choice == end",
            "then": "goodbye"
          }
        ]
      }
    }
  }
}
```

## Further Development

### 1. Media File Handling
- Implement media file handling utilities for image and video content
- Add support for file downloads and uploads

### 2. Additional Platform Support
- WhatsApp adapter implementation
- Facebook Messenger adapter implementation
- Web chat adapter implementation

### 3. Advanced Features
- LLM integration for dynamic responses
- Analytics dashboards for conversation metrics
- A/B testing of different conversation flows