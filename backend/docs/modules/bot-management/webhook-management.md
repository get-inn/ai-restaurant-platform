# Telegram Webhook Management

This document outlines the webhook management system for Telegram bots in the GET INN Restaurant Platform.

## Overview

The webhook management system automatically configures and maintains Telegram webhooks based on the environment (local development or production). It provides API endpoints for managing webhooks and includes a background worker to periodically check and refresh webhook configurations.

## Key Features

1. **Environment-aware configuration**:
   - Local development: Uses ngrok for temporary public URLs
   - Production: Uses configured domain name

2. **API endpoints for webhook management**:
   - Set webhook
   - Get webhook status
   - Delete webhook

3. **Background worker**:
   - Periodic checks every 5 minutes
   - Auto-refresh of broken or misconfigured webhooks

## API Endpoints

### Set Webhook

```
POST /v1/api/webhooks/telegram/{bot_id}/webhook/set
```

Sets or updates a webhook for the specified bot.

**Request Body**:
```json
{
  "drop_pending_updates": false,
  "secret_token": "optional-secret-token",
  "max_connections": 40,
  "allowed_updates": ["message", "callback_query"]
}
```

**Response**:
```json
{
  "url": "https://example.com/v1/api/webhooks/telegram/11111111-1111-1111-1111-111111111111",
  "has_custom_certificate": false,
  "pending_update_count": 0,
  "ip_address": "123.45.67.89",
  "last_error_date": null,
  "last_error_message": null,
  "max_connections": 40,
  "allowed_updates": ["message", "callback_query"]
}
```

### Get Webhook Status

```
GET /v1/api/webhooks/telegram/{bot_id}/webhook/status
```

Retrieves current webhook status for the specified bot.

**Response**:
```json
{
  "url": "https://example.com/v1/api/webhooks/telegram/11111111-1111-1111-1111-111111111111",
  "has_custom_certificate": false,
  "pending_update_count": 0,
  "ip_address": "123.45.67.89",
  "last_error_date": null,
  "last_error_message": null,
  "max_connections": 40,
  "allowed_updates": ["message", "callback_query"]
}
```

### Delete Webhook

```
POST /v1/api/webhooks/telegram/{bot_id}/webhook/delete
```

Deletes the webhook for the specified bot.

**Response**:
```json
{
  "success": true
}
```

## Database Schema

The webhook-related fields are stored in the `bot_platform_credential` model:

```python
class BotPlatformCredential(Base):
    __tablename__ = "bot_platform_credential"
    
    # Existing fields...
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    platform = Column(String, nullable=False)  # 'telegram', 'whatsapp', 'viber', etc.
    credentials = Column(JSONB, nullable=False)  # tokens and platform-specific settings
    
    # Webhook-related fields
    webhook_url = Column(String, nullable=True)
    webhook_last_checked = Column(DateTime, nullable=True)
    webhook_auto_refresh = Column(Boolean, nullable=False, default=True)
```

## Environment Detection

The webhook service automatically detects the environment and configures appropriate webhook URLs:

1. **Local Development**:
   - Uses ngrok to create temporary public tunnel
   - Webhook URL format: `https://<ngrok-subdomain>.ngrok.io/v1/api/webhooks/telegram/{bot_id}`

2. **Production**:
   - Uses configured domain from environment variables
   - Webhook URL format: `https://<domain>/v1/api/webhooks/telegram/{bot_id}`

## Configuration

The webhook management system is configured through environment variables:

```
# Webhook settings
USE_NGROK=false                             # Set to 'true' to use ngrok in local environment
NGROK_AUTHTOKEN=your-ngrok-auth-token       # Optional: Your ngrok authentication token
NGROK_PORT=8000                             # Port to expose through ngrok
WEBHOOK_DOMAIN=https://api.example.com      # Production webhook domain
```

## Background Worker

A Celery task runs periodically to check and maintain webhook configurations:

- Runs every 5 minutes
- Checks webhook status for all active bots
- Refreshes webhooks with issues automatically
- Logs errors and successes

The worker automatically refreshes a webhook if:
- The webhook URL is missing or invalid
- There have been recent errors with the webhook
- There are too many pending updates

## Local Development with ngrok

For local development, the webhook service can automatically create and manage ngrok tunnels:

1. Install the required packages:
   ```bash
   pip install pyngrok
   ```

2. Set environment variables:
   ```
   USE_NGROK=true
   NGROK_AUTHTOKEN=your-ngrok-auth-token  # Optional but recommended
   NGROK_PORT=8000
   ```

3. Start the development server
   ```bash
   ./backend/start-dev.sh --local-api
   ```

4. The webhook service will automatically create and use an ngrok tunnel

## Troubleshooting

### Common Issues

1. **Webhook Setup Failures**:
   - Verify your Telegram bot token is valid
   - Ensure the webhook URL is publicly accessible
   - Check network connectivity to Telegram API

2. **Local Development Issues**:
   - Verify ngrok is running and accessible
   - Check that USE_NGROK is set to 'true'
   - Ensure the correct port is configured

3. **Production Issues**:
   - Confirm WEBHOOK_DOMAIN is correctly set
   - Verify DNS resolution for your domain
   - Check firewall rules allow incoming connections

### Debugging Webhook Issues

To debug webhook issues:

1. Check webhook status:
   ```
   GET /v1/api/webhooks/telegram/{bot_id}/webhook/status
   ```

2. Examine logs for webhook-related errors:
   ```bash
   ./backend/start-dev.sh --logs
   ```

3. If using ngrok, check the ngrok dashboard for request details

## Security Considerations

- Use HTTPS for all webhook URLs
- Consider using a secret token for webhook validation
- Implement rate limiting for webhook endpoints
- Monitor for unusual webhook traffic patterns