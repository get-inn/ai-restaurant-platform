"""
Integration tests for auto-transition functionality in the bot management system.
"""

import pytest
import asyncio
from uuid import UUID, uuid4
from datetime import datetime
import json
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models import BotInstance, BotScenario, BotDialogState, BotPlatformCredential
from src.api.schemas.bots.instance_schemas import BotInstanceCreate
from src.api.schemas.bots.scenario_schemas import BotScenarioCreate
from src.bot_manager.dialog_manager import DialogManager
from src.bot_manager.conversation_logger import get_logger, LogEventType


@pytest.fixture
def auto_transition_scenario():
    """Create a test scenario with auto-transitions"""
    return {
        "version": "1.0",
        "name": "Auto-Transition Test Bot",
        "description": "Test scenario for auto-transition functionality",
        "start_step": "welcome",
        "steps": {
            "welcome": {
                "id": "welcome",
                "type": "message",
                "message": {
                    "text": "Welcome to the auto-transition test!"
                },
                "next_step": "auto_step_1",
                "auto_next": True,
                "auto_next_delay": 0.1  # Short delay for tests
            },
            "auto_step_1": {
                "id": "auto_step_1",
                "type": "message",
                "message": {
                    "text": "This is the first auto-transition."
                },
                "next_step": "auto_step_2",
                "auto_next": True,
                "auto_next_delay": 0.1  # Short delay for tests
            },
            "auto_step_2": {
                "id": "auto_step_2",
                "type": "message",
                "message": {
                    "text": "This is the second auto-transition."
                },
                "next_step": "input_step",
                "auto_next": False
            },
            "input_step": {
                "id": "input_step",
                "type": "message",
                "message": {
                    "text": "Please type your name:"
                },
                "expected_input": {
                    "type": "text",
                    "variable": "user_name"
                },
                "next_step": "thank_you"
            },
            "thank_you": {
                "id": "thank_you",
                "type": "message",
                "message": {
                    "text": "Thank you, {{user_name}}!"
                },
                "next_step": "auto_step_3",
                "auto_next": True,
                "auto_next_delay": 0.1  # Short delay for tests
            },
            "auto_step_3": {
                "id": "auto_step_3",
                "type": "message",
                "message": {
                    "text": "This is an auto-transition after user input."
                },
                "next_step": "final"
            },
            "final": {
                "id": "final",
                "type": "message",
                "message": {
                    "text": "Test completed."
                }
            }
        }
    }


@pytest.mark.asyncio
async def test_auto_transition_flow(db_session: AsyncSession, client: AsyncClient, app: FastAPI, auto_transition_scenario):
    """Test the complete flow of auto-transitions in a real scenario"""
    # Create a test bot
    bot_name = f"test-auto-transition-bot-{uuid4()}"
    bot_create = BotInstanceCreate(
        name=bot_name,
        description="Test bot for auto-transitions",
        is_active=True
    )
    
    # Create bot instance
    bot_response = await client.post(
        "/v1/api/bots/",
        json=bot_create.model_dump()
    )
    assert bot_response.status_code == 200
    bot_data = bot_response.json()
    bot_id = UUID(bot_data["id"])
    
    # Create a test scenario with auto-transitions
    scenario_create = BotScenarioCreate(
        bot_id=bot_id,
        name="Auto-Transition Test Scenario",
        description="Test scenario for auto-transition functionality",
        scenario_data=auto_transition_scenario,
        is_active=True
    )
    
    # Create scenario
    scenario_response = await client.post(
        f"/v1/api/bots/{bot_id}/scenarios/",
        json=scenario_create.model_dump()
    )
    assert scenario_response.status_code == 200
    scenario_data = scenario_response.json()
    scenario_id = UUID(scenario_data["id"])
    
    # Create a test platform for the bot
    platform_name = "telegram"
    platform_chat_id = f"test_chat_{uuid4().hex}"
    
    # Initialize DialogManager
    dialog_manager = DialogManager(db=db_session)
    
    # Mock platform adapter
    mock_adapter = type("MockAdapter", (), {
        "process_update": lambda self, update_data: {"type": "message", "content": {"type": "text", "text": update_data}},
        "send_text_message": lambda self, chat_id, text: {"success": True, "message_id": f"msg_{uuid4().hex}"},
        "send_buttons": lambda self, chat_id, text, buttons: {"success": True, "message_id": f"msg_{uuid4().hex}"}
    })()
    await dialog_manager.register_platform_adapter(platform_name, mock_adapter)
    
    # Test the auto-transition flow
    # First message to start the conversation
    response = await dialog_manager.process_incoming_message(
        bot_id=bot_id,
        platform=platform_name,
        platform_chat_id=platform_chat_id,
        update_data="/start"
    )
    
    assert response is not None
    assert "message" in response
    assert response["message"].get("text") == "Welcome to the auto-transition test!"
    assert "auto_next" in response and response["auto_next"] == True
    
    # Wait a bit to let auto-transitions happen
    await asyncio.sleep(0.5)
    
    # Verify that dialog state has progressed through the auto-transition chain
    dialog_states_query = await db_session.execute(
        "SELECT current_step FROM bot_dialog_state WHERE platform_chat_id = :chat_id",
        {"chat_id": platform_chat_id}
    )
    dialog_state_result = dialog_states_query.first()
    assert dialog_state_result is not None
    
    # The state should have advanced to input_step after auto-transitions
    assert dialog_state_result[0] == "input_step"
    
    # Now send a message to continue the conversation
    response = await dialog_manager.process_incoming_message(
        bot_id=bot_id,
        platform=platform_name,
        platform_chat_id=platform_chat_id,
        update_data="Test User"
    )
    
    assert response is not None
    assert "message" in response
    assert "Thank you, Test User!" in response["message"].get("text", "")
    assert "auto_next" in response and response["auto_next"] == True
    
    # Wait a bit to let the final auto-transition happen
    await asyncio.sleep(0.3)
    
    # Verify that dialog state has progressed to the final step
    dialog_states_query = await db_session.execute(
        "SELECT current_step FROM bot_dialog_state WHERE platform_chat_id = :chat_id",
        {"chat_id": platform_chat_id}
    )
    dialog_state_result = dialog_states_query.first()
    assert dialog_state_result is not None
    
    # The state should have advanced to auto_step_3 after the final auto-transition
    assert dialog_state_result[0] == "auto_step_3"


