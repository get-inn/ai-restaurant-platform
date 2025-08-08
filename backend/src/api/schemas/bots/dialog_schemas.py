from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class BotDialogStateBase(BaseModel):
    platform: str = Field(..., description="Platform name (e.g., telegram, whatsapp)")
    platform_chat_id: str = Field(..., description="Chat ID in the specific platform")
    current_step: str = Field(..., description="Current scenario step ID")
    collected_data: Dict[str, Any] = Field(default_factory=dict, description="Data collected during the dialog")


class BotDialogStateCreate(BotDialogStateBase):
    bot_id: UUID = Field(..., description="Bot ID")


class BotDialogStateUpdate(BaseModel):
    current_step: Optional[str] = None
    collected_data: Optional[Dict[str, Any]] = None
    last_interaction_at: Optional[datetime] = None


class BotDialogStateDB(BotDialogStateBase):
    id: UUID
    bot_id: UUID
    last_interaction_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BotDialogHistoryBase(BaseModel):
    message_type: str = Field(..., description="Type of message (user or bot)")
    message_data: Dict[str, Any] = Field(..., description="Message content and metadata")
    timestamp: datetime = Field(..., description="Message timestamp")


class BotDialogHistoryCreate(BotDialogHistoryBase):
    dialog_state_id: UUID = Field(..., description="Dialog state ID")


class BotDialogHistoryDB(BotDialogHistoryBase):
    id: UUID
    dialog_state_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MediaItem(BaseModel):
    type: str = Field(..., description="Type of media (image, video, audio, document)")
    file_id: str = Field(..., description="ID or reference to the media file")
    description: Optional[str] = Field(None, description="Optional description of the media")


class DialogMessage(BaseModel):
    text: str = Field(..., description="Message text")
    media: Optional[List[MediaItem]] = Field(default_factory=list, description="Media items to include in the message")
    media_ids: Optional[List[UUID]] = Field(default_factory=list, description="Legacy IDs of media files to include")


class DialogButtonOption(BaseModel):
    text: str = Field(..., description="Button text")
    value: str = Field(..., description="Button value")


class DialogResponse(BaseModel):
    message: DialogMessage
    buttons: Optional[List[DialogButtonOption]] = Field(default_factory=list, description="Buttons to display")


class DialogStateWithHistory(BotDialogStateDB):
    history: List[BotDialogHistoryDB] = Field(default_factory=list, description="Dialog message history")