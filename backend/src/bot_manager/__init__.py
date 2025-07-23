"""
Bot Management System

This package contains core components for the bot management system:
- Dialog Manager: Manages conversation flow and coordinates components
- Scenario Processor: Processes dialog scenarios and conversation logic
- State Repository: Handles persistence of dialog state and history
- Conversation Logger: Provides detailed logging for debugging

Usage:
    from src.bot_manager import DialogManager
    dialog_manager = DialogManager(db_session)
"""

from src.bot_manager.dialog_manager import DialogManager
from src.bot_manager.scenario_processor import ScenarioProcessor
from src.bot_manager.state_repository import StateRepository
from src.bot_manager.conversation_logger import ConversationLogger, get_logger, LogEventType

__all__ = ["DialogManager", "ScenarioProcessor", "StateRepository", 
           "ConversationLogger", "get_logger", "LogEventType"]