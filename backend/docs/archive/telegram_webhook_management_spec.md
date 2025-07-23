# Technical Specification: Telegram Webhook Management

## 1. Overview

This document outlines the technical specifications for implementing a Telegram webhook management system for the AI Restaurant Platform. The system will:

1. Configure webhooks automatically based on the environment (local vs. production)
2. Provide API endpoints for managing webhooks
3. Include a worker process to periodically check and refresh webhooks

## 2. Key Components

### 2.1. Environment-Aware Configuration

- **Local Development**: Use ngrok for creating temporary public URLs
- **Production**: Use configured domain name

### 2.2. API Endpoints

- Enable/disable webhooks
- Check webhook status
- Manually refresh webhook

### 2.3. Background Worker

- Periodic checks every 5 minutes
- Auto-refresh broken or misconfigured webhooks

## 3. API Endpoint Implementation

Add the following endpoints to `src/api/routers/webhooks/telegram.py`:

```python
@router.post("/{bot_id}/webhook/set")
async def set_webhook(
    bot_id: UUID,
    config: WebhookConfigSchema = Body(default=None),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> WebhookStatusSchema:
    """Set Telegram webhook for a bot with environment detection."""
    webhook_service = WebhookService(db)
    return await webhook_service.set_webhook(bot_id, config)

@router.get("/{bot_id}/webhook/status")
async def get_webhook_status(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> WebhookStatusSchema:
    """Get detailed webhook status including health metrics."""
    webhook_service = WebhookService(db)
    return await webhook_service.get_status(bot_id)

@router.post("/{bot_id}/webhook/delete")
async def delete_webhook(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, bool]:
    """Delete Telegram webhook for a bot."""
    webhook_service = WebhookService(db)
    success = await webhook_service.delete_webhook(bot_id)
    return {"success": success}
```

### 3.1 Request/Response Schemas

In `src/api/schemas/webhooks/telegram_schemas.py`:

```python
class WebhookConfigSchema(BaseModel):
    """Configuration for setting a webhook."""
    drop_pending_updates: bool = False
    secret_token: Optional[str] = None
    max_connections: Optional[int] = None
    allowed_updates: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

class WebhookStatusSchema(BaseModel):
    """Status information about a webhook."""
    url: Optional[str] = None
    has_custom_certificate: bool = False
    pending_update_count: int = 0
    ip_address: Optional[str] = None
    last_error_date: Optional[datetime] = None
    last_error_message: Optional[str] = None
    last_synchronization_error_date: Optional[datetime] = None
    max_connections: Optional[int] = None
    allowed_updates: Optional[List[str]] = None
    
    class Config:
        from_attributes = True
```

## 4. Environment Detection

Create a webhook manager class in `src/api/services/bots/webhook_service.py`:

```python
class WebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        
    def _is_local_environment(self) -> bool:
        """Detect if running in a local development environment."""
        env = os.getenv('ENV', '').lower()
        return env in ('local', 'development', 'dev') or self.settings.USE_NGROK
        
    async def get_webhook_url(self, bot_id: UUID) -> str:
        """Get the appropriate webhook URL based on environment."""
        base_path = f"/v1/api/webhooks/telegram/{bot_id}"
        
        if self._is_local_environment():
            return await self._get_ngrok_url(base_path)
        else:
            domain = self.settings.WEBHOOK_DOMAIN
            return f"{domain}{base_path}"
            
    async def _get_ngrok_url(self, path: str) -> str:
        """Get or create ngrok tunnel and return URL."""
        from pyngrok import ngrok, conf
        
        # Configure ngrok if auth token provided
        if self.settings.NGROK_AUTHTOKEN:
            conf.get_default().auth_token = self.settings.NGROK_AUTHTOKEN
            
        # Use existing tunnel or create new one
        tunnels = ngrok.get_tunnels()
        if tunnels:
            public_url = tunnels[0].public_url
        else:
            port = self.settings.NGROK_PORT or 8000
            public_url = ngrok.connect(port, bind_tls=True).public_url
            
        return f"{public_url}{path}"
```

## 5. Webhook Management

Extend the WebhookService with these methods:

