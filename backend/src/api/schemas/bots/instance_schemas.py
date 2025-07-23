from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class BotPlatformCredentialBase(BaseModel):
    platform: str = Field(..., description="Platform name (e.g., telegram, whatsapp)")
    credentials: dict = Field(..., description="Platform-specific credentials")
    is_active: bool = Field(default=True, description="Whether the credentials are active")


class BotPlatformCredentialCreate(BotPlatformCredentialBase):
    pass


class BotPlatformCredentialUpdate(BaseModel):
    platform: Optional[str] = None
    credentials: Optional[dict] = None
    is_active: Optional[bool] = None


class BotPlatformCredentialDB(BotPlatformCredentialBase):
    id: UUID
    bot_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BotInstanceBase(BaseModel):
    name: str = Field(..., description="Bot name")
    description: Optional[str] = Field(None, description="Bot description")
    is_active: bool = Field(default=True, description="Whether the bot is active")


class BotInstanceCreate(BotInstanceBase):
    account_id: UUID = Field(..., description="Account ID")
    platform_credentials: List[BotPlatformCredentialCreate] = Field(default_factory=list, description="Platform-specific credentials")


class BotInstanceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BotInstanceDB(BotInstanceBase):
    id: UUID
    account_id: UUID
    created_at: datetime
    updated_at: datetime
    platform_credentials: List[BotPlatformCredentialDB] = []

    class Config:
        from_attributes = True


class BotInstanceWithDetails(BotInstanceDB):
    pass