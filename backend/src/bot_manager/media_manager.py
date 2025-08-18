"""
Media Manager for bot dialog system.
Handles all media processing, validation, and sending logic.

Extracted from DialogManager to improve maintainability and separation of concerns.
"""
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple
import logging

from src.bot_manager.conversation_logger import ConversationLogger
from src.integrations.platforms.base import PlatformAdapter


class MediaManager:
    """
    Handles media processing and sending for bot conversations.
    Manages text, media items, buttons, and media groups.
    """
    
    def __init__(self, logger: ConversationLogger):
        """
        Initialize MediaManager.
        
        Args:
            logger: Conversation logger instance
        """
        self.logger = logger

    def extract_message_content(self, message: Union[str, Dict[str, Any], Any]) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Extract text and media content from different message formats.
        
        Args:
            message: Message content (str, DialogMessage, or dict)
            
        Returns:
            Tuple of (text_content, media_items)
        """
        text_content = None
        media_items = []
        
        if isinstance(message, str):
            text_content = message
        elif hasattr(message, 'text'):
            text_content = message.text
            if hasattr(message, 'media') and message.media:
                media_items = message.media if isinstance(message.media, list) else [message.media]
        elif isinstance(message, dict):
            text_content = message.get('text')
            media = message.get('media')
            if media:
                media_items = media if isinstance(media, list) else [media]
        
        return text_content, media_items
    
    def validate_media_items(self, media_items: List[Union[Dict[str, Any], Any]]) -> bool:
        """
        Validate media items for required attributes.
        
        Args:
            media_items: List of media items to validate (dicts or Pydantic objects)
            
        Returns:
            True if all media items are valid
        """
        if not media_items:
            return True
            
        for item in media_items:
            # Handle both dict and Pydantic object formats
            if isinstance(item, dict):
                media_type = item.get('type')
                file_id = item.get('file_id')
            else:
                # Pydantic object or similar
                media_type = getattr(item, 'type', None)
                file_id = getattr(item, 'file_id', None)
                
            if not media_type:
                self.logger.error("MEDIA_VALIDATION", f"Media item missing 'type': {item}")
                return False
                
            if media_type not in ['photo', 'video', 'audio', 'document', 'animation', 'image']:
                self.logger.error("MEDIA_VALIDATION", f"Invalid media type: {media_type}")
                return False
                
            if not file_id:
                self.logger.error("MEDIA_VALIDATION", f"Media item missing 'file_id': {item}")
                return False
        
        return True
    
    def log_media_content(self, media_items: List[Union[Dict[str, Any], Any]]) -> None:
        """
        Log detailed media content information.
        
        Args:
            media_items: List of media items to log (dicts or Pydantic objects)
        """
        if not media_items:
            return
            
        try:
            media_summary = []
            for item in media_items:
                # Handle both dict and Pydantic object formats
                if isinstance(item, dict):
                    media_type = item.get('type', 'unknown')
                    file_id = item.get('file_id', 'no_id')
                    caption = item.get('caption', '')
                else:
                    # Pydantic object or similar
                    media_type = getattr(item, 'type', 'unknown')
                    file_id = getattr(item, 'file_id', 'no_id')
                    caption = getattr(item, 'caption', '')
                
                file_id_preview = file_id[:20] + "..." if len(str(file_id)) > 20 else str(file_id)
                caption_preview = caption[:50] + "..." if len(caption) > 50 else caption
                
                media_summary.append({
                    'type': media_type,
                    'file_id_preview': file_id_preview,
                    'has_caption': bool(caption),
                    'caption_preview': caption_preview
                })
            
            self.logger.media_processing(
                "Media content details",
                "MEDIA_CONTENT_LOG",
                {
                    'media_count': len(media_items),
                    'media_items': media_summary
                }
            )
        except Exception as e:
            self.logger.error("MEDIA_CONTENT_LOG", f"Error logging media content: {str(e)}", exc_info=True)
    
    def log_media_scenario(
        self, 
        text_content: Optional[str], 
        media_items: List[Union[Dict[str, Any], Any]], 
        buttons: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Log comprehensive media scenario information.
        
        Args:
            text_content: Text content of the message
            media_items: List of media items (dicts or Pydantic objects)
            buttons: Optional list of buttons
        """
        try:
            scenario_data = {
                'has_text': bool(text_content),
                'text_length': len(text_content) if text_content else 0,
                'media_count': len(media_items),
                'has_buttons': bool(buttons),
                'button_count': len(buttons) if buttons else 0
            }
            
            if text_content:
                scenario_data['text_preview'] = text_content[:100] + "..." if len(text_content) > 100 else text_content
            
            if media_items:
                media_types = []
                for item in media_items:
                    if isinstance(item, dict):
                        media_types.append(item.get('type', 'unknown'))
                    else:
                        media_types.append(getattr(item, 'type', 'unknown'))
                scenario_data['media_types'] = media_types
            
            self.logger.info("MEDIA_SCENARIO", "Message composition analysis", scenario_data)
        except Exception as e:
            self.logger.error("MEDIA_SCENARIO", f"Error logging media scenario: {str(e)}", exc_info=True)
    
    def extract_media_info(self, media_item: Union[Dict[str, Any], Any]) -> Tuple[str, str]:
        """
        Extract media type and file_id from media item.
        
        Args:
            media_item: Media item (dict or Pydantic object)
            
        Returns:
            Tuple of (media_type, file_id)
        """
        if isinstance(media_item, dict):
            media_type = media_item.get('type', 'unknown')
            file_id = media_item.get('file_id', '')
        else:
            # Pydantic object or similar
            media_type = getattr(media_item, 'type', 'unknown')
            file_id = getattr(media_item, 'file_id', '')
        
        return media_type, file_id
    
    async def send_text_only_message(
        self,
        adapter: PlatformAdapter,
        platform_chat_id: str,
        text_content: str,
        buttons: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send text-only message without media.
        
        Args:
            adapter: Platform adapter
            platform_chat_id: Chat ID for the platform
            text_content: Text to send
            buttons: Optional buttons
            
        Returns:
            Send result
        """
        try:
            self.logger.info("TEXT_SEND", f"Sending text-only message", {
                'text_length': len(text_content),
                'has_buttons': bool(buttons)
            })
            
            if buttons:
                result = await adapter.send_buttons(
                    platform_chat_id,
                    text_content,
                    buttons
                )
            else:
                result = await adapter.send_text_message(
                    platform_chat_id, 
                    text_content
                )
            
            self.logger.info("TEXT_SEND", "Text message sent successfully", {
                'result_type': type(result).__name__
            })
            
            return result
        except Exception as e:
            self.logger.error("TEXT_SEND", f"Error sending text message: {str(e)}", exc_info=True)
            raise
    
    async def send_media_without_buttons(
        self,
        adapter: PlatformAdapter,
        platform_chat_id: str,
        media_type: str,
        file_id: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send single media item without buttons.
        
        Args:
            adapter: Platform adapter
            platform_chat_id: Chat ID for the platform
            media_type: Type of media
            file_id: File ID
            caption: Optional caption
            
        Returns:
            Send result
        """
        try:
            self.logger.info("MEDIA_SEND", f"Sending {media_type} without buttons", {
                'file_id_preview': file_id[:20] + "..." if len(file_id) > 20 else file_id,
                'has_caption': bool(caption)
            })
            
            result = await adapter.send_media_message(
                platform_chat_id,
                media_type,
                file_id,
                caption=caption
            )
            
            self.logger.info("MEDIA_SEND", f"{media_type.capitalize()} sent successfully")
            return result
        except Exception as e:
            self.logger.error("MEDIA_SEND", f"Error sending {media_type}: {str(e)}", exc_info=True)
            raise
    
    async def send_media_with_buttons(
        self,
        adapter: PlatformAdapter,
        platform_chat_id: str,
        media_type: str,
        file_id: str,
        buttons: List[Dict[str, Any]],
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send single media item with buttons.
        
        Args:
            adapter: Platform adapter
            platform_chat_id: Chat ID for the platform
            media_type: Type of media
            file_id: File ID
            buttons: Buttons to include
            caption: Optional caption
            
        Returns:
            Send result
        """
        try:
            self.logger.info("MEDIA_SEND", f"Sending {media_type} with buttons", {
                'file_id_preview': file_id[:20] + "..." if len(file_id) > 20 else file_id,
                'button_count': len(buttons),
                'has_caption': bool(caption)
            })
            
            result = await adapter.send_media_with_buttons(
                platform_chat_id,
                media_type,
                file_id,
                caption=caption,
                buttons=buttons
            )
            
            self.logger.info("MEDIA_SEND", f"{media_type.capitalize()} with buttons sent successfully")
            return result
        except Exception as e:
            self.logger.error("MEDIA_SEND", f"Error sending {media_type} with buttons: {str(e)}", exc_info=True)
            raise
    
    async def send_single_media_item(
        self,
        adapter: PlatformAdapter,
        platform_chat_id: str,
        media_item: Dict[str, Any],
        buttons: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a single media item with optional buttons.
        
        Args:
            adapter: Platform adapter
            platform_chat_id: Chat ID for the platform
            media_item: Media item to send
            buttons: Optional buttons
            
        Returns:
            Send result
        """
        media_type, file_id = self.extract_media_info(media_item)
        # Handle both dict and Pydantic object formats
        if isinstance(media_item, dict):
            caption = media_item.get('caption')
        else:
            caption = getattr(media_item, 'caption', None)
        
        if buttons:
            return await self.send_media_with_buttons(
                adapter, platform_chat_id, media_type, file_id, buttons, caption
            )
        else:
            return await self.send_media_without_buttons(
                adapter, platform_chat_id, media_type, file_id, caption
            )
    
    async def send_follow_up_buttons(
        self,
        adapter: PlatformAdapter,
        platform_chat_id: str,
        buttons: List[Dict[str, Any]],
        follow_up_text: str = "Please choose an option:"
    ) -> Dict[str, Any]:
        """
        Send buttons as a follow-up message after media group.
        
        Args:
            adapter: Platform adapter
            platform_chat_id: Chat ID for the platform
            buttons: Buttons to send
            follow_up_text: Text to accompany buttons
            
        Returns:
            Send result
        """
        try:
            self.logger.info("BUTTON_FOLLOWUP", "Sending follow-up buttons after media group", {
                'button_count': len(buttons),
                'follow_up_text': follow_up_text
            })
            
            # Small delay to ensure media group completes first
            await asyncio.sleep(0.1)
            
            result = await adapter.send_buttons(
                platform_chat_id,
                follow_up_text,
                buttons
            )
            
            if result.get("success", True):
                self.logger.info("BUTTON_FOLLOWUP", "Follow-up buttons sent successfully")
            else:
                self.logger.error("BUTTON_FOLLOWUP", f"Failed to send follow-up buttons: {result.get('error', 'Unknown error')}")
            
            return result
        except Exception as e:
            self.logger.error("BUTTON_FOLLOWUP", f"Error sending follow-up buttons: {str(e)}", exc_info=True)
            raise
    
    async def send_media_group(
        self,
        adapter: PlatformAdapter,
        platform_chat_id: str,
        media_items: List[Dict[str, Any]],
        buttons: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Send multiple media items as a group.
        
        Args:
            adapter: Platform adapter
            platform_chat_id: Chat ID for the platform
            media_items: List of media items to send
            buttons: Optional buttons (sent as follow-up if present)
            
        Returns:
            List of send results
        """
        if not self.validate_media_items(media_items):
            raise ValueError("Invalid media items provided")
        
        try:
            self.logger.info("MEDIA_GROUP", f"Sending media group", {
                'media_count': len(media_items),
                'has_buttons': bool(buttons)
            })
            
            results = []
            
            # Check if platform supports media groups
            if hasattr(adapter, 'send_media_group') and len(media_items) > 1:
                # Send as media group
                group_result = await adapter.send_media_group(platform_chat_id, media_items)
                results.append(group_result)
                
                # Send buttons as follow-up if present
                if buttons:
                    button_result = await self.send_follow_up_buttons(
                        adapter, platform_chat_id, buttons, "👆"
                    )
                    results.append(button_result)
            else:
                # Send media items individually
                for i, media_item in enumerate(media_items):
                    # Only include buttons with the last media item
                    item_buttons = buttons if i == len(media_items) - 1 else None
                    
                    result = await self.send_single_media_item(
                        adapter, platform_chat_id, media_item, item_buttons
                    )
                    results.append(result)
                    
                    # Small delay between individual media items
                    if i < len(media_items) - 1:
                        await asyncio.sleep(0.1)
            
            self.logger.info("MEDIA_GROUP", "Media group sent successfully", {
                'results_count': len(results)
            })
            
            return results
        except Exception as e:
            self.logger.error("MEDIA_GROUP", f"Error sending media group: {str(e)}", exc_info=True)
            raise
    
    async def process_message_sending(
        self,
        adapter: PlatformAdapter,
        platform_chat_id: str,
        message: Union[str, Dict[str, Any], Any],
        buttons: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing and sending messages with media.
        
        Args:
            adapter: Platform adapter
            platform_chat_id: Chat ID for the platform
            message: Message content (str, DialogMessage, or dict)
            buttons: Optional buttons
            
        Returns:
            Send result or results
        """
        try:
            # Extract content
            text_content, media_items = self.extract_message_content(message)
            
            # Log scenario
            self.log_media_scenario(text_content, media_items, buttons)
            self.log_media_content(media_items)
            
            # Determine sending strategy
            if not media_items:
                # Text-only message
                if not text_content:
                    raise ValueError("No content to send (neither text nor media)")
                
                return await self.send_text_only_message(
                    adapter, platform_chat_id, text_content, buttons
                )
            
            elif len(media_items) == 1:
                # Single media item
                media_item = media_items[0]
                
                # Add text as caption if present
                if isinstance(media_item, dict):
                    if text_content and not media_item.get('caption'):
                        media_item['caption'] = text_content
                else:
                    # For Pydantic objects, we can't modify the caption directly
                    # The caption should be handled at the adapter level if needed
                    pass
                
                return await self.send_single_media_item(
                    adapter, platform_chat_id, media_item, buttons
                )
            
            else:
                # Multiple media items - send text first, then media group, then buttons
                results = []
                
                # Send text first if present
                if text_content:
                    text_result = await self.send_text_only_message(
                        adapter, platform_chat_id, text_content
                    )
                    results.append(text_result)
                
                # Then send media group without buttons (buttons will be sent separately after)
                media_results = await self.send_media_group(
                    adapter, platform_chat_id, media_items, None
                )
                if isinstance(media_results, list):
                    results.extend(media_results)
                else:
                    results.append(media_results)
                
                # Finally send buttons separately if present
                if buttons:
                    button_result = await self.send_follow_up_buttons(
                        adapter, platform_chat_id, buttons, "👆"
                    )
                    results.append(button_result)
                
                return {
                    'type': 'media_group',
                    'results': results,
                    'count': len(results)
                }
        
        except Exception as e:
            self.logger.error("MEDIA_PROCESSING", f"Error in media processing: {str(e)}", exc_info=True)
            raise