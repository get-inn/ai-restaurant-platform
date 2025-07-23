from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from src.api.dependencies.async_db import get_async_db
from src.api.dependencies.auth import get_current_user
from src.api.core.logging_config import get_logger
from src.api.schemas.bots.dialog_schemas import (
    BotDialogStateDB,
    BotDialogHistoryDB,
    DialogStateWithHistory,
    BotDialogStateCreate,
    BotDialogStateUpdate
)
from src.api.services.bots.dialog_service import DialogService
from src.api.services.bots.instance_service import InstanceService


logger = get_logger("dialog_router")
sys_logger = logging.getLogger("dialog_router")


# Helper functions for user profile access
def get_user_role(current_user: Dict[str, Any]) -> str:
    """Extract role from either a UserProfile object or a dict."""
    return current_user.role if hasattr(current_user, "role") else current_user.get("role")

def get_user_account_id(current_user: Dict[str, Any]) -> Optional[str]:
    """Extract account_id from either a UserProfile object or a dict."""
    if hasattr(current_user, "account_id"):
        return str(current_user.account_id) if current_user.account_id else None
    return current_user.get("account_id")


router = APIRouter(
    tags=["dialogs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/bots/{bot_id}/dialogs", response_model=List[BotDialogStateDB])
async def get_bot_dialogs(
    bot_id: UUID,
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get all dialog states for a specific bot, optionally filtered by platform.
    """
    try:
        # Check if bot exists
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission to view dialogs for this bot
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view dialogs for this bot"
            )
        
        dialogs = await DialogService.get_all_bot_dialogs(db, bot_id, platform)
        return dialogs
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot dialogs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot dialogs: {str(e)}"
        )


@router.get("/bots/{bot_id}/dialogs/{platform}/{chat_id}", response_model=BotDialogStateDB)
async def get_dialog_state(
    bot_id: UUID,
    platform: str,
    chat_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get a dialog state by bot ID, platform, and platform chat ID.
    If the dialog doesn't exist yet, a new one will be created.
    """
    try:
        # Check if bot exists
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view dialogs for this bot"
            )
        
        # Get or create dialog state
        dialog_state = await DialogService.get_dialog_state(db, bot_id, platform, chat_id)
        
        # If dialog state doesn't exist, create a new one
        if not dialog_state:
            dialog_create = BotDialogStateCreate(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=chat_id,
                current_step="",
                collected_data={}
            )
            dialog_state = await DialogService.create_dialog_state(db, dialog_create)
        
        return dialog_state
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dialog state: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dialog state: {str(e)}"
        )


@router.get("/bots/{bot_id}/dialogs/{platform}/{chat_id}/history", response_model=Dict[str, List[BotDialogHistoryDB]])
async def get_dialog_history_by_chat(
    bot_id: UUID,
    platform: str,
    chat_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get the history for a dialog specified by bot_id, platform, and chat_id.
    """
    try:
        # Check if bot exists
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view dialog history for this bot"
            )
        
        # Get the dialog state
        dialog_state = await DialogService.get_dialog_state(db, bot_id, platform, chat_id)
        
        # If dialog state doesn't exist, return an empty history
        if not dialog_state:
            return {"messages": []}
        
        # Get the history for the dialog
        history = await DialogService.get_dialog_history(db, dialog_state.id, limit)
        
        return {"messages": history}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dialog history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dialog history: {str(e)}"
        )


@router.put("/bots/{bot_id}/dialogs/{platform}/{chat_id}", response_model=BotDialogStateDB)
async def update_dialog_state(
    bot_id: UUID,
    platform: str,
    chat_id: str,
    dialog_update: BotDialogStateUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Update a dialog state for a specific bot, platform, and chat ID.
    If the dialog doesn't exist yet, a new one will be created with the provided data.
    """
    try:
        # Check if bot exists
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update dialogs for this bot"
            )
        
        # Get existing dialog state or create new one
        dialog_state = await DialogService.get_dialog_state(db, bot_id, platform, chat_id)
        
        if not dialog_state:
            # Create new dialog state with the provided update data
            create_data = BotDialogStateCreate(
                bot_id=bot_id,
                platform=platform,
                platform_chat_id=chat_id,
                current_step=dialog_update.current_step or "",
                collected_data=dialog_update.collected_data or {}
            )
            dialog_state = await DialogService.create_dialog_state(db, create_data)
            return dialog_state
        
        # Update existing dialog state
        updated_dialog = await DialogService.update_dialog_state(
            db, dialog_state.id, dialog_update
        )
        if not updated_dialog:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update dialog state"
            )
        
        return updated_dialog
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dialog state: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dialog state: {str(e)}"
        )


@router.get("/dialogs/{dialog_id}", response_model=BotDialogStateDB)
async def get_dialog_state_by_id(
    dialog_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get a specific dialog state by ID.
    """
    try:
        dialog_state = await DialogService.get_dialog_state_by_id(db, dialog_id)
        if not dialog_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dialog state not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, dialog_state.bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission to view this dialog state
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this dialog state"
            )
        
        return dialog_state
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dialog state: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dialog state: {str(e)}"
        )


@router.get("/dialogs/{dialog_id}/history", response_model=List[BotDialogHistoryDB])
async def get_dialog_history(
    dialog_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get the history of a specific dialog.
    """
    try:
        # Get the dialog state first to check permissions
        dialog_state = await DialogService.get_dialog_state_by_id(db, dialog_id)
        if not dialog_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dialog state not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, dialog_state.bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this dialog history"
            )
        
        history = await DialogService.get_dialog_history(db, dialog_id, limit)
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dialog history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dialog history: {str(e)}"
        )


@router.get("/dialogs/{dialog_id}/with-history", response_model=DialogStateWithHistory)
async def get_dialog_with_history(
    dialog_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get a dialog state with its history in a single request.
    """
    try:
        # Get the dialog state with history
        dialog_with_history = await DialogService.get_dialog_state_with_history(db, dialog_id, limit)
        if not dialog_with_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dialog state not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, dialog_with_history.bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this dialog with history"
            )
        
        return dialog_with_history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dialog with history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dialog with history: {str(e)}"
        )


@router.delete("/dialogs/{dialog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dialog(
    dialog_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    Delete a dialog state and all its history.
    """
    try:
        # Get the dialog state first to check permissions
        dialog_state = await DialogService.get_dialog_state_by_id(db, dialog_id)
        if not dialog_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dialog state not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, dialog_state.bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this dialog"
            )
        
        result = await DialogService.delete_dialog_state(db, dialog_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dialog state not found or already deleted"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dialog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dialog: {str(e)}"
        )