```python
async def set_webhook(self, bot_id: UUID, config: Optional[WebhookConfigSchema] = None) -> WebhookStatusSchema:
    """Set webhook for a bot."""
    config = config or WebhookConfigSchema()
    
    # Get bot platform credentials
    cred_query = select(BotPlatformCredential).where(
        BotPlatformCredential.bot_id == bot_id,
        BotPlatformCredential.platform == "telegram",
        BotPlatformCredential.is_active == True
    )
    result = await self.db.execute(cred_query)
    credential = result.scalar_one_or_none()
    
    if not credential:
        raise HTTPException(status_code=404, detail=f"No Telegram credentials found for bot {bot_id}")
    
    # Get webhook URL
    webhook_url = await self.get_webhook_url(bot_id)
    
    # Initialize bot API
    bot_token = credential.credentials.get("token")
    if not bot_token:
        raise HTTPException(status_code=400, detail="Invalid Telegram token")
    
    bot = telegram.Bot(token=bot_token)
    
    # Set webhook
    await bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=config.drop_pending_updates,
        allowed_updates=config.allowed_updates,
        max_connections=config.max_connections,
        secret_token=config.secret_token
    )
    
    # Update database with webhook info
    credential.webhook_last_checked = datetime.utcnow()
    credential.webhook_url = webhook_url
    
    await self.db.commit()
    
    # Get and return status
    return await self.get_status(bot_id)

async def get_status(self, bot_id: UUID) -> WebhookStatusSchema:
    """Get webhook status."""
    # Get bot platform credentials
    cred_query = select(BotPlatformCredential).where(
        BotPlatformCredential.bot_id == bot_id,
        BotPlatformCredential.platform == "telegram",
        BotPlatformCredential.is_active == True
    )
    result = await self.db.execute(cred_query)
    credential = result.scalar_one_or_none()
    
    if not credential:
        raise HTTPException(status_code=404, detail=f"No Telegram credentials found for bot {bot_id}")
    
    # Initialize bot API
    bot_token = credential.credentials.get("token")
    if not bot_token:
        raise HTTPException(status_code=400, detail="Invalid Telegram token")
    
    bot = telegram.Bot(token=bot_token)
    
    # Get webhook info
    webhook_info = await bot.get_webhook_info()
    
    # Update database with last check time
    credential.webhook_last_checked = datetime.utcnow()
    await self.db.commit()
    
    # Return status
    return WebhookStatusSchema(
        url=webhook_info.url,
        has_custom_certificate=webhook_info.has_custom_certificate,
        pending_update_count=webhook_info.pending_update_count,
        ip_address=webhook_info.ip_address,
        last_error_date=webhook_info.last_error_date,
        last_error_message=webhook_info.last_error_message,
        max_connections=webhook_info.max_connections,
        allowed_updates=webhook_info.allowed_updates,
    )

async def delete_webhook(self, bot_id: UUID) -> bool:
    """Delete a webhook."""
    # Get bot platform credentials
    cred_query = select(BotPlatformCredential).where(
        BotPlatformCredential.bot_id == bot_id,
        BotPlatformCredential.platform == "telegram",
        BotPlatformCredential.is_active == True
    )
    result = await self.db.execute(cred_query)
    credential = result.scalar_one_or_none()
    
    if not credential:
        raise HTTPException(status_code=404, detail=f"No Telegram credentials found for bot {bot_id}")
    
    # Initialize bot API
    bot_token = credential.credentials.get("token")
    if not bot_token:
        raise HTTPException(status_code=400, detail="Invalid Telegram token")
    
    bot = telegram.Bot(token=bot_token)
    
    # Delete webhook
    await bot.delete_webhook()
    
    # Update database
    credential.webhook_last_checked = datetime.utcnow()
    credential.webhook_url = None
    await self.db.commit()
    
    return True
```

## 6. Database Updates

Add the following fields to BotPlatformCredential model in `src/api/models/bots.py`:

```python
class BotPlatformCredential(Base):
    # Existing fields...
    
    # Webhook-related fields
    webhook_url = Column(String, nullable=True)
    webhook_last_checked = Column(DateTime, nullable=True)
    webhook_auto_refresh = Column(Boolean, nullable=False, default=True)
```

Create a migration to add these fields:

```python
def upgrade():
    op.add_column('bot_platform_credential', sa.Column('webhook_url', sa.String(), nullable=True))
    op.add_column('bot_platform_credential', sa.Column('webhook_last_checked', sa.DateTime(), nullable=True))
    op.add_column('bot_platform_credential', sa.Column('webhook_auto_refresh', sa.Boolean(), nullable=False, server_default='true'))
```

