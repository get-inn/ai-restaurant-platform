"""
Pydantic schemas for iiko integration.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID


class IikoCredentials(BaseModel):
    """Schema for iiko credentials."""
    
    username: str = Field(..., description="iiko username")
    password: str = Field(..., description="iiko password")
    base_url: Optional[str] = Field(None, description="Custom base URL (optional)")


class IntegrationConnectionStatus(BaseModel):
    """Schema for integration connection status."""
    
    account_id: UUID = Field(..., description="Account ID")
    is_connected: bool = Field(..., description="Connection status")
    last_connected_at: Optional[datetime] = Field(None, description="Last successful connection time")
    connection_error: Optional[str] = Field(None, description="Error message if connection failed")
    integration_type: str = Field(..., description="Integration type")


class SyncRequest(BaseModel):
    """Schema for sync request."""
    
    entity_type: str = Field(..., description="Entity type to sync (restaurants, stores, suppliers, invoices)")
    
    @validator("entity_type")
    def validate_entity_type(cls, v):
        """Validate entity type."""
        valid_types = ["restaurants", "stores", "suppliers", "invoices"]
        if v not in valid_types:
            raise ValueError(f"Entity type must be one of {valid_types}")
        return v


class InvoiceSyncRequest(SyncRequest):
    """Schema for invoice sync request."""
    
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    days_back: int = Field(30, description="Number of days to look back")
    
    @validator("entity_type")
    def validate_entity_type(cls, v):
        """Override to ensure only invoices are allowed."""
        if v != "invoices":
            raise ValueError("Entity type must be 'invoices'")
        return v
    
    @validator("days_back")
    def validate_days_back(cls, v):
        """Validate days back."""
        if v < 1 or v > 365:
            raise ValueError("Days back must be between 1 and 365")
        return v


class SyncJobResponse(BaseModel):
    """Schema for sync job response."""
    
    status: str = Field(..., description="Status of the sync job (success, error)")
    message: str = Field(..., description="Status message")
    details: Optional[Dict[str, Any]] = Field(None, description="Detailed results")


class SyncLogEntry(BaseModel):
    """Schema for sync log entry."""
    
    id: UUID = Field(..., description="Log entry ID")
    account_id: UUID = Field(..., description="Account ID")
    integration_type: str = Field(..., description="Integration type")
    entity_type: str = Field(..., description="Entity type")
    timestamp: datetime = Field(..., description="Log timestamp")
    status: str = Field(..., description="Status (success, error)")
    message: str = Field(..., description="Log message")
    details: Optional[Dict[str, Any]] = Field(None, description="Detailed results")