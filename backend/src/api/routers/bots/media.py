from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import os
import logging

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
    tags=["media"],
    responses={404: {"description": "Not found"}},
)


@router.post("/bots/{bot_id}/media", response_model=MediaUploadResponse)
async def upload_media_file(
    bot_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Upload a media file for a bot.
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
        
        # Use a directory inside the settings-defined storage location
        storage_dir = os.path.join(settings.media_storage_path, "bot_media")
        
        media_file = await MediaService.create_media_file(db, file, bot_id, storage_dir)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create media file"
            )
        
        return MediaUploadResponse(
            media_id=media_file.id,
            file_name=media_file.file_name,
            file_type=media_file.file_type,
            storage_path=media_file.storage_path
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
    media_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Response:
    """
    Get the actual content of a media file.
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
                detail="You don't have permission to access this media file"
            )
        
        file_content = await MediaService.get_file_content(media_file.storage_path)
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file content not found"
            )
        
        # Return the file with the appropriate content type
        media_type = "application/octet-stream"  # Default
        if media_file.file_type == "image":
            extension = os.path.splitext(media_file.file_name)[1].lower()
            if extension == ".jpg" or extension == ".jpeg":
                media_type = "image/jpeg"
            elif extension == ".png":
                media_type = "image/png"
            elif extension == ".gif":
                media_type = "image/gif"
            else:
                media_type = f"image/{extension[1:]}"
        elif media_file.file_type == "video":
            extension = os.path.splitext(media_file.file_name)[1].lower()
            media_type = f"video/{extension[1:]}"
        elif media_file.file_type == "audio":
            extension = os.path.splitext(media_file.file_name)[1].lower()
            media_type = f"audio/{extension[1:]}"
        
        return Response(
            content=file_content.read(),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={media_file.file_name}"}
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
    Delete a media file and remove it from storage.
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