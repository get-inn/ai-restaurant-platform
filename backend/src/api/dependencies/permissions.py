"""
Shared permission system for bot management operations.
Consolidates duplicate permission checking logic across routers.
"""
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.api.dependencies.async_db import get_async_db
from src.api.dependencies.auth import get_current_user
from src.api.core.exceptions import PermissionDeniedError, NotFoundError
from src.api.services.bots.instance_service import InstanceService


def get_user_role(current_user: Dict[str, Any]) -> str:
    """Extract role from either a UserProfile object or a dict."""
    return current_user.role if hasattr(current_user, "role") else current_user.get("role")


def get_user_account_id(current_user: Dict[str, Any]) -> Optional[str]:
    """Extract account_id from either a UserProfile object or a dict."""
    if hasattr(current_user, "account_id"):
        return str(current_user.account_id) if current_user.account_id else None
    return current_user.get("account_id")


async def require_account_access(
    account_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Dependency that ensures user has access to the specified account.
    
    Args:
        account_id: Account ID to check access for
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: User profile if access is granted
        
    Raises:
        PermissionDeniedError: If user doesn't have access to the account
    """
    user_role = get_user_role(current_user)
    
    # Admins have access to everything
    if user_role == "admin":
        return current_user
    
    # Regular users can only access their own account
    user_account_id = get_user_account_id(current_user)
    if user_account_id != str(account_id):
        raise PermissionDeniedError(
            detail="You don't have permission to access this account's resources"
        )
    
    return current_user


async def require_bot_access(
    bot_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Dependency that ensures user has access to the specified bot.
    
    Args:
        bot_id: Bot ID to check access for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: User profile if access is granted
        
    Raises:
        PermissionDeniedError: If user doesn't have access to the bot
        NotFoundError: If bot doesn't exist
    """
    user_role = get_user_role(current_user)
    
    # Admins have access to everything
    if user_role == "admin":
        return current_user
    
    # Get the bot to check its account
    bot = await InstanceService.get_bot_instance(db, bot_id)
    if not bot:
        raise NotFoundError(detail="Bot not found")
    
    # Regular users can only access bots in their account
    user_account_id = get_user_account_id(current_user)
    if user_account_id != str(bot.account_id):
        raise PermissionDeniedError(
            detail="You don't have permission to access this bot"
        )
    
    return current_user


async def require_bot_by_account_access(
    account_id: UUID,
    bot_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Dependency that ensures user has access to a bot within a specific account.
    Validates both account access and that the bot belongs to that account.
    
    Args:
        account_id: Account ID to check
        bot_id: Bot ID to check
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: User profile if access is granted
        
    Raises:
        PermissionDeniedError: If user doesn't have access
        NotFoundError: If bot doesn't exist or doesn't belong to account
    """
    user_role = get_user_role(current_user)
    
    # Admins have access to everything
    if user_role == "admin":
        return current_user
    
    # Check account access first
    user_account_id = get_user_account_id(current_user)
    if user_account_id != str(account_id):
        raise PermissionDeniedError(
            detail="You don't have permission to access this account's resources"
        )
    
    # Verify bot belongs to the account
    bot = await InstanceService.get_bot_instance(db, bot_id)
    if not bot:
        raise NotFoundError(detail="Bot not found")
    
    if str(bot.account_id) != str(account_id):
        raise NotFoundError(detail="Bot not found in this account")
    
    return current_user


def check_admin_role(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Dependency that requires admin role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: User profile if user is admin
        
    Raises:
        PermissionDeniedError: If user is not admin
    """
    user_role = get_user_role(current_user)
    if user_role != "admin":
        raise PermissionDeniedError(
            detail="Admin role required for this operation"
        )
    
    return current_user