@pytest.mark.asyncio
async def test_auto_transition_history(db_session: AsyncSession, client: AsyncClient, app: FastAPI, auto_transition_scenario):
    """Test that auto-transitions are properly recorded in dialog history"""
    # Create a test bot
    bot_name = f"test-auto-history-bot-{uuid4()}"
    bot_create = BotInstanceCreate(
        name=bot_name,
        description="Test bot for auto-transition history",
        is_active=True
    )
    
    # Create bot instance
    bot_response = await client.post(
        "/v1/api/bots/",
        json=bot_create.model_dump()
    )
    assert bot_response.status_code == 200
    bot_data = bot_response.json()
    bot_id = UUID(bot_data["id"])
    
    # Create a test scenario with auto-transitions
    scenario_create = BotScenarioCreate(
        bot_id=bot_id,
        name="Auto-Transition History Test",
        description="Test scenario for auto-transition history",
        scenario_data=auto_transition_scenario,
        is_active=True
    )
    
    # Create scenario
    scenario_response = await client.post(
        f"/v1/api/bots/{bot_id}/scenarios/",
        json=scenario_create.model_dump()
    )
    assert scenario_response.status_code == 200
    
    # Create a test platform for the bot
    platform_name = "telegram"
    platform_chat_id = f"test_history_{uuid4().hex}"
    
    # Initialize DialogManager
    dialog_manager = DialogManager(db=db_session)
    
    # Mock platform adapter
    mock_adapter = type("MockAdapter", (), {
        "process_update": lambda self, update_data: {"type": "message", "content": {"type": "text", "text": update_data}},
        "send_text_message": lambda self, chat_id, text: {"success": True, "message_id": f"msg_{uuid4().hex}"},
        "send_buttons": lambda self, chat_id, text, buttons: {"success": True, "message_id": f"msg_{uuid4().hex}"}
    })()
    await dialog_manager.register_platform_adapter(platform_name, mock_adapter)
    
    # Start the conversation
    await dialog_manager.process_incoming_message(
        bot_id=bot_id,
        platform=platform_name,
        platform_chat_id=platform_chat_id,
        update_data="/start"
    )
    
    # Wait for auto-transitions
    await asyncio.sleep(0.5)
    
    # Get dialog state to find dialog_id
    dialog_states_query = await db_session.execute(
        "SELECT id FROM bot_dialog_state WHERE platform_chat_id = :chat_id",
        {"chat_id": platform_chat_id}
    )
    dialog_state_result = dialog_states_query.first()
    assert dialog_state_result is not None
    dialog_id = dialog_state_result[0]
    
    # Get dialog history
    history_response = await client.get(f"/v1/api/bots/dialogs/{dialog_id}/history")
    assert history_response.status_code == 200
    history_data = history_response.json()
    
    # Verify history records for auto-transitions
    assert len(history_data) >= 4  # Should have at least 4 entries (1 user + 3 bot messages)
    
    # Check that system auto-transition messages exist
    bot_messages = [entry for entry in history_data if entry["message_type"] == "bot"]
    assert len(bot_messages) >= 3  # At least 3 bot messages from auto-transitions
    
    # Check that the dialog progressed through all auto-transition steps
    current_step_query = await db_session.execute(
        "SELECT current_step FROM bot_dialog_state WHERE id = :dialog_id",
        {"dialog_id": dialog_id}
    )
    current_step = current_step_query.first()[0]
    assert current_step == "input_step"  # Should stop at the step requiring user input


