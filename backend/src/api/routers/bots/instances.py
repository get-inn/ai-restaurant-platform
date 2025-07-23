from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from src.api.dependencies.async_db import get_async_db
from src.api.dependencies.auth import get_current_user
from src.api.core.logging_config import get_logger
from src.api.schemas.bots.instance_schemas import (
    BotInstanceCreate,
    BotInstanceUpdate,
    BotInstanceDB
)
from src.api.services.bots.instance_service import InstanceService


logger = get_logger("bot_router")
sys_logger = logging.getLogger("bot_router")


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
    tags=["bots"],
    responses={404: {"description": "Not found"}},
)


@router.post("/accounts/{account_id}/bots", response_model=BotInstanceDB, status_code=status.HTTP_201_CREATED)
async def create_bot_instance(
    account_id: UUID,
    bot_data: BotInstanceCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Create a new bot instance for an account.
    """
    try:
        # Ensure account_id in path matches the one in the request body
        if str(account_id) != str(bot_data.account_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account ID in path must match account ID in request body"
            )
        
        # Check if current user has permission to create a bot for this account
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        
        if user_role != "admin" and user_account_id != str(account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create a bot for this account"
            )
        
        bot_instance = await InstanceService.create_bot_instance(db, bot_data)
        if not bot_instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return bot_instance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bot: {str(e)}"
        )


@router.get("/accounts/{account_id}/bots", response_model=List[BotInstanceDB])
async def get_account_bots(
    account_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get all bots for an account.
    """
    try:
        # Check if current user has permission to view bots for this account
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        
        if user_role != "admin" and user_account_id != str(account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view bots for this account"
            )
        
        bots = await InstanceService.get_account_bots(db, account_id)
        return bots
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account bots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bots: {str(e)}"
        )


@router.get("/bots/{bot_id}", response_model=BotInstanceDB)
async def get_bot(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get a bot by ID.
    """
    try:
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission to view this bot
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this bot"
            )
        
        return bot
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot: {str(e)}"
        )


@router.put("/bots/{bot_id}", response_model=BotInstanceDB)
async def update_bot_instance(
    bot_id: UUID,
    bot_update: BotInstanceUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Update a bot instance.
    """
    try:
        # Check if bot exists
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission to update this bot
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this bot"
            )
        
        # Update bot
        updated_bot = await InstanceService.update_bot_instance(db, bot_id, bot_update)
        if not updated_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        return updated_bot
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bot: {str(e)}"
        )


@router.delete("/bots/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot_instance(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    Delete a bot instance and all associated data.
    """
    try:
        # Check if bot exists
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission to delete this bot
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this bot"
            )
        
        # Delete bot
        success = await InstanceService.delete_bot_instance(db, bot_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete bot"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete bot: {str(e)}"
        )


@router.post("/bots/{bot_id}/activate", response_model=BotInstanceDB)
async def activate_bot(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Activate a bot.
    """
    try:
        # Check if bot exists
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission to activate this bot
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to activate this bot"
            )
        
        bot_instance = await InstanceService.activate_bot(db, bot_id, True)
        if not bot_instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        return bot_instance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate bot: {str(e)}"
        )


@router.post("/bots/{bot_id}/deactivate", response_model=BotInstanceDB)
async def deactivate_bot(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Deactivate a bot.
    """
    try:
        # Check if bot exists
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission to deactivate this bot
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to deactivate this bot"
            )
        
        bot_instance = await InstanceService.activate_bot(db, bot_id, False)
        if not bot_instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        return bot_instance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate bot: {str(e)}"
        )


@router.get("/bots", response_model=List[BotInstanceDB])
async def get_all_bots(
    account_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get all bots, optionally filtered by account ID.
    """
    try:
        if account_id:
            # Check if current user has permission to view bots for this account
            user_role = get_user_role(current_user)
            user_account_id = get_user_account_id(current_user)
            if user_role != "admin" and user_account_id != str(account_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view bots for this account"
                )
            
            return await InstanceService.get_account_bots(db, account_id)
        
        # If no account_id is provided and user is not admin, return only bots for their account
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id:
            return await InstanceService.get_account_bots(db, UUID(user_account_id))
        
        # Admin can see all bots
        if user_role == "admin":
            # TODO: Implement function to get all bots with filtering
            return []
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view all bots"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bots: {str(e)}"
        )