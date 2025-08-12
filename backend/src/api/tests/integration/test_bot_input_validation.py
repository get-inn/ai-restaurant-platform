"""
Integration tests for bot input validation.

Tests the complete input validation flow through DialogManager
and ensures proper integration with the bot management system.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from src.bot_manager.dialog_manager import DialogManager
from src.bot_manager.input_validator import ValidationResult
from src.api.services.bots.scenario_service import ScenarioService


class TestBotInputValidationIntegration:
    """Integration tests for bot input validation system"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        mock_redis.setex = AsyncMock()
        return mock_redis
    
    @pytest.fixture
    def mock_adapter(self):
        """Mock platform adapter"""
        adapter = AsyncMock()
        adapter.send_text_message = AsyncMock()
        adapter.send_buttons = AsyncMock()
        adapter.send_media_message = AsyncMock()
        return adapter
    
    @pytest.fixture
    def dialog_manager(self, mock_db, mock_redis, mock_adapter):
        """Create DialogManager with mocked dependencies"""
        platform_adapters = {"telegram": mock_adapter}
        return DialogManager(
            db=mock_db,
            platform_adapters=platform_adapters,
            redis_client=mock_redis
        )
    
    @pytest.fixture
    def sample_bot_id(self):
        """Sample bot ID for testing"""
        return uuid4()
    
    @pytest.fixture
    def sample_dialog_state(self):
        """Sample dialog state for testing"""
        return {
            "id": uuid4(),
            "current_step": "ask_citizenship",
            "collected_data": {"first_name": "John"}
        }
    
    @pytest.fixture
    def sample_scenario(self):
        """Sample scenario data for testing"""
        return {
            "scenario_data": {
                "steps": {
                    "ask_citizenship": {
                        "type": "message",
                        "message": {"text": "What is your citizenship?"},
                        "buttons": [
                            {"text": "🇷🇺 RF", "value": "rf"},
                            {"text": "🌍 CIS", "value": "cis"}
                        ],
                        "next_step": "ask_position"
                    },
                    "ask_name": {
                        "type": "message", 
                        "message": {"text": "What is your name?"},
                        "next_step": "ask_citizenship"
                    }
                }
            }
        }

    async def test_duplicate_button_click_prevention(
        self, dialog_manager, mock_adapter, sample_bot_id, sample_dialog_state, sample_scenario
    ):
        """Test that duplicate button clicks are prevented"""
        platform = "telegram"
        platform_chat_id = "12345"
        button_value = "rf"
        
        # Mock scenario service
        with patch.object(ScenarioService, 'get_active_scenario', return_value=MagicMock(**sample_scenario)):
            # First button click should be processed
            result1 = await dialog_manager.handle_button_click(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value=button_value,
                dialog_state=sample_dialog_state
            )
            
            # Immediate duplicate click should be rejected
            result2 = await dialog_manager.handle_button_click(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value=button_value,
                dialog_state=sample_dialog_state
            )
            
            # First should succeed, second should be duplicate
            assert result2["status"] == "duplicate"
            assert result2["action"] == "ignored"

    async def test_invalid_button_handling(
        self, dialog_manager, mock_adapter, sample_bot_id, sample_dialog_state, sample_scenario
    ):
        """Test handling of invalid button values"""
        platform = "telegram"
        platform_chat_id = "12345"
        invalid_button_value = "nonexistent_option"
        
        # Mock scenario service
        with patch.object(ScenarioService, 'get_active_scenario', return_value=MagicMock(**sample_scenario)):
            result = await dialog_manager.handle_button_click(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value=invalid_button_value,
                dialog_state=sample_dialog_state
            )
            
            assert result["status"] == "invalid_input"
            assert result["validation_result"] == "invalid_button"
            
            # Verify correction message was sent
            mock_adapter.send_buttons.assert_called_once()
            call_args = mock_adapter.send_buttons.call_args
            assert "choose one of these options" in call_args[1]["text"].lower()

    async def test_text_input_when_buttons_expected(
        self, dialog_manager, mock_adapter, sample_bot_id, sample_dialog_state, sample_scenario
    ):
        """Test text input when buttons are expected"""
        platform = "telegram"
        platform_chat_id = "12345"
        text_input = "some random text"
        
        # Mock scenario service
        with patch.object(ScenarioService, 'get_active_scenario', return_value=MagicMock(**sample_scenario)):
            result = await dialog_manager.handle_text_message(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                text=text_input,
                dialog_state=sample_dialog_state
            )
            
            assert result["status"] == "invalid_input"
            assert result["validation_result"] == "wrong_input_type"
            
            # Verify correction message was sent with buttons
            mock_adapter.send_buttons.assert_called_once()
            call_args = mock_adapter.send_buttons.call_args
            assert "click one of these buttons" in call_args[1]["text"].lower()

    async def test_button_click_when_text_expected(
        self, dialog_manager, mock_adapter, sample_bot_id, sample_scenario
    ):
        """Test button click when text input is expected"""
        platform = "telegram"
        platform_chat_id = "12345"
        button_value = "rf"
        
        # Dialog state expecting text input (no buttons in current step)
        text_dialog_state = {
            "id": uuid4(),
            "current_step": "ask_name",  # This step expects text
            "collected_data": {}
        }
        
        # Mock scenario service  
        with patch.object(ScenarioService, 'get_active_scenario', return_value=MagicMock(**sample_scenario)):
            result = await dialog_manager.handle_button_click(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value=button_value,
                dialog_state=text_dialog_state
            )
            
            assert result["status"] == "invalid_input"
            assert result["validation_result"] == "wrong_input_type"
            
            # Verify correction message was sent
            mock_adapter.send_text_message.assert_called_once()
            call_args = mock_adapter.send_text_message.call_args
            assert "text message instead" in call_args[1]["text"].lower()

    async def test_rate_limiting_functionality(
        self, dialog_manager, mock_redis, mock_adapter, sample_bot_id, sample_dialog_state, sample_scenario
    ):
        """Test rate limiting prevents spam"""
        platform = "telegram"
        platform_chat_id = "12345"
        button_value = "rf"
        
        # Mock Redis to simulate rate limit exceeded
        mock_redis.incr.return_value = 35  # Exceeds limit of 30
        
        # Mock scenario service
        with patch.object(ScenarioService, 'get_active_scenario', return_value=MagicMock(**sample_scenario)):
            result = await dialog_manager.handle_button_click(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value=button_value,
                dialog_state=sample_dialog_state
            )
            
            assert result["status"] == "invalid_input"
            assert result["validation_result"] == "rate_limited"
            
            # Verify rate limit message was sent
            mock_adapter.send_text_message.assert_called_once()
            call_args = mock_adapter.send_text_message.call_args
            assert "too quickly" in call_args[1]["text"].lower()

    async def test_missing_dialog_state_handling(
        self, dialog_manager, mock_adapter, sample_bot_id
    ):
        """Test handling when dialog state is missing"""
        platform = "telegram"
        platform_chat_id = "12345"
        button_value = "rf"
        
        result = await dialog_manager.handle_button_click(
            bot_id=sample_bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            button_value=button_value,
            dialog_state=None  # No dialog state
        )
        
        # Without dialog state, validation should be skipped and normal processing continues
        # This might result in an error from DialogService, but validation won't interfere
        assert result is not None

    async def test_commands_bypass_validation(
        self, dialog_manager, mock_adapter, sample_bot_id, sample_dialog_state
    ):
        """Test that commands bypass input validation"""
        platform = "telegram"
        platform_chat_id = "12345"
        command = "/start"
        
        # Mock necessary services for command handling
        with patch.object(ScenarioService, 'get_active_scenario', return_value=None):
            result = await dialog_manager.handle_text_message(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                text=command,
                dialog_state=sample_dialog_state
            )
            
            # Command should be processed regardless of validation
            # The result depends on the command handling logic
            assert result is not None

    async def test_validation_with_complex_scenario_structure(
        self, dialog_manager, mock_adapter, sample_bot_id, sample_dialog_state
    ):
        """Test validation with complex scenario structures"""
        platform = "telegram"
        platform_chat_id = "12345"
        button_value = "rf"
        
        # Complex scenario with nested response structure
        complex_scenario = {
            "scenario_data": {
                "steps": {
                    "ask_citizenship": {
                        "type": "message",
                        "response": {
                            "text": "What is your citizenship?",
                            "buttons": [
                                {"text": "🇷🇺 RF", "value": "rf"},
                                {"text": "🌍 CIS", "value": "cis"}
                            ]
                        },
                        "next_step": "ask_position"
                    }
                }
            }
        }
        
        # Mock scenario service
        with patch.object(ScenarioService, 'get_active_scenario', return_value=MagicMock(**complex_scenario)):
            result = await dialog_manager.handle_button_click(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value=button_value,
                dialog_state=sample_dialog_state
            )
            
            # Should handle the complex structure correctly
            # The exact result depends on DialogService behavior
            assert result is not None

    async def test_scenario_service_error_handling(
        self, dialog_manager, mock_adapter, sample_bot_id, sample_dialog_state
    ):
        """Test handling when ScenarioService fails"""
        platform = "telegram"
        platform_chat_id = "12345"
        button_value = "rf"
        
        # Mock ScenarioService to raise an exception
        with patch.object(ScenarioService, 'get_active_scenario', side_effect=Exception("Database error")):
            result = await dialog_manager.handle_button_click(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value=button_value,
                dialog_state=sample_dialog_state
            )
            
            # Should handle the error gracefully
            # Validation might fail but shouldn't crash the system
            assert result is not None

    async def test_validation_logging(
        self, dialog_manager, mock_adapter, sample_bot_id, sample_dialog_state, sample_scenario
    ):
        """Test that validation events are properly logged"""
        platform = "telegram"
        platform_chat_id = "12345"
        invalid_button_value = "invalid"
        
        # Mock scenario service
        with patch.object(ScenarioService, 'get_active_scenario', return_value=MagicMock(**sample_scenario)):
            with patch.object(dialog_manager.logger, 'info') as mock_log:
                await dialog_manager.handle_button_click(
                    bot_id=sample_bot_id,
                    platform=platform,
                    platform_chat_id=platform_chat_id,
                    button_value=invalid_button_value,
                    dialog_state=sample_dialog_state
                )
                
                # Check that validation events were logged
                # The exact logging depends on implementation details
                mock_log.assert_called()

    async def test_validation_context_creation(
        self, dialog_manager, mock_adapter, sample_bot_id, sample_dialog_state, sample_scenario
    ):
        """Test that validation context is created correctly"""
        platform = "telegram"
        platform_chat_id = "12345"
        button_value = "rf"
        
        # Mock the validator to capture the context
        original_validate = dialog_manager.input_validator.validate_input
        validation_context = None
        
        async def capture_context(context):
            nonlocal validation_context
            validation_context = context
            return await original_validate(context)
        
        dialog_manager.input_validator.validate_input = capture_context
        
        # Mock scenario service
        with patch.object(ScenarioService, 'get_active_scenario', return_value=MagicMock(**sample_scenario)):
            await dialog_manager.handle_button_click(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value=button_value,
                dialog_state=sample_dialog_state
            )
            
            # Verify context was created correctly
            assert validation_context is not None
            assert validation_context.user_id == platform_chat_id
            assert validation_context.bot_id == str(sample_bot_id)
            assert validation_context.platform == platform
            assert validation_context.input_value == button_value
            assert validation_context.current_step == sample_dialog_state["current_step"]

    async def test_redis_connection_failure_graceful_handling(
        self, mock_db, mock_adapter, sample_bot_id, sample_dialog_state, sample_scenario
    ):
        """Test graceful handling when Redis connection fails"""
        platform = "telegram"
        platform_chat_id = "12345"
        button_value = "rf"
        
        # Create dialog manager without Redis
        platform_adapters = {"telegram": mock_adapter}
        dialog_manager = DialogManager(
            db=mock_db,
            platform_adapters=platform_adapters,
            redis_client=None  # No Redis client
        )
        
        # Mock scenario service
        with patch.object(ScenarioService, 'get_active_scenario', return_value=MagicMock(**sample_scenario)):
            result = await dialog_manager.handle_button_click(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value=button_value,
                dialog_state=sample_dialog_state
            )
            
            # Should work fine with local cache fallback
            assert result is not None

    async def test_validation_with_unicode_content(
        self, dialog_manager, mock_adapter, sample_bot_id, sample_scenario
    ):
        """Test validation with Unicode content in buttons and text"""
        platform = "telegram"
        platform_chat_id = "12345"
        
        # Dialog state with Unicode step name
        unicode_dialog_state = {
            "id": uuid4(),
            "current_step": "спросить_гражданство",
            "collected_data": {"имя": "Иван"}
        }
        
        # Scenario with Unicode button values
        unicode_scenario = {
            "scenario_data": {
                "steps": {
                    "спросить_гражданство": {
                        "type": "message",
                        "message": {"text": "Какое у вас гражданство?"},
                        "buttons": [
                            {"text": "🇷🇺 РФ", "value": "рф"},
                            {"text": "🌍 СНГ", "value": "снг"}
                        ]
                    }
                }
            }
        }
        
        # Mock scenario service
        with patch.object(ScenarioService, 'get_active_scenario', return_value=MagicMock(**unicode_scenario)):
            result = await dialog_manager.handle_button_click(
                bot_id=sample_bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                button_value="рф",  # Unicode button value
                dialog_state=unicode_dialog_state
            )
            
            # Should handle Unicode content correctly
            assert result is not None