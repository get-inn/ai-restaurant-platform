from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Response, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import os
import logging
import mimetypes

from src.api.dependencies.async_db import get_async_db
from src.api.dependencies.auth import get_current_user
from src.api.core.logging_config import get_logger
from src.api.schemas.bots.media_schemas import (
    BotMediaFileDB,
    MediaUploadResponse,
    PlatformFileIDUpdate
)
from src.api.services.bots.media_service import MediaService
from src.api.services.bots.instance_service import InstanceService
from src.api.core.config import get_settings

settings = get_settings()
logger = get_logger("media_router")
sys_logger = logging.getLogger("media_router")

# Create security schemes
http_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="x-service-key", auto_error=False)

# Service key for internal service-to-service communication
SERVICE_KEY = "dialog_manager_service_key"

# Helper functions for user profile access
def get_user_role(current_user: Dict[str, Any]) -> str:
    """Extract role from either a UserProfile object or a dict."""
    return current_user.role if hasattr(current_user, "role") else current_user.get("role")

def get_user_account_id(current_user: Dict[str, Any]) -> Optional[str]:
    """Extract account_id from either a UserProfile object or a dict."""
    if hasattr(current_user, "account_id"):
        return str(current_user.account_id) if current_user.account_id else None
    return current_user.get("account_id")

# Authentication dependency with optional authentication
async def get_optional_auth(
    db: AsyncSession = Depends(get_async_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer),
    service_key: Optional[str] = Security(api_key_header)
) -> Optional[Dict[str, Any]]:
    """
    Check for either:
    1. Valid JWT token from get_current_user
    2. Valid service key for internal service-to-service communication
    3. Allow access to media files when both are not provided (for bot media)
    """
    # Check for service key first (fastest)
    if service_key and service_key == SERVICE_KEY:
        return {"role": "service", "service_name": "dialog_manager"}
    
    # Then check for JWT token
    if credentials:
        try:
            current_user = await get_current_user(credentials)
            logger.info(f"Authenticated user with role: {current_user.get('role')}, account_id: {current_user.get('account_id')}")
            return current_user
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            pass
    
    # No valid auth, but we'll still allow access specifically for media files
    # Permission checks will be done in the endpoint
    return None

router = APIRouter(
    tags=["media"],
    responses={404: {"description": "Not found"}},
)


async def _check_media_file_access(
    auth_result: Optional[Dict[str, Any]],
    media_file: BotMediaFileDB,
    bot: Any,
    media_id: str
) -> None:
    """
    Check if the requester has access to the media file.
    
    Access is granted in these cases:
    1. Requester is authenticated with admin or matching account_id
    2. Requester is a service with a valid service key
    3. Media file is referenced in bot scenarios (even without auth)
    
    Raises HTTPException with 403 status if access is denied.
    """
    # Log the media file ID and the requested media ID
    logger.debug(f"Checking access for media_id: {media_id}, media file ID: {media_file.id}")
    
    # Check if this is a scenario-referenced media file (always allow access)
    platform_file_ids = media_file.platform_file_ids or {}
    
    logger.debug(f"Platform file IDs: {platform_file_ids}")
    
    scenario_reference = False
    # Check if the media_id is in the platform_file_ids values
    for platform, file_id in platform_file_ids.items():
        logger.debug(f"Comparing {media_id} with {file_id}")
        if media_id == file_id:
            logger.debug(f"Scenario reference match found")
            scenario_reference = True
            break
    
    # If this is a scenario reference, always allow access regardless of auth
    if scenario_reference:
        logger.info(f"Access granted for scenario reference: {media_id}")
        return
    
    # If not a scenario reference, we need authentication
    if auth_result is None:
        logger.warning(f"No authentication provided for media_id: {media_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required for this media file"
        )
    
    # Log auth details
    logger.debug(f"Auth result: role={auth_result.get('role')}, account_id={auth_result.get('account_id')}")
    
    # If authenticated as admin or service, allow access
    if auth_result.get("role") in ["admin", "service"]:
        logger.info(f"Access granted for admin/service role: {auth_result.get('role')}")
        return
        
    # Otherwise, check if user has access to the bot's account
    user_account_id = get_user_account_id(auth_result)
    bot_account_id = str(bot.account_id) if bot.account_id else None
    
    logger.debug(f"Comparing user account ID {user_account_id} with bot account ID {bot_account_id}")
    
    if user_account_id != bot_account_id:
        logger.warning(f"Account ID mismatch: user={user_account_id}, bot={bot_account_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this media file"
        )
        
    logger.info(f"Access granted for account match: {user_account_id}")
    return


