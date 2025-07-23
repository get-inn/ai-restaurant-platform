from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

logger = logging.getLogger("dialog_service")
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.orm import joinedload

from src.api.models import BotDialogState, BotDialogHistory, BotInstance, BotScenario
from src.api.schemas.bots.dialog_schemas import (
    BotDialogStateCreate,
    BotDialogStateUpdate,
    BotDialogStateDB,
    BotDialogHistoryCreate,
    BotDialogHistoryDB,
    DialogStateWithHistory
)


class DialogService:
    @staticmethod
    async def create_dialog_state(
        db: AsyncSession, dialog_state: BotDialogStateCreate
    ) -> BotDialogStateDB:
        """Create a new dialog state for a user interaction with a bot"""
        now = datetime.now()
        db_dialog_state = BotDialogState(
            bot_id=dialog_state.bot_id,
            platform=dialog_state.platform,
            platform_chat_id=dialog_state.platform_chat_id,
            current_step=dialog_state.current_step,
            collected_data=dialog_state.collected_data,
            last_interaction_at=now
        )
        db.add(db_dialog_state)
        await db.commit()
        await db.refresh(db_dialog_state)
        return BotDialogStateDB.model_validate(db_dialog_state)

    @staticmethod
    async def get_dialog_state(
        db: AsyncSession, 
        bot_id: UUID, 
        platform: str, 
        platform_chat_id: str
    ) -> Optional[BotDialogStateDB]:
        """Get a dialog state by bot_id, platform and platform_chat_id"""
        try:
            logger.info(f"Getting dialog state for bot_id={bot_id}, platform={platform}, chat_id={platform_chat_id}")
            query = (
                select(BotDialogState)
                .where(
                    BotDialogState.bot_id == bot_id,
                    BotDialogState.platform == platform,
                    BotDialogState.platform_chat_id == platform_chat_id
                )
            )
            result = await db.execute(query)
            dialog_state = result.unique().scalars().first()
            
            if dialog_state:
                logger.info(f"Found existing dialog state with id={dialog_state.id}")
                return BotDialogStateDB.model_validate(dialog_state)
            logger.info(f"No existing dialog state found")
            return None
        except Exception as e:
            logger.error(f"Error in get_dialog_state: {str(e)}")
            raise

    @staticmethod
    async def get_dialog_state_by_id(
        db: AsyncSession, dialog_state_id: UUID
    ) -> Optional[BotDialogStateDB]:
        """Get a dialog state by its ID"""
        try:
            logger.info(f"Getting dialog state by id={dialog_state_id}")
            query = select(BotDialogState).where(BotDialogState.id == dialog_state_id)
            result = await db.execute(query)
            dialog_state = result.unique().scalars().first()
            
            if dialog_state:
                logger.info(f"Found dialog state with id={dialog_state_id}")
                return BotDialogStateDB.model_validate(dialog_state)
            logger.info(f"No dialog state found with id={dialog_state_id}")
            return None
        except Exception as e:
            logger.error(f"Error in get_dialog_state_by_id: {str(e)}")
            raise

    @staticmethod
    async def update_dialog_state(
        db: AsyncSession,
        dialog_state_id: UUID,
        dialog_state_update: BotDialogStateUpdate
    ) -> Optional[BotDialogStateDB]:
        """Update an existing dialog state"""
        query = select(BotDialogState).where(BotDialogState.id == dialog_state_id)
        result = await db.execute(query)
        db_dialog_state = result.unique().scalars().first()
        
        if not db_dialog_state:
            return None
        
        update_data = dialog_state_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_dialog_state, key, value)
        
        # Always update the last_interaction_at field when updating the dialog state
        if "last_interaction_at" not in update_data:
            db_dialog_state.last_interaction_at = datetime.now()
            
        await db.commit()
        await db.refresh(db_dialog_state)
        return BotDialogStateDB.model_validate(db_dialog_state)

    @staticmethod
    async def delete_dialog_state(db: AsyncSession, dialog_state_id: UUID) -> bool:
        """Delete a dialog state and all its history"""
        # First delete all history entries
        await db.execute(
            delete(BotDialogHistory)
            .where(BotDialogHistory.dialog_state_id == dialog_state_id)
        )
        
        # Then delete the dialog state
        result = await db.execute(
            delete(BotDialogState)
            .where(BotDialogState.id == dialog_state_id)
        )
        await db.commit()
        
        return result.rowcount > 0

    @staticmethod
    async def create_dialog_history_entry(
        db: AsyncSession, history_entry: BotDialogHistoryCreate
    ) -> BotDialogHistoryDB:
        """Create a new entry in the dialog history"""
        db_history_entry = BotDialogHistory(
            dialog_state_id=history_entry.dialog_state_id,
            message_type=history_entry.message_type,
            message_data=history_entry.message_data,
            timestamp=history_entry.timestamp
        )
        db.add(db_history_entry)
        await db.commit()
        await db.refresh(db_history_entry)
        return BotDialogHistoryDB.model_validate(db_history_entry)

    @staticmethod
    async def get_dialog_history(
        db: AsyncSession, dialog_state_id: UUID, limit: int = 50
    ) -> List[BotDialogHistoryDB]:
        """Get the history of a dialog, ordered by timestamp (newest first)"""
        query = (
            select(BotDialogHistory)
            .where(BotDialogHistory.dialog_state_id == dialog_state_id)
            .order_by(BotDialogHistory.timestamp.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        history_entries = result.unique().scalars().all()
        return [BotDialogHistoryDB.model_validate(entry) for entry in history_entries]

    @staticmethod
    async def get_dialog_state_with_history(
        db: AsyncSession, dialog_state_id: UUID, limit: int = 50
    ) -> Optional[DialogStateWithHistory]:
        """Get a dialog state with its history"""
        # Get the dialog state
        dialog_state = await DialogService.get_dialog_state_by_id(db, dialog_state_id)
        if not dialog_state:
            return None
        
        # Get the history
        history = await DialogService.get_dialog_history(db, dialog_state_id, limit)
        
        # Combine into a single response
        return DialogStateWithHistory(
            **dialog_state.model_dump(),
            history=history
        )

    @staticmethod
    async def get_all_bot_dialogs(
        db: AsyncSession, bot_id: UUID, platform: Optional[str] = None
    ) -> List[BotDialogStateDB]:
        """Get all dialog states for a specific bot, optionally filtered by platform"""
        query = select(BotDialogState).where(BotDialogState.bot_id == bot_id)
        
        if platform:
            query = query.where(BotDialogState.platform == platform)
            
        query = query.order_by(BotDialogState.last_interaction_at.desc())
        
        result = await db.execute(query)
        dialog_states = result.unique().scalars().all()
        return [BotDialogStateDB.model_validate(state) for state in dialog_states]

    @staticmethod
    async def process_user_input(
        db: AsyncSession,
        bot_id: UUID,
        platform: str,
        platform_chat_id: str,
        user_input: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Process user input and advance the dialog based on the scenario
        Returns the next response to send to the user
        """
        # First, get or create dialog state
        dialog_state = await DialogService.get_dialog_state(db, bot_id, platform, platform_chat_id)
        
        if not dialog_state:
            # Get the bot instance to verify it exists
            query = select(BotInstance).where(BotInstance.id == bot_id)
            result = await db.execute(query)
            bot_instance = result.unique().scalars().first()
            
            if not bot_instance:
                return None
                
            # Get active scenario
            query = (
                select(BotScenario)
                .where(
                    BotScenario.bot_id == bot_id,
                    BotScenario.is_active == True
                )
                .order_by(BotScenario.created_at.desc())
            )
            result = await db.execute(query)
            scenario = result.unique().scalars().first()
            
            if not scenario:
                return None
                
            # Create new dialog state starting with the first step
            first_step = scenario.scenario_data.get("steps", [])[0].get("id") if scenario.scenario_data.get("steps") else None
            
            if not first_step:
                return None
                
            dialog_state_create = BotDialogStateCreate(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=platform_chat_id,
                current_step=first_step,
                collected_data={}
            )
            dialog_state = await DialogService.create_dialog_state(db, dialog_state_create)
            
            # Logic to get the first message from the scenario
            # This is simplified - a real implementation would have more complex scenario processing
            step_data = next((s for s in scenario.scenario_data.get("steps", []) if s.get("id") == first_step), None)
            
            if not step_data:
                return None
                
            # Record user interaction in history
            history_entry = BotDialogHistoryCreate(
                dialog_state_id=dialog_state.id,
                message_type="user",
                message_data={"input": user_input},
                timestamp=datetime.now()
            )
            await DialogService.create_dialog_history_entry(db, history_entry)
            
            return {
                "message": step_data.get("message", {}),
                "buttons": step_data.get("buttons", []),
                "next_step": step_data.get("next_step")
            }
        else:
            # Existing dialog, process based on current state
            # This is where the main scenario processing logic would go
            # For now, just return a placeholder
            
            # Record user interaction in history
            history_entry = BotDialogHistoryCreate(
                dialog_state_id=dialog_state.id,
                message_type="user",
                message_data={"input": user_input},
                timestamp=datetime.now()
            )
            await DialogService.create_dialog_history_entry(db, history_entry)
            
            # Get active scenario
            query = (
                select(BotScenario)
                .where(
                    BotScenario.bot_id == bot_id,
                    BotScenario.is_active == True
                )
                .order_by(BotScenario.created_at.desc())
            )
            result = await db.execute(query)
            scenario = result.unique().scalars().first()
            
            if not scenario:
                return None
                
            # Find the current step in the scenario
            current_step_data = next(
                (s for s in scenario.scenario_data.get("steps", []) if s.get("id") == dialog_state.current_step), 
                None
            )
            
            if not current_step_data:
                return None
                
            # Update collected data based on user input and expected input type
            expected_input = current_step_data.get("expected_input", {})
            variable_name = expected_input.get("variable", "")
            
            if variable_name:
                # Update the dialog state with the collected data
                collected_data = dialog_state.collected_data.copy()
                collected_data[variable_name] = user_input
                
                update_data = BotDialogStateUpdate(
                    collected_data=collected_data
                )
                
                # If there's a next step defined, move to it
                next_step = current_step_data.get("next_step")
                if next_step:
                    update_data.current_step = next_step
                
                dialog_state = await DialogService.update_dialog_state(db, dialog_state.id, update_data)
                
                # Find the next step in the scenario
                next_step_data = next(
                    (s for s in scenario.scenario_data.get("steps", []) if s.get("id") == next_step), 
                    None
                ) if next_step else None
                
                if next_step_data:
                    return {
                        "message": next_step_data.get("message", {}),
                        "buttons": next_step_data.get("buttons", []),
                        "next_step": next_step_data.get("next_step")
                    }
            
            return {
                "message": {"text": "I'm not sure what to do next."},
                "buttons": [],
                "next_step": None
            }