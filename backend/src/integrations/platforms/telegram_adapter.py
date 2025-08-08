from typing import Dict, Any, List, Optional
import httpx
import json
import os
from datetime import datetime
from uuid import UUID

from src.integrations.platforms.base import PlatformAdapter


class TelegramAdapter(PlatformAdapter):
    """
    Telegram Bot API implementation of the PlatformAdapter
    """
    
    def __init__(self):
        self.api_url = "https://api.telegram.org/bot"
        self.file_api_url = "https://api.telegram.org/file/bot"
        self.token = None
        self.bot_info = None
    
    @property
    def platform_name(self) -> str:
        return "telegram"
    
    async def initialize(self, credentials: Dict[str, Any]) -> bool:
        """Initialize the adapter with Telegram bot token"""
        from src.bot_manager.conversation_logger import get_logger, LogEventType
        logger = get_logger(platform="telegram")
        
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
        logger = get_logger(platform="telegram")
        
        if not self.token:
            logger.error(LogEventType.ERROR, "Cannot send text message: Adapter not initialized")
            return {"success": False, "error": "Adapter not initialized"}
        
        try:
            # Configure httpx with increased timeout and retry settings
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.debug(LogEventType.ADAPTER, f"Sending text message to chat {chat_id}", {
                    "text_length": len(text),
                    "chat_id": chat_id
                })
                
                response = await client.post(
                    f"{self.api_url}{self.token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML"  # Support HTML formatting
                    }
                )
                
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
            logger.error(LogEventType.ERROR, "Connection timeout while sending text message to Telegram API", {
                "chat_id": chat_id,
                "text_length": len(text)
            })
            return {"success": False, "error": "Connection timeout"}
            
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
        # Use self.logger to maintain proper context
        logger = get_logger(platform="telegram")
        
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
        if not self.token:
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
        
        async with httpx.AsyncClient() as client:
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
            
            if response.status_code != 200:
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
        logger = get_logger(platform="telegram")
        
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