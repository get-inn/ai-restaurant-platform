from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from uuid import UUID


class PlatformAdapter(ABC):
    """
    Base abstract class for all messaging platform adapters.
    Each specific platform (Telegram, WhatsApp, etc.) should implement this interface.
    """
    
    def set_context(self, **kwargs):
        """
        Set context information for logging
        
        Args:
            **kwargs: Context key-value pairs like bot_id, dialog_id, etc.
        """
        # Store context in instance variables for logging
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, f"_context_{key}", value)
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the name of the platform (e.g., 'telegram', 'whatsapp')"""
        pass
    
    @abstractmethod
    async def initialize(self, credentials: Dict[str, Any]) -> bool:
        """
        Initialize the adapter with platform-specific credentials
        Returns True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def send_text_message(self, chat_id: str, text: str) -> Dict[str, Any]:
        """
        Send a text message to a chat
        Returns platform-specific response data
        """
        pass
    
    @abstractmethod
    async def send_media_message(
        self, 
        chat_id: str, 
        media_type: str, 
        file_path: str, 
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a media message (image, video, audio, etc.) to a chat
        Returns platform-specific response data
        """
        pass
    
    @abstractmethod
    async def send_buttons(
        self,
        chat_id: str,
        text: str,
        buttons: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Send a message with buttons to a chat
        Returns platform-specific response data
        """
        pass
    
    @abstractmethod
    async def set_webhook(self, webhook_url: str) -> bool:
        """
        Set or update the webhook URL for receiving updates
        Returns True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_webhook(self) -> bool:
        """
        Delete the webhook
        Returns True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_webhook_info(self) -> Dict[str, Any]:
        """
        Get information about the current webhook
        Returns platform-specific webhook information
        """
        pass
    
    @abstractmethod
    async def process_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an update received from the platform
        Transforms platform-specific format to a unified format
        Returns a standardized update object with user message/action details
        """
        pass
    
    @abstractmethod
    async def get_file_from_platform(self, file_id: str) -> Optional[bytes]:
        """
        Download a file from the platform using its file_id
        Returns the file content as bytes if successful, None otherwise
        """
        pass
    
    @abstractmethod
    async def upload_file_to_platform(self, file_path: str) -> Optional[str]:
        """
        Upload a file to the platform's servers
        Returns the platform-specific file_id if successful, None otherwise
        """
        pass