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

# Updated imports for python-telegram-bot v20+
import telegram
from telegram import Bot
from telegram.ext import Application
from telegram.constants import ParseMode
from telegram.error import TelegramError

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
        # The proper endpoint for webhooks should include bot_id
        base_path = f"{self.settings.API_V1_STR}/webhooks/telegram/{bot_id}"
        
        if self._is_local_environment():
            url = await self._get_ngrok_url(base_path)
            
            # Test if the URL is accessible
            try:
                # For local development, we'll just log a warning if we can't access the URL
                import socket
                from urllib.parse import urlparse
                parsed = urlparse(url)
                hostname = parsed.netloc.split(':')[0]
                
                try:
                    # Try to resolve the hostname
                    socket.gethostbyname(hostname)
                except socket.gaierror:
                    logger.warning(f"Hostname {hostname} may not be resolvable externally. Webhook registration might fail.")
            except Exception as e:
                logger.warning(f"Error checking hostname resolution: {e}")
                
            return url
        else:
            domain = self.settings.WEBHOOK_DOMAIN
            return f"{domain}{base_path}"
            
    async def _get_ngrok_url(self, path: str) -> str:
        """Get or create ngrok tunnel and return URL."""
        try:
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
        except Exception as e:
            logger.error(f"Error getting ngrok URL: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get ngrok URL: {str(e)}")

    async def set_webhook(self, bot_id: UUID, config: Optional[WebhookConfigSchema] = None) -> WebhookStatusSchema:
        """Set webhook for a bot."""
        config = config or WebhookConfigSchema()
        
        try:
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
            logger.info(f"Setting webhook URL for bot {bot_id} to {webhook_url}")
            
            # Initialize bot API
            bot_token = credential.credentials.get("token")
            if not bot_token:
                raise HTTPException(status_code=400, detail="Invalid Telegram token")
            
            try:
                # Updated for python-telegram-bot v20+
                # Create an application builder
                application = Application.builder().token(bot_token).build()
                
                # Set webhook using the application's bot
                # IMPORTANT NOTE FOR TELEGRAM WEBHOOK SETUP:
                # When running in local development with ngrok, the webhook URL must be simplified
                # This is because Telegram's webhook validation is strict and often fails with complex URLs
                # Especially when using ngrok's free tier which has DNS resolution limitations
                if self._is_local_environment():
                    # Strip out complex paths that might cause DNS resolution issues
                    from urllib.parse import urlparse
                    parsed_url = urlparse(webhook_url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    simplified_url = f"{base_url}/telegram"
                    logger.warning(f"Using simplified webhook URL for local development: {simplified_url}")
                    logger.warning("Note: You must have a route handler for /telegram in your application")
                    logger.warning("Check that src/api/main.py has the simplified_telegram_webhook endpoint defined")
                    webhook_url = simplified_url
                    
                webhook_params = {
                    "url": webhook_url,
                    "drop_pending_updates": config.drop_pending_updates
                }
                
                # Add optional parameters if provided
                if config.allowed_updates is not None:
                    webhook_params["allowed_updates"] = config.allowed_updates
                if config.max_connections is not None:
                    webhook_params["max_connections"] = config.max_connections
                if config.secret_token is not None:
                    webhook_params["secret_token"] = config.secret_token
                
                # Log the exact webhook parameters we're sending to Telegram
                logger.info(f"Setting webhook with these parameters: {webhook_params}")
                try:
                    await application.bot.set_webhook(**webhook_params)
                    logger.info(f"Successfully set webhook to: {webhook_url}")
                except Exception as e:
                    logger.error(f"Error setting webhook through standard method: {str(e)}")
                    
                    if "failed to resolve host" in str(e) or "Bad webhook" in str(e):
                        # Try direct Telegram API call as a fallback for local development
                        logger.warning("Attempting to set webhook through direct Telegram API call")
                        try:
                            import aiohttp
                            import json
                            
                            # Use simplified URL for better compatibility
                            if self._is_local_environment():
                                from urllib.parse import urlparse
                                parsed_url = urlparse(webhook_url)
                                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                webhook_url = f"{base_url}/telegram"
                                logger.warning(f"Using simplified URL for direct API call: {webhook_url}")
                            
                            # Make direct call to Telegram API
                            # For development environments, we may need to disable SSL verification
                            # This should only be used in development, never in production
                            ssl_context = None
                            if self._is_local_environment():
                                import ssl
                                ssl_context = ssl.create_default_context()
                                ssl_context.check_hostname = False
                                ssl_context.verify_mode = ssl.CERT_NONE
                                
                            async with aiohttp.ClientSession() as session:
                                api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
                                payload = {
                                    "url": webhook_url,
                                    "drop_pending_updates": webhook_params.get("drop_pending_updates", True)
                                }
                                
                                if "allowed_updates" in webhook_params:
                                    payload["allowed_updates"] = webhook_params["allowed_updates"]
                                if "max_connections" in webhook_params:
                                    payload["max_connections"] = webhook_params["max_connections"]
                                
                                async with session.post(api_url, json=payload, ssl=ssl_context) as response:
                                    response_text = await response.text()
                                    try:
                                        result = json.loads(response_text)
                                        if result.get("ok"):
                                            logger.info(f"Successfully set webhook through direct API: {webhook_url}")
                                            # Update the webhook URL in the database
                                            credential.webhook_url = webhook_url
                                            return
                                        else:
                                            logger.error(f"Direct Telegram API call failed: {result}")
                                            raise Exception(f"Direct Telegram API call failed: {result.get('description', 'Unknown error')}")
                                    except json.JSONDecodeError:
                                        logger.error(f"Invalid JSON response from Telegram API: {response_text}")
                                        raise Exception(f"Invalid response from Telegram API: {response_text}")
                        except Exception as direct_e:
                            logger.error(f"Direct API call failed: {str(direct_e)}")
                            import traceback
                            logger.error(f"Exception traceback: {traceback.format_exc()}")
                            raise Exception(f"Both standard and direct webhook setup methods failed: {str(e)} | {str(direct_e)}")
                    else:
                        # For other types of errors, just log and re-raise
                        import traceback
                        logger.error(f"Exception traceback: {traceback.format_exc()}")
                        raise
                
                # Update database with webhook info
                credential.webhook_last_checked = datetime.utcnow()
                credential.webhook_url = webhook_url
                
                await self.db.commit()
                
            except TelegramError as te:
                logger.error(f"Telegram API error when setting webhook: {te}")
                # Rollback database changes
                await self.db.rollback()
                raise HTTPException(status_code=400, detail=f"Telegram API error: {str(te)}")
            except Exception as e:
                logger.error(f"Unexpected error when setting webhook: {e}")
                # Rollback database changes
                await self.db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to set webhook: {str(e)}")
            
            # Get and return status
            return await self.get_status(bot_id)
        
        except HTTPException:
            # Re-raise HTTP exceptions as is
            raise
        except Exception as e:
            logger.error(f"Error in set_webhook: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def get_status(self, bot_id: UUID) -> WebhookStatusSchema:
        """Get webhook status."""
        try:
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
            
            try:
                # Updated for python-telegram-bot v20+
                application = Application.builder().token(bot_token).build()
                
                # Get webhook info
                webhook_info = await application.bot.get_webhook_info()
                
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
                
            except TelegramError as te:
                logger.error(f"Telegram API error when getting webhook status: {te}")
                raise HTTPException(status_code=400, detail=f"Telegram API error: {str(te)}")
            except Exception as e:
                logger.error(f"Unexpected error when getting webhook status: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get webhook status: {str(e)}")
                
        except HTTPException:
            # Re-raise HTTP exceptions as is
            raise
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def delete_webhook(self, bot_id: UUID) -> bool:
        """Delete a webhook."""
        try:
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
            
            try:
                # Updated for python-telegram-bot v20+
                application = Application.builder().token(bot_token).build()
                
                # Delete webhook
                await application.bot.delete_webhook()
                
                # Update database
                credential.webhook_last_checked = datetime.utcnow()
                credential.webhook_url = None
                await self.db.commit()
                
                return True
                
            except TelegramError as te:
                logger.error(f"Telegram API error when deleting webhook: {te}")
                await self.db.rollback()
                raise HTTPException(status_code=400, detail=f"Telegram API error: {str(te)}")
            except Exception as e:
                logger.error(f"Unexpected error when deleting webhook: {e}")
                await self.db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")
                
        except HTTPException:
            # Re-raise HTTP exceptions as is
            raise
        except Exception as e:
            logger.error(f"Error in delete_webhook: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")