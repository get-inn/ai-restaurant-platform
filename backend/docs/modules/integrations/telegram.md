# Telegram Integration

This document provides comprehensive information about the Telegram integration in the GET INN Restaurant Platform.

## Overview

The Telegram integration allows the platform to create and manage bots on the Telegram messaging platform. This integration enables interactive conversations with users through Telegram's messaging interface, supporting features like text messages, media sharing, buttons, and more.

## Architecture

The integration follows a webhook-based architecture:

1. **Webhook Endpoint**: Receives real-time updates from Telegram
2. **Platform Adapter**: Translates between Telegram's API and our internal bot system
3. **Bot Management System**: Processes messages and manages conversations
4. **Webhook Management**: Configures and maintains webhooks

### System Flow

```
┌────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Telegram  │◄──────┤  Webhook        │◄──────┤  Platform       │
│  API       │       │  Endpoint       │       │  Adapter        │
└─────┬──────┘       └────────┬────────┘       └────────┬────────┘
      │                       │                         │
      │                       │                         │
      │               ┌───────▼─────────────────────────▼──────┐
      └──────────────►│                                        │
                      │         Bot Management System          │
                      │                                        │
                      └──────────────────┬───────────────────┬─┘
                                         │                   │
                              ┌──────────▼───────┐ ┌─────────▼──────────┐
                              │ Dialog Manager   │ │ Conversation Logger │
                              └──────────────────┘ └────────────────────┘
```

## Setup Process

### Creating a Telegram Bot

To integrate with Telegram, you need to create a bot through BotFather:

1. Open Telegram and search for "BotFather"
2. Start a chat with BotFather
3. Send the command `/newbot` and follow the instructions
4. Note the bot token provided (format: `123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`)

### Adding the Bot to the Platform

1. Create a bot instance in the platform:
   ```
   POST /v1/api/accounts/{account_id}/bots
   {
     "name": "Restaurant Booking Bot",
     "description": "Bot for booking tables at our restaurant"
   }
   ```

2. Add Telegram credentials to the bot:
   ```
   POST /v1/api/bots/{bot_id}/platforms
   {
     "platform": "telegram",
     "credentials": {
       "token": "123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ"
     },
     "is_active": true
   }
   ```

3. Set up the webhook:
   ```
   POST /v1/api/webhooks/telegram/{bot_id}/webhook/set
   {
     "drop_pending_updates": true,
     "allowed_updates": ["message", "callback_query"]
   }
   ```

## Telegram API Integration

### Authentication

Telegram uses a token-based authentication system. All API requests include the bot token:

```
https://api.telegram.org/bot{token}/METHOD_NAME
```

### Webhook Registration

Webhooks are registered with the Telegram API:

```
https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}
```

The webhook URL follows this format:
```
https://{domain}/v1/api/webhooks/telegram/{bot_id}
```

### Webhook Data Format

Telegram sends webhook updates in JSON format:

```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 123,
    "from": {
      "id": 12345678,
      "first_name": "User",
      "username": "username"
    },
    "chat": {
      "id": 12345678,
      "first_name": "User",
      "username": "username",
      "type": "private"
    },
    "date": 1625097601,
    "text": "Hello bot!"
  }
}
```

## Platform Adapter

The platform adapter translates between Telegram's API format and our internal bot system.

### Key Functions

#### Receiving Messages

The adapter converts Telegram messages to our internal format:

```python
def convert_telegram_update(update: Dict[str, Any]) -> UserMessage:
    """Convert Telegram update to internal message format."""
    if "message" in update:
        message = update["message"]
        return UserMessage(
            platform="telegram",
            platform_user_id=str(message["from"]["id"]),
            platform_chat_id=str(message["chat"]["id"]),
            message_type="text",
            text=message.get("text", ""),
            media=_extract_media(message),
            metadata={
                "message_id": message["message_id"],
                "date": message["date"],
                "username": message["from"].get("username")
            }
        )
    elif "callback_query" in update:
        # Handle button clicks
        callback = update["callback_query"]
        return UserMessage(
            platform="telegram",
            platform_user_id=str(callback["from"]["id"]),
            platform_chat_id=str(callback["message"]["chat"]["id"]),
            message_type="button",
            text=callback["data"],
            metadata={
                "callback_query_id": callback["id"],
                "message_id": callback["message"]["message_id"]
            }
        )
    # Handle other update types...
```

#### Sending Messages

The adapter sends messages to Telegram in the appropriate format:

```python
async def send_message(self, chat_id: str, message: BotMessage) -> Dict[str, Any]:
    """Send a message to Telegram."""
    url = f"{self.api_base_url}/sendMessage"
    
    # Convert internal message format to Telegram format
    payload = {
        "chat_id": chat_id,
        "text": message.text,
        "parse_mode": "HTML"
    }
    
    # Add buttons if present
    if message.buttons:
        payload["reply_markup"] = {
            "inline_keyboard": self._format_buttons(message.buttons)
        }
    
    # Send the message
    response = await self.http_client.post(url, json=payload)
    return response.json()
```

