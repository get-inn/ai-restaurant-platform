"""
Pydantic schemas for the bot management API.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Annotated
from uuid import UUID
from pydantic import BaseModel, Field, UUID4, field_validator, ConfigDict


# Base schemas
class BotBase(BaseModel):
    """Base schema for bot instances."""
    name: str
    description: Optional[str] = None
    account_id: UUID  # Accept any UUID version
    is_active: bool = True


class BotCreate(BotBase):
    """Schema for creating a new bot instance."""
    platform_credentials: Optional[List[Dict[str, Any]]] = []


class BotUpdate(BaseModel):
    """Schema for updating an existing bot instance."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BotResponse(BotBase):
    """Schema for returning a bot instance."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID  # Accept any UUID version
    created_at: datetime
    updated_at: Optional[datetime] = None


# Platform Credential schemas
class PlatformCredentialBase(BaseModel):
    """Base schema for bot platform credentials."""
    platform: str
    credentials: Dict[str, Any]
    is_active: bool = True


class PlatformCredentialCreate(PlatformCredentialBase):
    """Schema for creating new platform credentials."""
    pass


class PlatformCredentialUpdate(BaseModel):
    """Schema for updating platform credentials."""
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class PlatformCredentialResponse(PlatformCredentialBase):
    """Schema for returning platform credentials."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    bot_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Override credentials to sanitize sensitive information
    credentials: Dict[str, Any]

    @field_validator('credentials')
    @classmethod
    def sanitize_credentials(cls, v):
        # Remove sensitive information like tokens
        sanitized = v.copy()
        if 'api_token' in sanitized:
            sanitized['api_token'] = '[REDACTED]'
        return sanitized


# Scenario schemas
class ScenarioStepBase(BaseModel):
    """Base schema for a scenario step."""
    id: str
    message: str
    next_step: Optional[str] = None
    input_type: Optional[str] = None
    options: Optional[List[str]] = None


class ScenarioBase(BaseModel):
    """Base schema for bot scenarios."""
    name: str
    description: Optional[str] = None
    version: str
    steps: List[Dict[str, Any]]
    is_active: bool = True
    
    @property
    def scenario_data(self) -> Dict[str, Any]:
        """Return the scenario data with steps."""
        return {"steps": self.steps}


class ScenarioCreate(ScenarioBase):
    """Schema for creating a new scenario."""
    bot_id: UUID


class ScenarioUpdate(BaseModel):
    """Schema for updating an existing scenario."""
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class ScenarioResponse(BaseModel):
    """Schema for returning a scenario."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    bot_id: UUID
    name: str
    description: Optional[str] = None
    version: str
    steps: List[Dict[str, Any]]
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @field_validator('steps', mode="before")
    @classmethod
    def extract_steps_from_scenario_data(cls, v, info):
        # Extract steps from scenario_data if it's a dict
        scenario_data = info.data.get('scenario_data')
        if not v and isinstance(scenario_data, dict):
            return scenario_data.get('steps', [])
        return v


# Dialog State schemas
class DialogStateBase(BaseModel):
    """Base schema for dialog states."""
    current_step: str
    collected_data: Dict[str, Any] = {}


class DialogStateCreate(DialogStateBase):
    """Schema for creating a new dialog state."""
    platform: str
    platform_chat_id: str
    bot_id: UUID


class DialogStateUpdate(BaseModel):
    """Schema for updating a dialog state."""
    current_step: Optional[str] = None
    collected_data: Optional[Dict[str, Any]] = None


class DialogStateResponse(DialogStateBase):
    """Schema for returning a dialog state."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    bot_id: UUID
    platform: str
    platform_chat_id: str
    last_interaction_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None


# Dialog History schemas
class DialogMessageBase(BaseModel):
    """Base schema for dialog messages."""
    message_type: str  # 'user' or 'bot'
    message_data: Dict[str, Any]
    timestamp: datetime


class DialogHistoryResponse(BaseModel):
    """Schema for returning dialog history."""
    model_config = ConfigDict(from_attributes=True)
    
    messages: List[DialogMessageBase]