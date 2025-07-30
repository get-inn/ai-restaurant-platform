"""
Test utilities for mocking Telegram API components.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional, Tuple, List

# Define TelegramError before using it
class TelegramError(Exception):
    """Mock TelegramError for testing error handling."""
    pass

class MockTelegramBot:
    """
    Mock for Telegram Bot with async methods.
    """
    def __init__(self, mock_responses: Optional[Dict[str, Any]] = None):
        """
        Initialize a mock Telegram bot with predefined responses.
        
        Args:
            mock_responses: Dictionary of method names to return values
        """
        self._responses = mock_responses or {}
        
        # Create default mock methods with proper AsyncMock
        self.set_webhook = AsyncMock(return_value=True)
        self.get_webhook_info = AsyncMock(return_value=MagicMock(
            url="https://example.com/webhook",
            has_custom_certificate=False,
            pending_update_count=0,
            ip_address="127.0.0.1",
            last_error_date=None,
            last_error_message=None,
            max_connections=40,
            allowed_updates=["message"]
        ))
        self.delete_webhook = AsyncMock(return_value=True)
        
        # Apply custom responses if provided
        for method_name, response in self._responses.items():
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                method.return_value = response


class MockApplication:
    """
    Mock for Telegram Application with async methods.
    """
    def __init__(self, bot: Optional[MockTelegramBot] = None):
        self.bot = bot or MockTelegramBot()


class MockApplicationBuilder:
    """
    Mock for Application.builder() chain.
    """
    def __init__(self, mock_bot: Optional[MockTelegramBot] = None):
        """
        Initialize a mock Application builder.
        
        Args:
            mock_bot: Optional mock bot to use
        """
        self.mock_bot = mock_bot or MockTelegramBot()
        self._token = None
    
    def token(self, token_str: str):
        """Mock token method that returns self for chaining."""
        self._token = token_str
        return self
    
    def build(self):
        """Mock build method that returns a mock application with a bot property."""
        mock_app = MockApplication(self.mock_bot)
        return mock_app


def create_telegram_mocks() -> Tuple[MagicMock, MockTelegramBot]:
    """
    Create and return mock Telegram modules for testing.
    
    Returns:
        Tuple of (mock_telegram, mock_bot)
    """
    # Create the mock telegram modules
    mock_telegram = MagicMock()
    
    # Set up the error module with a proper exception class
    mock_telegram.error = MagicMock()
    mock_telegram.error.TelegramError = TelegramError
    
    # Create a mock bot
    mock_bot = MockTelegramBot()
    
    # Create a mock Application class with proper builder
    mock_builder = MockApplicationBuilder(mock_bot)
    mock_app_class = MagicMock()
    mock_app_class.builder = MagicMock(return_value=mock_builder)
    
    # Set up the ext module
    mock_telegram.ext = MagicMock()
    mock_telegram.ext.Application = mock_app_class
    
    # Set up constants
    mock_telegram.constants = MagicMock()
    mock_telegram.constants.ParseMode = MagicMock()
    
    return mock_telegram, mock_bot


def patch_telegram_modules():
    """
    Create patches for telegram modules to be used in tests.
    
    Returns:
        List of patches that should be used in a context manager or as decorators
    """
    mock_telegram, _ = create_telegram_mocks()
    
    return [
        patch.dict('sys.modules', {'telegram': mock_telegram}),
        patch.dict('sys.modules', {'telegram.error': mock_telegram.error}),
        patch.dict('sys.modules', {'telegram.ext': mock_telegram.ext}),
        patch.dict('sys.modules', {'telegram.constants': mock_telegram.constants})
    ]