## Supported Features

The Telegram integration supports these features:

### Message Types

| Type | Description | Support |
|------|-------------|---------|
| Text | Plain text messages | ✓ |
| Media | Images, videos, documents | ✓ |
| Location | Geographic coordinates | ✓ |
| Contact | Phone numbers | ✓ |

### Interactive Elements

| Element | Description | Support |
|---------|-------------|---------|
| Buttons | Inline keyboard buttons | ✓ |
| Quick Replies | One-time keyboard | ✓ |
| Web App | Mini web applications | ✓ |
| Polls | Multiple-choice polls | ✓ |

### Other Features

| Feature | Description | Support |
|---------|-------------|---------|
| File Upload | User file uploads | ✓ |
| Webhooks | Real-time updates | ✓ |
| Commands | /command format | ✓ |
| Message Threading | Reply to specific messages | ✓ |

## Webhook Management

### Environment-Aware Configuration

The platform automatically configures webhooks based on the environment:

- **Development**: Uses ngrok to create a public URL for local development
- **Production**: Uses the configured domain name

### API Endpoints

```
# Set webhook for a bot
POST /v1/api/webhooks/telegram/{bot_id}/webhook/set

# Get webhook status
GET /v1/api/webhooks/telegram/{bot_id}/webhook/status

# Delete webhook
POST /v1/api/webhooks/telegram/{bot_id}/webhook/delete
```

### Automatic Health Checks

A background worker checks webhook health every 5 minutes and refreshes if needed:

- Detects broken webhooks
- Handles URL changes during deployment
- Recovers from Telegram API issues

## Local Development

For local development, the platform can use ngrok to create temporary public URLs:

### Setup with ngrok

1. Install ngrok and the required packages:
   ```bash
   pip install pyngrok
   ```

2. Set environment variables:
   ```bash
   export USE_NGROK=true
   export NGROK_AUTHTOKEN=your_ngrok_auth_token  # Optional but recommended
   ```

3. Start the development server:
   ```bash
   ./backend/start-dev.sh --local-api
   ```

4. The webhook URL will be automatically created and registered

## Security Considerations

### Token Security

- Store bot tokens securely in the database with appropriate encryption
- Never expose tokens in logs, URLs, or client-side code
- Regularly audit token access

### Webhook Security

- Use HTTPS for all webhook URLs
- Consider setting a secret token for webhook validation
- Implement rate limiting to prevent abuse

### Message Validation

- Validate all incoming messages before processing
- Sanitize user input to prevent injection attacks
- Implement limits on message size and frequency

## Monitoring and Logging

### Conversation Logging

The platform includes detailed logging for bot conversations:

```bash
# View logs for a specific bot
python -m scripts.bots.utils.view_bot_logs --bot-id BOT_ID

# Filter by chat ID
python -m scripts.bots.utils.view_bot_logs --platform telegram --chat-id CHAT_ID
```

### Health Metrics

Monitor these metrics for Telegram integration health:

- Webhook response time
- Message processing latency
- Error rates by message type
- API rate limit usage

## Troubleshooting

### Common Issues

1. **Webhook Setup Failures**
   - Verify the bot token is valid
   - Ensure the webhook URL is publicly accessible
   - Check for HTTPS certificate issues

2. **Message Delivery Issues**
   - Confirm the bot is not blocked by the user
   - Check for API rate limiting
   - Verify the chat ID is correct

3. **Button Callback Issues**
   - Ensure callback data is less than 64 bytes
   - Check that the message is less than 48 hours old
   - Verify the inline keyboard format

### Debugging Webhook Issues

To debug webhook issues:

1. Check webhook status:
   ```
   GET /v1/api/webhooks/telegram/{bot_id}/webhook/status
   ```

2. Review the logs for webhook registration attempts:
   ```bash
   ./backend/start-dev.sh --logs
   ```

3. If using ngrok, check the ngrok dashboard for request details

## API Reference

### Telegram Bot API

Full documentation is available at: https://core.telegram.org/bots/api

Key endpoints used:

| Endpoint | Description |
|----------|-------------|
| `sendMessage` | Send text messages |
| `sendPhoto` | Send images |
| `sendDocument` | Send files |
| `sendLocation` | Send geographic coordinates |
| `answerCallbackQuery` | Respond to button clicks |
| `setWebhook` | Configure webhook |
| `getWebhookInfo` | Get webhook status |

## Future Enhancements

Planned enhancements for the Telegram integration:

1. **Telegram Bot API 6.0+ Features**: Support for forum topics, reactions, and other new features
2. **Media Group Support**: Improved handling of grouped media messages
3. **Enhanced Security**: Additional security measures for webhooks
4. **Performance Optimization**: Caching and rate limit management
5. **Rich Media**: Better support for animated stickers and video notes

## Related Documentation

- [Bot Management Overview](../bot-management/overview.md)
- [Bot Scenario Format](../bot-management/scenario-format.md)
- [Webhook Management](../bot-management/webhook-management.md)
- [Conversation Logging](../bot-management/conversation-logging.md)