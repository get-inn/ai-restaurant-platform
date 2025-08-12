"""
Unit tests for the InputValidator system.

Tests all validation scenarios including duplicate detection, rate limiting,
button validation, and input type validation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from src.bot_manager.input_validator import (
    InputValidator,
    ValidationContext,
    InputType,
    ValidationResult,
    ValidationResponse
)


class TestInputValidator:
    """Test suite for InputValidator class"""
    
    @pytest.fixture
    def validator(self):
        """Create an InputValidator instance for testing"""
        return InputValidator(duplicate_window_seconds=2)
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        mock_redis.setex = AsyncMock()
        return mock_redis
    
    @pytest.fixture
    def validator_with_redis(self, mock_redis):
        """Create an InputValidator with mock Redis client"""
        return InputValidator(redis_client=mock_redis, duplicate_window_seconds=2)
    
    @pytest.fixture
    def base_context(self):
        """Create a base validation context for testing"""
        return ValidationContext(
            user_id="test_user",
            bot_id="test_bot",
            platform="telegram",
            platform_chat_id="12345",
            input_type=InputType.BUTTON_CLICK,
            input_value="option_1",
            expected_buttons=[
                {"text": "Option 1", "value": "option_1"},
                {"text": "Option 2", "value": "option_2"}
            ],
            current_step="step_1",
            dialog_state={"current_step": "step_1"},
            timestamp=datetime.utcnow()
        )
    
    @pytest.fixture
    def text_context(self):
        """Create a text message validation context"""
        return ValidationContext(
            user_id="test_user",
            bot_id="test_bot",
            platform="telegram",
            platform_chat_id="12345",
            input_type=InputType.TEXT_MESSAGE,
            input_value="Hello world",
            expected_buttons=None,  # No buttons expected for text
            current_step="text_step",
            dialog_state={"current_step": "text_step"},
            timestamp=datetime.utcnow()
        )

    # Test basic validation functionality
    async def test_valid_button_input(self, validator, base_context):
        """Test that valid button input passes validation"""
        result = await validator.validate_input(base_context)
        assert result.is_valid
        assert result.result == ValidationResult.VALID
        assert result.error_message is None
        assert result.correction_message is None

    async def test_valid_text_input(self, validator, text_context):
        """Test that valid text input passes validation"""
        result = await validator.validate_input(text_context)
        assert result.is_valid
        assert result.result == ValidationResult.VALID

    async def test_valid_command_input(self, validator, base_context):
        """Test that command input always passes validation"""
        base_context.input_type = InputType.COMMAND
        base_context.input_value = "/start"
        
        result = await validator.validate_input(base_context)
        assert result.is_valid
        assert result.result == ValidationResult.VALID

    # Test duplicate detection
    async def test_duplicate_detection_local_cache(self, validator, base_context):
        """Test duplicate detection using local cache"""
        # First input should be valid
        result1 = await validator.validate_input(base_context)
        assert result1.is_valid
        
        # Immediate duplicate should be rejected
        base_context.timestamp = datetime.utcnow()
        result2 = await validator.validate_input(base_context)
        assert not result2.is_valid
        assert result2.result == ValidationResult.DUPLICATE
        assert "wait a moment" in result2.correction_message.lower()

    async def test_duplicate_detection_after_window(self, validator, base_context):
        """Test that duplicates are allowed after the time window"""
        # First input
        result1 = await validator.validate_input(base_context)
        assert result1.is_valid
        
        # After duplicate window, should be valid again
        base_context.timestamp = datetime.utcnow() + timedelta(seconds=3)
        result2 = await validator.validate_input(base_context)
        assert result2.is_valid

    async def test_duplicate_detection_with_redis(self, validator_with_redis, mock_redis, base_context):
        """Test duplicate detection using Redis"""
        # Mock Redis to return no previous entry
        mock_redis.get.return_value = None
        
        result1 = await validator_with_redis.validate_input(base_context)
        assert result1.is_valid
        
        # Mock Redis to return recent timestamp
        recent_time = datetime.utcnow().isoformat()
        mock_redis.get.return_value = recent_time.encode()
        
        base_context.timestamp = datetime.utcnow()
        result2 = await validator_with_redis.validate_input(base_context)
        assert not result2.is_valid
        assert result2.result == ValidationResult.DUPLICATE

    async def test_redis_failure_fallback(self, validator_with_redis, mock_redis, base_context):
        """Test that Redis failures fall back to local cache"""
        # Mock Redis to raise an exception
        mock_redis.get.side_effect = Exception("Redis connection failed")
        
        # Should still work with local cache fallback
        result = await validator_with_redis.validate_input(base_context)
        assert result.is_valid

    # Test rate limiting
    async def test_rate_limiting_within_limit(self, validator_with_redis, mock_redis, base_context):
        """Test that requests within rate limit are allowed"""
        mock_redis.incr.return_value = 5  # Within limit of 30
        
        result = await validator_with_redis.validate_input(base_context)
        assert result.is_valid

    async def test_rate_limiting_exceeded(self, validator_with_redis, mock_redis, base_context):
        """Test that requests exceeding rate limit are rejected"""
        mock_redis.incr.return_value = 35  # Exceeds limit of 30
        
        result = await validator_with_redis.validate_input(base_context)
        assert not result.is_valid
        assert result.result == ValidationResult.RATE_LIMITED
        assert "too quickly" in result.correction_message.lower()

    async def test_rate_limiting_redis_failure(self, validator_with_redis, mock_redis, base_context):
        """Test that rate limiting failures don't block valid requests"""
        mock_redis.incr.side_effect = Exception("Redis connection failed")
        
        result = await validator_with_redis.validate_input(base_context)
        # Should pass validation despite Redis failure
        assert result.is_valid

    # Test button validation
    async def test_invalid_button_value(self, validator, base_context):
        """Test validation of invalid button values"""
        base_context.input_value = "invalid_option"
        
        result = await validator.validate_input(base_context)
        assert not result.is_valid
        assert result.result == ValidationResult.INVALID_BUTTON
        assert "choose one of these options" in result.correction_message.lower()
        assert result.should_retry_current_step
        assert result.suggested_buttons == base_context.expected_buttons

    async def test_button_click_when_none_expected(self, validator, base_context):
        """Test button click when no buttons are expected"""
        base_context.expected_buttons = None
        
        result = await validator.validate_input(base_context)
        assert not result.is_valid
        assert result.result == ValidationResult.WRONG_INPUT_TYPE
        assert "text message instead" in result.correction_message.lower()
        assert result.should_retry_current_step

    async def test_empty_expected_buttons(self, validator, base_context):
        """Test behavior when expected_buttons is empty list"""
        base_context.expected_buttons = []
        
        result = await validator.validate_input(base_context)
        assert not result.is_valid
        assert result.result == ValidationResult.WRONG_INPUT_TYPE

    # Test text input validation
    async def test_text_when_buttons_expected(self, validator, text_context):
        """Test text input when buttons are expected"""
        text_context.expected_buttons = [
            {"text": "Yes", "value": "yes"},
            {"text": "No", "value": "no"}
        ]
        
        result = await validator.validate_input(text_context)
        assert not result.is_valid
        assert result.result == ValidationResult.WRONG_INPUT_TYPE
        assert "click one of these buttons" in result.correction_message.lower()
        assert result.should_retry_current_step
        assert result.suggested_buttons == text_context.expected_buttons

    # Test dialog state validation
    async def test_missing_dialog_state(self, validator, base_context):
        """Test validation with missing dialog state"""
        base_context.dialog_state = None
        
        result = await validator.validate_input(base_context)
        assert not result.is_valid
        assert result.result == ValidationResult.STATE_MISMATCH
        assert "/start" in result.correction_message.lower()
        assert not result.should_retry_current_step

    async def test_empty_dialog_state(self, validator, base_context):
        """Test validation with empty dialog state"""
        base_context.dialog_state = {}
        base_context.current_step = ""
        
        result = await validator.validate_input(base_context)
        assert not result.is_valid
        assert result.result == ValidationResult.STATE_MISMATCH
        # For missing current step, should_retry_current_step is True
        assert result.should_retry_current_step

    async def test_missing_current_step(self, validator, base_context):
        """Test validation with missing current step"""
        base_context.current_step = ""
        
        result = await validator.validate_input(base_context)
        assert not result.is_valid
        assert result.result == ValidationResult.STATE_MISMATCH

    # Test hash creation
    def test_input_hash_creation(self, validator, base_context):
        """Test that input hashes are created consistently"""
        hash1 = validator._create_input_hash(base_context)
        hash2 = validator._create_input_hash(base_context)
        
        assert hash1 == hash2
        assert len(hash1) == 16  # MD5 hash truncated to 16 chars
        
        # Different input should create different hash
        base_context.input_value = "different_value"
        hash3 = validator._create_input_hash(base_context)
        assert hash1 != hash3

    # Test record valid input
    async def test_record_valid_input_local_cache(self, validator, base_context):
        """Test recording valid input in local cache"""
        await validator._record_valid_input(base_context)
        
        # Check that the input was recorded
        input_hash = validator._create_input_hash(base_context)
        cache_key = f"input:{base_context.bot_id}:{base_context.user_id}:{input_hash}"
        
        assert cache_key in validator.duplicate_cache
        assert validator.duplicate_cache[cache_key] == base_context.timestamp

    async def test_record_valid_input_with_redis(self, validator_with_redis, mock_redis, base_context):
        """Test recording valid input with Redis"""
        await validator_with_redis._record_valid_input(base_context)
        
        # Check that Redis setex was called
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[1] == 2  # duplicate_window_seconds
        assert args[2] == base_context.timestamp.isoformat()

    async def test_local_cache_cleanup(self, validator, base_context):
        """Test that old entries are cleaned from local cache"""
        # Add an old entry
        old_timestamp = datetime.utcnow() - timedelta(seconds=10)
        old_context = ValidationContext(
            user_id="old_user",
            bot_id=base_context.bot_id,
            platform=base_context.platform,
            platform_chat_id="old_chat",
            input_type=base_context.input_type,
            input_value="old_value",
            expected_buttons=None,
            current_step="old_step",
            dialog_state={"current_step": "old_step"},
            timestamp=old_timestamp
        )
        
        old_hash = validator._create_input_hash(old_context)
        old_key = f"input:{old_context.bot_id}:{old_context.user_id}:{old_hash}"
        validator.duplicate_cache[old_key] = old_timestamp
        
        # Record a new input (which should trigger cleanup)
        await validator._record_valid_input(base_context)
        
        # Old entry should be cleaned up
        assert old_key not in validator.duplicate_cache

    # Test exception handling
    async def test_validation_exception_handling(self, validator, base_context):
        """Test that validation exceptions are handled gracefully"""
        # Mock a method to raise an exception
        validator._check_duplicate_submission = AsyncMock(side_effect=Exception("Test exception"))
        
        result = await validator.validate_input(base_context)
        assert not result.is_valid
        assert result.result == ValidationResult.STATE_MISMATCH
        assert "something went wrong" in result.correction_message.lower()

    # Test different input types
    async def test_media_message_validation(self, validator, base_context):
        """Test validation of media message input"""
        base_context.input_type = InputType.MEDIA_MESSAGE
        base_context.input_value = {"type": "photo", "file_id": "123"}
        base_context.expected_buttons = None
        
        result = await validator.validate_input(base_context)
        assert result.is_valid

    # Test edge cases
    async def test_none_input_value(self, validator, base_context):
        """Test validation with None input value"""
        base_context.input_value = None
        
        # Should still validate but likely fail button validation
        result = await validator.validate_input(base_context)
        assert not result.is_valid
        assert result.result == ValidationResult.INVALID_BUTTON

    async def test_empty_string_input(self, validator, text_context):
        """Test validation with empty string input"""
        text_context.input_value = ""
        
        result = await validator.validate_input(text_context)
        # Empty string is still valid text input
        assert result.is_valid

    async def test_unicode_input_handling(self, validator, text_context):
        """Test validation with Unicode text input"""
        text_context.input_value = "Привет мир! 🌍"
        
        result = await validator.validate_input(text_context)
        assert result.is_valid

    # Test concurrent validation
    async def test_concurrent_validations(self, validator, base_context):
        """Test that concurrent validations work correctly"""
        # Create multiple contexts with slight time differences
        contexts = []
        for i in range(5):
            context = ValidationContext(
                user_id=f"user_{i}",
                bot_id=base_context.bot_id,
                platform=base_context.platform,
                platform_chat_id=f"chat_{i}",
                input_type=base_context.input_type,
                input_value=base_context.input_value,
                expected_buttons=base_context.expected_buttons,
                current_step=base_context.current_step,
                dialog_state=base_context.dialog_state,
                timestamp=datetime.utcnow() + timedelta(milliseconds=i)
            )
            contexts.append(context)
        
        # Run validations concurrently
        tasks = [validator.validate_input(context) for context in contexts]
        results = await asyncio.gather(*tasks)
        
        # All should be valid since they're from different users
        for result in results:
            assert result.is_valid

    # Test button text vs value matching
    async def test_button_value_matching_priority(self, validator, base_context):
        """Test that button values are matched, not text"""
        base_context.expected_buttons = [
            {"text": "Different Text", "value": "option_1"},
            {"text": "Option 2", "value": "option_2"}
        ]
        base_context.input_value = "option_1"  # Matches value, not text
        
        result = await validator.validate_input(base_context)
        assert result.is_valid

    async def test_button_with_missing_value(self, validator, base_context):
        """Test button validation with missing value field"""
        base_context.expected_buttons = [
            {"text": "Option 1"},  # Missing value
            {"text": "Option 2", "value": "option_2"}
        ]
        base_context.input_value = "option_1"
        
        result = await validator.validate_input(base_context)
        # Should fail since None is not equal to "option_1"
        assert not result.is_valid
        assert result.result == ValidationResult.INVALID_BUTTON