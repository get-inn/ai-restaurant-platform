"""
Pydantic schemas for Telegram webhook management.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WebhookConfigSchema(BaseModel):
    """Configuration for setting a webhook."""
    drop_pending_updates: bool = False
    secret_token: Optional[str] = None
    max_connections: Optional[int] = None
    allowed_updates: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class WebhookStatusSchema(BaseModel):
    """Status information about a webhook."""
    url: Optional[str] = None
    has_custom_certificate: bool = False
    pending_update_count: int = 0
    ip_address: Optional[str] = None
    last_error_date: Optional[datetime] = None
    last_error_message: Optional[str] = None
    last_synchronization_error_date: Optional[datetime] = None
    max_connections: Optional[int] = None
    allowed_updates: Optional[List[str]] = None
    
    class Config:
        from_attributes = True