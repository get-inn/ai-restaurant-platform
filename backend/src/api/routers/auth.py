from fastapi import APIRouter, Depends, Body, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional

from src.api.dependencies.db import get_db
from src.api.schemas.auth_schemas import (
    LoginRequest,
    Token,
    UserResponse,
    RefreshTokenRequest,
)
from src.api.services.auth_service import (
    authenticate_user,
    create_access_token,
    refresh_token,
    get_current_user,
    get_test_token,
)
from src.api.core.logging_config import get_logger
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
security = HTTPBearer()
logger = get_logger("restaurant_api")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/api/auth/login")


@router.post("/login", response_model=Token)
async def login_user(
    login_data: LoginRequest = Body(...),
    db: Session = Depends(get_db),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    try:
        user = authenticate_user(db, login_data.email, login_data.password)
        return create_access_token(user["id"])
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_request: RefreshTokenRequest = Body(...),
    db: Session = Depends(get_db),
) -> Any:
    """
    Refresh access token.
    """
    try:
        return refresh_token(db, refresh_request.refresh_token)
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout")
async def logout_user() -> Dict[str, str]:
    """
    Logout user.
    
    Note: In this implementation, tokens are revoked client-side by clearing them.
    A more secure approach would involve token blacklisting on the server.
    """
    return {"detail": "Successfully logged out"}


@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)) -> Any:
    """
    Get current user info.
    """
    return current_user




@router.post("/test-token", response_model=Token)
async def get_test_token_endpoint(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a test token for API testing.
    This endpoint is intended for testing purposes only.
    
    If user_id is provided, it will generate a token for that specific user.
    Otherwise, it will generate a token for the default test user.
    """
    try:
        # Use the default test user if no user_id is provided
        test_user_id = user_id or "00000000-0000-0000-0000-000000000001"
        
        logger.info(f"Getting test token for user ID: {test_user_id}")
        
        # Call the service function to generate the test token
        token_data = get_test_token(db, test_user_id)
        
        logger.info(f"Successfully generated token for user {test_user_id}")
        return token_data
        
    except HTTPException:
        # Re-throw HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Test token generation error: {str(e)}")
        db.rollback()  # Roll back any pending transactions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test token: {str(e)}",
        )