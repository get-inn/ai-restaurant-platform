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
            self.logger.error(LogEventType.ERROR, f"No adapter registered for platform {platform}")
            return False
        
        # We no longer skip sending messages in auto-transitions
        # This ensures all messages in the chain are properly delivered
        
        # Handle different types of message input
        if isinstance(message, str):
            # String message - convert to text only
            message_text = message
            media = []
        elif isinstance(message, dict):
            # Dictionary message - extract text and media
            message_text = message.get("text", "")
            media = message.get("media", [])
        else:
            # Assume it's a DialogMessage object
            message_text = getattr(message, 'text', "")
            # Check for media in the message object
            media = getattr(message, 'media', [])
            
        # Always log outgoing messages from dialog manager, regardless of context
        # This ensures all messages are properly tracked and visible in logs
        button_texts = [btn.get("text", "") if isinstance(btn, dict) else btn["text"] for btn in buttons] if buttons else []
        log_data = {
            "has_buttons": bool(buttons),
            "buttons": button_texts,
            "has_media": bool(media),
            "media_count": len(media) if media else 0,
            "platform": platform,
            "platform_chat_id": platform_chat_id,
            "bot_id": str(bot_id)
        }
        
        # Log all messages - no skipping based on flags
        self.logger.outgoing_message(message_text, log_data)
        
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
                        # If there's media, send as a combined message
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
                            sent = await self.send_message(
                                bot_id=bot_id,
                                platform=platform,
                                platform_chat_id=platform_chat_id,
                                message=message_text,
                                buttons=buttons
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