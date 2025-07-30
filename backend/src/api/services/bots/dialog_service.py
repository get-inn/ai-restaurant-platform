from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
import re

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
    def _evaluate_conditional_step(condition_data: Dict[str, Any], collected_data: Dict[str, Any]) -> Optional[str]:
        """
        Evaluate a conditional next_step based on collected data.
        Returns the target step ID or None if no condition matches.
        
        Condition format is:
        {
            "type": "conditional",
            "conditions": [
                {"if": "data_confirmed == 'yes'", "then": "first_day_instructions"},
                {"if": "data_confirmed == 'no'", "then": "welcome"}
            ]
        }
        """
        if not condition_data or not isinstance(condition_data, dict):
            return None
            
        if condition_data.get("type") != "conditional" or "conditions" not in condition_data:
            return None
            
        conditions = condition_data.get("conditions", [])
        for condition in conditions:
            condition_expr = condition.get("if")
            then_step = condition.get("then")
            
            if not condition_expr or not then_step:
                continue
                
            # Parse the condition expression
            # Simple implementation for expressions like "variable == 'value'"
            parts = condition_expr.split("==")
            if len(parts) != 2:
                continue
                
            var_name = parts[0].strip()
            expected_value = parts[1].strip().strip("'\"")
            
            # Check if the variable exists in collected data
            if var_name in collected_data:
                actual_value = collected_data.get(var_name)
                if str(actual_value) == expected_value:
                    return then_step
        
        # If there's an else condition
        for condition in conditions:
            if "else" in condition:
                return condition.get("else")
                
        return None
    
    @staticmethod
    def _replace_variables(message_data: Dict[str, Any], collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace variable placeholders in message text with collected data values.
        Variable format is {{variable_name}}.
        """
        if not message_data or not collected_data:
            return message_data
            
        # Create a copy of the message data to avoid modifying the original
        result = dict(message_data)
        
        # Process text field if it exists
        if "text" in result and isinstance(result["text"], str):
            text = result["text"]
            
            # Find all variable placeholders and replace them
            pattern = r'\{\{(\w+)\}\}'
            
            def replace_var(match):
                var_name = match.group(1)
                if var_name in collected_data:
                    return str(collected_data[var_name])
                return match.group(0)  # Return original if not found
                
            # Use re.sub to replace all variables
            text = re.sub(pattern, replace_var, text)
                    
            # Update the text in the result
            result["text"] = text
            
        return result
    
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
            steps = scenario.scenario_data.get("steps", {})
            start_step = scenario.scenario_data.get("start_step")
            first_step = None
            
            # Handle different formats of steps: could be list or dictionary
            if start_step:
                # If a start step is specified in the scenario, use that
                first_step = start_step
            elif isinstance(steps, list) and steps:
                # If steps is a list, use the first item's id
                first_step = steps[0].get("id")
            elif isinstance(steps, dict) and steps:
                # If steps is a dictionary, use the first key
                first_step = list(steps.keys())[0]
            
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
            steps = scenario.scenario_data.get("steps", {})
            step_data = None
            
            # Handle different formats of steps: could be list or dictionary
            if isinstance(steps, list):
                # If steps is a list, find the step with matching id
                step_data = next((s for s in steps if s.get("id") == first_step), None)
            elif isinstance(steps, dict):
                # If steps is a dictionary, get the step by key
                step_data = steps.get(first_step)
                if step_data is not None and step_data.get("id") is None:
                    # Ensure the step has an id field
                    step_data = {**step_data, "id": first_step}
            
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
            
            # Process the message to replace variables
            message = step_data.get("message", {})
            processed_message = DialogService._replace_variables(message, {})
            
            return {
                "message": processed_message,
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
            steps = scenario.scenario_data.get("steps", {})
            current_step_data = None
            
            # Handle different formats of steps: could be list or dictionary
            if isinstance(steps, list):
                # If steps is a list, find the step with matching id
                current_step_data = next((s for s in steps if s.get("id") == dialog_state.current_step), None)
            elif isinstance(steps, dict):
                # If steps is a dictionary, get the step by key
                current_step_data = steps.get(dialog_state.current_step)
                if current_step_data is not None and current_step_data.get("id") is None:
                    # Ensure the step has an id field
                    current_step_data = {**current_step_data, "id": dialog_state.current_step}
            
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
                
                # Handle different types of next_step values
                if isinstance(next_step, dict):
                    # This is a conditional step
                    evaluated_step = DialogService._evaluate_conditional_step(next_step, collected_data)
                    if evaluated_step:
                        # Use the evaluated target step
                        update_data.current_step = evaluated_step
                elif next_step:
                    # This is a simple string step ID
                    update_data.current_step = next_step
                
                dialog_state = await DialogService.update_dialog_state(db, dialog_state.id, update_data)
                
                # Find the next step in the scenario
                steps = scenario.scenario_data.get("steps", {})
                next_step_data = None
                
                # Get the updated dialog state after evaluating conditionals
                dialog_state = await DialogService.get_dialog_state_by_id(db, dialog_state.id)
                if not dialog_state:
                    return None
                    
                # Use the resolved current_step from the database
                next_step_id = dialog_state.current_step
                
                # Handle different formats of steps: could be list or dictionary
                if isinstance(steps, list):
                    # If steps is a list, find the step with matching id
                    next_step_data = next((s for s in steps if s.get("id") == next_step_id), None)
                elif isinstance(steps, dict):
                    # If steps is a dictionary, get the step by key
                    next_step_data = steps.get(next_step_id)
                    if next_step_data is not None and next_step_data.get("id") is None:
                        # Ensure the step has an id field
                        next_step_data = {**next_step_data, "id": next_step_id}
                
                if next_step_data:
                    # Process the message to replace variables
                    message = next_step_data.get("message", {})
                    processed_message = DialogService._replace_variables(message, dialog_state.collected_data)
                    
                    return {
                        "message": processed_message,
                        "buttons": next_step_data.get("buttons", []),
                        "next_step": next_step_data.get("next_step")
                    }
            
            # Process the message to replace variables
            message = {"text": "I'm not sure what to do next."}
            processed_message = DialogService._replace_variables(message, dialog_state.collected_data)
            
            return {
                "message": processed_message,
                "buttons": [],
                "next_step": None
            }