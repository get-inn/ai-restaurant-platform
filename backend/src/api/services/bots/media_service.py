from typing import List, Optional, Dict, BinaryIO, Tuple
from uuid import UUID
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from fastapi import UploadFile
import mimetypes

from src.api.models import BotMediaFile, BotInstance
from src.api.schemas.bots.media_schemas import (
    BotMediaFileCreate,
    BotMediaFileUpdate,
    BotMediaFileDB,
    PlatformFileIDUpdate
)


class MediaService:
    @staticmethod
    async def determine_content_type(file_name: str, file_type: str, content_type: Optional[str] = None) -> str:
        """Determine the appropriate content type based on file name and type"""
        if content_type:
            return content_type
            
        # Try to get content type from file extension
        extension = os.path.splitext(file_name)[1].lower()
        guessed_type = mimetypes.guess_type(file_name)[0]
        if guessed_type:
            return guessed_type
            
        # Fall back to basic types based on file_type
        if file_type == "image":
            if extension in [".jpg", ".jpeg"]:
                return "image/jpeg"
            elif extension == ".png":
                return "image/png"
            elif extension == ".gif":
                return "image/gif"
            else:
                return f"image/{extension[1:]}" if extension else "image/unknown"
        elif file_type == "video":
            return f"video/{extension[1:]}" if extension else "video/mp4"
        elif file_type == "audio":
            return f"audio/{extension[1:]}" if extension else "audio/mpeg"
        elif file_type == "document" and extension == ".pdf":
            return "application/pdf"
            
        # Default fallback
        return "application/octet-stream"

    @staticmethod
    async def create_media_file(
        db: AsyncSession, 
        file: UploadFile, 
        bot_id: UUID,
        storage_dir: Optional[str] = None  # Parameter kept for backward compatibility
    ) -> Optional[BotMediaFileDB]:
        """Create a new media file entry and store file content in the database"""
        # Check if the bot exists
        query = select(BotInstance).where(BotInstance.id == bot_id)
        result = await db.execute(query)
        bot_instance = result.scalars().first()
        
        if not bot_instance:
            return None
        
        # Determine file type from content-type or extension
        content_type = file.content_type
        file_type = content_type.split('/')[0] if content_type else "unknown"
        filename = file.filename
        
        # Read file content into memory
        file_content = await file.read()
        file_size = len(file_content)
        
        # Ensure content type is properly set
        final_content_type = await MediaService.determine_content_type(
            file_name=filename, 
            file_type=file_type,
            content_type=content_type
        )
        
        # Create database entry
        db_media_file = BotMediaFile(
            bot_id=bot_id,
            file_type=file_type,
            file_name=filename,
            file_content=file_content,
            content_type=final_content_type,
            file_size=file_size,
            platform_file_ids={}
        )
        
        db.add(db_media_file)
        await db.commit()
        await db.refresh(db_media_file)
        
        return BotMediaFileDB.model_validate(db_media_file)

    @staticmethod
    async def get_media_file(db: AsyncSession, media_id: UUID) -> Optional[BotMediaFileDB]:
        """Get media file by ID"""
        query = select(BotMediaFile).where(BotMediaFile.id == media_id)
        result = await db.execute(query)
        media_file = result.scalars().first()
        
        if media_file:
            return BotMediaFileDB.model_validate(media_file)
        return None
        
    @staticmethod
    async def get_media_file_by_platform_id(db: AsyncSession, bot_id: UUID, platform: str, file_id: str) -> Optional[BotMediaFileDB]:
        """Get media file by platform-specific file ID"""
        # Construct query to find media files for this bot
        query = select(BotMediaFile).where(BotMediaFile.bot_id == bot_id)
        result = await db.execute(query)
        media_files = result.scalars().all()
        
        # Check each file's platform_file_ids dictionary for the requested ID
        for media_file in media_files:
            platform_file_ids = media_file.platform_file_ids or {}
            if platform in platform_file_ids and platform_file_ids[platform] == file_id:
                return BotMediaFileDB.model_validate(media_file)
            
            # If no platform-specific match, check if the file_id matches directly
            # This handles scenario file_ids like "company_history_image"
            if file_id in platform_file_ids.values():
                return BotMediaFileDB.model_validate(media_file)
        
        return None
        
    @staticmethod
    async def find_media_file_by_id_or_name(db: AsyncSession, id_or_name: str) -> Optional[BotMediaFileDB]:
        """Find media file by UUID or by scenario file_id name"""
        # First, try to interpret as UUID
        try:
            media_id = UUID(id_or_name)
            # Look up by ID
            query = select(BotMediaFile).where(BotMediaFile.id == media_id)
            result = await db.execute(query)
            media_file = result.scalars().first()
            if media_file:
                return BotMediaFileDB.model_validate(media_file)
        except ValueError:
            # Not a valid UUID, might be a file_id
            pass
        
        # Try to find by platform_file_ids in any bot
        query = select(BotMediaFile)
        result = await db.execute(query)
        media_files = result.scalars().all()
        
        for media_file in media_files:
            platform_file_ids = media_file.platform_file_ids or {}
            # Check if the ID matches any platform's file_id
            if id_or_name in platform_file_ids.values():
                return BotMediaFileDB.model_validate(media_file)
        
        return None

    @staticmethod
    async def update_media_file(
        db: AsyncSession,
        media_id: UUID,
        media_update: BotMediaFileUpdate
    ) -> Optional[BotMediaFileDB]:
        """Update media file details"""
        query = select(BotMediaFile).where(BotMediaFile.id == media_id)
        result = await db.execute(query)
        db_media_file = result.scalars().first()
        
        if not db_media_file:
            return None
        
        update_data = media_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_media_file, key, value)
            
        await db.commit()
        await db.refresh(db_media_file)
        return BotMediaFileDB.model_validate(db_media_file)

    @staticmethod
    async def update_platform_file_id(
        db: AsyncSession,
        media_id: UUID,
        platform_file_id: PlatformFileIDUpdate
    ) -> Optional[BotMediaFileDB]:
        """Update or add a platform-specific file ID"""
        query = select(BotMediaFile).where(BotMediaFile.id == media_id)
        result = await db.execute(query)
        db_media_file = result.scalars().first()
        
        if not db_media_file:
            return None
        
        # Update the platform file ID mapping
        platform_file_ids = db_media_file.platform_file_ids or {}
        platform_file_ids[platform_file_id.platform] = platform_file_id.file_id
        db_media_file.platform_file_ids = platform_file_ids
            
        await db.commit()
        await db.refresh(db_media_file)
        return BotMediaFileDB.model_validate(db_media_file)

    @staticmethod
    async def delete_media_file(db: AsyncSession, media_id: UUID) -> bool:
        """Delete a media file from the database"""
        query = select(BotMediaFile).where(BotMediaFile.id == media_id)
        result = await db.execute(query)
        media_file = result.scalars().first()
        
        if not media_file:
            return False
        
        # Delete database entry (file content is deleted automatically)
        await db.delete(media_file)
        await db.commit()
        
        return True

    @staticmethod
    async def get_bot_media_files(
        db: AsyncSession, 
        bot_id: UUID, 
        file_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[BotMediaFileDB]:
        """Get all media files for a specific bot, optionally filtered by file type"""
        query = select(BotMediaFile).where(BotMediaFile.bot_id == bot_id)
        
        if file_type:
            query = query.where(BotMediaFile.file_type == file_type)
        
        query = query.order_by(BotMediaFile.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        media_files = result.scalars().all()
        
        return [BotMediaFileDB.model_validate(file) for file in media_files]

    @staticmethod
    async def get_file_content(db: AsyncSession, media_id: UUID) -> Optional[Tuple[bytes, str]]:
        """Get file content and content type from the database"""
        query = select(BotMediaFile).where(BotMediaFile.id == media_id)
        result = await db.execute(query)
        media_file = result.scalars().first()
        
        if not media_file or not media_file.file_content:
            return None
        
        return (media_file.file_content, media_file.content_type)