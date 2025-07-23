from typing import List, Optional, Dict, BinaryIO
from uuid import UUID
import os
import shutil
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from fastapi import UploadFile

from src.api.models import BotMediaFile, BotInstance
from src.api.schemas.bots.media_schemas import (
    BotMediaFileCreate,
    BotMediaFileUpdate,
    BotMediaFileDB,
    PlatformFileIDUpdate
)


class MediaService:
    @staticmethod
    async def create_media_file(
        db: AsyncSession, 
        file: UploadFile, 
        bot_id: UUID,
        storage_dir: str
    ) -> Optional[BotMediaFileDB]:
        """Create a new media file entry and save the file to storage"""
        # Check if the bot exists
        query = select(BotInstance).where(BotInstance.id == bot_id)
        result = await db.execute(query)
        bot_instance = result.scalars().first()
        
        if not bot_instance:
            return None
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Determine file type from content-type or extension
        file_type = file.content_type.split('/')[0] if file.content_type else "unknown"
        
        # Create a storage path for the file
        filename = file.filename
        storage_path = os.path.join(storage_dir, f"{bot_id}_{datetime.now().timestamp()}_{filename}")
        
        # Save the file
        with open(storage_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create database entry
        media_create = BotMediaFileCreate(
            bot_id=bot_id,
            file_type=file_type,
            file_name=filename,
            storage_path=storage_path,
            platform_file_ids={}
        )
        
        db_media_file = BotMediaFile(
            bot_id=media_create.bot_id,
            file_type=media_create.file_type,
            file_name=media_create.file_name,
            storage_path=media_create.storage_path,
            platform_file_ids=media_create.platform_file_ids
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
        """Delete a media file and remove it from storage"""
        query = select(BotMediaFile).where(BotMediaFile.id == media_id)
        result = await db.execute(query)
        media_file = result.scalars().first()
        
        if not media_file:
            return False
        
        # Remove the file from storage if it exists
        if os.path.exists(media_file.storage_path):
            os.remove(media_file.storage_path)
        
        # Delete database entry
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
    async def get_file_content(file_path: str) -> Optional[BinaryIO]:
        """Get file content from storage path"""
        if os.path.exists(file_path):
            return open(file_path, "rb")
        return None