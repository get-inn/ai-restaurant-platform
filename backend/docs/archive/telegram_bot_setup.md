# Telegram Bot Setup Guide

This document provides instructions for setting up and integrating Telegram bots with the Restaurant Platform backend.

## Prerequisites

- A Telegram account
- The BotFather Telegram bot (to create new bots)
- A running instance of the Restaurant Platform backend
- For webhook setup: A publicly accessible server or ngrok for local development

## Creating a New Telegram Bot

1. Open Telegram and search for "BotFather"
2. Start a chat with BotFather and send the command `/newbot`
3. Follow the prompts to choose a name and username for your bot
4. BotFather will provide you with a token for your bot - save this token securely

## Adding Bot to the Platform

1. Navigate to the Bot Management section of the administration panel
2. Click "Add New Bot" and fill in the required details:
   - Name: A descriptive name for your bot
   - Description: Optional information about the bot's purpose
3. Under Platform Credentials, select "Telegram" and enter the token provided by BotFather
4. Click "Save" to create the bot instance

## Webhook Setup

For the bot to receive messages from Telegram, you need to set up a webhook:

### Production Environment

In production, the webhook URL should follow this pattern:
```
https://<your-domain>/v1/api/webhook/telegram/<bot-id>
```

Where:
- `<your-domain>` is your production server domain
- `<bot-id>` is the UUID of your bot instance in the platform

### Local Development with ngrok

For local development, you can use ngrok to expose your local server:

1. Install ngrok if you haven't already
2. Start your local API server
3. Start ngrok by running:
   ```
   ngrok http 8000
   ```
4. Use the provided HTTPS URL as your webhook base, resulting in:
   ```
   https://<ngrok-subdomain>.ngrok-free.app/v1/api/webhook/telegram/<bot-id>
   ```

### Setting the Webhook URL

You can set the webhook URL using the platform's test script:

```bash
python scripts/test_telegram_adapter.py --token YOUR_BOT_TOKEN --chat-id YOUR_CHAT_ID --webhook-url https://your-domain.com/v1/api/webhook/telegram/your-bot-id --set-webhook
```

Alternatively, you can set it directly via Telegram's API:

```bash
curl -F "url=https://your-domain.com/v1/api/webhook/telegram/your-bot-id" https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

### Verifying Webhook Setup

To check if your webhook is correctly configured:

```bash
python scripts/test_telegram_adapter.py --token YOUR_BOT_TOKEN --chat-id YOUR_CHAT_ID --get-webhook-info
```

## Testing the Bot

After setting up the bot and webhook, you can test it:

1. Find your bot on Telegram by its username
2. Start a conversation with the bot
3. The bot should respond according to the configured scenario

## Troubleshooting

### Common Issues

1. **404 Not Found errors**:
   - Ensure the webhook URL is correctly formatted with the `/v1/api/webhook/telegram/` prefix
   - Verify that the bot ID in the URL is correct

2. **Webhook validation errors**:
   - Ensure you're using HTTPS (not HTTP) for the webhook URL
   - Check that your server is accessible from the internet

3. **Authentication errors**:
   - Verify that the bot token is correctly set in the platform credentials

4. **Message not being processed**:
   - Check the platform logs for errors
   - Ensure the bot's scenario is properly configured and active

### Getting Webhook Information

To debug webhook issues, you can retrieve the current webhook information:

```bash
python scripts/test_telegram_adapter.py --token YOUR_BOT_TOKEN --chat-id YOUR_CHAT_ID --get-webhook-info
```

This will show the current webhook URL, any pending updates, and any errors encountered.

## Advanced Configuration

### Bot Scenario Setup

Refer to the [Bot Management Architecture](bot_management_architecture.md) document for details on creating and managing bot scenarios.

### Media File Handling

The platform supports sending and receiving images, documents, and other media files through the Telegram API. Media files are stored in the platform's storage system and can be referenced in scenarios.

### Bot Commands

You can set up bot commands via BotFather using the `/setcommands` command. Common commands to include:

- `/start` - Begin or restart the conversation
- `/help` - Show help information
- `/cancel` - Cancel the current operation

## Security Considerations

- Store bot tokens securely and never commit them to version control
- Use HTTPS for all webhook URLs
- Consider implementing additional validation for webhook requests
- Regularly rotate bot tokens if high security is required

## API Reference

For more details on the available API endpoints for bot management, refer to the [API Documentation](http://localhost:8000/docs) when running the backend locally.