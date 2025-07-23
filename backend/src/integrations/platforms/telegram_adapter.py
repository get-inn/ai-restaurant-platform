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
        if "token" not in credentials:
            return False
        
        self.token = credentials["token"]
        
        # Test the token by getting bot information
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_url}{self.token}/getMe")
            
            if response.status_code != 200:
                return False
            
            self.bot_info = response.json().get("result")
            return True
    
    async def send_text_message(self, chat_id: str, text: str) -> Dict[str, Any]:
        """Send a text message to a Telegram chat"""
        if not self.token:
            return {"success": False, "error": "Adapter not initialized"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}{self.token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"  # Support HTML formatting
                }
            )
            
            if response.status_code != 200:
                return {"success": False, "error": response.text}
            
            return {"success": True, "result": response.json().get("result")}
    
    async def send_media_message(
        self, 
        chat_id: str, 
        media_type: str, 
        file_path: str, 
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a media message to a Telegram chat"""
        if not self.token:
            return {"success": False, "error": "Adapter not initialized"}
        
        # Map media types to Telegram methods
        method_map = {
            "image": "sendPhoto",
            "video": "sendVideo",
            "audio": "sendAudio",
            "document": "sendDocument"
        }
        
        # Get the appropriate method or default to sendDocument
        method = method_map.get(media_type.lower(), "sendDocument")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {"success": False, "error": "File not found"}
        
        # For Telegram, we need to send the file as multipart/form-data
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as file:
                # Create form data with the file and optional caption
                files = {media_type: file}
                data = {"chat_id": chat_id}
                
                if caption:
                    data["caption"] = caption
                
                response = await client.post(
                    f"{self.api_url}{self.token}/{method}",
                    files=files,
                    data=data
                )
                
                if response.status_code != 200:
                    return {"success": False, "error": response.text}
                
                return {"success": True, "result": response.json().get("result")}
    
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
        # Extract message or callback query
        message = update_data.get("message")
        callback_query = update_data.get("callback_query")
        
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
                    result["content"] = {
                        "type": media_type,
                        "file_id": media_content[-1].get("file_id") if media_type == "photo" else media_content.get("file_id"),
                        "caption": message.get("caption", "")
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
        
        async with httpx.AsyncClient() as client:
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