@pytest.mark.asyncio
async def test_auto_transition_logs(db_session: AsyncSession, client: AsyncClient, app: FastAPI, auto_transition_scenario):
    """Test that appropriate logs are generated for auto-transitions"""
    # Create a mock logger to capture logs
    logs = []
    mock_logger = type("MockLogger", (), {
        "auto_transition": lambda self, message, data=None: logs.append({"type": "auto_transition", "message": message, "data": data}),
        "info": lambda self, event_type, message, data=None: logs.append({"type": event_type, "message": message, "data": data}),
        "debug": lambda self, event_type, message, data=None: logs.append({"type": event_type, "message": message, "data": data}),
        "error": lambda self, event_type, message, data=None, exc_info=None: logs.append({"type": event_type, "message": message, "data": data}),
        "set_context": lambda self, **kwargs: None,
    })()
    
    # Create a test bot
    bot_name = f"test-auto-logs-bot-{uuid4()}"
    bot_create = BotInstanceCreate(
        name=bot_name,
        description="Test bot for auto-transition logs",
        is_active=True
    )
    
    # Create bot instance
    bot_response = await client.post(
        "/v1/api/bots/",
        json=bot_create.model_dump()
    )
    assert bot_response.status_code == 200
    bot_data = bot_response.json()
    bot_id = UUID(bot_data["id"])
    
    # Create a test scenario with auto-transitions
    scenario_create = BotScenarioCreate(
        bot_id=bot_id,
        name="Auto-Transition Logs Test",
        description="Test scenario for auto-transition logs",
        scenario_data=auto_transition_scenario,
        is_active=True
    )
    
    # Create scenario
    scenario_response = await client.post(
        f"/v1/api/bots/{bot_id}/scenarios/",
        json=scenario_create.model_dump()
    )
    assert scenario_response.status_code == 200
    
    # Create a test platform for the bot
    platform_name = "telegram"
    platform_chat_id = f"test_logs_{uuid4().hex}"
    
    # Initialize DialogManager with mock logger
    dialog_manager = DialogManager(db=db_session)
    dialog_manager.logger = mock_logger
    
    # Mock platform adapter
    mock_adapter = type("MockAdapter", (), {
        "process_update": lambda self, update_data: {"type": "message", "content": {"type": "text", "text": update_data}},
        "send_text_message": lambda self, chat_id, text: {"success": True, "message_id": f"msg_{uuid4().hex}"},
        "send_buttons": lambda self, chat_id, text, buttons: {"success": True, "message_id": f"msg_{uuid4().hex}"}
    })()
    await dialog_manager.register_platform_adapter(platform_name, mock_adapter)
    
    # Start the conversation
    await dialog_manager.process_incoming_message(
        bot_id=bot_id,
        platform=platform_name,
        platform_chat_id=platform_chat_id,
        update_data="/start"
    )
    
    # Wait for auto-transitions
    await asyncio.sleep(0.5)
    
    # Check for auto-transition logs
    auto_transition_logs = [log for log in logs if log["type"] == "auto_transition"]
    assert len(auto_transition_logs) > 0
    
    # Verify that we have logs for starting and completing auto-transitions
    start_logs = [log for log in auto_transition_logs if "Starting auto-transition" in log["message"]]
    complete_logs = [log for log in auto_transition_logs if "Auto-transition completed" in log["message"]]
    
    assert len(start_logs) > 0
    assert len(complete_logs) > 0
    
    # Verify that transition_id is present in the logs for tracking chains
    for log in auto_transition_logs:
        assert "data" in log
        assert log["data"] is not None
        assert "transition_id" in log["data"]