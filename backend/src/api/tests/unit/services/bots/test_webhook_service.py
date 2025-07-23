"""
Unit tests for the Telegram webhook service.
"""
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import HTTPException

# Mock these modules since we don't need the real ones for unit tests
import sys
sys.modules['telegram'] = MagicMock()
sys.modules['pyngrok'] = MagicMock()
sys.modules['pyngrok.ngrok'] = MagicMock()
sys.modules['pyngrok.conf'] = MagicMock()

# Import after mocking
from src.api.services.bots.webhook_service import WebhookService
from src.api.schemas.webhooks.telegram_schemas import WebhookConfigSchema, WebhookStatusSchema


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def webhook_service(mock_db):
    return WebhookService(mock_db)


@pytest.mark.asyncio
async def test_is_local_environment(webhook_service):
    """Test environment detection logic"""
    # Test local environment detection
    with patch.dict('os.environ', {'ENV': 'development'}):
        assert webhook_service._is_local_environment() is True
        
    # Test production environment detection
    with patch.dict('os.environ', {'ENV': 'production'}):
        with patch('src.api.core.config.get_settings', return_value=MagicMock(USE_NGROK=False)):
            assert webhook_service._is_local_environment() is False


@pytest.mark.asyncio
async def test_get_webhook_url_production(webhook_service):
    """Test webhook URL generation in production environment"""
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    
    # Set up the mock settings
    mock_settings = MagicMock()
    mock_settings.WEBHOOK_DOMAIN = "https://api.example.com"
    mock_settings.API_V1_STR = "/v1/api"
    webhook_service.settings = mock_settings
    
    # Mock the _is_local_environment method
    webhook_service._is_local_environment = lambda: False
    
    # Test the get_webhook_url method
    url = await webhook_service.get_webhook_url(bot_id)
    assert url == f"https://api.example.com/v1/api/webhooks/telegram/{bot_id}"


@pytest.mark.asyncio
async def test_get_webhook_url_development(webhook_service):
    """Test webhook URL generation in development environment with ngrok"""
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    
    # Set up the mock settings
    mock_settings = MagicMock()
    mock_settings.API_V1_STR = "/v1/api"
    webhook_service.settings = mock_settings
    
    # Mock the _is_local_environment and _get_ngrok_url methods
    webhook_service._is_local_environment = lambda: True
    webhook_service._get_ngrok_url = AsyncMock(return_value="https://abc123.ngrok.io/v1/api/webhooks/telegram/11111111-1111-1111-1111-111111111111")
    
    # Test the get_webhook_url method
    url = await webhook_service.get_webhook_url(bot_id)
    assert url == "https://abc123.ngrok.io/v1/api/webhooks/telegram/11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_set_webhook(webhook_service, mock_db):
    """Test setting a webhook"""
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    
    # Mock database query result
    mock_credential = MagicMock()
    mock_credential.credentials = {"token": "mock_token"}
    mock_db.execute = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_credential
    mock_db.commit = AsyncMock()
    
    # Set up mocks for method calls
    webhook_service.get_webhook_url = AsyncMock(return_value="https://example.com/webhook")
    webhook_service.get_status = AsyncMock(return_value=WebhookStatusSchema(url="https://example.com/webhook"))
    
    # Mock telegram Bot
    import telegram
    mock_bot = AsyncMock()
    mock_bot.set_webhook = AsyncMock()
    telegram.Bot = MagicMock(return_value=mock_bot)
    
    # Call the method
    result = await webhook_service.set_webhook(bot_id)
    
    # Assertions
    webhook_service.get_webhook_url.assert_called_once_with(bot_id)
    mock_bot.set_webhook.assert_called_once()
    assert mock_credential.webhook_url == "https://example.com/webhook"
    assert isinstance(mock_credential.webhook_last_checked, datetime)
    mock_db.commit.assert_called_once()
    webhook_service.get_status.assert_called_once_with(bot_id)
    assert isinstance(result, WebhookStatusSchema)
    assert result.url == "https://example.com/webhook"


@pytest.mark.asyncio
async def test_set_webhook_with_config(webhook_service, mock_db):
    """Test setting a webhook with specific configuration"""
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    config = WebhookConfigSchema(
        drop_pending_updates=True,
        max_connections=50,
        allowed_updates=["message", "callback_query"]
    )
    
    # Mock database query result
    mock_credential = MagicMock()
    mock_credential.credentials = {"token": "mock_token"}
    mock_db.execute = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_credential
    mock_db.commit = AsyncMock()
    
    # Set up mocks for method calls
    webhook_service.get_webhook_url = AsyncMock(return_value="https://example.com/webhook")
    webhook_service.get_status = AsyncMock(return_value=WebhookStatusSchema(url="https://example.com/webhook"))
    
    # Mock telegram Bot
    import telegram
    mock_bot = AsyncMock()
    mock_bot.set_webhook = AsyncMock()
    telegram.Bot = MagicMock(return_value=mock_bot)
    
    # Call the method
    result = await webhook_service.set_webhook(bot_id, config)
    
    # Assertions
    webhook_service.get_webhook_url.assert_called_once_with(bot_id)
    mock_bot.set_webhook.assert_called_once_with(
        url="https://example.com/webhook",
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
        max_connections=50,
        secret_token=None
    )
    assert mock_credential.webhook_url == "https://example.com/webhook"
    mock_db.commit.assert_called_once()
    webhook_service.get_status.assert_called_once_with(bot_id)


