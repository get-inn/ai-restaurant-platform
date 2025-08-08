from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class BotMediaFileBase(BaseModel):
    file_type: str = Field(..., description="Media file type (image, video, audio, etc.)")
    file_name: str = Field(..., description="Original file name")
    content_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., description="Size of the file in bytes")
    platform_file_ids: Optional[Dict[str, str]] = Field(default_factory=dict, description="Map of platform->file_id")


class BotMediaFileCreate(BotMediaFileBase):
    bot_id: UUID = Field(..., description="Bot ID")


class BotMediaFileUpdate(BaseModel):
    file_type: Optional[str] = None
    file_name: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    platform_file_ids: Optional[Dict[str, str]] = None


class BotMediaFileDB(BotMediaFileBase):
    id: UUID
    bot_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MediaUploadResponse(BaseModel):
    media_id: UUID = Field(..., description="ID of the uploaded media file")
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="Media file type")
    content_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., description="Size of the file in bytes")


class PlatformFileIDUpdate(BaseModel):
    platform: str = Field(..., description="Platform name (e.g., telegram, whatsapp)")
    file_id: str = Field(..., description="Platform-specific file ID")