"""
Unit tests for auto-transition functionality in the bot management system.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, ANY
from uuid import UUID, uuid4
from datetime import datetime

from src.bot_manager.dialog_manager import DialogManager
from src.bot_manager.scenario_processor import ScenarioProcessor
from src.bot_manager.state_repository import StateRepository
from src.bot_manager.conversation_logger import LogEventType


@pytest.fixture
def dialog_manager():
    """Create a DialogManager with mocked dependencies"""
    db = AsyncMock()
    platform_adapters = {"telegram": AsyncMock()}
    state_repository = AsyncMock(spec=StateRepository)
    scenario_processor = AsyncMock(spec=ScenarioProcessor)
    
    # Mock the get_logger method
    logger = MagicMock()
    with patch("src.bot_manager.dialog_manager.get_logger", return_value=logger):
        dm = DialogManager(
            db=db,
            platform_adapters=platform_adapters,
            state_repository=state_repository,
            scenario_processor=scenario_processor
        )
    
    return dm


@pytest.fixture
def response_with_auto_next():
    """Create a sample response with auto_next enabled"""
    return {
        "message": {
            "text": "This is an auto-transition message",
            "media": []
        },
        "buttons": [],
        "next_step": "next_auto_step",
        "auto_next": True,
        "auto_next_delay": 0.1  # Short delay for tests
    }


@pytest.mark.asyncio
async def test_process_auto_next_step(dialog_manager):
    """Test the _process_auto_next_step method"""
    # Setup
    bot_id = uuid4()
    platform = "telegram"
    platform_chat_id = "123456"
    step_id = "auto_step"
    transition_id = "test_transition"
    
    # Mock dialog state
    dialog_state = {
        "id": uuid4(),
        "bot_id": bot_id,
        "platform": platform,
        "platform_chat_id": platform_chat_id,
        "current_step": "current_step",
        "collected_data": {}
    }
    dialog_manager.state_repository.get_dialog_state.return_value = dialog_state
    
    # Mock scenario
    scenario = MagicMock()
    scenario_service_mock = AsyncMock()
    scenario_service_mock.get_active_scenario.return_value = scenario
    
    # Mock DialogService
    dialog_service_mock = AsyncMock()
    dialog_service_mock.process_user_input.return_value = {
        "message": {"text": "Auto-transition response"},
        "buttons": [],
        "next_step": "next_step",
        "auto_next": False
    }
    
    # Call the method
    with patch("src.bot_manager.dialog_manager.ScenarioService.get_active_scenario", 
               scenario_service_mock.get_active_scenario), \
         patch("src.bot_manager.dialog_manager.DialogService.process_user_input", 
               dialog_service_mock.process_user_input), \
         patch.object(dialog_manager, "send_message", AsyncMock(return_value=True)):
        
        await dialog_manager._process_auto_next_step(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            step_id=step_id,
            transition_id=transition_id
        )
    
    # Verify
    dialog_manager.state_repository.get_dialog_state.assert_called_once_with(
        bot_id=bot_id, platform=platform, platform_chat_id=platform_chat_id
    )
    scenario_service_mock.get_active_scenario.assert_called_once_with(dialog_manager.db, bot_id)
    dialog_service_mock.process_user_input.assert_called_once_with(
        dialog_manager.db, bot_id, platform, platform_chat_id, "@AUTO_TRANSITION@"
    )
    dialog_manager.send_message.assert_called_once()
    dialog_manager.logger.auto_transition.assert_called()


@pytest.mark.asyncio
async def test_auto_transition_chain(dialog_manager):
    """Test a chain of auto-transitions"""
    # Setup
    bot_id = uuid4()
    platform = "telegram"
    platform_chat_id = "123456"
    step_id = "auto_step_1"
    
    # Mock dialog state
    dialog_state = {
        "id": uuid4(),
        "bot_id": bot_id,
        "platform": platform,
        "platform_chat_id": platform_chat_id,
        "current_step": "current_step",
        "collected_data": {}
    }
    dialog_manager.state_repository.get_dialog_state.return_value = dialog_state
    
    # Mock scenario
    scenario = MagicMock()
    scenario_service_mock = AsyncMock()
    scenario_service_mock.get_active_scenario.return_value = scenario
    
    # Mock DialogService responses for chained auto-transitions
    # First response (auto-transition)
    response1 = {
        "message": {"text": "Auto-transition 1"},
        "buttons": [],
        "next_step": "auto_step_2",
        "auto_next": True,
        "auto_next_delay": 0.1  # Short delay for tests
    }
    
    # Second response (auto-transition)
    response2 = {
        "message": {"text": "Auto-transition 2"},
        "buttons": [],
        "next_step": "auto_step_3",
        "auto_next": True,
        "auto_next_delay": 0.1  # Short delay for tests
    }
    
    # Third response (final, no auto-transition)
    response3 = {
        "message": {"text": "Final message"},
        "buttons": [],
        "next_step": "next_regular_step",
        "auto_next": False
    }
    
    dialog_service_mock = AsyncMock()
    dialog_service_mock.process_user_input.side_effect = [response1, response2, response3]
    
    # Call the method
    with patch("src.bot_manager.dialog_manager.ScenarioService.get_active_scenario", 
               scenario_service_mock.get_active_scenario), \
         patch("src.bot_manager.dialog_manager.DialogService.process_user_input", 
               dialog_service_mock.process_user_input), \
         patch.object(dialog_manager, "send_message", AsyncMock(return_value=True)), \
         patch("asyncio.sleep", AsyncMock()):  # Skip sleep delay for faster tests
        
        await dialog_manager._process_auto_next_step(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            step_id=step_id
        )
    
    # Verify
    assert dialog_service_mock.process_user_input.call_count == 3
    assert dialog_manager.send_message.call_count == 3
    assert dialog_manager.logger.auto_transition.call_count >= 6  # At least 6 logs (2 per transition)


@pytest.mark.asyncio
async def test_handle_text_message_with_auto_next(dialog_manager):
    """Test that handle_text_message correctly triggers auto-transitions"""
    # Setup
    bot_id = uuid4()
    platform = "telegram"
    platform_chat_id = "123456"
    text = "test message"
    
    # Mock dialog state
    dialog_state = {
        "id": uuid4(),
        "bot_id": bot_id,
        "platform": platform,
        "platform_chat_id": platform_chat_id,
        "current_step": "current_step",
        "collected_data": {}
    }
    
    # Mock response with auto_next
    response = {
        "message": {"text": "Response with auto-next"},
        "buttons": [],
        "next_step": "auto_step",
        "auto_next": True,
        "auto_next_delay": 0.1  # Short delay for tests
    }
    
    dialog_service_mock = AsyncMock()
    dialog_service_mock.process_user_input.return_value = response
    
    # Mock send_message
    send_message_mock = AsyncMock(return_value=True)
    
    # Mock _process_auto_next_step
    process_auto_next_mock = AsyncMock()
    
    # Call the method
    with patch("src.bot_manager.dialog_manager.DialogService.process_user_input", 
               dialog_service_mock.process_user_input), \
         patch.object(dialog_manager, "send_message", send_message_mock), \
         patch.object(dialog_manager, "_process_auto_next_step", process_auto_next_mock), \
         patch("asyncio.sleep", AsyncMock()):  # Skip sleep delay for faster tests
        
        result = await dialog_manager.handle_text_message(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            text=text,
            dialog_state=dialog_state
        )
    
    # Verify
    dialog_service_mock.process_user_input.assert_called_once_with(
        dialog_manager.db, bot_id, platform, platform_chat_id, text
    )
    send_message_mock.assert_called_once()
    process_auto_next_mock.assert_called_once()
    assert result == response


@pytest.mark.asyncio
async def test_error_handling_in_auto_transition(dialog_manager):
    """Test error handling during auto-transition"""
    # Setup
    bot_id = uuid4()
    platform = "telegram"
    platform_chat_id = "123456"
    step_id = "error_step"
    
    # Mock dialog state
    dialog_state = {
        "id": uuid4(),
        "bot_id": bot_id,
        "platform": platform,
        "platform_chat_id": platform_chat_id,
        "current_step": "current_step",
        "collected_data": {},
        "metadata": {}
    }
    dialog_manager.state_repository.get_dialog_state.return_value = dialog_state
    
    # Mock scenario
    scenario = MagicMock()
    scenario_service_mock = AsyncMock()
    scenario_service_mock.get_active_scenario.return_value = scenario
    
    # Mock DialogService to raise an exception
    dialog_service_mock = AsyncMock()
    dialog_service_mock.process_user_input.side_effect = Exception("Test error")
    
    # Call the method
    with patch("src.bot_manager.dialog_manager.ScenarioService.get_active_scenario", 
               scenario_service_mock.get_active_scenario), \
         patch("src.bot_manager.dialog_manager.DialogService.process_user_input", 
               dialog_service_mock.process_user_input):
        
        await dialog_manager._process_auto_next_step(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            step_id=step_id
        )
    
    # Verify error was logged
    dialog_manager.logger.error.assert_called_with(
        LogEventType.AUTO_TRANSITION,
        f"Error during auto-transition for step '{step_id}': Test error",
        {"step_id": step_id, "error": "Test error", "transition_id": ANY},
        exc_info=ANY
    )
    
    # Verify error was stored in dialog state metadata
    dialog_manager.state_repository.update_dialog_state.assert_called_once()
    update_call_args = dialog_manager.state_repository.update_dialog_state.call_args[0][0]
    assert "metadata" in update_call_args
    assert "auto_transition_error" in update_call_args["metadata"]
    assert update_call_args["metadata"]["auto_transition_error"]["step_id"] == step_id


if __name__ == "__main__":
    pytest.main(["-v", "test_auto_transition.py"])