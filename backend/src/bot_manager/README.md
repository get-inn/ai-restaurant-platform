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