## 7. Background Worker

Create a task in `src/worker/tasks/bots/webhook_tasks.py`:

```python
@shared_task(name="check_telegram_webhooks")
async def check_telegram_webhooks():
    """Check and refresh Telegram webhooks if needed."""
    async with AsyncSessionLocal() as db:
        # Get all active Telegram bot credentials
        query = select(BotPlatformCredential).where(
            BotPlatformCredential.platform == "telegram",
            BotPlatformCredential.is_active == True,
            BotPlatformCredential.webhook_auto_refresh == True
        )
        
        result = await db.execute(query)
        credentials = result.scalars().all()
        
        webhook_service = WebhookService(db)
        
        for cred in credentials:
            try:
                # Skip if checked recently (less than 4 minutes ago)
                if (cred.webhook_last_checked and 
                    datetime.utcnow() - cred.webhook_last_checked < timedelta(minutes=4)):
                    continue
                    
                # Get webhook status
                status = await webhook_service.get_status(cred.bot_id)
                
                # Check if webhook needs refresh
                needs_refresh = (
                    not status.url or
                    (status.last_error_date and 
                     datetime.utcnow() - status.last_error_date < timedelta(hours=1)) or
                    status.pending_update_count > 100
                )
                
                # Refresh webhook if needed
                if needs_refresh:
                    logger.info(f"Refreshing webhook for bot {cred.bot_id}")
                    await webhook_service.set_webhook(cred.bot_id)
                
            except Exception as e:
                logger.error(f"Error checking webhook for bot {cred.bot_id}: {str(e)}")
```

Configure Celery task in `src/worker/celery_app.py`:

```python
app.conf.beat_schedule = {
    # Other tasks...
    
    'check-telegram-webhooks': {
        'task': 'src.worker.tasks.bots.webhook_tasks.check_telegram_webhooks',
        'schedule': 300.0,  # 5 minutes
    },
}
```

## 8. Configuration

Add to application settings in `src/api/core/config.py`:

```python
# Webhook settings
USE_NGROK = os.getenv("USE_NGROK", "false").lower() == "true"
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", None)
NGROK_PORT = int(os.getenv("NGROK_PORT", "8000"))
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN", "https://api.getinn.ai")
```

## 9. Dependencies

Add to requirements.txt:

```
python-telegram-bot>=20.0
pyngrok>=5.1.0
```

## 10. Testing Specification

### 10.1. Unit Tests

Create unit tests in `src/api/tests/unit/services/bots/test_webhook_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from uuid import UUID
import telegram
from fastapi import HTTPException

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
    
    with patch.object(webhook_service, '_is_local_environment', return_value=False):
        with patch('src.api.core.config.get_settings', return_value=MagicMock(
            WEBHOOK_DOMAIN="https://api.example.com",
            API_V1_STR="/v1/api"
        )):
            url = await webhook_service.get_webhook_url(bot_id)
            assert url == f"https://api.example.com/v1/api/webhooks/telegram/{bot_id}"


@pytest.mark.asyncio
async def test_get_webhook_url_development(webhook_service):
    """Test webhook URL generation in development environment with ngrok"""
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    
    with patch.object(webhook_service, '_is_local_environment', return_value=True):
        with patch.object(webhook_service, '_get_ngrok_url', return_value="https://abc123.ngrok.io/v1/api/webhooks/telegram/11111111-1111-1111-1111-111111111111"):
            url = await webhook_service.get_webhook_url(bot_id)
            assert url == "https://abc123.ngrok.io/v1/api/webhooks/telegram/11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_set_webhook(webhook_service, mock_db):
    """Test setting a webhook"""
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    
    # Mock database query result
    mock_credential = MagicMock()
    mock_credential.credentials = {"token": "mock_token"}
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_credential
    
    # Mock webhook_url generation
    with patch.object(webhook_service, 'get_webhook_url', return_value="https://example.com/webhook"):
        # Mock telegram Bot
        mock_bot = AsyncMock()
        with patch('telegram.Bot', return_value=mock_bot):
            # Mock get_status
            with patch.object(webhook_service, 'get_status', return_value=WebhookStatusSchema(url="https://example.com/webhook")):
                result = await webhook_service.set_webhook(bot_id)
                
                # Assertions
                mock_bot.set_webhook.assert_called_once()
                assert mock_credential.webhook_url == "https://example.com/webhook"
                assert isinstance(mock_credential.webhook_last_checked, datetime)
                mock_db.commit.assert_called_once()
                assert isinstance(result, WebhookStatusSchema)
                assert result.url == "https://example.com/webhook"
```

