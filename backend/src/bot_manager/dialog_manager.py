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
from src.bot_manager.conversation_logger import get_logger, LogEventType, _thread_local, ConversationLogger
from src.bot_manager.media_manager import MediaManager
from src.bot_manager.input_validator import InputValidator, ValidationContext, InputType, ValidationResult
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
        scenario_processor: ScenarioProcessor = None,
        media_manager: MediaManager = None,
        redis_client=None
    ):
        """
        Initialize the dialog manager.
        
        Args:
            db: Database session
            platform_adapters: Dict mapping platform names to adapter instances
            state_repository: Optional custom state repository
            scenario_processor: Optional custom scenario processor
            media_manager: Optional custom media manager
            redis_client: Optional Redis client for input validation
        """
        self.db = db
        self.platform_adapters = platform_adapters or {}
        self.state_repository = state_repository or StateRepository(db)
        self.scenario_processor = scenario_processor or ScenarioProcessor()
        self.logger = get_logger()
        # MediaManager will be initialized per conversation context
        self._media_manager_class = media_manager.__class__ if media_manager else MediaManager
        # Initialize input validator
        self.input_validator = InputValidator(redis_client=redis_client)
    
    def _get_media_manager(self, bot_id: UUID, platform: str, platform_chat_id: str) -> MediaManager:
        """
        Get a MediaManager instance for the current conversation context.
        
        Args:
            bot_id: ID of the bot
            platform: Platform identifier  
            platform_chat_id: Chat ID in the platform
            
        Returns:
            MediaManager instance with conversation context
        """
        # Create conversation logger for this specific context
        conversation_logger = ConversationLogger(
            bot_id=str(bot_id),
            dialog_id=f"{platform}:{platform_chat_id}",
            platform=platform,
            platform_chat_id=platform_chat_id
        )
        
        return self._media_manager_class(conversation_logger)
    
    async def _validate_user_input(
        self,
        bot_id: UUID,
        platform: str,
        platform_chat_id: str,
        input_type: InputType,
        input_value: str,
        dialog_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Validate user input and handle invalid inputs with appropriate responses.
        
        Returns:
            None if input is valid and processing should continue,
            Dict with response info if input is invalid and was handled
        """
        # Get current step info for validation
        current_step = dialog_state.get("current_step", "")
        expected_buttons = await self._get_expected_buttons_for_step(bot_id, current_step)
        
        # Create validation context
        validation_context = ValidationContext(
            user_id=platform_chat_id,
            bot_id=str(bot_id),
            platform=platform,
            platform_chat_id=platform_chat_id,
            input_type=input_type,
            input_value=input_value,
            expected_buttons=expected_buttons,
            current_step=current_step,
            dialog_state=dialog_state,
            timestamp=datetime.utcnow()
        )
        
        # Validate input
        validation_result = await self.input_validator.validate_input(validation_context)
        
        if not validation_result.is_valid:
            return await self._handle_invalid_input(
                validation_result, platform, platform_chat_id, expected_buttons
            )
        
        return None
    
    async def _get_expected_buttons_for_step(
        self, 
        bot_id: UUID, 
        step_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get expected buttons for a given scenario step.
        """
        try:
            # Get active scenario
            active_scenario = await ScenarioService.get_active_scenario(self.db, bot_id)
            if not active_scenario or not step_id:
                return None
            
            steps = active_scenario.scenario_data.get("steps", {})
            step_data = None
            
            if isinstance(steps, list):
                for step in steps:
                    if step.get("id") == step_id:
                        step_data = step
                        break
            elif isinstance(steps, dict):
                step_data = steps.get(step_id)
            
            if not step_data:
                return None
            
            # Extract buttons from step data
            buttons = step_data.get("buttons")
            if buttons:
                return buttons
            
            # Check if buttons are in response
            response = step_data.get("response")
            if isinstance(response, dict) and "buttons" in response:
                return response["buttons"]
            
            return None
            
        except Exception as e:
            self.logger.error(LogEventType.ERROR, f"Error getting expected buttons: {str(e)}")
            return None
    
    async def _handle_invalid_input(
        self,
        validation_result,
        platform: str,
        platform_chat_id: str,
        expected_buttons: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Handle invalid input by sending appropriate correction message.
        """
        adapter = await self.get_platform_adapter(platform)
        if not adapter:
            return {"status": "error", "message": "No adapter available"}
        
        response_sent = False
        
        if validation_result.result == ValidationResult.DUPLICATE:
            # For duplicates, we might not want to send any response
            # to avoid spamming the user
            self.logger.info(LogEventType.PROCESSING, f"Duplicate input detected for {platform_chat_id}")
            return {"status": "duplicate", "action": "ignored"}
            
        elif validation_result.correction_message:
            # Send correction message
            if validation_result.suggested_buttons:
                await adapter.send_buttons(
                    chat_id=platform_chat_id,
                    text=validation_result.correction_message,
                    buttons=validation_result.suggested_buttons
                )
                response_sent = True
            else:
                await adapter.send_text_message(
                    chat_id=platform_chat_id,
                    text=validation_result.correction_message
                )
                response_sent = True
        
        if validation_result.should_retry_current_step and not response_sent and expected_buttons:
            # Re-send current step with buttons
            button_texts = [btn.get('text', btn.get('value', 'Unknown')) for btn in expected_buttons]
            await adapter.send_buttons(
                chat_id=platform_chat_id,
                text=f"Please choose one of these options: {', '.join(button_texts)}",
                buttons=expected_buttons
            )
        
        return {
            "status": "invalid_input",
            "validation_result": validation_result.result.value,
            "action": "correction_sent"
        }
        
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
            # Commands bypass input validation as they can interrupt flows
            return await self.handle_command(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                command=text,
                dialog_state=dialog_state
            )
        
        # Validate text input
        if dialog_state:  # Only validate if we have a dialog state
            validation_response = await self._validate_user_input(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                input_type=InputType.TEXT_MESSAGE,
                input_value=text,
                dialog_state=dialog_state
            )
            
            # If validation failed and was handled, return the validation response
            if validation_response:
                return validation_response
        
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
        # Validate button input
        if dialog_state:  # Only validate if we have a dialog state
            validation_response = await self._validate_user_input(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                input_type=InputType.BUTTON_CLICK,
                input_value=button_value,
                dialog_state=dialog_state
            )
            
            # If validation failed and was handled, return the validation response
            if validation_response:
                return validation_response
        
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
        Uses the extracted MediaManager for all media processing.
        
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
        
        try:
            # Get MediaManager instance for this conversation context
            media_manager = self._get_media_manager(bot_id, platform, platform_chat_id)
            
            # Use MediaManager to process and send the message
            result = await media_manager.process_message_sending(
                adapter=adapter,
                platform_chat_id=platform_chat_id,
                message=message,
                buttons=buttons
            )
            
            # Return success status
            if isinstance(result, dict):
                return result.get("success", True)
            else:
                return True
                
        except Exception as e:
            self.logger.error(LogEventType.ERROR, f"Error sending message: {str(e)}")
            return False
        
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
