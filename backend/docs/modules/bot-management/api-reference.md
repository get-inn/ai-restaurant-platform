# Bot Management API Reference

## Overview

The Bot Management API provides comprehensive endpoints for managing chat bots, scenarios, platform integrations, and conversation state. All endpoints require authentication and return JSON responses.

## Authentication

All API endpoints require authentication using the existing GET INN platform authentication system. Include the authentication token in the request headers:

```
Authorization: Bearer <your-token>
```

## Base URL

```
https://your-domain.com/v1/api
```

For local development:
```
http://localhost:8000/v1/api
```

## Bot Instance Management

### List Bots

Get all bots for an account.

```http
GET /accounts/{account_id}/bots
```

**Parameters:**
- `account_id` (UUID, path): Account identifier

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "account_id": "uuid",
      "name": "Bot Name",
      "description": "Bot description",
      "is_active": true,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

### Create Bot

Create a new bot instance.

```http
POST /accounts/{account_id}/bots
```

**Request Body:**
```json
{
  "name": "Bot Name",
  "description": "Optional bot description"
}
```

**Response:**
```json
{
  "id": "uuid",
  "account_id": "uuid",
  "name": "Bot Name",
  "description": "Optional bot description",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Get Bot

Get a specific bot by ID.

```http
GET /bots/{bot_id}
```

**Parameters:**
- `bot_id` (UUID, path): Bot identifier

**Response:**
```json
{
  "id": "uuid",
  "account_id": "uuid",
  "name": "Bot Name",
  "description": "Bot description",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Update Bot

Update an existing bot.

```http
PUT /bots/{bot_id}
```

**Request Body:**
```json
{
  "name": "Updated Bot Name",
  "description": "Updated description"
}
```

### Delete Bot

Delete a bot instance.

```http
DELETE /bots/{bot_id}
```

**Response:** `204 No Content`

### Activate/Deactivate Bot

```http
POST /bots/{bot_id}/activate
POST /bots/{bot_id}/deactivate
```

**Response:**
```json
{
  "id": "uuid",
  "is_active": true
}
```

## Platform Credentials

### List Platform Credentials

Get all platform credentials for a bot.

```http
GET /bots/{bot_id}/platforms
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "bot_id": "uuid",
      "platform": "telegram",
      "is_active": true,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

### Add Platform Credentials

Add credentials for a specific platform.

```http
POST /bots/{bot_id}/platforms
```

**Request Body:**
```json
{
  "platform": "telegram",
  "credentials": {
    "token": "bot_token_here"
  }
}
```

### Get Platform Credentials

Get credentials for a specific platform.

```http
GET /bots/{bot_id}/platforms/{platform}
```

**Parameters:**
- `platform` (string, path): Platform name (telegram, whatsapp, etc.)

### Update Platform Credentials

Update credentials for a platform.

```http
PUT /bots/{bot_id}/platforms/{platform}
```

**Request Body:**
```json
{
  "credentials": {
    "token": "updated_bot_token"
  }
}
```

### Delete Platform Credentials

Remove credentials for a platform.

```http
DELETE /bots/{bot_id}/platforms/{platform}
```

## Scenario Management

### List Scenarios

Get all scenarios for a bot.

```http
GET /bots/{bot_id}/scenarios
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "bot_id": "uuid",
      "name": "Onboarding Scenario",
      "description": "Staff onboarding flow",
      "version": "1.0",
      "is_active": true,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

### Create Scenario

Create a new scenario.

```http
POST /bots/{bot_id}/scenarios
```

**Request Body:**
```json
{
  "name": "Scenario Name",
  "description": "Scenario description",
  "version": "1.0",
  "scenario_data": {
    "version": "1.0",
    "steps": {
      "welcome": {
        "id": "welcome",
        "type": "message",
        "message": {
          "text": "Welcome message"
        },
        "next_step": "next_step"
      }
    }
  }
}
```

### Get Scenario

Get a specific scenario.

```http
GET /scenarios/{scenario_id}
```

**Response:**
```json
{
  "id": "uuid",
  "bot_id": "uuid",
  "name": "Scenario Name",
  "description": "Scenario description",
  "scenario_data": {
    "version": "1.0",
    "steps": {
      // scenario steps...
    }
  },
  "version": "1.0",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Update Scenario

Update an existing scenario.

```http
PUT /scenarios/{scenario_id}
```

### Delete Scenario

Delete a scenario.

```http
DELETE /scenarios/{scenario_id}
```

### Activate Scenario

Activate a scenario for use.

```http
POST /scenarios/{scenario_id}/activate
```

## Dialog Management

### List Dialogs

Get active dialogs for a bot.

```http
GET /bots/{bot_id}/dialogs
```

**Query Parameters:**
- `platform` (string, optional): Filter by platform
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 50)

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "bot_id": "uuid",
      "platform": "telegram",
      "platform_chat_id": "123456789",
      "current_step": "welcome",
      "collected_data": {},
      "last_interaction_at": "2023-01-01T00:00:00Z",
      "created_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

### Get Platform Dialogs

Get dialogs for a specific platform.

```http
GET /bots/{bot_id}/platforms/{platform}/dialogs
```

### Get Dialog

Get a specific dialog.

```http
GET /dialogs/{dialog_id}
```

**Response:**
```json
{
  "id": "uuid",
  "bot_id": "uuid",
  "platform": "telegram",
  "platform_chat_id": "123456789",
  "current_step": "welcome",
  "collected_data": {
    "first_name": "John",
    "last_name": "Doe"
  },
  "last_interaction_at": "2023-01-01T00:00:00Z",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Delete Dialog

Delete a dialog (end conversation).

```http
DELETE /dialogs/{dialog_id}
```

### Get Dialog History

Get conversation history for a dialog.

```http
GET /dialogs/{dialog_id}/history
```

**Query Parameters:**
- `page` (integer, optional): Page number
- `per_page` (integer, optional): Items per page
- `order` (string, optional): Sort order (asc, desc)

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "dialog_state_id": "uuid",
      "message_type": "user",
      "message_data": {
        "type": "text",
        "content": "Hello"
      },
      "timestamp": "2023-01-01T00:00:00Z"
    }
  ]
}
```

## Media Management

### List Media Files

Get all media files for a bot.

```http
GET /bots/{bot_id}/media
```

**Query Parameters:**
- `file_type` (string, optional): Filter by file type (image, video, audio, document)
- `page` (integer, optional): Page number
- `per_page` (integer, optional): Items per page

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "bot_id": "uuid",
      "file_type": "image",
      "file_name": "welcome.jpg",
      "storage_path": "/path/to/file",
      "platform_file_ids": {
        "telegram": "platform_file_id"
      },
      "created_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

### Upload Media File

Upload a new media file.

```http
POST /bots/{bot_id}/media
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Media file to upload
- `file_type`: Type of media (image, video, audio, document)
- `description` (optional): File description

