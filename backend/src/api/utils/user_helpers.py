"""
User profile utility functions.
Eliminates duplicate user profile access patterns across routers.
"""
from typing import Dict, Any, Optional


def get_user_role(current_user: Dict[str, Any]) -> str:
    """
    Extract role from either a UserProfile object or a dict.
    
    Args:
        current_user: User profile object or dictionary
        
    Returns:
        User role as string
    """
    return current_user.role if hasattr(current_user, "role") else current_user.get("role")


def get_user_account_id(current_user: Dict[str, Any]) -> Optional[str]:
    """
    Extract account_id from either a UserProfile object or a dict.
    
    Args:
        current_user: User profile object or dictionary
        
    Returns:
        Account ID as string, or None if not present
    """
    if hasattr(current_user, "account_id"):
        return str(current_user.account_id) if current_user.account_id else None
    return current_user.get("account_id")


def get_user_id(current_user: Dict[str, Any]) -> Optional[str]:
    """
    Extract user ID from either a UserProfile object or a dict.
    
    Args:
        current_user: User profile object or dictionary
        
    Returns:
        User ID as string, or None if not present
    """
    if hasattr(current_user, "id"):
        return str(current_user.id) if current_user.id else None
    return current_user.get("id")


def is_admin_user(current_user: Dict[str, Any]) -> bool:
    """
    Check if the current user has admin role.
    
    Args:
        current_user: User profile object or dictionary
        
    Returns:
        True if user is admin, False otherwise
    """
    user_role = get_user_role(current_user)
    return user_role == "admin"


def get_user_display_name(current_user: Dict[str, Any]) -> str:
    """
    Get a display name for the user (email or username).
    
    Args:
        current_user: User profile object or dictionary
        
    Returns:
        Display name as string
    """
    # Try email first
    if hasattr(current_user, "email") and current_user.email:
        return current_user.email
    elif isinstance(current_user, dict) and current_user.get("email"):
        return current_user["email"]
    
    # Fall back to username
    if hasattr(current_user, "username") and current_user.username:
        return current_user.username
    elif isinstance(current_user, dict) and current_user.get("username"):
        return current_user["username"]
    
    # Fall back to ID
    user_id = get_user_id(current_user)
    return f"User {user_id}" if user_id else "Unknown User"


def format_user_context(current_user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format user information for logging context.
    
    Args:
        current_user: User profile object or dictionary
        
    Returns:
        Dictionary with user context for logging
    """
    return {
        "user_id": get_user_id(current_user),
        "user_role": get_user_role(current_user),
        "account_id": get_user_account_id(current_user),
        "display_name": get_user_display_name(current_user)
    }