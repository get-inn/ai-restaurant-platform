import os
from fastapi import Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import ValidationError
from typing import Optional

from src.api.core.config import get_settings
from src.api.core.exceptions import AuthError, PermissionDeniedError
from src.api.dependencies.db import get_db
from src.api.schemas.auth_schemas import TokenPayload, UserRole
from src.api.services.auth_service import get_user_profile_by_id

settings = get_settings()
security = HTTPBearer()

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """
    Validate JWT token and extract user ID.
    
    Args:
        credentials: HTTP auth credentials
        
    Returns:
        str: User ID
        
    Raises:
        AuthError: If token is invalid
    """
    try:
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise AuthError(detail="Could not validate credentials")
        
    return token_data.sub


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user profile.
    
    Args:
        user_id: User ID from token
        db: Database session
        
    Returns:
        dict: User profile
        
    Raises:
        AuthError: If user not found
    """
    user = get_user_profile_by_id(db, user_id)
    if not user:
        raise AuthError(detail="User not found")
    return user


def check_role(allowed_roles: list[UserRole]):
    """
    Create a dependency that checks if the current user has one of the allowed roles.
    
    Args:
        allowed_roles: List of allowed roles
        
    Returns:
        function: Dependency function
    """
    async def _check_role(user = Depends(get_current_user)):
        # Handle both UserProfile objects and dictionaries
        user_role = user.role if hasattr(user, 'role') else user.get('role')
        if user_role not in [role.value for role in allowed_roles]:
            raise PermissionDeniedError(
                detail=f"Role {user_role} not authorized for this operation"
            )
        return user
    return _check_role


def has_account_access(account_id: str = None, restaurant_id: str = None, store_id: str = None):
    """
    Check if user has access to the specified account, restaurant, or store.
    
    Args:
        account_id: Optional account ID to check
        restaurant_id: Optional restaurant ID to check
        store_id: Optional store ID to check
        
    Returns:
        function: Dependency function
    """
    async def _has_access(
        user = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        # Admin has access to everything
        user_role = user.role if hasattr(user, 'role') else user.get('role')
        if user_role == UserRole.ADMIN.value:
            return user
            
        # TODO: Implement access check logic for other roles
        # This will need to query the database to check relationships
        # between accounts, restaurants, and stores
        
        return user
    return _has_access