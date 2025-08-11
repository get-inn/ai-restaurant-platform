from typing import Dict, Any, List, Optional
import httpx
import json
import os
import asyncio
import tempfile
import imghdr
from datetime import datetime
from uuid import UUID
from typing import Dict, Any, List, Optional, Tuple, BinaryIO

from src.integrations.platforms.base import PlatformAdapter
from src.bot_manager.conversation_logger import get_logger, LogEventType


class TelegramAdapter(PlatformAdapter):
    """
    Telegram Bot API implementation of the PlatformAdapter
    """
    
    def __init__(self):
        self.api_url = "https://api.telegram.org/bot"
        self.file_api_url = "https://api.telegram.org/file/bot"
        self.token = None
        self.bot_info = None
    
    def _get_logger_context(self):
        """Get stored context for logging"""
        context = {}
        # Extract context from instance variables
        for key in dir(self):
            if key.startswith("_context_"):
                context_key = key[9:]  # Remove '_context_' prefix
                context[context_key] = getattr(self, key)
        
        # Also check if there's any thread-local context from conversation_logger
        try:
            from src.bot_manager.conversation_logger import _thread_local
            if hasattr(_thread_local, 'context'):
                # Include any relevant thread-local context
                context.update(_thread_local.context)
        except ImportError:
            pass
            
        return context
        
    def _get_logger(self):
        """Get a properly configured logger with context"""
        context = self._get_logger_context()
        context = {k: v for k, v in context.items() if not k.startswith('skip_') and k != 'platform'}
        return get_logger(platform="telegram", **context)
        
    def _get_extension_for_content_type(self, content_type: str) -> str:
        """Get file extension based on content type
        
        Args:
            content_type: The MIME type of the content
            
        Returns:
            Appropriate file extension including the leading dot
        """
        if content_type.startswith("image/jpeg"):
            return ".jpg"
        elif content_type.startswith("image/png"):
            return ".png"
        elif content_type.startswith("image/gif"):
            return ".gif"
        elif content_type.startswith("video/"):
            return ".mp4"
        elif content_type.startswith("audio/"):
            return ".mp3"
        elif content_type == "application/pdf":
            return ".pdf"
        else:
            return ".bin"  # Default
    
    @property
    def platform_name(self) -> str:
        return "telegram"
    
    async def initialize(self, credentials: Dict[str, Any]) -> bool:
        """Initialize the adapter with Telegram bot token"""
        from src.bot_manager.conversation_logger import get_logger, LogEventType
        
        # Get context for logging
        context = self._get_logger_context()
        
        # Create logger with clean context
        # Remove any legacy skip flags and platform key if present to avoid duplicates
        context = {k: v for k, v in context.items() if not k.startswith('skip_') and k != 'platform'}
        logger = get_logger(platform="telegram", **context)
        
        if "token" not in credentials:
            logger.error(LogEventType.ERROR, "No token provided in credentials")
            return False
        
        self.token = credentials["token"]
        
        # Test the token by getting bot information
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:  # Increased timeout
                logger.debug(LogEventType.ADAPTER, "Testing Telegram token with getMe request")
                response = await client.get(f"{self.api_url}{self.token}/getMe")
                
                if response.status_code != 200:
                    logger.error(LogEventType.ERROR, f"Failed to validate token: {response.status_code}", {
                        "status_code": response.status_code,
                        "response": response.text[:200]
                    })
                    return False
                
                self.bot_info = response.json().get("result")
                logger.info(LogEventType.ADAPTER, "Successfully validated Telegram token", {
                    "bot_id": self.bot_info.get("id"),
                    "bot_name": self.bot_info.get("username")
                })
                return True
                
        except httpx.ConnectTimeout:
            logger.error(LogEventType.ERROR, "Connection timeout while connecting to Telegram API", {
                "api_url": f"{self.api_url}[token]/getMe",
                "timeout": "30 seconds"
            })
            # Continue with the webhook processing even if we can't validate the token
            # This allows the bot to work in environments with intermittent connectivity
            self.bot_info = {"id": "unknown", "username": "unknown_bot"}
            return True
            
        except Exception as e:
            logger.error(LogEventType.ERROR, f"Error initializing Telegram adapter: {str(e)}", {
                "exception": str(e)
            })
            # Continue with the webhook processing even if we can't validate the token
            self.bot_info = {"id": "unknown", "username": "unknown_bot"}
            return True
    
    async def send_text_message(self, chat_id: str, text: str) -> Dict[str, Any]:
        """Send a text message to a Telegram chat"""
        from src.bot_manager.conversation_logger import get_logger, LogEventType
        
        # Get context for logging
        context = self._get_logger_context()
        
        # Create logger with clean context
        # Remove any legacy skip flags and platform key if present to avoid duplicates
        context = {k: v for k, v in context.items() if not k.startswith('skip_') and k != 'platform'}
        logger = get_logger(platform="telegram", **context)
        
        if not self.token:
            logger.error(LogEventType.ERROR, "Cannot send text message: Adapter not initialized")
            return {"success": False, "error": "Adapter not initialized"}
            
        # Process message sending
            
        # Log all outgoing messages
        logger.info(LogEventType.OUTGOING, f"Sent: {text}", {
            "chat_id": chat_id,
            "has_buttons": False,
            "text_length": len(text)
        })
        
        try:
            # Configure httpx with increased timeout and retry settings
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.debug(LogEventType.ADAPTER, f"Sending text message to chat {chat_id}", {
                    "text_length": len(text),
                    "chat_id": chat_id
                })
                
                # Implement automatic retry for network issues
                max_retries = 2
                retry_delay = 1.0
                
                for retry in range(max_retries + 1):
                    try:
                        response = await client.post(
                            f"{self.api_url}{self.token}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": text,
                                "parse_mode": "HTML"  # Support HTML formatting
                            }
                        )
                        
                        # If we got here, the request succeeded
                        break
                    except httpx.ConnectTimeout:
                        if retry < max_retries:
                            # Log the retry attempt
                            logger.warning(LogEventType.ADAPTER, f"Connection timeout, retrying ({retry+1}/{max_retries})", {
                                "chat_id": chat_id,
                                "retry_count": retry + 1,
                                "max_retries": max_retries,
                                "retry_delay": retry_delay
                            })
                            # Wait before retrying
                            await asyncio.sleep(retry_delay)
                        else:
                            # We've exhausted our retries, re-raise the exception
                            raise
                
                if response.status_code != 200:
                    error_msg = response.text
                    logger.error(LogEventType.ERROR, f"Failed to send text message: API returned {response.status_code}", {
                        "status_code": response.status_code,
                        "error": error_msg[:200] if len(error_msg) > 200 else error_msg
                    })
                    return {"success": False, "error": error_msg}
                
                result = response.json().get("result")
                logger.debug(LogEventType.ADAPTER, "Text message sent successfully", {
                    "message_id": result.get("message_id") if result else None,
                    "chat_id": chat_id
                })
                return {"success": True, "result": result}
                
        except httpx.ConnectTimeout:
            logger.error(LogEventType.ERROR, "Connection timeout while sending text message to Telegram API after retries", {
                "chat_id": chat_id,
                "text_length": len(text),
                "max_retries": max_retries
            })
            # Return a status that allows the conversation to continue
            return {"success": False, "error": "Connection timeout", "retry_recommended": True}
            
        except Exception as e:
            logger.error(LogEventType.ERROR, f"Error sending text message: {str(e)}", {
                "exception": str(e),
                "chat_id": chat_id
            })
            return {"success": False, "error": f"Exception: {str(e)}"}
    
    async def send_media_message(
        self, 
        chat_id: str, 
        media_type: str, 
        file_path: str, 
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a media message to a Telegram chat"""
        from src.bot_manager.conversation_logger import get_logger, LogEventType
        # Get context for logging
        context = self._get_logger_context()
        
        # Create logger with clean context
        # Remove any legacy skip flags and platform key if present to avoid duplicates
        context = {k: v for k, v in context.items() if not k.startswith('skip_') and k != 'platform'}
        logger = get_logger(platform="telegram", **context)
        
        logger.debug(LogEventType.ADAPTER, f"Sending media message of type '{media_type}'", {
            "chat_id": chat_id,
            "media_type": media_type,
            "file_path": file_path,
            "has_caption": caption is not None
        })
        
        if not self.token:
            logger.error(LogEventType.ERROR, "Cannot send media: Adapter not initialized")
            return {"success": False, "error": "Adapter not initialized"}
        
        # Map media types to Telegram methods and file parameter names
        telegram_map = {
            "image": {"method": "sendPhoto", "file_param": "photo"},
            "video": {"method": "sendVideo", "file_param": "video"},
            "audio": {"method": "sendAudio", "file_param": "audio"},
            "document": {"method": "sendDocument", "file_param": "document"}
        }
        
        # Get the appropriate method and file parameter name for this media type
        media_info = telegram_map.get(media_type.lower(), {"method": "sendDocument", "file_param": "document"})
        method = media_info["method"]
        file_param = media_info["file_param"]
        
        logger.info(LogEventType.MEDIA, f"Using Telegram API method '{method}' for media type '{media_type}'", {
            "file_parameter": file_param
        })
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(LogEventType.ERROR, f"Cannot send media: File not found at path '{file_path}'")
            return {"success": False, "error": "File not found"}
        
        # For Telegram, we need to send the file as multipart/form-data
        async with httpx.AsyncClient() as client:
            # Log more details about the file
            file_size = os.path.getsize(file_path)
            file_exists = os.path.exists(file_path)
            file_readable = os.access(file_path, os.R_OK)
            
            logger.info(LogEventType.MEDIA, f"Preparing to send media file from {file_path}", {
                "file_path": file_path,
                "file_exists": file_exists,
                "file_readable": file_readable,
                "file_size": file_size,
                "media_type": media_type
            })
            
            try:
                # Validate the image format if sending an image
                if media_type == "image":
                    import imghdr
                    detected_format = imghdr.what(file_path)
                    
                    logger.info(LogEventType.MEDIA, f"Detected image format: {detected_format}", {
                        "file_path": file_path,
                        "media_type": media_type,
                        "detected_format": detected_format
                    })
                    
                    # If we can't detect a valid image format, switch to document
                    if not detected_format:
                        logger.warning(LogEventType.MEDIA, "File doesn't appear to be a valid image, sending as document", {
                            "file_path": file_path
                        })
                        media_type = "document"
                        media_info = telegram_map.get(media_type.lower(), {"method": "sendDocument", "file_param": "document"})
                        method = media_info["method"]
                        file_param = media_info["file_param"]
                
                with open(file_path, "rb") as file:
                    # Read first few bytes to verify file content
                    file_header = file.read(20)
                    file.seek(0)  # Reset file pointer to beginning
                    
                    # Create form data with the file and optional caption
                    # Use the correct file parameter name for Telegram's API (e.g., "photo" for images)
                    files = {file_param: file}
                    data = {"chat_id": chat_id}
                    
                    if caption:
                        data["caption"] = caption
                        
                    # Limit caption to 1024 characters (Telegram limit)
                    if caption and len(caption) > 1024:
                        data["caption"] = caption[:1021] + "..."
                    
                    logger.debug(LogEventType.ADAPTER, f"Sending request to Telegram API: {method}", {
                        "method": method,
                        "chat_id": chat_id,
                        "file_size": file_size,
                        "file_header_hex": file_header.hex()[:40] if file_header else "None"
                    })
                    
                    response = await client.post(
                        f"{self.api_url}{self.token}/{method}",
                        files=files,
                        data=data,
                        timeout=60.0  # Increase timeout for large files
                    )
            except Exception as e:
                logger.error(LogEventType.ERROR, f"Exception while sending media: {str(e)}", {
                    "exception": str(e),
                    "file_path": file_path,
                    "media_type": media_type
                })
                return {"success": False, "error": f"Exception: {str(e)}"}
            
            # Process response outside of try block
            if response.status_code != 200:
                error_msg = response.text
                
                # Try to parse the error message for more details
                error_details = {}
                try:
                    error_json = response.json()
                    error_details = {
                        "ok": error_json.get("ok"),
                        "error_code": error_json.get("error_code"),
                        "description": error_json.get("description")
                    }
                except Exception:
                    pass
                
                logger.error(LogEventType.ERROR, f"Failed to send media: API returned {response.status_code}", {
                    "status_code": response.status_code,
                    "error": error_msg[:200] if len(error_msg) > 200 else error_msg,
                    "media_type": media_type,
                    "method": method,
                    "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    **error_details
                })
                
                # Check for specific error types and try to recover
                if "IMAGE_PROCESS_FAILED" in error_msg and media_type == "image":
                    logger.warning(LogEventType.MEDIA, "IMAGE_PROCESS_FAILED error, retrying as document", {
                        "original_media_type": media_type
                    })
                    
                    # Retry as document
                    try:
                        with open(file_path, "rb") as file:
                            retry_response = await client.post(
                                f"{self.api_url}{self.token}/sendDocument",
                                files={"document": file},
                                data={"chat_id": chat_id, "caption": caption} if caption else {"chat_id": chat_id},
                                timeout=60.0
                            )
                            
                            if retry_response.status_code == 200:
                                logger.info(LogEventType.MEDIA, "Successfully sent media as document after retry")
                                return {"success": True, "result": retry_response.json().get("result")}
                    except Exception as e:
                        logger.error(LogEventType.ERROR, f"Error during fallback to document: {str(e)}")
                
                return {"success": False, "error": error_msg}
            
            result = response.json().get("result")
            logger.info(LogEventType.MEDIA, f"Successfully sent {media_type} media to Telegram", {
                "message_id": result.get("message_id"),
                "chat_id": result.get("chat", {}).get("id"),
                "media_type": media_type,
                "response": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            })
            return {"success": True, "result": result}
    
    async def send_buttons(
        self,
        chat_id: str,
        text: str,
        buttons: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Send a message with inline keyboard buttons to a Telegram chat"""
        from src.bot_manager.conversation_logger import get_logger, LogEventType
        
        # Get context for logging
        context = self._get_logger_context()
        
        # Create logger with clean context
        # Remove any legacy skip flags and platform key if present to avoid duplicates
        context = {k: v for k, v in context.items() if not k.startswith('skip_') and k != 'platform'}
        logger = get_logger(platform="telegram", **context)
        
        if not self.token:
            logger.error(LogEventType.ERROR, "Cannot send buttons: Adapter not initialized")
            return {"success": False, "error": "Adapter not initialized"}
        
        # Transform our generic button format to Telegram's inline keyboard format
        keyboard = []
        # Create rows of 2 buttons each
        for i in range(0, len(buttons), 2):
            row = []
            for button in buttons[i:i+2]:
                row.append({
                    "text": button.get("text", "Button"),
                    "callback_data": button.get("value", "")
                })
            keyboard.append(row)
        
        # Log all outgoing messages
        logger.info(LogEventType.OUTGOING, f"Sent: {text}", {
            "has_buttons": True, 
            "buttons": [btn.get("text", "Button") for btn in buttons], 
            "chat_id": chat_id
        })
        
        try:
            # Use a timeout of 30 seconds and configure retries
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.debug(LogEventType.ADAPTER, f"Sending buttons message to Telegram API", {
                    "chat_id": chat_id,
                    "button_count": len(buttons),
                    "text_length": len(text)
                })
                
                # Implement automatic retry for network issues
                max_retries = 2
                retry_delay = 1.0
                
                for retry in range(max_retries + 1):
                    try:
                        response = await client.post(
                            f"{self.api_url}{self.token}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": text,
                                "parse_mode": "HTML",
                                "reply_markup": {
                                    "inline_keyboard": keyboard
                                }
                            }
                        )
                        
                        # If we got here, the request succeeded
                        break
                    except httpx.ConnectTimeout:
                        if retry < max_retries:
                            # Log the retry attempt
                            logger.warning(LogEventType.ADAPTER, f"Connection timeout, retrying ({retry+1}/{max_retries})", {
                                "chat_id": chat_id,
                                "retry_count": retry + 1,
                                "max_retries": max_retries,
                                "retry_delay": retry_delay
                            })
                            # Wait before retrying
                            await asyncio.sleep(retry_delay)
                        else:
                            # We've exhausted our retries, re-raise the exception
                            raise
        except httpx.ConnectTimeout:
            logger.error(LogEventType.ERROR, "Connection timeout while sending buttons to Telegram API after retries", {
                "chat_id": chat_id,
                "text_length": len(text),
                "button_count": len(buttons),
                "timeout": "30 seconds",
                "max_retries": max_retries
            })
            # Return partial success to allow the conversation to continue
            return {"success": False, "error": "Connection timeout", "retry_recommended": True}
        except Exception as e:
            logger.error(LogEventType.ERROR, f"Error sending buttons message: {str(e)}", {
                "exception": str(e),
                "chat_id": chat_id
            })
            return {"success": False, "error": f"Exception: {str(e)}"}
            
        if response.status_code != 200:
            logger.error(LogEventType.ERROR, f"Failed to send buttons message: {response.status_code}", {
                "status_code": response.status_code,
                "error": response.text[:200] if len(response.text) > 200 else response.text
            })
            return {"success": False, "error": response.text}
        
        return {"success": True, "result": response.json().get("result")}
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """Set the webhook URL for receiving Telegram updates"""
        if not self.token:
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}{self.token}/setWebhook",
                json={"url": webhook_url}
            )
            
            if response.status_code != 200:
                return False
            
            result = response.json()
            return result.get("ok", False)
    
    async def delete_webhook(self) -> bool:
        """Delete the Telegram webhook"""
        if not self.token:
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_url}{self.token}/deleteWebhook")
            
            if response.status_code != 200:
                return False
            
            result = response.json()
            return result.get("ok", False)
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """Get information about the current Telegram webhook"""
        if not self.token:
            return {"success": False, "error": "Adapter not initialized"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_url}{self.token}/getWebhookInfo")
            
            if response.status_code != 200:
                return {"success": False, "error": response.text}
            
            return {"success": True, "result": response.json().get("result")}
    
    async def process_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Telegram update and transform it to a unified format
        """
        from src.bot_manager.conversation_logger import get_logger, LogEventType
        
        # Get context for logging
        context = self._get_logger_context()
        
        # Create logger with clean context
        # Remove any legacy skip flags and platform key if present to avoid duplicates
        context = {k: v for k, v in context.items() if not k.startswith('skip_') and k != 'platform'}
        logger = get_logger(platform="telegram", **context)
        
        # Extract message or callback query
        message = update_data.get("message")
        callback_query = update_data.get("callback_query")
        
        logger.debug(LogEventType.ADAPTER, "Processing Telegram update", {
            "update_type": "message" if message else "callback_query" if callback_query else "other",
            "has_message": message is not None,
            "has_callback_query": callback_query is not None
        })
        
        result = {
            "platform": "telegram",
            "timestamp": datetime.now().isoformat(),
            "raw_update": update_data
        }
        
        if message:
            # Process regular message
            chat_id = str(message.get("chat", {}).get("id"))
            user_id = str(message.get("from", {}).get("id"))
            text = message.get("text", "")
            
            result.update({
                "chat_id": chat_id,
                "user_id": user_id,
                "type": "message",
                "content": {
                    "type": "text",
                    "text": text
                }
            })
            
            # Check for media content
            for media_type in ["photo", "video", "audio", "document", "voice"]:
                if media_type in message:
                    media_content = message.get(media_type)
                    file_id = media_content[-1].get("file_id") if media_type == "photo" else media_content.get("file_id")
                    caption = message.get("caption", "")
                    
                    logger.info(LogEventType.MEDIA, f"Detected incoming {media_type} media in Telegram message", {
                        "media_type": media_type,
                        "file_id": file_id,
                        "has_caption": bool(caption),
                        "caption_length": len(caption) if caption else 0,
                        "caption_preview": caption[:50] + "..." if caption and len(caption) > 50 else caption,
                        "file_unique_id": media_content[-1].get("file_unique_id") if media_type == "photo" else media_content.get("file_unique_id", "unknown")
                    })
                    
                    result["content"] = {
                        "type": media_type,
                        "file_id": file_id,
                        "caption": caption
                    }
                    break
            
        elif callback_query:
            # Process button callback
            message = callback_query.get("message", {})
            chat_id = str(message.get("chat", {}).get("id"))
            user_id = str(callback_query.get("from", {}).get("id"))
            data = callback_query.get("data", "")
            
            result.update({
                "chat_id": chat_id,
                "user_id": user_id,
                "type": "callback",
                "content": {
                    "type": "button",
                    "value": data
                }
            })
        
        return result
    
    async def get_file_from_platform(self, file_id: str) -> Optional[bytes]:
        """Download a file from Telegram using its file_id"""
        if not self.token:
            return None
        
        # First, get file path on Telegram servers
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}{self.token}/getFile",
                params={"file_id": file_id}
            )
            
            if response.status_code != 200:
                return None
            
            file_path = response.json().get("result", {}).get("file_path")
            
            if not file_path:
                return None
            
            # Now download the file
            file_response = await client.get(f"{self.file_api_url}{self.token}/{file_path}")
            
            if file_response.status_code != 200:
                return None
            
            return file_response.content
    
    async def upload_file_to_platform(self, file_path: str) -> Optional[str]:
        """
        Upload a file to Telegram's servers
        Note: Telegram doesn't support direct file uploads to their servers,
        files are uploaded when sending messages. This method will attempt to
        send the file to a temporary chat and get the file_id.
        """
        
    async def send_media_with_buttons(
        self, 
        chat_id: str, 
        media_type: str, 
        file_path: str, 
        caption: Optional[str] = None,
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Send a media message with buttons using Telegram's inline keyboard
        
        Args:
            chat_id: The Telegram chat ID to send to
            media_type: Type of media (image, video, audio, document)
            file_path: Path or ID of the media file
            caption: Optional caption text for the media
            buttons: Optional list of button objects with text and value
            
        Returns:
            Dict with success status and response information
        """
        logger = self._get_logger()
        
        if not self.token:
            logger.error(LogEventType.ERROR, "Cannot send media with buttons: Adapter not initialized")
            return {"success": False, "error": "Adapter not initialized"}
        
        # Map media types to Telegram methods and file parameter names
        telegram_map = {
            "image": {"method": "sendPhoto", "file_param": "photo"},
            "video": {"method": "sendVideo", "file_param": "video"},
            "audio": {"method": "sendAudio", "file_param": "audio"},
            "document": {"method": "sendDocument", "file_param": "document"}
        }
        
        # Get the appropriate method and file parameter name for this media type
        media_info = telegram_map.get(media_type.lower(), {"method": "sendDocument", "file_param": "document"})
        method = media_info["method"]
        file_param = media_info["file_param"]
        
        # Create inline keyboard if buttons provided
        reply_markup = None
        if buttons and len(buttons) > 0:
            # Convert buttons to Telegram's inline keyboard format
            inline_keyboard = []
            row = []
            
            # Group buttons in rows of 2 (or configure as needed)
            for i, btn in enumerate(buttons):
                callback_data = btn.get("value", f"btn_{i}")
                if len(callback_data) > 64:  # Telegram limit
                    callback_data = callback_data[:60] + "..."
                    
                row.append({
                    "text": btn.get("text", "Button"),
                    "callback_data": callback_data
                })
                
                # Create a new row after every 2 buttons
                if (i + 1) % 2 == 0 or i == len(buttons) - 1:
                    inline_keyboard.append(row)
                    row = []
                    
            reply_markup = {"inline_keyboard": inline_keyboard}
        
        # Get the actual file path from file_id
        actual_file_path = await self._get_file_path_from_id(file_path)
        if not actual_file_path:
            logger.error(LogEventType.ERROR, f"Cannot send media with buttons: Unable to retrieve file for '{file_path}'")
            return {"success": False, "error": "File not found"}
            
        # Check if file exists
        if not os.path.exists(actual_file_path):
            logger.error(LogEventType.ERROR, f"Cannot send media with buttons: File not found at path '{actual_file_path}'")
            return {"success": False, "error": "File not found"}
        
        # Log the operation with detail
        logger.info(LogEventType.MEDIA, f"Sending {media_type} with buttons using {method}", {
            "chat_id": chat_id,
            "media_type": media_type,
            "button_count": len(buttons) if buttons else 0,
            "file_path": actual_file_path
        })
        
        # For Telegram, we need to send the file as multipart/form-data with reply_markup
        async with httpx.AsyncClient() as client:
            try:
                # Validate the image format if sending an image
                if media_type == "image":
                    import imghdr
                    detected_format = imghdr.what(actual_file_path)
                    
                    # If we can't detect a valid image format, switch to document
                    if not detected_format:
                        logger.warning(LogEventType.MEDIA, "File doesn't appear to be a valid image, sending as document")
                        media_type = "document"
                        media_info = telegram_map.get(media_type.lower(), {"method": "sendDocument", "file_param": "document"})
                        method = media_info["method"]
                        file_param = media_info["file_param"]
                
                with open(actual_file_path, "rb") as file:
                    # Create form data with the file, caption and reply markup
                    files = {file_param: file}
                    data = {"chat_id": chat_id}
                    
                    if caption:
                        data["caption"] = caption
                        # Allow HTML formatting in captions
                        data["parse_mode"] = "HTML"
                    
                    # Add reply markup for buttons
                    if reply_markup:
                        data["reply_markup"] = json.dumps(reply_markup)
                    
                    # Make the request to Telegram API
                    url = f"{self.api_url}{self.token}/{method}"
                    response = await client.post(url, data=data, files=files)
                    response_data = response.json()
                    
                    if response_data.get("ok", False):
                        result = response_data.get("result", {})
                        logger.info(LogEventType.MEDIA, f"Successfully sent {media_type} with buttons to Telegram", {
                            "message_id": result.get("message_id"),
                            "chat_id": chat_id,
                            "response_sample": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                        })
                        return {
                            "success": True,
                            "message_id": result.get("message_id"),
                            "response": result
                        }
                    else:
                        error_code = response_data.get("error_code")
                        error_description = response_data.get("description")
                        logger.error(LogEventType.ERROR, f"Failed to send media with buttons: {error_code}", {
                            "status_code": error_code,
                            "error": error_description
                        })
                        return {
                            "success": False,
                            "error": error_description,
                            "error_code": error_code
                        }
            except Exception as e:
                logger.error(LogEventType.ERROR, f"Exception sending media with buttons: {str(e)}", {
                    "exception_type": type(e).__name__,
                    "chat_id": chat_id,
                    "media_type": media_type,
                    "file_path": actual_file_path,
                    "file_exists": os.path.exists(actual_file_path) if actual_file_path else False,
                    "buttons_count": len(buttons) if buttons else 0,
                    "has_caption": bool(caption)
                }, exc_info=True)
                
                # Fallback: try simplified approach
                logger.info(LogEventType.MEDIA, "Attempting fallback: send media and buttons separately")
                try:
                    # Send media without buttons first
                    media_result = await self.send_media_message(chat_id, media_type, actual_file_path, caption)
                    if media_result.get("success"):
                        # Then send buttons as a separate message
                        if buttons:
                            button_result = await self.send_buttons(chat_id, "Choose an option:", buttons)
                            logger.info(LogEventType.MEDIA, "Fallback successful: sent media and buttons separately")
                            return {
                                "success": True,
                                "message_id": media_result.get("message_id"),
                                "fallback_used": True
                            }
                        return media_result
                except Exception as fallback_error:
                    logger.error(LogEventType.ERROR, f"Fallback also failed: {str(fallback_error)}")
                    
                return {"success": False, "error": str(e)}
    async def send_media_group(
        self,
        chat_id: str,
        media_items: List[Dict[str, Any]],
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send multiple media items as a group using Telegram's sendMediaGroup API
        
        Args:
            chat_id: The Telegram chat ID to send to
            media_items: List of media item objects with type and file_id
            caption: Optional caption text for the media group
            
        Returns:
            Dict with success status and response information
        """
        logger = self._get_logger()
        
        if not self.token:
            logger.error(LogEventType.ERROR, "Cannot send media group: Adapter not initialized")
            return {"success": False, "error": "Adapter not initialized"}
        
        if not media_items or len(media_items) == 0:
            logger.error(LogEventType.ERROR, "Cannot send media group: No media items provided")
            return {"success": False, "error": "No media items provided"}
        
        # Telegram requires at least 2 items for a media group, but allows max 10
        if len(media_items) < 2:
            logger.warning(LogEventType.MEDIA, "Only one media item provided for media group, using single media send instead")
            # Get the single item
            item = media_items[0]
            # Extract type and file_id
            media_type = item.get("type", "image") if isinstance(item, dict) else getattr(item, "type", "image")
            file_id = item.get("file_id", "") if isinstance(item, dict) else getattr(item, "file_id", "")
            # Get file path
            file_path = await self._get_file_path_from_id(file_id)
            if not file_path:
                return {"success": False, "error": f"Could not retrieve file for id: {file_id}"}
            # Send as single media
            return await self.send_media_message(chat_id, media_type, file_path, caption)
        
        if len(media_items) > 10:
            logger.warning(LogEventType.MEDIA, "More than 10 media items provided, only first 10 will be sent")
            media_items = media_items[:10]
        
        # Log the operation
        logger.info(LogEventType.MEDIA, f"Preparing to send media group with {len(media_items)} items", {
            "chat_id": chat_id,
            "media_count": len(media_items),
            "has_caption": bool(caption),
            "caption_length": len(caption) if caption else 0
        })
        
        # Convert our media items to Telegram's InputMedia format
        input_media = []
        files = {}
        
        for i, item in enumerate(media_items):
            # Handle both dict and object formats
            if isinstance(item, dict):
                media_type = item.get("type", "image").lower()
                file_id = item.get("file_id", "")
                description = item.get("description", "")
            else:
                media_type = getattr(item, "type", "image").lower()
                file_id = getattr(item, "file_id", "")
                description = getattr(item, "description", "")
            
            # Map to Telegram's media type
            if media_type == "image":
                input_type = "photo"
            elif media_type in ["video", "audio", "document"]:
                input_type = media_type
            else:
                input_type = "document"  # Default fallback
            
            # Get file path from ID
            file_path = await self._get_file_path_from_id(file_id)
            if not file_path:
                logger.warning(LogEventType.MEDIA, f"Could not retrieve file for id: {file_id}, skipping")
                continue
            
            # Only the first media item can have a caption in Telegram
            item_caption = caption if i == 0 else None
            
            # Create unique key for this file in the request
            file_key = f"file_{i}"
            
            # Add to input media array
            media_item = {
                "type": input_type,
                "media": f"attach://{file_key}",
                "caption": item_caption,
                "parse_mode": "HTML" if item_caption else None
            }
            
            # Add optional description as caption if no main caption provided
            if not item_caption and description:
                media_item["caption"] = description
                media_item["parse_mode"] = "HTML"
            
            input_media.append(media_item)
            
            # Add file to files dict with unique key
            try:
                files[file_key] = open(file_path, "rb")
            except Exception as e:
                logger.error(LogEventType.ERROR, f"Failed to open file {file_path}: {str(e)}")
                # Clean up already opened files
                for f in files.values():
                    f.close()
                return {"success": False, "error": f"Failed to open media file: {str(e)}"}
        
        # If we couldn't process any media items, return error
        if not input_media:
            logger.error(LogEventType.ERROR, "No valid media items to send")
            return {"success": False, "error": "No valid media items to send"}
        
        try:
            # Prepare API request
            url = f"{self.api_url}{self.token}/sendMediaGroup"
            data = {
                "chat_id": chat_id,
                "media": json.dumps(input_media)
            }
            
            # Send the request
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, files=files)
                response_data = response.json()
                
                # Clean up files
                for f in files.values():
                    f.close()
                
                # Check response
                if response_data.get("ok", False):
                    result = response_data.get("result", [])
                    message_ids = [msg.get("message_id") for msg in result]
                    
                    logger.info(LogEventType.MEDIA, f"Successfully sent media group with {len(message_ids)} items", {
                        "message_ids": message_ids,
                        "chat_id": chat_id
                    })
                    
                    return {
                        "success": True,
                        "message_ids": message_ids,
                        "response": result
                    }
                else:
                    error_code = response_data.get("error_code")
                    error_description = response_data.get("description")
                    
                    logger.error(LogEventType.ERROR, f"Failed to send media group: {error_code}", {
                        "status_code": error_code,
                        "error": error_description
                    })
                    
                    return {
                        "success": False,
                        "error": error_description,
                        "error_code": error_code
                    }
        
        except Exception as e:
            # Clean up files on exception
            for f in files.values():
                try:
                    f.close()
                except:
                    pass
            
            logger.error(LogEventType.ERROR, f"Exception sending media group: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_file_path_from_id(self, file_id: str) -> Optional[str]:
        """Helper method to get a file path from a media ID
        
        Args:
            file_id: The media file ID to retrieve
            
        Returns:
            Path to the local temporary file if successful, None otherwise
        """
        logger = self._get_logger()
        
        # Validate input
        if not file_id:
            logger.error(LogEventType.ERROR, "Cannot retrieve file: Empty file_id provided")
            return None
        
        # Check if file_id is a valid path already
        if os.path.exists(file_id) and os.path.isfile(file_id):
            logger.debug(LogEventType.MEDIA, f"File already exists at path: {file_id}")
            return file_id
        
        # Construct API URL to get media by file_id
        api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        media_url = f"{api_base_url}/v1/api/media/{file_id}/content"
        
        logger.info(LogEventType.MEDIA, f"Retrieving media from API: {media_url}", {
            "url": media_url,
            "file_id": file_id
        })
        
        # Fetch the media file with timeout and retry logic
        max_retries = 2
        retry_count = 0
        last_error = None
        
        while retry_count <= max_retries:
            try:
                # Track timing for performance monitoring
                start_time = datetime.now()
                
                async with httpx.AsyncClient(timeout=20.0) as client:
                    response = await client.get(media_url)
                    
                    # Calculate download time
                    download_time = (datetime.now() - start_time).total_seconds() * 1000  # ms
                    
                    if response.status_code == 200:
                        # Determine proper file extension based on content type
                        content_type = response.headers.get("content-type", "")
                        ext = self._get_extension_for_content_type(content_type)
                        content_length = len(response.content)
                        
                        # Log download metrics
                        logger.debug(LogEventType.MEDIA, f"Downloaded {content_length} bytes in {download_time:.2f}ms", {
                            "content_type": content_type,
                            "content_length": content_length,
                            "download_time_ms": download_time,
                            "download_speed_kbps": (content_length / 1024) / (download_time / 1000) if download_time > 0 else 0
                        })
                        
                        # Save to temporary file with proper extension
                        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                            tmp.write(response.content)
                            tmp_path = tmp.name
                        
                        logger.info(LogEventType.MEDIA, f"Saved media to temporary file with extension {ext}", {
                            "content_type": content_type,
                            "extension": ext,
                            "file_size": content_length,
                            "file_id": file_id,
                            "temp_path": tmp_path
                        })
                        
                        return tmp_path
                    else:
                        error_message = f"Failed to retrieve media file: Status {response.status_code}"
                        last_error = error_message
                        
                        # For certain status codes, retrying won't help
                        if response.status_code in [400, 404, 403]:
                            logger.error(LogEventType.MEDIA, error_message, {
                                "status_code": response.status_code,
                                "response": response.text[:200],
                                "file_id": file_id
                            })
                            return None
                        
                        # For other status codes, we might retry
                        if retry_count < max_retries:
                            retry_count += 1
                            retry_delay = retry_count * 1.5  # Exponential backoff
                            logger.warning(LogEventType.MEDIA, f"Retrying media download after error ({retry_count}/{max_retries})", {
                                "status_code": response.status_code,
                                "retry_count": retry_count,
                                "retry_delay": retry_delay,
                                "file_id": file_id
                            })
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            logger.error(LogEventType.MEDIA, f"Failed to retrieve media after {max_retries} retries", {
                                "status_code": response.status_code,
                                "response": response.text[:200],
                                "file_id": file_id,
                                "max_retries": max_retries
                            })
                            return None
            except httpx.TimeoutException:
                last_error = "Connection timeout"  
                if retry_count < max_retries:
                    retry_count += 1
                    retry_delay = retry_count * 1.5  # Exponential backoff
                    logger.warning(LogEventType.MEDIA, f"Timeout retrieving media, retrying ({retry_count}/{max_retries})", {
                        "error": "Connection timeout",
                        "retry_count": retry_count,
                        "retry_delay": retry_delay,
                        "file_id": file_id
                    })
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.error(LogEventType.ERROR, f"Timeout retrieving media after {max_retries} retries", {
                        "error": "Connection timeout",
                        "file_id": file_id,
                        "max_retries": max_retries
                    })
                    return None
            except Exception as e:
                last_error = str(e)
                logger.error(LogEventType.ERROR, f"Error retrieving media file: {str(e)}", {
                    "exception": str(e),
                    "exception_type": type(e).__name__,
                    "file_id": file_id,
                    "retry_count": retry_count
                })
                
                # Only retry on certain errors
                if retry_count < max_retries and isinstance(e, (httpx.NetworkError, httpx.ConnectError)):
                    retry_count += 1
                    retry_delay = retry_count * 1.5  # Exponential backoff
                    logger.warning(LogEventType.MEDIA, f"Network error retrieving media, retrying ({retry_count}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    return None
        
        # If we got here, all retries failed
        logger.error(LogEventType.ERROR, f"All attempts to retrieve media failed: {last_error}")
        return None
        if not self.token or not self.bot_info:
            return None
        
        # This is a workaround since Telegram doesn't have a dedicated upload API
        # We send the file to ourselves (the bot's private chat) to get the file_id
        bot_id = self.bot_info.get("id")
        
        if not bot_id:
            return None
        
        # Determine the file type
        file_extension = os.path.splitext(file_path)[1].lower()
        method = "sendDocument"  # Default
        
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            method = "sendPhoto"
            file_key = "photo"
        elif file_extension in ['.mp4', '.mov', '.avi']:
            method = "sendVideo"
            file_key = "video"
        elif file_extension in ['.mp3', '.ogg', '.wav']:
            method = "sendAudio"
            file_key = "audio"
        else:
            file_key = "document"
        
        async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout for uploads
            with open(file_path, "rb") as file:
                response = await client.post(
                    f"{self.api_url}{self.token}/{method}",
                    files={file_key: file},
                    data={"chat_id": bot_id}
                )
                
                if response.status_code != 200:
                    return None
                
                result = response.json().get("result")
                
                if not result:
                    return None
                
                # Extract file_id based on the file type
                if method == "sendPhoto":
                    # Photos come in multiple sizes, get the largest one
                    return result.get("photo", [{}])[-1].get("file_id")
                else:
                    # Other file types have the file_id directly in the result
                    file_obj = result.get(file_key.lower())
                    return file_obj.get("file_id") if file_obj else None