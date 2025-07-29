"""
Unit tests for the conversation logger.
"""
import os
import json
import logging
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import uuid
from threading import Thread
from datetime import datetime

# Import modules to be tested
from src.bot_manager.conversation_logger import (
    ConversationLogger, 
    LogEventType, 
    get_logger
)


class TestConversationLogger(unittest.TestCase):
    """Test case for the ConversationLogger class"""

    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for log files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Set environment variables for testing
        self.old_env = {}
        for key in ['BOT_LOG_LEVEL', 'BOT_LOG_FORMAT', 'BOT_FILE_LOGGING', 'BOT_LOG_DIR']:
            self.old_env[key] = os.environ.get(key)
        
        os.environ['BOT_LOG_LEVEL'] = 'DEBUG'
        os.environ['BOT_LOG_FORMAT'] = 'json'
        os.environ['BOT_FILE_LOGGING'] = 'false'  # Disable file logging for tests
        os.environ['BOT_LOG_DIR'] = self.temp_dir.name
        
        # Clear any existing handlers from the logger
        logger = logging.getLogger("bot.conversation")
        if logger.handlers:
            logger.handlers.clear()

    def tearDown(self):
        """Clean up after tests"""
        # Restore environment variables
        for key, value in self.old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        # Clean up temporary directory
        self.temp_dir.cleanup()

    @patch('logging.Logger.log')
    def test_basic_logging(self, mock_log):
        """Test basic logging functionality"""
        # Create a logger instance
        logger = ConversationLogger(
            bot_id="test-bot",
            dialog_id="test-dialog",
            platform="test-platform",
            platform_chat_id="test-chat-id"
        )
        
        # Log a test message
        logger.info(LogEventType.PROCESSING, "Test message")
        
        # Verify the log call
        mock_log.assert_called_once()
        
        # Check log level
        self.assertEqual(mock_log.call_args[0][0], logging.INFO)
        
        # Check that context is included
        log_context = mock_log.call_args[0][2]
        self.assertEqual(log_context.get("bot_id"), "test-bot")
        self.assertEqual(log_context.get("dialog_id"), "test-dialog")
        self.assertEqual(log_context.get("platform"), "test-platform")
        self.assertEqual(log_context.get("platform_chat_id"), "test-chat-id")
        self.assertEqual(log_context.get("event_type"), LogEventType.PROCESSING)

    @patch('logging.Logger.log')
    def test_specialized_logging_methods(self, mock_log):
        """Test specialized logging methods"""
        logger = ConversationLogger(bot_id="test-bot")
        
        # Test incoming message logging
        logger.incoming_message("Hello bot", {"user_id": "user123"})
        self.assertEqual(mock_log.call_args[0][0], logging.INFO)
        self.assertEqual(mock_log.call_args[0][1], "Received: Hello bot")
        self.assertEqual(mock_log.call_args[0][2].get("event_type"), LogEventType.INCOMING)
        self.assertEqual(mock_log.call_args[0][2].get("user_id"), "user123")
        
        # Test outgoing message logging
        mock_log.reset_mock()
        logger.outgoing_message("Hello user", {"buttons": ["Option 1", "Option 2"]})
        self.assertEqual(mock_log.call_args[0][0], logging.INFO)
        self.assertEqual(mock_log.call_args[0][1], "Sent: Hello user")
        self.assertEqual(mock_log.call_args[0][2].get("event_type"), LogEventType.OUTGOING)
        self.assertEqual(mock_log.call_args[0][2].get("buttons"), ["Option 1", "Option 2"])
        
        # Test state change logging
        mock_log.reset_mock()
        logger.state_change("welcome_step", {"previous_step": "initial"})
        self.assertEqual(mock_log.call_args[0][0], logging.INFO)
        self.assertEqual(mock_log.call_args[0][1], "Dialog state changed to step: welcome_step")
        self.assertEqual(mock_log.call_args[0][2].get("event_type"), LogEventType.STATE_CHANGE)
        self.assertEqual(mock_log.call_args[0][2].get("previous_step"), "initial")
        
        # Test variable update logging
        mock_log.reset_mock()
        logger.variable_update("user_name", "John Doe")
        self.assertEqual(mock_log.call_args[0][0], logging.DEBUG)
        self.assertEqual(mock_log.call_args[0][1], "Variable 'user_name' set to 'John Doe'")
        self.assertEqual(mock_log.call_args[0][2].get("event_type"), LogEventType.VARIABLE)
        self.assertEqual(mock_log.call_args[0][2].get("variable"), "user_name")
        self.assertEqual(mock_log.call_args[0][2].get("value"), "John Doe")

    @patch('logging.Logger.log')
    def test_context_management(self, mock_log):
        """Test context management"""
        logger = ConversationLogger()
        
        # Set initial context
        logger.set_context(
            bot_id="test-bot",
            platform="telegram"
        )
        
        # Log a message with initial context
        logger.info(LogEventType.PROCESSING, "Test message")
        self.assertEqual(mock_log.call_args[0][2].get("bot_id"), "test-bot")
        self.assertEqual(mock_log.call_args[0][2].get("platform"), "telegram")
        
        # Update context
        logger.set_context(
            dialog_id="test-dialog",
            platform_chat_id="12345678"
        )
        
        # Log a message with updated context
        mock_log.reset_mock()
        logger.info(LogEventType.PROCESSING, "Test message")
        self.assertEqual(mock_log.call_args[0][2].get("bot_id"), "test-bot")
        self.assertEqual(mock_log.call_args[0][2].get("platform"), "telegram")
        self.assertEqual(mock_log.call_args[0][2].get("dialog_id"), "test-dialog")
        self.assertEqual(mock_log.call_args[0][2].get("platform_chat_id"), "12345678")
        
        # Clear specific context values
        logger.clear_context("platform")
        
        # Log a message with partially cleared context
        mock_log.reset_mock()
        logger.info(LogEventType.PROCESSING, "Test message")
        self.assertEqual(mock_log.call_args[0][2].get("bot_id"), "test-bot")
        self.assertEqual(mock_log.call_args[0][2].get("platform", None), None)
        self.assertEqual(mock_log.call_args[0][2].get("dialog_id"), "test-dialog")
        
        # Clear all context
        logger.clear_context()
        
        # Log a message with cleared context
        mock_log.reset_mock()
        logger.info(LogEventType.PROCESSING, "Test message")
        self.assertEqual(mock_log.call_args[0][2].get("bot_id", None), None)
        self.assertEqual(mock_log.call_args[0][2].get("dialog_id", None), None)

    @patch('logging.Logger.log')
    def test_sensitive_data_protection(self, mock_log):
        """Test sensitive data protection"""
        logger = ConversationLogger(bot_id="test-bot")
        
        # Log a message with sensitive data
        logger.info(LogEventType.PROCESSING, "Processing credentials", {
            "api_key": "secret-api-key",
            "token": "secret-token",
            "password": "secret-password",
            "user_data": {
                "name": "John",
                "email": "john@example.com",
                "auth_token": "secret-auth-token"
            }
        })
        
        # Check that sensitive data is redacted
        log_context = mock_log.call_args[0][2]
        self.assertEqual(log_context.get("api_key"), "***REDACTED***")
        self.assertEqual(log_context.get("token"), "***REDACTED***")
        self.assertEqual(log_context.get("password"), "***REDACTED***")
        self.assertEqual(log_context.get("user_data").get("auth_token"), "***REDACTED***")
        
        # Check that non-sensitive data is preserved
        self.assertEqual(log_context.get("user_data").get("name"), "John")
        self.assertEqual(log_context.get("user_data").get("email"), "john@example.com")

    @patch('logging.Logger.log')
    def test_error_logging_with_exception(self, mock_log):
        """Test error logging with exception information"""
        logger = ConversationLogger(bot_id="test-bot")
        
        try:
            # Raise an exception
            raise ValueError("Test error")
        except Exception as e:
            # Log the exception
            logger.error(LogEventType.ERROR, "An error occurred", exc_info=e)
        
        # Check that exception information is included
        log_context = mock_log.call_args[0][2]
        self.assertEqual(log_context.get("exception_type"), "ValueError")
        self.assertEqual(log_context.get("exception_message"), "Test error")
        self.assertIn("traceback", log_context)
        self.assertIn("ValueError: Test error", log_context.get("traceback"))

    def test_thread_isolation(self):
        """Test thread isolation of context"""
        logger1 = ConversationLogger(bot_id="thread1-bot")
        
        # Store results from thread
        thread2_context = {}
        
        # Define a function to run in a separate thread
        def thread_function():
            logger2 = ConversationLogger(bot_id="thread2-bot")
            
            # Capture the context in thread 2
            nonlocal thread2_context
            with patch('logging.Logger.log') as mock_log:
                logger2.info(LogEventType.PROCESSING, "Thread 2 message")
                thread2_context = mock_log.call_args[0][2].copy()
        
        # Start a separate thread
        thread = Thread(target=thread_function)
        thread.start()
        thread.join()
        
        # Verify that thread contexts are isolated
        with patch('logging.Logger.log') as mock_log:
            logger1.info(LogEventType.PROCESSING, "Thread 1 message")
            thread1_context = mock_log.call_args[0][2]
        
        self.assertEqual(thread1_context.get("bot_id"), "thread1-bot")
        self.assertEqual(thread2_context.get("bot_id"), "thread2-bot")
        
    def test_get_logger_factory_function(self):
        """Test the get_logger factory function"""
        # Create a logger with specific context
        bot_id = str(uuid.uuid4())
        dialog_id = str(uuid.uuid4())
        logger = get_logger(
            bot_id=bot_id,
            dialog_id=dialog_id,
            platform="telegram",
            platform_chat_id="12345678"
        )
        
        # Verify that the logger has the correct context
        with patch('logging.Logger.log') as mock_log:
            logger.info(LogEventType.PROCESSING, "Test message")
            log_context = mock_log.call_args[0][2]
            
            self.assertEqual(log_context.get("bot_id"), bot_id)
            self.assertEqual(log_context.get("dialog_id"), dialog_id)
            self.assertEqual(log_context.get("platform"), "telegram")
            self.assertEqual(log_context.get("platform_chat_id"), "12345678")


if __name__ == "__main__":
    unittest.main()