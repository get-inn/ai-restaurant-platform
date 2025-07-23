from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class BotScenarioBase(BaseModel):
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    version: str = Field(..., description="Scenario version")
    scenario_data: Dict[str, Any] = Field(..., description="Full scenario structure in JSON")
    is_active: bool = Field(default=True, description="Whether the scenario is active")


class BotScenarioCreate(BotScenarioBase):
    bot_id: UUID = Field(..., description="Bot ID")


class BotScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    scenario_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class BotScenarioActivate(BaseModel):
    is_active: bool = Field(..., description="Set to true to activate, false to deactivate")


class BotScenarioUpload(BaseModel):
    file_content: str = Field(..., description="Scenario JSON content as string")


class BotScenarioDB(BotScenarioBase):
    id: UUID
    bot_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True