### 10.2. Integration Tests

Create integration tests in `src/api/tests/integration/test_webhook_api.py`:

```python
import pytest
import os
from fastapi.testclient import TestClient
from uuid import UUID, uuid4

from src.api.tests.base import BaseAPITest
from src.api.core.config import get_settings


class TestWebhookAPI(BaseAPITest):
    """
    Integration tests for webhook management endpoints.
    """
    
    # Get API base URL from environment variable or use default
    api_base_url = os.environ.get("API_TEST_URL", "http://localhost:8000")
    
    # Use fixed account ID for tests
    test_account_id = "00000000-0000-0000-0000-000000000001"
    
    def setup_method(self):
        """Setup for each test method"""
        # Get a test token directly from the API
        response = self.client.post("/v1/api/auth/test-token")
        assert response.status_code == 200, f"Failed to get test token: {response.text}"
        
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create a test bot for webhooks
        bot_data = {
            "name": "Webhook Test Bot",
            "description": "Bot for testing webhook functionality",
            "account_id": self.test_account_id,
            "is_active": True,
            "platform_credentials": []
        }
        
        response = self.client.post(
            f"{self.api_base_url}/v1/api/accounts/{bot_data['account_id']}/bots", 
            json=bot_data,
            headers=self.headers
        )
        
        assert response.status_code == 201, f"Failed to create bot: {response.text}"
        self.bot_id = response.json()["id"]
        
        # Add Telegram platform credential
        credential_data = {
            "platform": "telegram",
            "credentials": {
                "token": "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            },
            "is_active": True
        }
        
        response = self.client.post(
            f"{self.api_base_url}/v1/api/bots/{self.bot_id}/platforms",
            json=credential_data,
            headers=self.headers
        )
        
        assert response.status_code == 201, f"Failed to add credential: {response.text}"
    
    def test_set_webhook(self):
        """
        Test setting a webhook.
        """
        # Mock the external dependency (telegram.Bot.set_webhook)
        # In real tests, use a mocking library or approach compatible with your test setup
        
        webhook_data = {
            "drop_pending_updates": True,
            "max_connections": 40,
            "allowed_updates": ["message", "callback_query"]
        }
        
        response = self.client.post(
            f"{self.api_base_url}/v1/api/webhooks/telegram/{self.bot_id}/webhook/set",
            json=webhook_data,
            headers=self.headers
        )
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        
    def test_get_webhook_status(self):
        """
        Test getting webhook status.
        """
        response = self.client.get(
            f"{self.api_base_url}/v1/api/webhooks/telegram/{self.bot_id}/webhook/status",
            headers=self.headers
        )
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "pending_update_count" in data
        
    def test_delete_webhook(self):
        """
        Test deleting a webhook.
        """
        response = self.client.post(
            f"{self.api_base_url}/v1/api/webhooks/telegram/{self.bot_id}/webhook/delete",
            headers=self.headers
        )
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
```

### 10.3. Mock Strategy for External Services

For testing webhook functionality without actual network calls to Telegram API:

1. **Unit Tests**: 
   - Use AsyncMock to patch the telegram.Bot class
   - Mock external API calls like set_webhook, get_webhook_info, delete_webhook
   
2. **Integration Tests**:
   - Create a test fixture that swaps the real WebhookService with a mocked version
   - For CI/CD, create a telegram bot mock that can be deployed during testing

### 10.4. Environment Testing

Test the service across different environments:

1. **Local Development**:
   - Verify ngrok tunnels are created and used correctly
   - Ensure webhook URLs correctly use ngrok domain

2. **Production**:
   - Verify configured domain is used for webhook URLs
   - Test webhook auto-refresh functionality

## 11. Implementation Timeline

1. Database schema updates - 2 hours
2. WebhookService implementation - 4 hours
3. API endpoints - 2 hours
4. Background worker - 2 hours
5. Unit and integration tests - 4 hours

Total estimated time: 1.5 days