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
                        
                        # Generate a unique transition ID to track this chain
                        transition_id = f"auto_trans_{uuid.uuid4().hex[:8]}"
                        
                        # Reset chain position counter for a new chain
                        self._chain_position = 1
                        
                        # Get the correct auto-transition target step from the scenario
                        auto_step = await self._get_scenario_next_step(
                            bot_id=bot_id,
                            platform=platform,
                            platform_chat_id=platform_chat_id,
                            fallback_next_step=next_step
                        )
                        
                        # Handle auto-transitions that might duplicate messages
                        # Get the current step from dialog state
                        from_step = dialog_state.get("current_step") if isinstance(dialog_state, dict) else getattr(dialog_state, "current_step", "unknown")
                        
                        # Prepare thread-local context for clean auto-transition
                        if hasattr(_thread_local, 'context'):
                            # Ensure no deprecated flags are present
                            _thread_local.context = {k: v for k, v in _thread_local.context.items() 
                                                    if not k.startswith('skip_')}
                            self.logger.debug(LogEventType.AUTO_TRANSITION, 
                                             "Prepared thread-local context for auto-transition", 
                                             {"from_step": from_step, "to_step": auto_step})
                        
                        self.logger.auto_transition(
                            f"Starting auto-transition to step '{auto_step}' with delay {auto_next_delay}s",
                            {
                                "next_step": next_step, 
                                "auto_step": auto_step,
                                "delay": auto_next_delay,
                                "from_step": dialog_state.get("current_step") if isinstance(dialog_state, dict) else getattr(dialog_state, "current_step", "unknown") if dialog_state else "unknown",
                                "transition_id": transition_id,
                                "chain_position": 1,
                                "initial_step_sequence": [dialog_state.get("current_step") if isinstance(dialog_state, dict) else getattr(dialog_state, "current_step", "unknown") if dialog_state else "unknown", auto_step]
                            }
                        )
                        
                        # Wait for the specified delay
                        import asyncio
                        await asyncio.sleep(auto_next_delay)
                        
                        # Begin auto-transition processing with clean context
                        
                        # In the new architecture, auto-transitions should always be in state_only mode
                        # since DialogService has already sent the message
                        
                        # First, check if the DialogService just updated the step in the response
                        if response and "next_step" in response and response["next_step"] == auto_step:
                            is_duplicate_step = True
                            self.logger.debug(LogEventType.AUTO_TRANSITION, 
                                             f"Detected potential duplicate: DialogService just returned '{auto_step}' as next_step", 
                                             {"current_response_next_step": response["next_step"], 
                                              "auto_step": auto_step})
                        else:
                            # Otherwise check the current step in dialog state
                            current_message_step = dialog_state.get("current_step") if isinstance(dialog_state, dict) else getattr(dialog_state, "current_step", None)
                            is_duplicate_step = current_message_step == auto_step
                        
                        self.logger.debug(LogEventType.AUTO_TRANSITION, 
                                         f"Auto-transition check for duplicate step: {current_message_step} -> {auto_step}", 
                                         {"is_duplicate": is_duplicate_step})
                        
                        if is_duplicate_step:
                            # Skip the duplicate step and go directly to its next step
                            self.logger.info(LogEventType.AUTO_TRANSITION, 
                                           f"Detected duplicate step in auto-transition chain, skipping to next step",
                                           {"current_step": current_message_step, 
                                            "skipped_step": auto_step, 
                                            "transition_id": transition_id})
                            
                            # Find the next step that would follow this one
                            next_after_duplicate = await self._get_scenario_next_step(
                                bot_id=bot_id,
                                platform=platform,
                                platform_chat_id=platform_chat_id,
                                fallback_next_step=None
                            )
                            
                            if next_after_duplicate:
                                self.logger.info(LogEventType.AUTO_TRANSITION, 
                                               f"Redirecting auto-transition to '{next_after_duplicate}' to avoid duplicate",
                                               {"original_step": auto_step, 
                                                "redirected_to": next_after_duplicate, 
                                                "transition_id": transition_id})
                                
                                # Process the next step instead
                                await self._process_auto_next_step(
                                    bot_id=bot_id,
                                    platform=platform,
                                    platform_chat_id=platform_chat_id,
                                    step_id=next_after_duplicate,
                                    transition_id=transition_id,
                                    state_only=False  # Allow message sending for next step
                                )
                            else:
                                self.logger.warning(LogEventType.AUTO_TRANSITION, 
                                                 f"Cannot find next step after duplicate step '{auto_step}', stopping auto-transition",
                                                 {"transition_id": transition_id})
                        else:
                            # Check current dialog state before proceeding with auto-transition
                            current_dialog_state = await self.state_repository.get_dialog_state(
                                bot_id=bot_id,
                                platform=platform,
                                platform_chat_id=platform_chat_id
                            )
                            current_step = current_dialog_state.get("current_step") if isinstance(current_dialog_state, dict) else getattr(current_dialog_state, "current_step", None)
                            
                            # Only proceed if we're not already at the target step
                            if current_step != auto_step:
                                # Process as normal
                                await self._process_auto_next_step(
                                    bot_id=bot_id,
                                    platform=platform,
                                    platform_chat_id=platform_chat_id,
                                    step_id=auto_step,
                                    transition_id=transition_id,
                                    state_only=True  # Only update state, don't send messages
                                )
                            else:
                                self.logger.info(LogEventType.AUTO_TRANSITION, 
                                              f"Skipping redundant auto-transition to step '{auto_step}' - already at this step",
                                              {"current_step": current_step, 
                                               "auto_step": auto_step, 
                                               "transition_id": transition_id})
                        
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
                    
                    # Generate a unique transition ID to track this chain
                    transition_id = f"auto_trans_{uuid.uuid4().hex[:8]}"
                    
                    # Reset chain position counter for a new chain
                    self._chain_position = 1
                    
                    # Get the correct auto-transition target step from the scenario
                    auto_step = await self._get_scenario_next_step(
                        bot_id=bot_id,
                        platform=platform,
                        platform_chat_id=platform_chat_id,
                        fallback_next_step=next_step
                    )
                    
                    # Handle auto-transitions that might duplicate messages
                    # Get the current step from dialog state
                    from_step = dialog_state.get("current_step") if isinstance(dialog_state, dict) else getattr(dialog_state, "current_step", "unknown")
                    
                    # Prepare thread-local context for clean auto-transition
                    if hasattr(_thread_local, 'context'):
                        # Ensure no deprecated flags are present
                        _thread_local.context = {k: v for k, v in _thread_local.context.items() 
                                                if not k.startswith('skip_')}
                        self.logger.debug(LogEventType.AUTO_TRANSITION, 
                                         "Prepared thread-local context for auto-transition", 
                                         {"from_step": from_step, "to_step": auto_step})
                    
                    self.logger.auto_transition(
                        f"Starting auto-transition to step '{auto_step}' with delay {auto_next_delay}s",
                        {
                            "next_step": next_step, 
                            "auto_step": auto_step,
                            "delay": auto_next_delay,
                            "from_step": dialog_state.get("current_step") if isinstance(dialog_state, dict) else getattr(dialog_state, "current_step", "unknown") if dialog_state else "unknown",
                            "transition_id": transition_id,
                            "chain_position": 1,
                            "initial_step_sequence": [dialog_state.get("current_step") if isinstance(dialog_state, dict) else getattr(dialog_state, "current_step", "unknown") if dialog_state else "unknown", auto_step]
                        }
                    )
                    
                    # Wait for the specified delay
                    import asyncio
                    await asyncio.sleep(auto_next_delay)
                    
                    # Get current step from dialog state
                    current_step = dialog_state.get("current_step") if isinstance(dialog_state, dict) else getattr(dialog_state, "current_step", "unknown") if dialog_state else "unknown"
                    
                    # Check if the auto-transition is to the current step that just sent a message
                    is_duplicate_step = current_step == auto_step
                    
                    self.logger.debug(LogEventType.AUTO_TRANSITION, 
                                     f"Auto-transition check for duplicate step: {current_step} -> {auto_step}", 
                                     {"is_duplicate": is_duplicate_step})
                    
                    if is_duplicate_step:
                        # Skip the duplicate step and go directly to its next step
                        self.logger.info(LogEventType.AUTO_TRANSITION, 
                                       f"Detected duplicate step in auto-transition chain, skipping to next step",
                                       {"current_step": current_step, 
                                        "skipped_step": auto_step, 
                                        "transition_id": transition_id})
                        
                        # Find the next step that would follow this one
                        next_after_duplicate = await self._get_scenario_next_step(
                            bot_id=bot_id,
                            platform=platform,
                            platform_chat_id=platform_chat_id,
                            fallback_next_step=None
                        )
                        
                        if next_after_duplicate:
                            self.logger.info(LogEventType.AUTO_TRANSITION, 
                                           f"Redirecting auto-transition to '{next_after_duplicate}' to avoid duplicate",
                                           {"original_step": auto_step, 
                                            "redirected_to": next_after_duplicate, 
                                            "transition_id": transition_id})
                            
                            # Process the next step instead
                            await self._process_auto_next_step(
                                bot_id=bot_id,
                                platform=platform,
                                platform_chat_id=platform_chat_id,
                                step_id=next_after_duplicate,
                                transition_id=transition_id,
                                source_step=current_step,
                                state_only=False  # Allow message sending for next step
                            )
                        else:
                            self.logger.warning(LogEventType.AUTO_TRANSITION, 
                                             f"Cannot find next step after duplicate step '{auto_step}', stopping auto-transition",
                                             {"transition_id": transition_id})
                    else:
                        # Check current dialog state before proceeding with auto-transition
                        current_dialog_state = await self.state_repository.get_dialog_state(
                            bot_id=bot_id,
                            platform=platform,
                            platform_chat_id=platform_chat_id
                        )
                        latest_step = current_dialog_state.get("current_step") if isinstance(current_dialog_state, dict) else getattr(current_dialog_state, "current_step", None)
                        
                        # Only proceed if we're not already at the target step
                        if latest_step != auto_step:
                            # Process as normal
                            await self._process_auto_next_step(
                                bot_id=bot_id,
                                platform=platform,
                                platform_chat_id=platform_chat_id,
                                step_id=auto_step,
                                transition_id=transition_id,
                                source_step=current_step,
                                state_only=True  # Only update state, don't send messages
                            )
                        else:
                            self.logger.info(LogEventType.AUTO_TRANSITION, 
                                          f"Skipping redundant auto-transition to step '{auto_step}' - already at this step",
                                          {"current_step": latest_step, 
                                           "auto_step": auto_step, 
                                           "transition_id": transition_id})
                    
        
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
        
        # Use message text if available, otherwise use default prompt
        button_text = message_text.strip() if message_text and message_text.strip() else "Please select an option:"
        
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
            
    async def _get_scenario_next_step(
        self, 
        bot_id: UUID, 
        platform: str, 
        platform_chat_id: str,
        fallback_next_step: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the correct next step from the scenario based on current dialog state
        
        Args:
            bot_id: ID of the bot
            platform: Platform identifier
            platform_chat_id: Chat ID in the platform
            fallback_next_step: Fallback step ID to use if scenario lookup fails
            
        Returns:
            The correct next step ID, or fallback_next_step if not found
        """
        # Get the active scenario
        scenario = await ScenarioService.get_active_scenario(self.db, bot_id)
        if not scenario:
            self.logger.error(LogEventType.ERROR, "No active scenario found for bot")
            return fallback_next_step
            
        # Get the current dialog state
        dialog_state = await self.state_repository.get_dialog_state(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id
        )
        
        if not dialog_state:
            self.logger.error(LogEventType.ERROR, "Dialog state not found")
            return fallback_next_step
        
        # Get the current step ID from dialog state
        current_step_id = None
        if hasattr(dialog_state, "current_step"):
            current_step_id = dialog_state.current_step
        elif isinstance(dialog_state, dict):
            current_step_id = dialog_state.get("current_step")
        
        if not current_step_id:
            self.logger.error(LogEventType.ERROR, "Current step not found in dialog state")
            return fallback_next_step
        
        # Use ScenarioProcessor to get the full step data with proper next_step
        scenario_processor = ScenarioProcessor()
        current_collected_data = {}
        
        if hasattr(dialog_state, "collected_data"):
            current_collected_data = dialog_state.collected_data or {}
        elif isinstance(dialog_state, dict):
            current_collected_data = dialog_state.get("collected_data", {})
        
        # Process the current step to get its true next_step
        step_data = scenario_processor.process_step(
            scenario.scenario_data,
            current_step_id,
            current_collected_data
        )
        
        # Get the correct next step from the processed step data
        next_step = step_data.get("next_step_id")
        
        # Log what we determined
        self.logger.debug(LogEventType.AUTO_TRANSITION, f"Determined next step from scenario", {
            "current_step_id": current_step_id,
            "next_step_from_scenario": next_step,
            "fallback_next_step": fallback_next_step,
            "scenario": scenario.name
        })
        
        # Fall back to the provided next_step if we couldn't determine it
        if not next_step:
            next_step = fallback_next_step
            
        return next_step
            
    async def _process_auto_next_step(
        self,
        bot_id: UUID,
        platform: str,
        platform_chat_id: str,
        step_id: str,
        transition_id: str = None,
        _step_sequence: List[str] = None,  # Internal tracking of steps in sequence
        source_step: str = None,  # Track the step that initiated this transition
        state_only: bool = False  # If True, only update state without sending messages
    ) -> None:
        """
        Process a step that should be automatically transitioned to without user input.
        
        This method will be called multiple times in a chain for auto-transitions.
        
        Args:
            bot_id: ID of the bot
            platform: Platform identifier
            platform_chat_id: Chat ID in the platform
            step_id: ID of the step to process
            transition_id: Optional ID to track a chain of auto-transitions
            _step_sequence: Internal tracking of steps already processed in this chain
        """
        # Enhanced logging for auto-transition tracking
        if source_step:
            self.logger.info(LogEventType.AUTO_TRANSITION,
                          f"Auto-transition from '{source_step}' to '{step_id}'",
                          {"source_step": source_step,
                           "target_step": step_id,
                           "transition_id": transition_id})
        import asyncio
        from datetime import datetime
        import uuid
        from typing import List
        
        # Generate a transition_id if not provided to track this chain of auto-transitions
        if not transition_id:
            transition_id = f"auto_trans_{uuid.uuid4().hex[:8]}"
            
        # Initialize step sequence tracking if this is the first step in the chain
        if _step_sequence is None:
            _step_sequence = []
        
        # Add current step to the sequence
        _step_sequence.append(step_id)
        
        # Log detailed step sequence for debugging
        self.logger.debug(LogEventType.AUTO_TRANSITION, f"Auto-transition step sequence: {_step_sequence}", {
            "sequence": _step_sequence,
            "transition_id": transition_id
        })
        
        # Check if the dialog state is already at this step to avoid duplicate execution
        # This is our primary prevention mechanism for duplicate step execution
        try:
            check_dialog_state = await self.state_repository.get_dialog_state(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id
            )
            
            # Only continue if this dialog state exists
            if check_dialog_state:
                current_step = check_dialog_state.get("current_step") if isinstance(check_dialog_state, dict) else getattr(check_dialog_state, "current_step", None)
                
                # If we're already at this step, log and return early to prevent duplicate execution
                if current_step == step_id:
                    self.logger.info(LogEventType.AUTO_TRANSITION, 
                                  f"Preventing duplicate execution: dialog is already at step '{step_id}'", 
                                  {"current_step": current_step, 
                                   "target_step": step_id,
                                   "transition_id": transition_id})
                    return
        except Exception as e:
            # Log but continue - this is just a defensive check
            self.logger.warning(LogEventType.AUTO_TRANSITION, 
                             f"Error checking current step: {str(e)}", 
                             {"error": str(e)})
            
        # Get dialog state
        try:
            dialog_state = await self.state_repository.get_dialog_state(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id
            )
            
            # Log found citizenship for debugging
            citizenship = "unknown"
            if hasattr(dialog_state, "collected_data") and dialog_state.collected_data:
                citizenship = dialog_state.collected_data.get("citizenship", "unknown")
            elif isinstance(dialog_state, dict) and dialog_state.get("collected_data"):
                citizenship = dialog_state["collected_data"].get("citizenship", "unknown")
                
            # Enhanced logging for debugging conditional scenarios
            self.logger.info(LogEventType.AUTO_TRANSITION,
                           f"Processing auto-transition step with citizenship value: '{citizenship}'",
                           {"step_id": step_id,
                            "citizenship": citizenship,
                            "transition_id": transition_id})
        except Exception as e:
            # Error is already logged properly above
            self.logger.error(LogEventType.ERROR, f"Failed to retrieve dialog state in auto-transition: {str(e)}", exc_info=e)
            dialog_state = None
        
        if not dialog_state:
            self.logger.error(
                LogEventType.AUTO_TRANSITION,
                f"Failed to process auto-transition: Dialog state not found",
                {"step_id": step_id, "transition_id": transition_id}
            )
            return
            
        # Get dialog ID based on type
        dialog_id = dialog_state.id if hasattr(dialog_state, "id") else dialog_state["id"]
        
        # Set context for logging
        self.logger.set_context(dialog_id=str(dialog_id))
        
        # Log the auto-transition processing with more details
        self.logger.auto_transition(
            f"Processing auto-transition step '{step_id}'",
            {
                "step_id": step_id,
                "dialog_id": str(dialog_id),
                "transition_id": transition_id,
                "step_sequence": _step_sequence,
                "sequence_position": len(_step_sequence),
                "chain_logging_id": f"auto_chain_{transition_id}_{len(_step_sequence)}"  # Unique ID for filtering log chain
            }
        )
        
        # Get scenario
        active_scenario = await ScenarioService.get_active_scenario(self.db, bot_id)
        if not active_scenario:
            self.logger.error(
                LogEventType.AUTO_TRANSITION,
                f"Failed to process auto-transition: No active scenario found",
                {"step_id": step_id, "transition_id": transition_id}
            )
            return
            
        # Record start time for performance tracking
        start_time = datetime.now()
        
        try:
            # Update dialog state to point to the correct step for auto-transition
            from src.api.schemas.bots.dialog_schemas import BotDialogStateUpdate
            
            # Create update with new current step
            update_data = BotDialogStateUpdate(
                current_step=step_id
            )
            
            # Get the dialog state ID based on its type
            dialog_id = dialog_state.id if hasattr(dialog_state, "id") else dialog_state["id"]
            
            # Update the dialog state to the new step
            await DialogService.update_dialog_state(
                self.db, dialog_id, update_data
            )
            
            # Get the updated dialog state
            dialog_state = await DialogService.get_dialog_state_by_id(
                self.db, dialog_id
            )
            
            # Get the active scenario
            active_scenario = await ScenarioService.get_active_scenario(self.db, bot_id)
            
            # Process the step directly to get its content
            # Handle dialog_state properly based on its type (dict or Pydantic model)
            collected_data = {}
            if hasattr(dialog_state, "collected_data"):
                # It's a Pydantic model
                collected_data = dialog_state.collected_data or {}
            elif isinstance(dialog_state, dict):
                # It's a dictionary
                collected_data = dialog_state.get("collected_data", {})
                
            self.logger.debug(LogEventType.AUTO_TRANSITION, f"Processing step content for step_id '{step_id}'", {
                "transition_id": transition_id,
                "collected_data_keys": list(collected_data.keys()),
                "scenario_name": active_scenario.name,
                "scenario_id": str(active_scenario.id),
                "dialog_state_type": type(dialog_state).__name__
            })
            step_data = self.scenario_processor.process_step(
                active_scenario.scenario_data,
                step_id,
                collected_data
            )
            # Extract step type and message preview for debugging
            step_type = step_data.get("current_step_type", "unknown")
            message_text = "No message"
            if step_data.get("message") and "text" in step_data.get("message"):
                message_text = step_data["message"]["text"]
                message_preview = (message_text[:100] + "...") if len(message_text) > 100 else message_text
            else:
                message_preview = "No message text"
                
            # Enhanced logging for step content in auto-transitions
            self.logger.info(LogEventType.AUTO_TRANSITION,
                          f"Step content for '{step_id}': Type={step_type}",
                          {"step_id": step_id,
                           "step_type": step_type,
                           "message_preview": message_preview[:100] + "..." if len(message_preview) > 100 else message_preview,
                           "has_buttons": step_data.get("buttons") is not None,
                           "transition_id": transition_id})
                
            self.logger.debug(LogEventType.AUTO_TRANSITION, f"Step content processed successfully", {
                "transition_id": transition_id,
                "has_message": step_data.get("message") is not None,
                "has_buttons": step_data.get("buttons") is not None,
                "next_step_id": step_data.get("next_step_id"),
                "error": step_data.get("error"),
                "step_type": step_type,
                "message_preview": message_preview,
                "critical_debug": True,
                "is_conditional": step_type == "conditional_message"
            })
            
            # Create an empty input to simulate user input for auto-transition
            # We use a special marker value to indicate this is an auto-transition
            empty_input = "@AUTO_TRANSITION@"
            
            # Log the current state before processing
            self.logger.debug(LogEventType.AUTO_TRANSITION, f"Before DialogService.process_user_input for step '{step_id}'", {
                "current_step": step_id,
                "transition_id": transition_id,
                "sequence": _step_sequence
            })
            
            # Get the platform adapter that we'll need later
            adapter = await self.get_platform_adapter(platform)
            if not adapter:
                self.logger.error(LogEventType.ERROR, f"No adapter registered for platform {platform}")
                return
            
            # Process the step through DialogService - this will handle state updates
            # If state_only is True, we only update state without sending messages
            empty_input_marker = "@AUTO_TRANSITION_NO_MESSAGE@" if state_only else "@AUTO_TRANSITION@"
            response = await DialogService.process_user_input(
                self.db, bot_id, platform, platform_chat_id, empty_input_marker
            )
            
            # Log the response for debugging
            next_step_in_response = response.get("next_step") if response else None
            self.logger.debug(LogEventType.AUTO_TRANSITION, f"After DialogService.process_user_input for step '{step_id}'", {
                "next_step_from_response": next_step_in_response,
                "original_next_step_from_step_data": step_data.get("next_step_id"),
                "has_response": response is not None,
                "transition_id": transition_id,
                "sequence": _step_sequence
            })
            
            # Preserve next_step from scenario processing when DialogService returns None
            original_next_step = step_data.get("next_step_id")
            if not next_step_in_response and original_next_step:
                self.logger.info(LogEventType.AUTO_TRANSITION, 
                                f"Preserving original next_step from scenario data: '{original_next_step}'", 
                                {"original_next_step": original_next_step, 
                                 "transition_id": transition_id})
                
                # Update the response to include the correct next_step from step_data
                if response:
                    # Store the original response next_step for logging
                    original_response_next_step = response.get("next_step")
                    
                    # Update with the preserved next_step from scenario
                    response["next_step"] = original_next_step
                    
                    # Add more detailed logging about the replacement
                    if original_response_next_step != original_next_step:
                        self.logger.debug(LogEventType.AUTO_TRANSITION, 
                                         f"Replaced response next_step '{original_response_next_step}' with '{original_next_step}'",
                                         {"original_response_next_step": original_response_next_step,
                                          "preserved_next_step": original_next_step,
                                          "step_id": step_id,
                                          "transition_id": transition_id})
            
            # Always prioritize the current step's content for display in auto-transitions
            # This ensures conditional messages are displayed before proceeding to the next step
            step_message = step_data.get("message")
            
            # Check if this is a conditional_message step that has matched a condition
            if step_data.get("message") is not None:
                # Log detailed information about using the step's content
                step_type = step_data.get("current_step_type", "unknown")
                message_text = "No message text"
                if step_message and "text" in step_message:
                    message_text = (step_message["text"][:100] + "...") if len(step_message["text"]) > 100 else step_message["text"]
                
                self.logger.info(LogEventType.AUTO_TRANSITION, "Using step content for display in auto-transition", {
                    "transition_id": transition_id,
                    "step_id": step_id,
                    "step_type": step_type,
                    "has_step_message": step_message is not None,
                    "has_response": response is not None,
                    "response_next_step": response.get("next_step") if response else None,
                    "step_data_next_step": step_data.get("next_step_id"),
                    "message_preview": message_text,
                    "is_conditional_message": step_type == "conditional_message",
                    "chain_logging_id": f"auto_chain_{transition_id}",
                    "collected_data_keys": list(collected_data.keys()) if hasattr(dialog_state, "collected_data") and dialog_state.collected_data else []
                })
                
                # For conditional message steps, ensure we have a valid next_step
                response_next_step = response.get("next_step") if response else None
                step_data_next_step = step_data.get("next_step_id")
                
                # First try to use response next_step, fall back to step_data if needed
                next_step = response_next_step if response_next_step else step_data_next_step
                
                # Extract citizenship for enhanced debugging of conditional messages
                citizenship = "unknown"
                if hasattr(dialog_state, "collected_data") and dialog_state.collected_data:
                    citizenship = dialog_state.collected_data.get("citizenship", "unknown")
                elif isinstance(dialog_state, dict) and dialog_state.get("collected_data"):
                    citizenship = dialog_state["collected_data"].get("citizenship", "unknown")
                
                # Enhanced logging for conditional message next_step resolution
                self.logger.info(LogEventType.AUTO_TRANSITION, 
                              f"Selected next_step '{next_step}' for conditional message with citizenship={citizenship}", 
                              {"from_response": response_next_step,
                               "from_step_data": step_data_next_step,
                               "final_selection": next_step,
                               "citizenship_value": citizenship,
                               "step_type": step_data.get("current_step_type"),
                               "transition_id": transition_id})
                
                response = {
                    "message": step_message,
                    "buttons": step_data.get("buttons", []),
                    "next_step": next_step,
                    "auto_next": step_data.get("auto_next", False),
                    "auto_next_delay": step_data.get("auto_next_delay", 1.5)
                }
            # If no message in current step, fall back to original logic for handling empty responses
            elif not response or not response.get("message") or response.get("message", {}).get("text", "") == "I'm not sure what to do next.":
                # Log detailed information about the fallback scenario
                self.logger.info(LogEventType.AUTO_TRANSITION, "Using directly processed step content instead of DialogService response", {
                    "transition_id": transition_id,
                    "step_id": step_id,
                    "response_status": "fallback",
                    "has_response": response is not None,
                    "response_message_text": response.get("message", {}).get("text", "") if response else "None",
                    "step_data_message": step_data.get("message", {}).get("text", "") if step_data.get("message") else "None"
                })
                
                # Replace the response with our directly processed step data
                response = {
                    "message": step_data.get("message", {}),
                    "buttons": step_data.get("buttons", []),
                    "next_step": step_data.get("next_step_id"),
                    "auto_next": step_data.get("auto_next", False),
                    "auto_next_delay": step_data.get("auto_next_delay", 1.5)
                }
            
            if not response:
                self.logger.error(
                    LogEventType.AUTO_TRANSITION,
                    f"Auto-transition failed: No response from DialogService",
                    {"step_id": step_id, "transition_id": transition_id}
                )
                return
                
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000  # in ms
            
            # Send the message
            message = response.get("message", {})
            buttons = response.get("buttons", [])
            next_step = response.get("next_step")
            auto_next = response.get("auto_next", False)
            auto_next_delay = response.get("auto_next_delay", 1.5)
            
            # Log successful auto-transition
            self.logger.auto_transition(
                f"Auto-transition completed for step '{step_id}'",
                {
                    "step_id": step_id,
                    "next_step": next_step,
                    "has_auto_next": auto_next,
                    "transition_id": transition_id,
                    "execution_time_ms": execution_time,
                    "step_sequence": _step_sequence,
                    "sequence_position": len(_step_sequence)
                }
            )
            
            # Send the message to the user
            if message:
                # Initialize sent variable to avoid UnboundLocalError
                sent = True  # Default to True when skipping message send
                
                # Convert dictionary message to appropriate format
                if isinstance(message, dict):
                    message_text = message.get("text", "")
                    media = message.get("media", [])
                    
                    # Extract citizenship data for enhanced logging if available
                    citizenship = "unknown"
                    if hasattr(dialog_state, "collected_data") and dialog_state.collected_data:
                        citizenship = dialog_state.collected_data.get("citizenship", "unknown")
                    elif isinstance(dialog_state, dict) and dialog_state.get("collected_data"):
                        citizenship = dialog_state["collected_data"].get("citizenship", "unknown")
                    
                    # Log auto-transition outgoing message with enhanced details
                    self.logger.auto_transition_message(message_text, {
                        "has_buttons": bool(buttons),
                        "buttons": [btn.get("text", "") if isinstance(btn, dict) else btn for btn in buttons] if buttons else [],
                        "has_media": bool(media),
                        "media_count": len(media) if media else 0,
                        "transition_id": transition_id,
                        "step_id": step_id,
                        "next_step": next_step,
                        "message_preview": (message_text[:100] + "...") if message_text and len(message_text) > 100 else message_text,
                        "chain_logging_id": f"auto_chain_{transition_id}",
                        "step_type": step_data.get("current_step_type") if step_data else "unknown",
                        "citizenship_value": citizenship,
                        "sequence_position": len(_step_sequence) if _step_sequence else 0
                    })
                    
                    # Message sending is controlled by the state_only parameter
                    if state_only:
                        self.logger.debug(LogEventType.AUTO_TRANSITION,
                                       f"Message sending disabled for step {step_id} (state_only mode)",
                                       {"transition_id": transition_id, 
                                        "step_id": step_id,
                                        "chain_position": len(_step_sequence) if _step_sequence else 0})
                    else:
                        # Send message with proper media handling
                        if media:
                            sent = await self.send_message(
                                bot_id=bot_id,
                                platform=platform,
                                platform_chat_id=platform_chat_id,
                                message={
                                    "text": message_text,
                                    "media": media
                                },
                                buttons=buttons
                            )
                        else:
                            # No media
                            if buttons:
                                sent = await adapter.send_buttons(
                                    chat_id=platform_chat_id,
                                    text=message_text,
                                    buttons=buttons
                                )
                            else:
                                sent = await adapter.send_text_message(
                                    chat_id=platform_chat_id,
                                    text=message_text
                                )
                        
                    # Ensure thread-local context is clean after message sending
                    if hasattr(_thread_local, 'context'):
                        # Remove any skip flags that might still be present
                        _thread_local.context = {k: v for k, v in _thread_local.context.items() 
                                                if not k.startswith('skip_')}
                        self.logger.debug(LogEventType.AUTO_TRANSITION, 
                            "Ensured clean context after message sending", 
                            {"step_id": step_id, "transition_id": transition_id})
                else:
                    # If message is already in the right format, send it directly
                    sent = await self.send_message(
                        bot_id=bot_id,
                        platform=platform,
                        platform_chat_id=platform_chat_id,
                        message=message,
                        buttons=buttons
                    )
                
                if isinstance(sent, dict) and not sent.get("success", False):
                    # Check if retry is recommended (e.g., network timeout)
                    retry_recommended = sent.get("retry_recommended", False)
                    
                    if retry_recommended:
                        self.logger.warning(
                            LogEventType.AUTO_TRANSITION,
                            f"Failed to send message for auto-transition but continuing (network issue)",
                            {"step_id": step_id, "transition_id": transition_id, "retry_recommended": True}
                        )
                    else:
                        self.logger.error(
                            LogEventType.AUTO_TRANSITION,
                            f"Failed to send message for auto-transition",
                            {"step_id": step_id, "transition_id": transition_id}
                        )
                    
            # Update dialog state with the correct next step from the processed step
            if next_step:
                # Create update with new current step
                update_data = BotDialogStateUpdate(
                    current_step=next_step
                )
                
                # Get the dialog state ID based on its type
                dialog_id = dialog_state.id if hasattr(dialog_state, "id") else dialog_state["id"]
                
                # Update the dialog state to the next step
                await DialogService.update_dialog_state(
                    self.db, dialog_id, update_data
                )
            
            # Final verification: ensure we have a valid next_step for auto-transitions
            if not next_step and step_data and step_data.get("next_step_id"):
                next_step = step_data.get("next_step_id")
                self.logger.info(LogEventType.AUTO_TRANSITION, 
                               f"Fallback to original next_step from step_data: '{next_step}'", 
                               {"fallback_next_step": next_step, 
                                "transition_id": transition_id})
            
            # Check if this step also has auto_next and continue the chain if needed
            if auto_next and next_step:
                # Log the next auto-transition in chain
                # Extract citizenship data for enhanced logging
                citizenship = "unknown"
                if hasattr(dialog_state, "collected_data") and dialog_state.collected_data:
                    citizenship = dialog_state.collected_data.get("citizenship", "unknown")
                elif isinstance(dialog_state, dict) and dialog_state.get("collected_data"):
                    citizenship = dialog_state["collected_data"].get("citizenship", "unknown")
                    
                # Log with very detailed information for debugging
                self.logger.auto_transition(
                    f"Continuing auto-transition chain to step '{next_step}'",
                    {
                        "next_step": next_step,
                        "delay": auto_next_delay,
                        "from_step": step_id,
                        "transition_id": transition_id,
                        "chain_position": getattr(self, "_chain_position", 1) + 1,
                        "chain_logging_id": f"auto_chain_{transition_id}",
                        "citizenship_value": citizenship,
                        "next_step_type": "to_be_determined",  # Will be determined when next step is processed
                        "current_step_type": step_data.get("current_step_type") if step_data else "unknown",
                        "full_trace": True  # Mark this as part of the full trace for filtering logs
                    }
                )
                
                # Increment chain position counter
                self._chain_position = getattr(self, "_chain_position", 1) + 1
                
                # Check for maximum chain length to prevent infinite loops
                if self._chain_position > 10:  # Limit to 10 auto-transitions in a row
                    self.logger.warning(
                        LogEventType.AUTO_TRANSITION,
                        f"Auto-transition chain limit reached (10 steps), stopping chain",
                        {"transition_id": transition_id, "chain_length": self._chain_position}
                    )
                    return
                    
                # Log chain continuation 
                self.logger.info(LogEventType.AUTO_TRANSITION, 
                             f"Auto-transition chain continuation scheduled after {auto_next_delay}s delay", 
                             {
                                 "next_step": next_step,
                                 "delay": auto_next_delay,
                                 "transition_id": transition_id,
                                 "chain_position": getattr(self, "_chain_position", 1),
                                 "chain_tracking_id": f"chain_{transition_id}",
                                 "citizenship_value": citizenship
                             })

                # Pre-delay logging is handled by the auto_transition logger call above
                                
                # Wait for the specified delay
                try:
                    await asyncio.sleep(auto_next_delay)
                    
                    # Log continuation of auto-transition chain after delay
                    self.logger.info(LogEventType.AUTO_TRANSITION, 
                                 f"Auto-transition delay completed, continuing to step '{next_step}'", 
                                 {
                                     "next_step": next_step,
                                     "transition_id": transition_id,
                                     "delay_completed": True,
                                     "chain_tracking_id": f"chain_{transition_id}",
                                     "citizenship_value": citizenship,
                                     "source_step": step_id
                                 })
                    
                    # Ensure thread-local context is clean before continuing the chain
                    if hasattr(_thread_local, 'context'):
                        # Remove any skip flags that might still be present
                        _thread_local.context = {k: v for k, v in _thread_local.context.items() 
                                                if not k.startswith('skip_')}
                        self.logger.debug(LogEventType.AUTO_TRANSITION, 
                                        "Prepared clean context before continuing chain", 
                                        {"next_step": next_step, "transition_id": transition_id})
                        
                    # Process the next auto-transition, passing the step sequence
                    await self._process_auto_next_step(
                        bot_id=bot_id,
                        platform=platform,
                        platform_chat_id=platform_chat_id,
                        step_id=next_step,
                        transition_id=transition_id,
                        _step_sequence=_step_sequence,
                        state_only=False  # Allow message sending for the next step in chain
                    )
                except Exception as e:
                    import traceback
                    # Catch and log any exceptions in the auto-transition process at ERROR level to make sure they're visible
                    self.logger.error(LogEventType.ERROR, 
                                     f"CRITICAL ERROR IN AUTO-TRANSITION CHAIN: {str(e)}", 
                                     {"error": str(e), 
                                      "transition_id": transition_id,
                                      "next_step": next_step,
                                      "exception_details": traceback.format_exc()}, 
                                     exc_info=e)
        except Exception as e:
            # Log auto-transition error
            self.logger.error(
                LogEventType.AUTO_TRANSITION,
                f"Error during auto-transition for step '{step_id}': {str(e)}",
                {"step_id": step_id, "error": str(e), "transition_id": transition_id},
                exc_info=e
            )
            
            # Update state to indicate auto-transition failure
            dialog_state = await self.state_repository.get_dialog_state(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id
            )
            if dialog_state:
                # Handle dialog state based on its type
                if hasattr(dialog_state, "metadata"):
                    # Pydantic model
                    metadata = dialog_state.metadata or {}
                    metadata["auto_transition_error"] = {
                        "step_id": step_id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    # Create a proper update
                    from src.api.schemas.bots.dialog_schemas import BotDialogStateUpdate
                    update_data = BotDialogStateUpdate(metadata=metadata)
                    dialog_id = dialog_state.id
                    await DialogService.update_dialog_state(self.db, dialog_id, update_data)
                else:
                    # Dictionary
                    dialog_state["metadata"] = dialog_state.get("metadata", {}) or {}
                    dialog_state["metadata"]["auto_transition_error"] = {
                        "step_id": step_id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.state_repository.update_dialog_state(dialog_state)