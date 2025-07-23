"""
State Repository for Bot Management System

This module is responsible for:
1. Managing persistence of dialog state
2. Providing access to dialog history
3. Synchronizing state across different components
4. Optimizing state access for performance
"""

from typing import Dict, Any, List, Optional, Union
from uuid import UUID
import logging
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.bot_manager.conversation_logger import get_logger, LogEventType

from src.api.models import BotDialogState, BotDialogHistory
from src.api.schemas.bots.dialog_schemas import (
    BotDialogStateCreate,
    BotDialogStateUpdate,
    BotDialogStateDB,
    BotDialogHistoryCreate,
    BotDialogHistoryDB
)

# Configure logging
logger = logging.getLogger(__name__)


class StateRepository:
    """
    Repository for managing dialog state persistence and retrieval.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the state repository.
        
        Args:
            db: Database session
        """
        self.db = db
        self._cache = {}  # Simple in-memory cache for active dialog states
        self.logger = get_logger()
        
    async def get_dialog_state(
        self,
        bot_id: UUID,
        platform: str,
        platform_chat_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a dialog state for a specific bot, platform, and chat.
        
        Args:
            bot_id: The bot instance ID
            platform: Platform identifier (telegram, whatsapp, etc.)
            platform_chat_id: Chat ID in the platform
            
        Returns:
            The dialog state or None if not found
        """
        # Check cache first
        cache_key = f"{bot_id}:{platform}:{platform_chat_id}"
        if cache_key in self._cache:
            self.logger.debug(LogEventType.CACHE, "Dialog state found in cache", 
                           {"bot_id": str(bot_id), "platform": platform, "platform_chat_id": platform_chat_id})
            return self._cache[cache_key]
            
        # Query the database
        self.logger.debug(LogEventType.STATE, "Querying dialog state from database", 
                       {"bot_id": str(bot_id), "platform": platform, "platform_chat_id": platform_chat_id})
        query = (
            select(BotDialogState)
            .where(
                BotDialogState.bot_id == bot_id,
                BotDialogState.platform == platform,
                BotDialogState.platform_chat_id == platform_chat_id
            )
        )
        result = await self.db.execute(query)
        dialog_state = result.scalars().first()
        
        if dialog_state:
            # Convert to dictionary for easier manipulation
            state_dict = {
                "id": dialog_state.id,
                "bot_id": dialog_state.bot_id,
                "platform": dialog_state.platform,
                "platform_chat_id": dialog_state.platform_chat_id,
                "current_step": dialog_state.current_step,
                "collected_data": dialog_state.collected_data,
                "last_interaction_at": dialog_state.last_interaction_at,
                "created_at": dialog_state.created_at,
                "updated_at": dialog_state.updated_at
            }
            # Update cache
            self._cache[cache_key] = state_dict
            self.logger.debug(LogEventType.STATE, "Dialog state retrieved from database", 
                           {"current_step": dialog_state.current_step})
            return state_dict
            
        self.logger.debug(LogEventType.STATE, "No dialog state found")
        return None
        
    async def create_dialog_state(
        self,
        bot_id: UUID,
        platform: str,
        platform_chat_id: str,
        current_step: str,
        collected_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new dialog state.
        
        Args:
            bot_id: The bot instance ID
            platform: Platform identifier
            platform_chat_id: Chat ID in the platform
            current_step: Initial step ID
            collected_data: Initial collected data (optional)
            
        Returns:
            The created dialog state
        """
        collected_data = collected_data or {}
        now = datetime.now()
        
        # Create dialog state in the database
        self.logger.info(LogEventType.STATE_CHANGE, f"Creating new dialog state with step '{current_step}'", {
            "bot_id": str(bot_id),
            "platform": platform,
            "platform_chat_id": platform_chat_id
        })
        
        dialog_state_create = BotDialogStateCreate(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            current_step=current_step,
            collected_data=collected_data
        )
        
        db_dialog_state = BotDialogState(
            bot_id=dialog_state_create.bot_id,
            platform=dialog_state_create.platform,
            platform_chat_id=dialog_state_create.platform_chat_id,
            current_step=dialog_state_create.current_step,
            collected_data=dialog_state_create.collected_data,
            last_interaction_at=now
        )
        
        self.db.add(db_dialog_state)
        await self.db.commit()
        await self.db.refresh(db_dialog_state)
        
        # Convert to dictionary
        state_dict = {
            "id": db_dialog_state.id,
            "bot_id": db_dialog_state.bot_id,
            "platform": db_dialog_state.platform,
            "platform_chat_id": db_dialog_state.platform_chat_id,
            "current_step": db_dialog_state.current_step,
            "collected_data": db_dialog_state.collected_data,
            "last_interaction_at": db_dialog_state.last_interaction_at,
            "created_at": db_dialog_state.created_at,
            "updated_at": db_dialog_state.updated_at
        }
        
        # Update cache
        cache_key = f"{bot_id}:{platform}:{platform_chat_id}"
        self._cache[cache_key] = state_dict
        
        self.logger.debug(LogEventType.CACHE, "Dialog state added to cache", 
                       {"cache_key": cache_key})
        
        return state_dict
        
    async def update_dialog_state(
        self,
        state_id: UUID,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing dialog state.
        
        Args:
            state_id: ID of the dialog state to update
            update_data: Dictionary of fields to update
            
        Returns:
            The updated dialog state or None if not found
        """
        # Query the database
        query = select(BotDialogState).where(BotDialogState.id == state_id)
        result = await self.db.execute(query)
        db_dialog_state = result.scalars().first()
        
        if not db_dialog_state:
            self.logger.warning(LogEventType.ERROR, f"Dialog state not found for update: {state_id}")
            return None
            
        # Update fields
        self.logger.debug(LogEventType.STATE, f"Updating dialog state {state_id}", 
                       {"update_keys": list(update_data.keys())})
        
        for key, value in update_data.items():
            if hasattr(db_dialog_state, key):
                # Special logging for current_step changes
                if key == "current_step" and db_dialog_state.current_step != value:
                    self.logger.info(LogEventType.STATE_CHANGE, 
                                   f"Dialog step changed from '{db_dialog_state.current_step}' to '{value}'")
                
                # Special logging for collected_data changes
                elif key == "collected_data" and isinstance(value, dict):
                    new_keys = set(value.keys()) - set(db_dialog_state.collected_data.keys() if db_dialog_state.collected_data else {})
                    if new_keys:
                        self.logger.debug(LogEventType.VARIABLE, 
                                        f"Added new collected data: {', '.join(new_keys)}")
                
                setattr(db_dialog_state, key, value)
                
        # Always update last_interaction_at when updating dialog state
        db_dialog_state.last_interaction_at = datetime.now()
        self.logger.debug(LogEventType.STATE, "Updated last_interaction_at timestamp")
        
        await self.db.commit()
        await self.db.refresh(db_dialog_state)
        
        # Convert to dictionary
        state_dict = {
            "id": db_dialog_state.id,
            "bot_id": db_dialog_state.bot_id,
            "platform": db_dialog_state.platform,
            "platform_chat_id": db_dialog_state.platform_chat_id,
            "current_step": db_dialog_state.current_step,
            "collected_data": db_dialog_state.collected_data,
            "last_interaction_at": db_dialog_state.last_interaction_at,
            "created_at": db_dialog_state.created_at,
            "updated_at": db_dialog_state.updated_at
        }
        
        # Update cache
        cache_key = f"{db_dialog_state.bot_id}:{db_dialog_state.platform}:{db_dialog_state.platform_chat_id}"
        self._cache[cache_key] = state_dict
        
        return state_dict
        
    async def delete_dialog_state(self, state_id: UUID) -> bool:
        """
        Delete a dialog state and its history.
        
        Args:
            state_id: ID of the dialog state to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Query the database to get info for cache key
        query = select(BotDialogState).where(BotDialogState.id == state_id)
        result = await self.db.execute(query)
        dialog_state = result.scalars().first()
        
        if not dialog_state:
            return False
            
        # Remove from cache
        cache_key = f"{dialog_state.bot_id}:{dialog_state.platform}:{dialog_state.platform_chat_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
            
        # Delete from database (history first)
        try:
            # This will cascade delete history entries
            await self.db.delete(dialog_state)
            await self.db.commit()
            self.logger.info(LogEventType.STATE, f"Dialog state deleted: {state_id}", 
                           {"platform": dialog_state.platform, "platform_chat_id": dialog_state.platform_chat_id})
            return True
        except Exception as e:
            self.logger.error(LogEventType.ERROR, f"Error deleting dialog state: {e}", exc_info=e)
            await self.db.rollback()
            return False
            
    async def add_to_history(
        self,
        dialog_state_id: UUID,
        message_type: str,
        message_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Add an entry to the dialog history.
        
        Args:
            dialog_state_id: ID of the associated dialog state
            message_type: Type of message ('user' or 'bot')
            message_data: Message content and metadata
            
        Returns:
            The created history entry or None if failed
        """
        now = datetime.now()
        
        # Create history entry in the database
        history_entry = BotDialogHistory(
            dialog_state_id=dialog_state_id,
            message_type=message_type,
            message_data=message_data,
            timestamp=now
        )
        
        try:
            self.db.add(history_entry)
            await self.db.commit()
            await self.db.refresh(history_entry)
            
            self.logger.debug(LogEventType.DIALOG, f"Added {message_type} message to history", 
                           {"dialog_state_id": str(dialog_state_id)})
            
            # Convert to dictionary
            entry_dict = {
                "id": history_entry.id,
                "dialog_state_id": history_entry.dialog_state_id,
                "message_type": history_entry.message_type,
                "message_data": history_entry.message_data,
                "timestamp": history_entry.timestamp,
                "created_at": history_entry.created_at
            }
            
            return entry_dict
        except Exception as e:
            self.logger.error(LogEventType.ERROR, f"Error adding history entry: {e}", exc_info=e)
            await self.db.rollback()
            return None
            
    async def get_dialog_history(
        self,
        dialog_state_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get the history of a dialog.
        
        Args:
            dialog_state_id: ID of the dialog state
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            
        Returns:
            List of history entries, ordered by timestamp (newest first)
        """
        # Query the database
        query = (
            select(BotDialogHistory)
            .where(BotDialogHistory.dialog_state_id == dialog_state_id)
            .order_by(BotDialogHistory.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        history_entries = result.scalars().all()
        
        # Convert to list of dictionaries
        history_list = []
        for entry in history_entries:
            history_list.append({
                "id": entry.id,
                "dialog_state_id": entry.dialog_state_id,
                "message_type": entry.message_type,
                "message_data": entry.message_data,
                "timestamp": entry.timestamp,
                "created_at": entry.created_at
            })
            
        return history_list
        
    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        cache_size = len(self._cache)
        self._cache = {}
        self.logger.debug(LogEventType.CACHE, f"Cache cleared ({cache_size} entries removed)")