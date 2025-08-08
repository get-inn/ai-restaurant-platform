"""
Conversation Logger for Bot Management System

This module provides detailed logging for bot conversations to facilitate debugging.
It logs conversation events at various stages of processing and is designed to work
within Docker containers in both development and production environments.

Features:
1. Structured JSON logs for easy parsing and filtering
2. Container-friendly logging to stdout/stderr for Docker log drivers
3. Optional file logging with configurable paths for volume mounts
4. Context-aware logging with bot, platform, and conversation identifiers
5. Performance optimized for production environments
"""

from typing import Dict, Any, Optional, List, Union, Callable
from uuid import UUID
import logging
import json
import sys
from datetime import datetime
import os
from enum import Enum
import traceback
import threading

# Environment-aware configuration
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
LOG_LEVEL = os.environ.get("BOT_LOG_LEVEL", "INFO")
LOG_FORMAT = os.environ.get("BOT_LOG_FORMAT", "json")  # json or text
LOG_DIR = os.environ.get("BOT_LOG_DIR", "/app/logs" if os.path.exists("/app") else "logs")
# Modified for testing
FILE_LOGGING = True  # Force file logging regardless of environment variable

# Thread-local storage for context
_thread_local = threading.local()

# Define log event types
class LogEventType(str, Enum):
    INCOMING = "INCOMING"     # Incoming message from user
    PROCESSING = "PROCESSING" # Processing step
    DECISION = "DECISION"     # Decision point
    STATE_CHANGE = "STATE_CHANGE"    # State change
    OUTGOING = "OUTGOING"     # Outgoing message to user
    ERROR = "ERROR"           # Error during processing
    WEBHOOK = "WEBHOOK"       # Webhook event
    VARIABLE = "VARIABLE"     # Variable update
    CONDITION = "CONDITION"   # Condition evaluation
    ADAPTER = "ADAPTER"       # Platform adapter operations
    DIALOG = "DIALOG"         # Dialog operations
    SCENARIO = "SCENARIO"     # Scenario operations
    CACHE = "CACHE"           # Cache operations
    MEDIA = "MEDIA"           # Media content operations

# Ensure log directory exists if file logging is enabled
if FILE_LOGGING and not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# Set up the root logger
logger = logging.getLogger("bot.conversation")
logger.setLevel(getattr(logging, LOG_LEVEL.upper()))

# Force DEBUG level for console to see all logs
console_log_level = "DEBUG"

# Prevent propagation to root logger to avoid duplicate logs
logger.propagate = False

# Clear any existing handlers
if logger.handlers:
    logger.handlers.clear()

# Create console handler for Docker logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(getattr(logging, console_log_level.upper()))

# Create formatters
if LOG_FORMAT == "json":
    # JSON formatter for structured logging and tools like ELK
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = record.args.copy() if record.args else {}
            log_data.update({
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage()
            })
            
            # Add exception info if available
            if record.exc_info:
                log_data["exception"] = {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                    "traceback": traceback.format_exception(*record.exc_info)
                }
                
            return json.dumps(log_data)
            
    formatter = JsonFormatter()
else:
    # Text formatter for human readability
    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Set up file logging if enabled
if FILE_LOGGING:
    log_file = f"{LOG_DIR}/bot_conversations_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
    logger.addHandler(file_handler)
    logger.info(f"File logging enabled at {log_file}", {"event_type": "SYSTEM"})


