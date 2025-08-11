"""
Dialog Manager for Bot Management System

This module is responsible for:
1. Managing dialog state and flow
2. Processing user inputs according to scenarios
3. Generating appropriate responses
4. Coordinating with platform adapters for message delivery
5. Logging detailed conversation flows for debugging
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from uuid import UUID
import json
from datetime import datetime
import threading

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
from src.bot_manager.conversation_logger import get_logger, LogEventType, _thread_local
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
                auto_next = response.get("auto_next", False)
                auto_next_delay = response.get("auto_next_delay", 1.5)
                
                self.logger.debug(LogEventType.PROCESSING, "Dialog service returned response", {
                    "has_message": bool(message),
                    "has_buttons": bool(buttons),
                    "next_step": next_step,
                    "auto_next": auto_next,
                    "auto_next_delay": auto_next_delay
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
            # In the _process_auto_next_step method, we'll control this with the allow_dialog_service_message parameter
            if response:
                adapter = await self.get_platform_adapter(platform)
                if adapter:
                    message = response.get("message", {})
                    buttons = response.get("buttons", [])
                    message_text = message.get("text", "")
                    media = message.get("media", [])
                    auto_next = response.get("auto_next", False)
                    auto_next_delay = response.get("auto_next_delay", 1.5)
                    next_step = response.get("next_step")
                    
                    if buttons:
                        formatted_buttons = [
                            {"text": btn.get("text", ""), "value": btn.get("value", "")}
                            for btn in buttons
                        ]
                        
                        self.logger.debug(LogEventType.ADAPTER, f"Sending message with {len(buttons)} buttons")
                        
                        # Check if media is present
                        if media:
                            self.logger.info(LogEventType.MEDIA, f"Found media with buttons in message, sending media first", {
                                "media_count": len(media),
                                "button_count": len(buttons),
                                "next_step": next_step
                            })
                            
                            # Log media details
                            for media_item in media:
                                self.logger.media_processing("sending", media_item.get("type", "unknown"), {
                                    "file_id": media_item.get("file_id"),
                                    "description": media_item.get("description"),
                                    "with_buttons": True
                                })
                            
                            # Process all media together with buttons
                            await self.send_message(
                                bot_id=bot_id,
                                platform=platform,
                                platform_chat_id=platform_chat_id,
                                message={
                                    "text": message_text,
                                    "media": media
                                },
                                buttons=formatted_buttons
                            )
                        else:
                            # No media, just send buttons
                            await adapter.send_buttons(
                                chat_id=platform_chat_id,
                                text=message_text,
                                buttons=formatted_buttons
                            )
                    else:
                        self.logger.debug(LogEventType.ADAPTER, "Sending text message")
                        
                        # Log media details if present
                        if media:
                            for media_item in media:
                                self.logger.media_processing("sending", media_item.get("type", "unknown"), {
                                    "file_id": media_item.get("file_id"),
                                    "description": media_item.get("description"),
                                    "with_buttons": False
                                })
                            
                            # Send message with media
                            await self.send_message(
                                bot_id=bot_id,
                                platform=platform,
                                platform_chat_id=platform_chat_id,
                                message={
                                    "text": message_text,
                                    "media": media
                                }
                            )
                        else:
                            await adapter.send_text_message(
                                chat_id=platform_chat_id,
                                text=message_text
                            )
                    
                    # Handle auto-transition if enabled
                    if auto_next and next_step:
                        import uuid
                        import asyncio
                        
                        transition_id = f"auto_trans_{uuid.uuid4().hex[:8]}"
                        
                        self.logger.auto_transition(
                            f"Starting auto-transition to step '{next_step}' with delay {auto_next_delay}s",
                            {"next_step": next_step, "delay": auto_next_delay, "transition_id": transition_id}
                        )
                        
                        # Wait for the specified delay
                        await asyncio.sleep(auto_next_delay)
                        
                        # Process the auto-transition step
                        await self._process_auto_next_step(
                            bot_id=bot_id,
                            platform=platform,
                            platform_chat_id=platform_chat_id,
                            step_id=next_step,
                            transition_id=transition_id
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
                media = message.get("media", [])
                message_text = message.get("text", "")
                
                # Set adapter context for better logging
                if hasattr(adapter, "set_context") and callable(getattr(adapter, "set_context")):
                    dialog_id = None
                    if dialog_state:
                        if hasattr(dialog_state, "id"):
                            dialog_id = str(dialog_state.id)
                        elif isinstance(dialog_state, dict) and "id" in dialog_state:
                            dialog_id = str(dialog_state["id"])
                    adapter.set_context(bot_id=str(bot_id), dialog_id=dialog_id)
                auto_next = response.get("auto_next", False)
                auto_next_delay = response.get("auto_next_delay", 1.5)
                next_step = response.get("next_step")
                
                if buttons:
                    formatted_buttons = [
                        {"text": btn.get("text", ""), "value": btn.get("value", "")}
                        for btn in buttons
                    ]
                    
                    # Check if media is present
                    if media:
                        self.logger.info(LogEventType.MEDIA, f"Found media with buttons in message, sending media first", {
                            "media_count": len(media),
                            "button_count": len(buttons),
                            "next_step": next_step
                        })
                        
                        # Log media details
                        for media_item in media:
                            self.logger.media_processing("sending", media_item.get("type", "unknown"), {
                                "file_id": media_item.get("file_id"),
                                "description": media_item.get("description"),
                                "with_buttons": True
                            })
                        
                        # Process all media together with buttons
                        await self.send_message(
                            bot_id=bot_id,
                            platform=platform,
                            platform_chat_id=platform_chat_id,
                            message={
                                "text": message_text,
                                "media": media
                            },
                            buttons=formatted_buttons
                        )
                    else:
                        # No media, just send buttons
                        await adapter.send_buttons(
                            chat_id=platform_chat_id,
                            text=message_text,
                            buttons=formatted_buttons
                        )
                else:
                    if media:
                        # Handle media without buttons
                        for media_item in media:
                            self.logger.media_processing("sending", media_item.get("type", "unknown"), {
                                "file_id": media_item.get("file_id"),
                                "description": media_item.get("description"),
                                "with_buttons": False
                            })
                        
                        # Send message with media
                        await self.send_message(
                            bot_id=bot_id,
                            platform=platform,
                            platform_chat_id=platform_chat_id,
                            message={
                                "text": message_text,
                                "media": media
                            }
                        )
                    else:
                        # No media, send text message
                        await adapter.send_text_message(
                            chat_id=platform_chat_id,
                            text=message_text
                        )
                
                # Handle auto-transition if enabled
                if auto_next and next_step:
                    import uuid
                    import asyncio
                    
                    transition_id = f"auto_trans_{uuid.uuid4().hex[:8]}"
                    
                    self.logger.auto_transition(
                        f"Starting auto-transition to step '{next_step}' with delay {auto_next_delay}s",
                        {"next_step": next_step, "delay": auto_next_delay, "transition_id": transition_id}
                    )
                    
                    # Wait for the specified delay
                    await asyncio.sleep(auto_next_delay)
                    
                    # Process the auto-transition step
                    await self._process_auto_next_step(
                        bot_id=bot_id,
                        platform=platform,
                        platform_chat_id=platform_chat_id,
                        step_id=next_step,
                        transition_id=transition_id
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
        message: Union[str, DialogMessage, Dict[str, Any]],
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """
        Send a message to a user through the appropriate platform adapter.
        
        Args:
            bot_id: ID of the bot sending the message
            platform: Platform identifier
            platform_chat_id: Chat ID in the platform
            message: Text message, DialogMessage object, or message dict
            buttons: Optional list of buttons to include
            
        Returns:
            True if the message was sent successfully, False otherwise
        """
        adapter = await self.get_platform_adapter(platform)
        if not adapter:
            self.logger.error(LogEventType.ERROR, f"No adapter registered for platform {platform}")
            return False
        
        # Extract message content based on type
        message_text, media = self._extract_message_content(message)
        
        # Log the outgoing message
        self._log_outgoing_message(message_text, media, buttons, platform, platform_chat_id, bot_id)
        
        # Process and send the message
        if media:
            # Message contains media content
            result = await self._process_media_sending(
                adapter=adapter,
                chat_id=platform_chat_id,
                media=media,
                message_text=message_text,
                buttons=buttons,
                platform=platform
            )
        else:
            # Text-only message
            result = await self._send_text_only_message(adapter, platform_chat_id, message_text, buttons)
        
        # Log enhanced scenario information for media messages
        if media:
            self._log_media_scenario(media, buttons, platform)
            
        return result.get("success", False)
        
    def _extract_message_content(self, message: Union[str, DialogMessage, Dict[str, Any]]) -> Tuple[str, List[Any]]:
        """Extract text and media content from different message formats
        
        Args:
            message: The message in any supported format
            
        Returns:
            Tuple of (message_text, media_list)
        """
        if isinstance(message, str):
            # String message - text only
            return message, []
        elif isinstance(message, dict):
            # Dictionary message
            return message.get("text", ""), message.get("media", [])
        else:
            # DialogMessage object
            return getattr(message, 'text', ""), getattr(message, 'media', [])
    
    def _log_outgoing_message(
        self, 
        message_text: str, 
        media: List[Any], 
        buttons: Optional[List[Dict[str, str]]],
        platform: str,
        platform_chat_id: str,
        bot_id: UUID
    ) -> None:
        """Log information about an outgoing message"""
        # Extract button text for logging
        button_texts = []
        if buttons:
            for btn in buttons:
                if isinstance(btn, dict):
                    button_texts.append(btn.get("text", ""))
                else:
                    button_texts.append(btn["text"])
        
        # Log data about this message
        log_data = {
            "has_buttons": bool(buttons),
            "buttons": button_texts,
            "has_media": bool(media),
            "media_count": len(media) if media else 0,
            "platform": platform,
            "platform_chat_id": platform_chat_id,
            "bot_id": str(bot_id)
        }
        
        # Log the message content
        self.logger.outgoing_message(message_text, log_data)
        
        # Additional logging for media content
        if media:
            self._log_media_content(media, buttons, platform, platform_chat_id, message_text)
    
    def _validate_media_items(self, media: List[Any]) -> bool:
        """Validate media items to ensure they have required attributes
        
        Args:
            media: List of media items to validate
            
        Returns:
            True if at least one valid media item exists, False otherwise
        """
        valid_count = 0
        invalid_items = []
        
        for i, item in enumerate(media):
            # Check for required fields based on item type
            if isinstance(item, dict):
                if not item.get('file_id'):
                    invalid_items.append({"index": i, "reason": "missing file_id", "item_type": "dict"})
                else:
                    valid_count += 1
            else:  # Object-like item
                if not hasattr(item, 'file_id') or not getattr(item, 'file_id'):
                    invalid_items.append({"index": i, "reason": "missing file_id attribute", "item_type": type(item).__name__})
                else:
                    valid_count += 1
        
        # Log validation results if any issues found
        if invalid_items:
            self.logger.warning(LogEventType.MEDIA, f"Found {len(invalid_items)} invalid media items", {
                "valid_count": valid_count,
                "invalid_count": len(invalid_items),
                "invalid_details": invalid_items
            })
        
        return valid_count > 0

    def _log_media_content(
        self, 
        media: List[Any], 
        buttons: Optional[List[Dict[str, str]]],
        platform: str,
        platform_chat_id: str,
        message_text: str
    ) -> None:
        """Log detailed information about media content"""
        # Extract media details for logging
        media_types = []
        media_ids = []
        media_details = []
        
        for m in media:
            if isinstance(m, dict):
                media_type = m.get('type', 'unknown')
                file_id = m.get('file_id', 'unknown')
                description = m.get('description', '')
            else:  # Object
                media_type = getattr(m, 'type', 'unknown')
                file_id = getattr(m, 'file_id', 'unknown')
                description = getattr(m, 'description', '')
                
            media_types.append(media_type)
            media_ids.append(file_id)
            media_details.append({
                "type": media_type,
                "file_id": file_id[:10] + "..." if len(file_id) > 10 else file_id,
                "has_description": bool(description)
            })
        
        # Log basic media content information
        self.logger.info(LogEventType.MEDIA, f"Media content detected in message: {len(media)} items", {
            "media_count": len(media),
            "media_types": media_types,
            "media_ids": media_ids,
            "has_buttons": buttons is not None,
            "platform": platform
        })
        
        # Log more detailed processing information
        self.logger.info(LogEventType.MEDIA, f"Processing media content: {len(media)} items", {
            "media_count": len(media),
            "chat_id": platform_chat_id,
            "has_buttons": buttons is not None,
            "button_count": len(buttons) if buttons else 0,
            "message_text": message_text[:100] + "..." if message_text and len(message_text) > 100 else message_text,
            "media_details": media_details
        })
    
    def _log_media_scenario(
        self, 
        media: List[Any], 
        buttons: Optional[List[Dict[str, str]]],
        platform: str
    ) -> None:
        """Log comprehensive media scenario information"""
        # Default values if not provided in context
        step_id = "unknown_step"  
        step_type = "unknown"
        
        # Prepare media item information
        media_items = []
        for m in media:
            media_items.append({
                "file_id": getattr(m, 'file_id', 'unknown') if hasattr(m, 'file_id') else m.get('file_id', 'unknown'),
                "type": getattr(m, 'type', 'unknown') if hasattr(m, 'type') else m.get('type', 'unknown'),
                "description": getattr(m, 'description', '') if hasattr(m, 'description') else m.get('description', '')
            })
        
        # Log the comprehensive scenario information
        self.logger.media_scenario(
            step_id,
            len(media),
            {
                "media_items": media_items,
                "step_type": step_type,
                "has_buttons": buttons is not None,
                "button_count": len(buttons) if buttons else 0,
                "platform": platform
            }
        )
        
    async def _process_media_sending(
        self, 
        adapter: PlatformAdapter,
        chat_id: str,
        media: List[Any],
        message_text: str,
        buttons: Optional[List[Dict[str, str]]],
        platform: str
    ) -> Dict[str, Any]:
        """Process and send media messages, handling multiple media items
        
        Args:
            adapter: The platform adapter to use for sending
            chat_id: The platform chat ID to send to
            media: List of media items to send
            message_text: Text message or caption
            buttons: Optional list of buttons to include
            platform: Platform identifier (telegram, whatsapp, etc.)
            
        Returns:
            Dict with success status and response information
        """
        # Handle case with no media items
        if not media or len(media) == 0:
            return await self._send_text_only_message(adapter, chat_id, message_text, buttons)
        
        # Log the media processing
        self._log_media_processing_start(media, platform, buttons)
        
        # Send multiple media items as a group
        if len(media) > 1:
            return await self._send_media_group(adapter, chat_id, media, message_text, buttons, platform)
        
        # Handle single media item
        return await self._send_single_media_item(adapter, chat_id, media[0], message_text, buttons, platform)
    
    async def _send_text_only_message(
        self,
        adapter: PlatformAdapter,
        chat_id: str,
        text: str,
        buttons: Optional[List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        """Send a text-only message with optional buttons"""
        self.logger.debug(LogEventType.MEDIA, "No media items to send, using text message")
        if buttons:
            return await adapter.send_buttons(
                chat_id=chat_id,
                text=text,
                buttons=buttons
            )
        else:
            return await adapter.send_text_message(
                chat_id=chat_id,
                text=text
            )
    
    def _log_media_processing_start(self, media: List[Any], platform: str, buttons: Optional[List[Dict[str, str]]]):
        """Log information about media processing at the start"""
        self.logger.info(LogEventType.MEDIA, f"Processing {len(media)} media item(s)", {
            "media_count": len(media),
            "platform": platform,
            "has_buttons": buttons is not None and len(buttons) > 0,
            "media_types": [item.get('type', 'unknown') if isinstance(item, dict) else getattr(item, 'type', 'unknown') for item in media]
        })
    
    async def _send_media_group(
        self, 
        adapter: PlatformAdapter,
        chat_id: str,
        media: List[Any],
        message_text: str,
        buttons: Optional[List[Dict[str, str]]],
        platform: str
    ) -> Dict[str, Any]:
        """Send multiple media items as a group with optional follow-up buttons"""
        self.logger.info(LogEventType.MEDIA, f"Processing {len(media)} media items as a group", {
            "media_count": len(media),
            "platform": platform,
            "has_buttons": buttons is not None and len(buttons) > 0,
            "media_types": [item.get('type', 'unknown') if isinstance(item, dict) else getattr(item, 'type', 'unknown') for item in media]
        })
        
        # Pre-check validation for media items
        valid_media = self._validate_media_items(media)
        if not valid_media:
            self.logger.error(LogEventType.ERROR, "No valid media items found in group")
            return {"success": False, "error": "No valid media items"}
        
        try:
            # Detailed timing and tracking
            start_time = datetime.now()
            self.logger.debug(LogEventType.MEDIA, "Sending media group to adapter")
            
            # Send the media as a group
            result = await adapter.send_media_group(
                chat_id=chat_id,
                media_items=media,
                caption=message_text
            )
            
            # Calculate and log processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000  # ms
            self.logger.debug(LogEventType.MEDIA, f"Media group send completed in {processing_time:.2f}ms", {
                "success": result.get("success", False),
                "processing_time_ms": processing_time,
                "message_ids": result.get("message_ids", [])
            })
            
            # Enhanced error handling for failed send operations
            if not result.get("success", False):
                error_detail = result.get("error", "Unknown error")
                self.logger.error(LogEventType.ERROR, f"Media group send failed: {error_detail}", {
                    "error": error_detail,
                    "error_code": result.get("error_code"),
                    "platform": platform
                })
                # Continue with fallback strategy
                self.logger.warning(LogEventType.MEDIA, "Falling back to sending first media item only")
                return await self._send_single_media_item(adapter, chat_id, media[0], message_text, buttons, platform)
            
            # If buttons are provided and media send was successful, send them as follow-up
            if buttons and result.get("success", True):
                await self._send_follow_up_buttons(adapter, chat_id, message_text, buttons, result)
            
            return result
            
        except Exception as e:
            self.logger.error(LogEventType.ERROR, f"Failed to send media group: {str(e)}", {
                "exception": str(e),
                "exception_type": type(e).__name__,
                "platform": platform,
                "chat_id": chat_id,
                "media_count": len(media)
            }, exc_info=e)
            self.logger.warning(LogEventType.MEDIA, "Exception during media group send, falling back to single media item")
            # Fall back to sending just the first media item
            try:
                return await self._send_single_media_item(adapter, chat_id, media[0], message_text, buttons, platform)
            except Exception as fallback_error:
                self.logger.error(LogEventType.ERROR, f"Fallback strategy also failed: {str(fallback_error)}")
                # Ultimate fallback: send text only
                return await self._send_text_only_message(adapter, chat_id, message_text, buttons)
    
    async def _send_follow_up_buttons(
        self,
        adapter: PlatformAdapter,
        chat_id: str,
        message_text: str,
        buttons: List[Dict[str, str]],
        result: Dict[str, Any]
    ) -> None:
        """Send buttons as a follow-up message after sending media"""
        self.logger.info(LogEventType.MEDIA, "Sending buttons as follow-up after media group", {
            "button_count": len(buttons),
            "button_texts": [btn.get("text", "") for btn in buttons[:5]] + (["..."] if len(buttons) > 5 else []),
            "chat_id": chat_id,
            "media_message_ids": result.get("message_ids", [])
        })
        
        # For follow-up buttons after media group, use minimal text to avoid duplication
        # Since the media group already shows the full message as caption
        button_text = "Выберите вариант:" if message_text and message_text.strip() else "Please select an option:"
        
        try:
            # Track timing for performance monitoring
            start_time = datetime.now()
            
            button_result = await adapter.send_buttons(
                chat_id=chat_id,
                text=button_text,
                buttons=buttons
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000  # ms
            
            # Log button send result
            if button_result.get("success", False):
                self.logger.debug(LogEventType.MEDIA, "Successfully sent follow-up buttons", {
                    "processing_time_ms": processing_time,
                    "button_message_id": button_result.get("message_id"),
                    "success": True
                })
            else:
                self.logger.warning(LogEventType.ERROR, "Failed to send follow-up buttons", {
                    "error": button_result.get("error", "Unknown error"),
                    "error_code": button_result.get("error_code"),
                    "processing_time_ms": processing_time
                })
            
            # Add button result to main result
            result["buttons_sent"] = button_result.get("success", False)
            result["button_message_id"] = button_result.get("message_id")
            
        except Exception as e:
            self.logger.error(LogEventType.ERROR, f"Error sending follow-up buttons: {str(e)}", {
                "exception": str(e),
                "exception_type": type(e).__name__,
                "chat_id": chat_id,
                "button_count": len(buttons)
            })
            
            # Update result to reflect button failure
            result["buttons_sent"] = False
            result["button_error"] = str(e)
    
    async def _send_single_media_item(
        self,
        adapter: PlatformAdapter,
        chat_id: str,
        media_item: Any,
        message_text: str,
        buttons: Optional[List[Dict[str, str]]],
        platform: str
    ) -> Dict[str, Any]:
        """Send a single media item with optional buttons"""
        # Extract media type and file_id
        media_type, file_id = self._extract_media_info(media_item)
        
        self.logger.info(LogEventType.MEDIA, f"Processing single media item: {media_type} with file_id {file_id}", {
            "media_type": media_type,
            "file_id": file_id,
            "platform": platform,
            "has_buttons": buttons is not None and len(buttons) > 0
        })
        
        # Use appropriate send method based on whether buttons are included
        if buttons:
            return await self._send_media_with_buttons(adapter, chat_id, media_type, file_id, message_text, buttons)
        else:
            return await self._send_media_without_buttons(adapter, chat_id, media_type, file_id, message_text)
    
    def _extract_media_info(self, media_item: Any) -> Tuple[str, str]:
        """Extract media type and file_id from a media item"""
        if hasattr(media_item, 'type'):  # It's a Pydantic object
            media_type = getattr(media_item, 'type', 'image')  # Default to image
            file_id = getattr(media_item, 'file_id', None)
        else:  # It's a dictionary
            media_type = media_item.get('type', 'image')  # Default to image
            file_id = media_item.get('file_id')
            
        return media_type, file_id
    
    async def _send_media_with_buttons(
        self,
        adapter: PlatformAdapter,
        chat_id: str,
        media_type: str,
        file_id: str,
        message_text: str,
        buttons: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Send a media item with buttons"""
        self.logger.debug(LogEventType.MEDIA, f"Sending {media_type} with buttons", {
            "media_type": media_type,
            "file_id": file_id[:15] + "..." if len(file_id) > 15 else file_id,
            "button_count": len(buttons),
            "chat_id": chat_id,
            "caption_length": len(message_text) if message_text else 0
        })
        
        try:
            # Track timing for performance monitoring
            start_time = datetime.now()
            
            result = await adapter.send_media_with_buttons(
                chat_id=chat_id,
                media_type=media_type,
                file_path=file_id,  # Adapter will handle retrieval
                caption=message_text,
                buttons=buttons
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000  # ms
            
            if result.get("success", False):
                self.logger.debug(LogEventType.MEDIA, f"Successfully sent {media_type} with buttons", {
                    "processing_time_ms": processing_time,
                    "message_id": result.get("message_id"),
                    "media_type": media_type
                })
            else:
                self.logger.error(LogEventType.ERROR, f"Failed to send {media_type} with buttons", {
                    "error": result.get("error", "Unknown error"),
                    "error_code": result.get("error_code"),
                    "media_type": media_type
                })
                
            return result
            
        except Exception as e:
            self.logger.error(LogEventType.ERROR, f"Error sending media with buttons: {str(e)}", {
                "exception": str(e),
                "exception_type": type(e).__name__,
                "media_type": media_type,
                "file_id": file_id[:15] + "..." if len(file_id) > 15 else file_id,
            }, exc_info=e)
            
            self.logger.warning(LogEventType.MEDIA, f"Falling back to text message with buttons due to {type(e).__name__}")
            
            try:
                # Fallback to text message with buttons
                return await adapter.send_buttons(
                    chat_id=chat_id,
                    text=f"[Media unavailable] {message_text}",  # Indicate media failed to send
                    buttons=buttons
                )
            except Exception as fallback_error:
                # Handle fallback error with comprehensive logging
                self.logger.error(LogEventType.ERROR, f"Fallback to text also failed: {str(fallback_error)}", {
                    "original_error": str(e),
                    "fallback_error": str(fallback_error),
                    "chat_id": chat_id
                })
                return {"success": False, "error": f"Media send failed and fallback failed: {str(fallback_error)}"}
    
    async def _send_media_without_buttons(
        self,
        adapter: PlatformAdapter,
        chat_id: str,
        media_type: str,
        file_id: str,
        message_text: str
    ) -> Dict[str, Any]:
        """Send a media item without buttons"""
        try:
            return await adapter.send_media_message(
                chat_id=chat_id,
                media_type=media_type,
                file_path=file_id,  # Adapter will handle retrieval
                caption=message_text
            )
        except Exception as e:
            self.logger.error(LogEventType.ERROR, f"Error sending media message: {str(e)}", exc_info=e)
            self.logger.warning(LogEventType.MEDIA, "Falling back to text message")
            return await adapter.send_text_message(
                chat_id=chat_id,
                text=message_text
            )
        
    
    # Removed skip_logging functionality as we want to always log all messages
            
            
    async def _process_auto_next_step(
        self,
        bot_id: UUID,
        platform: str,
        platform_chat_id: str,
        step_id: str,
        transition_id: str = None
    ) -> None:
        """
        Process a step that should be automatically transitioned to without user input.
        Simplified version without complex duplicate prevention logic.
        """
        self.logger.info(LogEventType.AUTO_TRANSITION, f"Processing auto-transition to step '{step_id}'", {
            "step_id": step_id,
            "transition_id": transition_id
        })
        
        try:
            # Simple approach: just use DialogService to process the auto-transition
            response = await DialogService.process_user_input(
                self.db, bot_id, platform, platform_chat_id, "@AUTO_TRANSITION@"
            )
            
            if not response:
                self.logger.error(LogEventType.AUTO_TRANSITION, f"No response from DialogService for step '{step_id}'")
                return
                
            # Send the message to the user
            adapter = await self.get_platform_adapter(platform)
            if not adapter:
                self.logger.error(LogEventType.ERROR, f"No adapter registered for platform {platform}")
                return
                
            message = response.get("message", {})
            buttons = response.get("buttons", [])
            next_step = response.get("next_step")
            auto_next = response.get("auto_next", False)
            auto_next_delay = response.get("auto_next_delay", 1.5)
            
            if message:
                message_text = message.get("text", "")
                media = message.get("media", [])
                
                # Send message with media and buttons if present
                if media:
                    await self.send_message(
                        bot_id=bot_id,
                        platform=platform,
                        platform_chat_id=platform_chat_id,
                        message={"text": message_text, "media": media},
                        buttons=buttons
                    )
                elif buttons:
                    await adapter.send_buttons(
                        chat_id=platform_chat_id,
                        text=message_text,
                        buttons=buttons
                    )
                else:
                    await adapter.send_text_message(
                        chat_id=platform_chat_id,
                        text=message_text
                    )
            
            # Handle chained auto-transitions with loop prevention
            if auto_next and next_step:
                import asyncio
                
                # Prevent infinite loops by checking if we're transitioning to the same step
                if next_step == step_id:
                    self.logger.error(LogEventType.AUTO_TRANSITION, f"Infinite loop detected: step '{step_id}' transitions to itself", {
                        "step_id": step_id,
                        "next_step": next_step,
                        "transition_id": transition_id
                    })
                    return
                
                self.logger.auto_transition(
                    f"Continuing auto-transition chain to step '{next_step}' after {auto_next_delay}s",
                    {"next_step": next_step, "delay": auto_next_delay, "transition_id": transition_id}
                )
                
                await asyncio.sleep(auto_next_delay)
                
                await self._process_auto_next_step(
                    bot_id=bot_id,
                    platform=platform,
                    platform_chat_id=platform_chat_id,
                    step_id=next_step,
                    transition_id=transition_id
                )
                
        except Exception as e:
            self.logger.error(LogEventType.AUTO_TRANSITION, f"Error in auto-transition for step '{step_id}': {str(e)}", {
                "step_id": step_id,
                "error": str(e),
                "transition_id": transition_id
            }, exc_info=e)
