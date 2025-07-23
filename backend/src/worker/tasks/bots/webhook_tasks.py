"""
Background tasks for managing Telegram webhook health.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.api.models import BotPlatformCredential
from src.api.services.bots.webhook_service import WebhookService
from src.worker.celery_app import shared_task
from src.api.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


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