class ConversationLogger:
    """
    Logger for bot conversations that provides detailed logs for debugging.
    
    Designed to work well in Docker environments with configurable output formats
    and destinations. Optimized for performance and ease of debugging.
    """
    
    def __init__(
        self, 
        bot_id: Optional[Union[UUID, str]] = None,
        dialog_id: Optional[Union[UUID, str]] = None,
        platform: Optional[str] = None,
        platform_chat_id: Optional[str] = None
    ):
        """
        Initialize the conversation logger.
        
        Args:
            bot_id: Optional bot ID for context
            dialog_id: Optional dialog ID for context
            platform: Optional platform name for context
            platform_chat_id: Optional platform chat ID for context
        """
        # Initialize thread-local context if needed
        if not hasattr(_thread_local, 'context'):
            _thread_local.context = {}
        
        # Set initial context
        self.set_context(
            bot_id=str(bot_id) if bot_id else None,
            dialog_id=str(dialog_id) if dialog_id else None,
            platform=platform,
            platform_chat_id=platform_chat_id
        )
    
    def set_context(self, **kwargs):
        """
        Set or update context values for all subsequent log messages.
        
        Args:
            **kwargs: Context key-value pairs
        """
        for key, value in kwargs.items():
            if value is not None:
                _thread_local.context[key] = value
    
    def clear_context(self, *keys):
        """
        Clear specific context values or all if no keys specified.
        
        Args:
            *keys: Keys to clear from the context
        """
        if not keys:
            _thread_local.context.clear()
        else:
            for key in keys:
                if key in _thread_local.context:
                    del _thread_local.context[key]
    
    def _log(self, level: int, event_type: LogEventType, message: str, data: Optional[Dict[str, Any]] = None):
        """
        Internal method to format and send a log message.
        
        Args:
            level: Log level
            event_type: Type of event being logged
            message: Log message
            data: Additional data to include in the log
        """
        # Create log context by combining thread-local context with any provided data
        log_context = _thread_local.context.copy()
        log_context["event_type"] = event_type
        
        if data:
            # Merge data but don't overwrite existing context
            for key, value in data.items():
                if key not in log_context:
                    log_context[key] = value
        
        # Clean sensitive data before logging
        self._clean_sensitive_data(log_context)
        
        # Log the message with the combined context
        logger.log(level, message, log_context)
    
    def _clean_sensitive_data(self, data: Dict[str, Any]):
        """
        Remove or mask sensitive data before logging.
        
        Args:
            data: Data dictionary to clean
        """
        sensitive_keys = ["token", "password", "secret", "api_key", "auth", "credentials"]
        
        def recursive_clean(obj):
            if isinstance(obj, dict):
                for key in list(obj.keys()):
                    if any(sensitive in key.lower() for sensitive in sensitive_keys):
                        obj[key] = "***REDACTED***"
                    else:
                        recursive_clean(obj[key])
            elif isinstance(obj, list):
                for item in obj:
                    recursive_clean(item)
        
        recursive_clean(data)
    
    # Convenience methods for different log levels and event types
    def debug(self, event_type: LogEventType, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a debug message"""
        self._log(logging.DEBUG, event_type, message, data)
    
    def info(self, event_type: LogEventType, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an info message"""
        self._log(logging.INFO, event_type, message, data)
    
    def warning(self, event_type: LogEventType, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a warning message"""
        self._log(logging.WARNING, event_type, message, data)
    
    def error(self, event_type: LogEventType, message: str, data: Optional[Dict[str, Any]] = None, exc_info=None):
        """Log an error message"""
        if exc_info:
            # Add exception details to the data
            data = data or {}
            data.update({
                "exception_type": type(exc_info).__name__,
                "exception_message": str(exc_info),
                "traceback": traceback.format_exc()
            })
        self._log(logging.ERROR, event_type, message, data)
    
    # Specialized logging methods for specific event types
    def incoming_message(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an incoming message from a user"""
        self.info(LogEventType.INCOMING, f"Received: {message}", data)
    
    def outgoing_message(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an outgoing message to a user"""
        self.info(LogEventType.OUTGOING, f"Sent: {message}", data)
    
    def media_processing(self, operation: str, media_type: str, data: Optional[Dict[str, Any]] = None):
        """Log a media processing operation"""
        combined_data = {"media_type": media_type}
        if data:
            combined_data.update(data)
        # Use info level to ensure it's always visible in logs
        self.info(LogEventType.MEDIA, f"Media {operation}: {media_type}", combined_data)
    
    def webhook_received(self, platform: str, data: Optional[Dict[str, Any]] = None):
        """Log a webhook event"""
        self.info(LogEventType.WEBHOOK, f"Webhook received from {platform}", data)
    
    def state_change(self, step_id: str, data: Optional[Dict[str, Any]] = None):
        """Log a dialog state change"""
        self.info(LogEventType.STATE_CHANGE, f"Dialog state changed to step: {step_id}", data)
    
    def variable_update(self, variable: str, value: Any, data: Optional[Dict[str, Any]] = None):
        """Log a variable update"""
        # Create a safe string representation of the value for the log message
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value)
        else:
            value_str = str(value)
            
        # Truncate long values in the log message (but keep full value in data)
        if len(value_str) > 50:
            value_str = value_str[:47] + "..."
            
        combined_data = {"variable": variable, "value": value}
        if data:
            combined_data.update(data)
            
        self.debug(LogEventType.VARIABLE, f"Variable '{variable}' set to '{value_str}'", combined_data)
    
    def condition_evaluation(self, condition: str, result: bool, data: Optional[Dict[str, Any]] = None):
        """Log a condition evaluation"""
        combined_data = {"condition": condition, "result": result}
        if data:
            combined_data.update(data)
            
        self.debug(LogEventType.CONDITION, f"Condition '{condition}' evaluated to {result}", combined_data)
    
    def adapter_operation(self, platform: str, operation: str, data: Optional[Dict[str, Any]] = None):
        """Log a platform adapter operation"""
        self.debug(LogEventType.ADAPTER, f"{platform} adapter: {operation}", data)


# Create a global instance of the logger
conversation_logger = ConversationLogger()

def get_logger(
    bot_id: Optional[Union[UUID, str]] = None,
    dialog_id: Optional[Union[UUID, str]] = None,
    platform: Optional[str] = None,
    platform_chat_id: Optional[str] = None
) -> ConversationLogger:
    """
    Factory function to get a logger with the specified context.
    
    Args:
        bot_id: Bot ID for context
        dialog_id: Dialog ID for context
        platform: Platform name for context
        platform_chat_id: Platform chat ID for context
        
    Returns:
        ConversationLogger instance
    """
    return ConversationLogger(bot_id, dialog_id, platform, platform_chat_id)