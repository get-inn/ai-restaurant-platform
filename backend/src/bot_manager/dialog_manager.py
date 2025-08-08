"""
Dialog Manager for Bot Management System

This module is responsible for:
1. Managing dialog state and flow
2. Processing user inputs according to scenarios
3. Generating appropriate responses
4. Coordinating with platform adapters for message delivery
5. Logging detailed conversation flows for debugging
"""

from typing import Dict, Any, List, Optional, Union
from uuid import UUID
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.services.bots.dialog_service import DialogService
from src.api.services.bots.scenario_service import ScenarioService
from src.api.services.bots.instance_service import InstanceService
from src.api.schemas.bots.dialog_schemas import (
    BotDialogStateCreate, 
    BotDialogStateUpdate,
    DialogMessage,
    DialogButtonOption,
    DialogResponse
)
from src.bot_manager.scenario_processor import ScenarioProcessor
from src.bot_manager.state_repository import StateRepository
from src.bot_manager.conversation_logger import get_logger, LogEventType
from src.integrations.platforms.base import PlatformAdapter


class DialogManager:
    """
    Main dialog management component for handling bot conversations.
    Coordinates between scenario processing, state management and platform adapters.
    """

    def __init__(
        self, 
        db: AsyncSession,
        platform_adapters: Dict[str, PlatformAdapter] = None,
        state_repository: StateRepository = None,
        scenario_processor: ScenarioProcessor = None
    ):
        """
        Initialize the dialog manager.
        
        Args:
            db: Database session
            platform_adapters: Dict mapping platform names to adapter instances
            state_repository: Optional custom state repository
            scenario_processor: Optional custom scenario processor
        """
        self.db = db
        self.platform_adapters = platform_adapters or {}
        self.state_repository = state_repository or StateRepository(db)
        self.scenario_processor = scenario_processor or ScenarioProcessor()
        self.logger = get_logger()
        
    async def register_platform_adapter(self, platform: str, adapter: PlatformAdapter) -> bool:
        """Register a platform adapter"""
        if platform in self.platform_adapters:
            self.logger.warning(LogEventType.ADAPTER, f"Overwriting existing adapter for platform {platform}")
        
        self.platform_adapters[platform] = adapter
        self.logger.info(LogEventType.ADAPTER, f"Platform adapter registered for {platform}")
        return True
        
    async def get_platform_adapter(self, platform: str) -> Optional[PlatformAdapter]:
        """Get the adapter for a specific platform"""
        return self.platform_adapters.get(platform)
        
    async def process_incoming_message(
        self,
        bot_id: UUID, 
        platform: str,
        platform_chat_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process an incoming message from a platform webhook.
        
        Args:
            bot_id: ID of the bot receiving the message
            platform: Platform identifier (telegram, whatsapp, etc.)
            platform_chat_id: Chat ID in the platform
            update_data: Raw update data from the platform
            
        Returns:
            Response information or None if no response is required
        """
        # Set up conversation context for logging
        conversation_context = {
            "bot_id": str(bot_id),
            "platform": platform,
            "platform_chat_id": platform_chat_id
        }
        self.logger.set_context(**conversation_context)
        
        # Log the incoming webhook
        self.logger.webhook_received(platform, {
            "update_data_sample": str(update_data)[:200] + "..." if len(str(update_data)) > 200 else str(update_data),
            "timestamp": datetime.now().isoformat()
        })
        
        # Get the platform adapter
        adapter = await self.get_platform_adapter(platform)
        if not adapter:
            self.logger.error(LogEventType.ERROR, f"No adapter registered for platform {platform}")
            return None
            
        # Process the update through the adapter to get standardized format
        self.logger.debug(LogEventType.PROCESSING, "Processing update through platform adapter")
        processed_update = await adapter.process_update(update_data)
        
        if not processed_update:
            self.logger.warning(LogEventType.ERROR, f"Failed to process update for platform {platform}")
            return None
            
        # Extract message content
        message_type = processed_update.get("type")
        content = processed_update.get("content", {})
        
        self.logger.info(LogEventType.PROCESSING, f"Processed update type: {message_type}", {
            "message_type": message_type,
            "content_type": content.get("type")
        })
        
        # Get or initialize the dialog state
        self.logger.debug(LogEventType.STATE_CHANGE, "Retrieving dialog state")
        dialog_state = await self.state_repository.get_dialog_state(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id
        )
        
        # Update logger with dialog_id if available
        if dialog_state and "id" in dialog_state:
            self.logger.set_context(dialog_id=str(dialog_state["id"]))
            self.logger.debug(LogEventType.STATE_CHANGE, "Retrieved existing dialog state", {
                "current_step": dialog_state.get("current_step"),
                "collected_data_keys": list(dialog_state.get("collected_data", {}).keys()) 
            })
        else:
            self.logger.debug(LogEventType.STATE_CHANGE, "No existing dialog state found")
        
        # Handle message based on type
        if message_type == "message":
            content_type = content.get("type", "")
            
            if content_type == "text":
                # Handle text messages
                user_input = content.get("text", "")
                self.logger.incoming_message(user_input, {"message_type": "text"})
                
                response = await self.handle_text_message(
                    bot_id=bot_id,
                    platform=platform,
                    platform_chat_id=platform_chat_id,
                    text=user_input,
                    dialog_state=dialog_state
                )
                return response
                
            elif content_type in ["photo", "video", "audio", "document", "voice", "image"]:
                # Handle media messages
                file_id = content.get("file_id", "")
                caption = content.get("caption", "")
                
                self.logger.info(LogEventType.MEDIA, f"Received {content_type} media", {
                    "media_type": content_type,
                    "file_id": file_id,
                    "has_caption": bool(caption),
                    "caption": caption[:100] if caption else ""
                })
                
                # Process media message similar to text messages, using caption as text if available
                text_to_process = caption if caption else f"[{content_type.upper()}]"
                self.logger.incoming_message(text_to_process, {
                    "message_type": "media",
                    "media_type": content_type,
                    "file_id": file_id
                })
                
                # Process the media message through the dialog service
                response = await self.handle_text_message(
                    bot_id=bot_id,
                    platform=platform,
                    platform_chat_id=platform_chat_id,
                    text=text_to_process,
                    dialog_state=dialog_state
                )
                return response
            
        elif message_type == "callback" and content.get("type") == "button":
            button_value = content.get("value", "")
            self.logger.incoming_message(f"Button click: {button_value}", {"message_type": "button"})
            
            response = await self.handle_button_click(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value=button_value,
                dialog_state=dialog_state
            )
            return response
            
        self.logger.warning(LogEventType.ERROR, f"Unhandled message type: {message_type}")
        return None
        
    async def handle_text_message(
        self,
        bot_id: UUID,
        platform: str,
        platform_chat_id: str,
        text: str,
        dialog_state: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a text message from a user.
        
        Args:
            bot_id: ID of the bot receiving the message
            platform: Platform identifier
            platform_chat_id: Chat ID in the platform
            text: Text message content
            dialog_state: Current dialog state (if available)
            
        Returns:
            Response information or None if no response is required
        """
        # Special handling for command messages (starting with /)
        if text.startswith('/'):
            self.logger.info(LogEventType.PROCESSING, f"Handling command: {text}")
            return await self.handle_command(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                command=text,
                dialog_state=dialog_state
            )
        
        # Process through the dialog service
        self.logger.debug(LogEventType.PROCESSING, f"Processing text message through dialog service", {
            "current_step": dialog_state.get("current_step") if dialog_state else None
        })
        
        try:
            response = await DialogService.process_user_input(
                self.db, bot_id, platform, platform_chat_id, text
            )
            
            # Log response details
            if response:
                message = response.get("message", {})
                message_text = message.get("text", "")
                buttons = response.get("buttons", [])
                next_step = response.get("next_step")
                
                self.logger.debug(LogEventType.PROCESSING, "Dialog service returned response", {
                    "has_message": bool(message),
                    "has_buttons": bool(buttons),
                    "next_step": next_step
                })
                
                # Log state transition if available
                if next_step and dialog_state and dialog_state.get("current_step") != next_step:
                    self.logger.state_change(next_step, {
                        "previous_step": dialog_state.get("current_step"),
                        "transition_trigger": "text_input"
                    })
            else:
                self.logger.debug(LogEventType.PROCESSING, "Dialog service returned no response")
                
            # If we have a response, send it through the platform adapter
            if response:
                adapter = await self.get_platform_adapter(platform)
                if adapter:
                    message = response.get("message", {})
                    buttons = response.get("buttons", [])
                    message_text = message.get("text", "")
                    media = message.get("media", [])
                    
                    if buttons:
                        formatted_buttons = [
                            {"text": btn.get("text", ""), "value": btn.get("value", "")}
                            for btn in buttons
                        ]
                        
                        self.logger.debug(LogEventType.ADAPTER, f"Sending message with {len(buttons)} buttons")
                        self.logger.outgoing_message(message_text, {
                            "buttons": [b.get("text") for b in buttons],
                            "has_buttons": True,
                            "has_media": bool(media),
                            "media_count": len(media) if media else 0
                        })
                        
                        # Log media details if present
                        if media:
                            for media_item in media:
                                self.logger.media_processing("sending", media_item.get("type", "unknown"), {
                                    "file_id": media_item.get("file_id"),
                                    "description": media_item.get("description"),
                                    "with_buttons": True
                                })
                        
                        await adapter.send_buttons(
                            chat_id=platform_chat_id,
                            text=message_text,
                            buttons=formatted_buttons
                        )
                    else:
                        self.logger.debug(LogEventType.ADAPTER, "Sending text message")
                        self.logger.outgoing_message(message_text, {
                            "has_media": bool(media),
                            "media_count": len(media) if media else 0
                        })
                        
                        # Log media details if present
                        if media:
                            for media_item in media:
                                self.logger.media_processing("sending", media_item.get("type", "unknown"), {
                                    "file_id": media_item.get("file_id"),
                                    "description": media_item.get("description"),
                                    "with_buttons": False
                                })
                        
                        await adapter.send_text_message(
                            chat_id=platform_chat_id,
                            text=message_text
                        )
                else:
                    self.logger.error(LogEventType.ERROR, f"No adapter found for platform {platform}")
            
            return response
            
        except Exception as e:
            self.logger.error(LogEventType.ERROR, f"Error processing text message: {str(e)}", exc_info=e)
            return None
        
    async def handle_button_click(
        self,
        bot_id: UUID,
        platform: str,
        platform_chat_id: str,
        button_value: str,
        dialog_state: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a button click from a user.
        
        Args:
            bot_id: ID of the bot receiving the click
            platform: Platform identifier
            platform_chat_id: Chat ID in the platform
            button_value: Value of the button that was clicked
            dialog_state: Current dialog state (if available)
            
        Returns:
            Response information or None if no response is required
        """
        # Process through the dialog service
        response = await DialogService.process_user_input(
            self.db, bot_id, platform, platform_chat_id, button_value
        )
        
        # If we have a response, send it through the platform adapter
        if response:
            adapter = await self.get_platform_adapter(platform)
            if adapter:
                message = response.get("message", {})
                buttons = response.get("buttons", [])
                
                if buttons:
                    formatted_buttons = [
                        {"text": btn.get("text", ""), "value": btn.get("value", "")}
                        for btn in buttons
                    ]
                    await adapter.send_buttons(
                        chat_id=platform_chat_id,
                        text=message.get("text", ""),
                        buttons=formatted_buttons
                    )
                else:
                    await adapter.send_text_message(
                        chat_id=platform_chat_id,
                        text=message.get("text", "")
                    )
        
        return response
        
    async def handle_command(
        self,
        bot_id: UUID,
        platform: str,
        platform_chat_id: str,
        command: str,
        dialog_state: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle a special command from a user (usually starting with /).
        
        Args:
            bot_id: ID of the bot receiving the command
            platform: Platform identifier
            platform_chat_id: Chat ID in the platform
            command: The command (with /)
            dialog_state: Current dialog state (if available)
            
        Returns:
            Response information or None if no response is required
        """
        command = command.lower()
        
        # Handle standard commands
        if command == '/start':
            # Reset dialog state and start from beginning
            if dialog_state:
                await DialogService.delete_dialog_state(self.db, dialog_state["id"])
            
            # Get active scenario
            active_scenario = await ScenarioService.get_active_scenario(self.db, bot_id)
            if not active_scenario:
                adapter = await self.get_platform_adapter(platform)
                if adapter:
                    await adapter.send_text_message(
                        chat_id=platform_chat_id,
                        text="Sorry, no active scenario found for this bot."
                    )
                return None
            
            # Process welcome step
            start_step = "welcome"
            if "start_step" in active_scenario.scenario_data:
                start_step = active_scenario.scenario_data["start_step"]
            
            # Create new dialog state
            dialog_state_create = BotDialogStateCreate(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                current_step=start_step,
                collected_data={}
            )
            await DialogService.create_dialog_state(self.db, dialog_state_create)
            
            # Find the welcome step
            steps = active_scenario.scenario_data.get("steps", {})
            welcome_step = None
            
            if isinstance(steps, list):
                for step in steps:
                    if step.get("id") == start_step:
                        welcome_step = step
                        break
            elif isinstance(steps, dict):
                welcome_step = steps.get(start_step)
            
            if welcome_step:
                adapter = await self.get_platform_adapter(platform)
                if adapter:
                    message = welcome_step.get("message", {})
                    buttons = welcome_step.get("buttons", [])
                    media = message.get("media", [])
                    
                    # Create a DialogMessage object from the message data
                    from src.api.schemas.bots.dialog_schemas import DialogMessage, MediaItem
                    
                    # Convert any media dictionaries to MediaItem objects
                    media_items = []
                    if media:
                        for item in media:
                            media_items.append(MediaItem(
                                type=item.get("type", "unknown"),
                                file_id=item.get("file_id", ""),
                                description=item.get("description")
                            ))
                    
                    dialog_message = DialogMessage(
                        text=message.get("text", ""),
                        media=media_items
                    )
                    
                    self.logger.info(LogEventType.MEDIA, f"Welcome step has {len(media_items)} media items", {
                        "media_count": len(media_items),
                        "media_types": [m.type for m in media_items] if media_items else [],
                        "media_ids": [m.file_id for m in media_items] if media_items else []
                    })
                    
                    if buttons:
                        formatted_buttons = [
                            {"text": btn.get("text", ""), "value": btn.get("value", "")}
                            for btn in buttons
                        ]
                        # Use send_message with media and buttons
                        await self.send_message(
                            bot_id=bot_id,
                            platform=platform,
                            platform_chat_id=platform_chat_id,
                            message=dialog_message,
                            buttons=formatted_buttons
                        )
                    else:
                        # Use send_message with media but no buttons
                        await self.send_message(
                            bot_id=bot_id,
                            platform=platform,
                            platform_chat_id=platform_chat_id,
                            message=dialog_message
                        )
                        
                return {
                    "message": welcome_step.get("message", {}),
                    "buttons": welcome_step.get("buttons", []),
                    "next_step": welcome_step.get("next_step")
                }
                
        elif command == '/help':
            adapter = await self.get_platform_adapter(platform)
            if adapter:
                await adapter.send_text_message(
                    chat_id=platform_chat_id,
                    text=(
                        "Available commands:\n"
                        "/start - Start or restart the conversation\n"
                        "/help - Show this help message\n"
                        "/reset - Reset the current conversation"
                    )
                )
            return {
                "message": {
                    "text": "Help information displayed."
                }
            }
            
        elif command == '/reset':
            if dialog_state:
                await DialogService.delete_dialog_state(self.db, dialog_state["id"])
                adapter = await self.get_platform_adapter(platform)
                if adapter:
                    await adapter.send_text_message(
                        chat_id=platform_chat_id,
                        text="Conversation has been reset. Send /start to begin a new conversation."
                    )
                return {
                    "message": {
                        "text": "Conversation reset successfully."
                    }
                }
        
        # If no special handling, just process as regular input
        return await self.handle_text_message(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            text=command,
            dialog_state=dialog_state
        )

    async def send_message(
        self,
        bot_id: UUID,
        platform: str,
        platform_chat_id: str,
        message: Union[str, DialogMessage],
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """
        Send a message to a user through the appropriate platform adapter.
        
        Args:
            bot_id: ID of the bot sending the message
            platform: Platform identifier
            platform_chat_id: Chat ID in the platform
            message: Text message or DialogMessage object
            buttons: Optional list of buttons to include
            
        Returns:
            True if the message was sent successfully, False otherwise
        """
        adapter = await self.get_platform_adapter(platform)
        if not adapter:
            logger.error(f"No adapter registered for platform {platform}")
            return False
        
        # Convert string message to DialogMessage if needed
        if isinstance(message, str):
            message_text = message
            message = DialogMessage(text=message_text)
            # No media in string messages
            media = []
        else:
            message_text = message.text
            # Check for media in the message object
            media = getattr(message, 'media', [])
            
        # Debug log for media content
        if media:
            self.logger.info(LogEventType.MEDIA, f"Media content detected in message: {len(media)} items", {
                "media_count": len(media),
                "media_types": [getattr(m, 'type', 'unknown') if hasattr(m, 'type') else m.get('type', 'unknown') for m in media],
                "media_ids": [getattr(m, 'file_id', 'unknown') if hasattr(m, 'file_id') else m.get('file_id', 'unknown') for m in media],
                "has_buttons": buttons is not None,
                "platform": platform
            })
        
        if buttons:
            result = await adapter.send_buttons(
                chat_id=platform_chat_id,
                text=message_text,
                buttons=buttons
            )
        else:
            # Check if we need to send media
            if media:
                # For simplicity, just send the first media item
                # In a real implementation, you might want to send multiple media items
                media_item = media[0]
                
                # Handle both Pydantic MediaItem objects and dictionaries
                if hasattr(media_item, 'type'):  # It's a Pydantic object
                    media_type = getattr(media_item, 'type', 'image')  # Default to image
                    file_id = getattr(media_item, 'file_id', None)
                else:  # It's a dictionary
                    media_type = media_item.get('type', 'image')  # Default to image
                    file_id = media_item.get('file_id')
                
                self.logger.info(LogEventType.MEDIA, f"Preparing to send {media_type} media with file_id {file_id}", {
                    "media_type": media_type,
                    "file_id": file_id,
                    "chat_id": platform_chat_id,
                    "media_item": str(media_item),
                    "media_item_type": type(media_item).__name__,
                    "all_media_count": len(media),
                    "message_text": message_text[:100] + "..." if message_text and len(message_text) > 100 else message_text
                })
                
                # Attempt to use API endpoint to retrieve media file
                try:
                    # Use API endpoint to retrieve media file
                    import httpx
                    import tempfile
                    import os
                    
                    # Construct API URL to get media by file_id
                    # The endpoint now supports access without authentication for scenario media
                    api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
                    media_url = f"{api_base_url}/v1/api/media/{file_id}/content"
                    
                    self.logger.info(LogEventType.MEDIA, f"Retrieving media from API: {media_url}", {
                        "url": media_url,
                        "platform": platform,
                        "file_id": file_id,
                        "media_type": media_type,
                        "api_base_url": api_base_url
                    })
                    
                    # Fetch the media file
                    async with httpx.AsyncClient() as client:
                        response = await client.get(media_url)
                        
                        if response.status_code == 200:
                            # Determine proper file extension based on content type
                            content_type = response.headers.get("content-type", "")
                            ext = ".bin"  # Default extension
                            
                            if content_type.startswith("image/jpeg"):
                                ext = ".jpg"
                            elif content_type.startswith("image/png"):
                                ext = ".png"
                            elif content_type.startswith("image/gif"):
                                ext = ".gif"
                            elif content_type.startswith("video/"):
                                ext = ".mp4"
                            elif content_type.startswith("audio/"):
                                ext = ".mp3"
                            elif content_type == "application/pdf":
                                ext = ".pdf"
                            
                            # Save to temporary file with proper extension
                            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                                tmp.write(response.content)
                                tmp_path = tmp.name
                                
                            self.logger.info(LogEventType.MEDIA, f"Saved media to temporary file with extension {ext}", {
                                "content_type": content_type,
                                "extension": ext,
                                "file_size": len(response.content)
                            })
                                
                            self.logger.info(LogEventType.MEDIA, f"Successfully retrieved media from API", {
                                "file_id": file_id,
                                "temp_path": tmp_path,
                                "content_length": len(response.content),
                                "content_type": response.headers.get("content-type", "unknown"),
                                "headers": str(dict(response.headers)),
                                "status_code": response.status_code,
                                "media_type": media_type
                            })
                            
                            # Try to determine if the file is actually a supported format
                            import imghdr
                            detected_format = imghdr.what(tmp_path)
                            
                            self.logger.info(LogEventType.MEDIA, f"Detected image format: {detected_format}", {
                                "file_path": tmp_path,
                                "declared_media_type": media_type,
                                "detected_format": detected_format
                            })
                            
                            # If it's not a recognized image format but we're trying to send as an image,
                            # fall back to sending as a document
                            if media_type == "image" and not detected_format:
                                self.logger.warning(LogEventType.MEDIA, "Unrecognized image format, falling back to document", {
                                    "original_media_type": media_type,
                                    "fallback": "document"
                                })
                                media_type = "document"
                            
                            # Send the media
                            result = await adapter.send_media_message(
                                chat_id=platform_chat_id,
                                media_type=media_type,
                                file_path=tmp_path,
                                caption=message_text if message_text else None
                            )
                            
                            # Clean up the temporary file
                            try:
                                os.unlink(tmp_path)
                            except Exception as e:
                                self.logger.warning(LogEventType.MEDIA, f"Failed to delete temporary file: {e}", 
                                                   {"path": tmp_path})
                            
                            # Check if media sending succeeded
                            if not result.get("success", False):
                                self.logger.error(LogEventType.MEDIA, f"Failed to send media: {result.get('error')}", 
                                                 {"file_id": file_id})
                                # Fall back to text message
                                result = await adapter.send_text_message(
                                    chat_id=platform_chat_id,
                                    text=message_text
                                )
                        else:
                            self.logger.error(LogEventType.MEDIA, 
                                           f"Failed to retrieve media file: Status {response.status_code}", 
                                           {"status": response.status_code, "response": response.text[:200]})
                            # Fall back to text-only message
                            result = await adapter.send_text_message(
                                chat_id=platform_chat_id,
                                text=message_text
                            )
                except Exception as e:
                    # Log any errors during media sending
                    self.logger.error(LogEventType.ERROR, 
                        f"Error sending media: {str(e)}", 
                        {"error": str(e), "media_type": media_type, "file_id": file_id})
                    
                    # Fall back to text message
                    result = await adapter.send_text_message(
                        chat_id=platform_chat_id,
                        text=message_text
                    )
            else:
                # Regular text message
                result = await adapter.send_text_message(
                    chat_id=platform_chat_id,
                    text=message_text
                )
            
        return result.get("success", False)
        
    def _get_file_extension_for_media_type(self, media_type: str) -> str:
        """Get appropriate file extension for a media type"""
        media_type = media_type.lower()
        if media_type == "image":
            return ".jpg"
        elif media_type == "video":
            return ".mp4"
        elif media_type == "audio":
            return ".mp3"
        elif media_type == "document":
            return ".pdf"
        else:
            return ".bin"  # Generic binary extension