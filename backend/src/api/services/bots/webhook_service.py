"""
Telegram webhook management service.
"""
import os
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
import logging
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import telegram
from pyngrok import ngrok, conf

from src.api.core.config import get_settings
from src.api.models import BotPlatformCredential
from src.api.schemas.webhooks.telegram_schemas import WebhookConfigSchema, WebhookStatusSchema


logger = logging.getLogger(__name__)


class WebhookService:
    """Service for managing Telegram bot webhooks."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        
    def _is_local_environment(self) -> bool:
        """Detect if running in a local development environment."""
        env = os.getenv('ENV', '').lower()
        return env in ('local', 'development', 'dev') or self.settings.USE_NGROK
        
    async def get_webhook_url(self, bot_id: UUID) -> str:
        """Get the appropriate webhook URL based on environment."""
        base_path = f"{self.settings.API_V1_STR}/webhooks/telegram/{bot_id}"
        
        if self._is_local_environment():
            return await self._get_ngrok_url(base_path)
        else:
            domain = self.settings.WEBHOOK_DOMAIN
            return f"{domain}{base_path}"
            
    async def _get_ngrok_url(self, path: str) -> str:
        """Get or create ngrok tunnel and return URL."""
        # Configure ngrok if auth token provided
        if self.settings.NGROK_AUTHTOKEN:
            conf.get_default().auth_token = self.settings.NGROK_AUTHTOKEN
            
        # Use existing tunnel or create new one
        tunnels = ngrok.get_tunnels()
        if tunnels:
            public_url = tunnels[0].public_url
        else:
            port = self.settings.NGROK_PORT
            public_url = ngrok.connect(port, bind_tls=True).public_url
            
        return f"{public_url}{path}"

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