@pytest.mark.asyncio
async def test_set_webhook_credential_not_found(webhook_service, mock_db):
    """Test setting a webhook when credential is not found"""
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    
    # Mock database query result to return None
    mock_db.execute = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    
    # Assert that HTTPException is raised
    with pytest.raises(HTTPException) as excinfo:
        await webhook_service.set_webhook(bot_id)
    
    # Assertions
    assert excinfo.value.status_code == 404
    assert f"No Telegram credentials found for bot {bot_id}" in str(excinfo.value.detail)
    # Verify the database was queried
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_set_webhook_invalid_token(webhook_service, mock_db):
    """Test setting a webhook with invalid token"""
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    
    # Mock database query result with invalid token
    mock_credential = MagicMock()
    mock_credential.credentials = {}  # Empty credentials, no token
    mock_db.execute = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_credential
    
    # Set up mocks for method calls
    webhook_service.get_webhook_url = AsyncMock(return_value="https://example.com/webhook")
    
    # Assert that HTTPException is raised
    with pytest.raises(HTTPException) as excinfo:
        await webhook_service.set_webhook(bot_id)
    
    # Assertions
    assert excinfo.value.status_code == 400
    assert "Invalid Telegram token" in str(excinfo.value.detail)
    # Verify the webhook URL was retrieved before checking the token
    webhook_service.get_webhook_url.assert_called_once_with(bot_id)


@pytest.mark.asyncio
async def test_get_status(webhook_service, mock_db):
    """Test getting webhook status"""
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    
    # Mock database query result
    mock_credential = MagicMock()
    mock_credential.credentials = {"token": "mock_token"}
    mock_db.execute = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_credential
    mock_db.commit = AsyncMock()
    
    # Mock telegram Bot and webhook_info
    import telegram
    mock_webhook_info = MagicMock(
        url="https://example.com/webhook",
        has_custom_certificate=False,
        pending_update_count=5,
        ip_address="192.168.1.1",
        last_error_date=None,
        last_error_message=None,
        max_connections=40,
        allowed_updates=["message"]
    )
    mock_bot = AsyncMock()
    mock_bot.get_webhook_info = AsyncMock(return_value=mock_webhook_info)
    telegram.Bot = MagicMock(return_value=mock_bot)
    
    # Call the method
    result = await webhook_service.get_status(bot_id)
    
    # Assertions
    mock_bot.get_webhook_info.assert_called_once()
    assert result.url == "https://example.com/webhook"
    assert result.pending_update_count == 5
    assert result.ip_address == "192.168.1.1"
    assert result.max_connections == 40
    assert result.allowed_updates == ["message"]
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_webhook(webhook_service, mock_db):
    """Test deleting a webhook"""
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    
    # Mock database query result
    mock_credential = MagicMock()
    mock_credential.credentials = {"token": "mock_token"}
    mock_db.execute = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_credential
    mock_db.commit = AsyncMock()
    
    # Mock telegram Bot
    import telegram
    mock_bot = AsyncMock()
    mock_bot.delete_webhook = AsyncMock()
    telegram.Bot = MagicMock(return_value=mock_bot)
    
    # Call the method
    result = await webhook_service.delete_webhook(bot_id)
    
    # Assertions
    mock_bot.delete_webhook.assert_called_once()
    assert mock_credential.webhook_url is None
    assert isinstance(mock_credential.webhook_last_checked, datetime)
    mock_db.commit.assert_called_once()
    assert result is True


@pytest.mark.asyncio
async def test_ngrok_url_generation(webhook_service):
    """Test ngrok URL generation"""
    path = "/v1/api/webhooks/telegram/123"
    
    # Setup for mock settings
    mock_settings = MagicMock()
    mock_settings.NGROK_AUTHTOKEN = None
    mock_settings.NGROK_PORT = 8000
    webhook_service.settings = mock_settings
    
    # Mock pyngrok modules
    import pyngrok.ngrok
    import pyngrok.conf
    
    # Test with existing tunnel
    mock_tunnel = MagicMock(public_url="https://abc123.ngrok.io")
    pyngrok.ngrok.get_tunnels = MagicMock(return_value=[mock_tunnel])
    pyngrok.conf.get_default = MagicMock(return_value=MagicMock())
    
    # Call the method
    url = await webhook_service._get_ngrok_url(path)
    assert url == "https://abc123.ngrok.io/v1/api/webhooks/telegram/123"
    pyngrok.ngrok.get_tunnels.assert_called_once()
    
    # Test with no existing tunnels
    pyngrok.ngrok.get_tunnels = MagicMock(return_value=[])
    mock_connect = MagicMock()
    mock_connect.public_url = "https://new-tunnel.ngrok.io"
    pyngrok.ngrok.connect = MagicMock(return_value=mock_connect)
    
    # Call the method again
    url = await webhook_service._get_ngrok_url(path)
    assert url == "https://new-tunnel.ngrok.io/v1/api/webhooks/telegram/123"
    pyngrok.ngrok.connect.assert_called_once_with(8000, bind_tls=True)