**Response:**
```json
{
  "id": "uuid",
  "bot_id": "uuid",
  "file_type": "image",
  "file_name": "uploaded_file.jpg",
  "storage_path": "/path/to/file",
  "created_at": "2023-01-01T00:00:00Z"
}
```

### Get Media File

Get media file metadata.

```http
GET /media/{media_id}
```

**Response:**
```json
{
  "id": "uuid",
  "bot_id": "uuid",
  "file_type": "image",
  "file_name": "image.jpg",
  "storage_path": "/path/to/file",
  "platform_file_ids": {},
  "created_at": "2023-01-01T00:00:00Z"
}
```

### Get Media File Content

Download the actual media file.

```http
GET /media/{media_id}/content
```

**Response:** Binary file content with appropriate Content-Type header.

### Delete Media File

Delete a media file.

```http
DELETE /media/{media_id}
```

## Webhooks

### Telegram Webhook

Endpoint for receiving Telegram webhook updates.

```http
POST /webhook/telegram/{bot_id}
```

**Parameters:**
- `bot_id` (UUID, path): Bot identifier

**Request Body:** Telegram webhook update object (handled automatically)

**Response:**
```json
{
  "status": "ok"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Validation error message",
  "errors": [
    {
      "field": "field_name",
      "message": "Field validation error"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": "Request validation failed",
  "errors": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

API endpoints are subject to rate limiting:
- 100 requests per minute per authenticated user
- 1000 requests per hour per account

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Webhooks and Real-time Updates

### Webhook Configuration

Webhooks are automatically configured when platform credentials are added. The webhook URLs follow this pattern:

```
https://your-domain.com/v1/api/webhook/{platform}/{bot_id}
```

### Webhook Security

- All webhook requests are validated using platform-specific security mechanisms
- Request signatures are verified where available
- Rate limiting applies to webhook endpoints

## SDKs and Libraries

Official SDKs are available for:
- Python: `getinn-bot-sdk`
- JavaScript/Node.js: `@getinn/bot-sdk`
- TypeScript: `@getinn/bot-sdk` (with type definitions)

## Examples

### Creating a Complete Bot Setup

```python
import requests

# Create bot
bot_response = requests.post("/v1/api/accounts/account-id/bots", json={
    "name": "Welcome Bot",
    "description": "Greets new users"
})
bot_id = bot_response.json()["id"]

# Add Telegram credentials
requests.post(f"/v1/api/bots/{bot_id}/platforms", json={
    "platform": "telegram",
    "credentials": {"token": "your-bot-token"}
})

# Create scenario
requests.post(f"/v1/api/bots/{bot_id}/scenarios", json={
    "name": "Welcome Scenario",
    "version": "1.0",
    "scenario_data": {
        "version": "1.0",
        "steps": {
            "welcome": {
                "id": "welcome",
                "type": "message",
                "message": {"text": "Welcome!"},
                "next_step": None
            }
        }
    }
})

# Activate bot
requests.post(f"/v1/api/bots/{bot_id}/activate")
```

## Support

For API support and questions:
- Documentation: [https://docs.getinn.com/bot-api](https://docs.getinn.com/bot-api)
- Support Email: api-support@getinn.com
- GitHub Issues: [https://github.com/getinn/bot-api/issues](https://github.com/getinn/bot-api/issues)