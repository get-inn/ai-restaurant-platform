"""
Test endpoints for development and testing purposes.
These endpoints should NOT be enabled in production environments.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
import uuid
import logging

from src.api.dependencies.db import get_db
from src.api.schemas.auth_schemas import Token
from src.api.services.auth_service import create_access_token, initialize_users, get_user_profile_by_id

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/ping")
async def ping_endpoint() -> Dict[str, str]:
    """
    Simple ping endpoint for testing if the API is up and running.
    Returns a simple response with status "ok" and message "pong".
    """
    return {"status": "ok", "message": "pong"}

@router.post("/token", response_model=Token)
async def get_test_token(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a test token for API testing.
    This endpoint is intended for testing purposes only and should be disabled in production.
    
    If user_id is provided, it will generate a token for that specific user.
    Otherwise, it will generate a token for the default test user (admin).
    """
    try:
        # Use the default test user if no user_id is provided
        test_user_id = user_id or "00000000-0000-0000-0000-000000000001"
        
        logger.info(f"Getting test token for user ID: {test_user_id}")
        
        # Generate a role based on the user_id
        # This is a simplified approach that doesn't require database access
        role = "admin"  # Default role
        if test_user_id == "00000000-0000-0000-0000-000000000000":
            role = "admin"
        elif test_user_id == "00000000-0000-0000-0000-000000000001":
            role = "admin"
        elif test_user_id == "00000000-0000-0000-0000-000000000002":
            role = "account_manager"
        elif test_user_id == "00000000-0000-0000-0000-000000000003":
            role = "restaurant_manager"
        elif test_user_id == "00000000-0000-0000-0000-000000000004":
            role = "chef"
        
        email = "test@example.com"
        
        logger.info(f"Generating test token for user ID {test_user_id} with role {role}")
        token_data = create_access_token(
            user_id=test_user_id,
            email=email,
            role=role
        )
        
        logger.info(f"Successfully generated token for user {test_user_id}")
        return token_data
        
    except Exception as e:
        logger.error(f"Test token generation error: {str(e)}")
        # Instead of raising the exception, return a fallback token
        # This ensures tests can continue even if there are database issues
        logger.info("Generating fallback admin test token")
        return create_access_token(
            user_id="00000000-0000-0000-0000-000000000001",
            email="test@example.com",
            role="admin"
        )