from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from src.api.dependencies.async_db import get_async_db
from src.api.dependencies.auth import get_current_user
from src.api.core.logging_config import get_logger
from src.api.schemas.bots.instance_schemas import (
    BotPlatformCredentialCreate,
    BotPlatformCredentialUpdate,
    BotPlatformCredentialDB
)
from src.api.services.bots.instance_service import InstanceService
from src.api.services.bots.platform_service import PlatformService


logger = get_logger("platform_router")
sys_logger = logging.getLogger("platform_router")


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


@router.post("/bots/{bot_id}/platforms", response_model=BotPlatformCredentialDB, status_code=status.HTTP_201_CREATED)
async def add_platform_credential(
    bot_id: UUID,
    credential_data: BotPlatformCredentialCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Add platform credentials to a bot.
    """
    try:
        sys_logger.info(f"Creating platform credential for bot_id={bot_id}")
        
        # Check if bot exists and user has permission
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
                detail="You don't have permission to add credentials to this bot"
            )
        
        # Add platform credential
        platform_credential = await InstanceService.add_platform_credential(db, bot_id, credential_data)
        if not platform_credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
            
        return platform_credential
    except HTTPException:
        raise
    except Exception as e:
        sys_logger.error(f"Error creating platform credential: {str(e)}")
        sys_logger.exception("Full exception details:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create platform credential: {str(e)}"
        )


@router.get("/bots/{bot_id}/platforms", response_model=List[BotPlatformCredentialDB])
async def get_bot_platform_credentials(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get all platform credentials for a bot.
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
                detail="You don't have permission to view credentials for this bot"
            )
        
        # Get all platform credentials for this bot
        credentials = await InstanceService.get_bot_platform_credentials(db, bot_id)
        return credentials
    except HTTPException:
        raise
    except Exception as e:
        sys_logger.error(f"Error getting platform credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform credentials: {str(e)}"
        )


@router.get("/bots/{bot_id}/platforms/{platform}", response_model=BotPlatformCredentialDB)
async def get_platform_credential(
    bot_id: UUID,
    platform: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get platform credentials for a bot and specific platform.
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
                detail="You don't have permission to view credentials for this bot"
            )
            
        # Get the credential
        credential = await InstanceService.get_platform_credential(db, bot_id, platform)
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No credentials found for platform {platform}"
            )
            
        return credential
    except HTTPException:
        raise
    except Exception as e:
        sys_logger.error(f"Error getting platform credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform credential: {str(e)}"
        )


@router.put("/bots/{bot_id}/platforms/{platform}", response_model=BotPlatformCredentialDB)
async def update_platform_credential(
    bot_id: UUID,
    platform: str,
    credential: BotPlatformCredentialUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Update platform credentials for a bot.
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
                detail="You don't have permission to update credentials for this bot"
            )
            
        # Update the credential
        updated_credential = await InstanceService.update_platform_credential(db, bot_id, platform, credential)
        if not updated_credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No credentials found for platform {platform}"
            )
            
        return updated_credential
    except HTTPException:
        raise
    except Exception as e:
        sys_logger.error(f"Error updating platform credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update platform credential: {str(e)}"
        )


@router.delete("/bots/{bot_id}/platforms/{platform}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform_credential(
    bot_id: UUID,
    platform: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    Delete platform credentials for a bot.
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
                detail="You don't have permission to delete credentials for this bot"
            )
            
        # Delete the credential
        result = await InstanceService.delete_platform_credential(db, bot_id, platform)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No credentials found for platform {platform}"
            )
            
        return None
    except HTTPException:
        raise
    except Exception as e:
        sys_logger.error(f"Error deleting platform credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete platform credential: {str(e)}"
        )