@router.post("/bots/{bot_id}/media", response_model=MediaUploadResponse)
async def upload_media_file(
    bot_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Upload a media file for a bot and store it in the database.
    """
    try:
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
                detail="You don't have permission to upload media for this bot"
            )
        
        # Create media file directly in the database
        media_file = await MediaService.create_media_file(db, file, bot_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create media file"
            )
        
        return MediaUploadResponse(
            media_id=media_file.id,
            file_name=media_file.file_name,
            file_type=media_file.file_type,
            content_type=media_file.content_type,
            file_size=media_file.file_size
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading media file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload media file: {str(e)}"
        )


@router.get("/bots/{bot_id}/media", response_model=List[BotMediaFileDB])
async def get_bot_media_files(
    bot_id: UUID,
    file_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get all media files for a specific bot, optionally filtered by file type.
    """
    try:
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
                detail="You don't have permission to view media files for this bot"
            )
        
        media_files = await MediaService.get_bot_media_files(db, bot_id, file_type, limit, offset)
        return media_files
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot media files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot media files: {str(e)}"
        )


@router.get("/media/{media_id}", response_model=BotMediaFileDB)
async def get_media_file_metadata(
    media_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get metadata for a specific media file.
    """
    try:
        media_file = await MediaService.get_media_file(db, media_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, media_file.bot_id)
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
                detail="You don't have permission to view this media file"
            )
        
        return media_file
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting media file metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get media file metadata: {str(e)}"
        )




@router.get("/media/{media_id}/content")
async def get_media_file_content(
    media_id: str,
    db: AsyncSession = Depends(get_async_db),
    auth_result: Optional[Dict[str, Any]] = Depends(get_optional_auth)
) -> Response:
    """
    Get the actual content of a media file from the database.
    
    The media_id can be either:
    - A UUID of the media file in the database
    - A platform-specific file ID (like "company_history_image")
    
    Authentication is optional for this endpoint, but access may be restricted 
    based on the media file type and requesting context.
    """
    try:
        # Find the media file by UUID or file_id
        media_file = await MediaService.find_media_file_by_id_or_name(db, media_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Get the bot info
        bot = await InstanceService.get_bot_instance(db, media_file.bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Handle authorization based on auth_result
        await _check_media_file_access(auth_result, media_file, bot, media_id)
        
        # Get file content directly from database
        # Always use the media file's ID from the database, not the input media_id
        # This ensures we're reading the correct content even if accessed via a platform file ID
        media_uuid = media_file.id
        
        # Log which UUID we're using for debugging
        logger.debug(f"Using media UUID for content retrieval: {media_uuid}")
        logger.debug(f"Original media_id parameter: {media_id}")
            
        file_content_result = await MediaService.get_file_content(db, media_uuid)
        if not file_content_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file content not found"
            )
            
        content_bytes, content_type = file_content_result
        
        # Ensure we're using a valid content type
        final_content_type = content_type
        if not content_type or content_type == "application/octet-stream":
            # Try to guess from filename
            guessed_type = mimetypes.guess_type(media_file.file_name)[0]
            if guessed_type:
                final_content_type = guessed_type
        
        logger.debug(f"Serving media content with type: {final_content_type}, original: {content_type}")
        
        return Response(
            content=content_bytes,
            media_type=final_content_type,
            headers={
                "Content-Disposition": f"attachment; filename={media_file.file_name}",
                "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting media file content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get media file content: {str(e)}"
        )




@router.post("/media/{media_id}/platform-id", response_model=BotMediaFileDB)
async def update_platform_file_id(
    media_id: UUID,
    platform_file_id: PlatformFileIDUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Update or add a platform-specific file ID for a media file.
    """
    try:
        # Get the media file first to check permissions
        media_file_check = await MediaService.get_media_file(db, media_id)
        if not media_file_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, media_file_check.bot_id)
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
                detail="You don't have permission to update this media file"
            )
        
        media_file = await MediaService.update_platform_file_id(db, media_id, platform_file_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found or update failed"
            )
        return media_file
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating platform file ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update platform file ID: {str(e)}"
        )




@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media_file(
    media_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    Delete a media file from the database.
    """
    try:
        # Get the media file first to check permissions
        media_file = await MediaService.get_media_file(db, media_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, media_file.bot_id)
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
                detail="You don't have permission to delete this media file"
            )
        
        result = await MediaService.delete_media_file(db, media_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found or deletion failed"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting media file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete media file: {str(e)}"
        )