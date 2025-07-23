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
        self.logger.debug(LogEventType.STATE, "Retrieving dialog state")
        dialog_state = await self.state_repository.get_dialog_state(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id
        )
        
        # Update logger with dialog_id if available
        if dialog_state and "id" in dialog_state:
            self.logger.set_context(dialog_id=str(dialog_state["id"]))
            self.logger.debug(LogEventType.STATE, "Retrieved existing dialog state", {
                "current_step": dialog_state.get("current_step"),
                "collected_data_keys": list(dialog_state.get("collected_data", {}).keys()) 
            })
        else:
            self.logger.debug(LogEventType.STATE, "No existing dialog state found")
        
        # Handle message based on type
        if message_type == "message" and content.get("type") == "text":
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
                    
                    if buttons:
                        formatted_buttons = [
                            {"text": btn.get("text", ""), "value": btn.get("value", "")}
                            for btn in buttons
                        ]
                        
                        self.logger.debug(LogEventType.ADAPTER, f"Sending message with {len(buttons)} buttons")
                        self.logger.outgoing_message(message_text, {
                            "buttons": [b.get("text") for b in buttons],
                            "has_buttons": True
                        })
                        
                        await adapter.send_buttons(
                            chat_id=platform_chat_id,
                            text=message_text,
                            buttons=formatted_buttons
                        )
                    else:
                        self.logger.debug(LogEventType.ADAPTER, "Sending text message")
                        self.logger.outgoing_message(message_text)
                        
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
        else:
            message_text = message.text
        
        if buttons:
            result = await adapter.send_buttons(
                chat_id=platform_chat_id,
                text=message_text,
                buttons=buttons
            )
        else:
            result = await adapter.send_text_message(
                chat_id=platform_chat_id,
                text=message_text
            )
            
        return result.get("success", False)