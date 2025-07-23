"""
iiko data type definitions.

This module contains Pydantic models for iiko API data structures.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field


class IikoBase(BaseModel):
    """Base model for iiko entities."""
    
    iiko_id: str = Field(..., description="iiko identifier")
    iiko_metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw iiko data")


class IikoRestaurant(IikoBase):
    """
    Model representing an iiko restaurant (department).
    
    Maps to internal Restaurant model.
    """
    
    name: str
    code: Optional[str] = None
    parent_id: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    account_number: Optional[str] = None
    corporate_id: Optional[str] = None
    is_active: bool = True


class IikoStore(IikoBase):
    """
    Model representing an iiko store.
    
    Maps to internal Store model.
    """
    
    name: str
    code: Optional[str] = None
    department_id: str  # References iiko restaurant/department
    is_active: bool = True


class IikoSupplier(IikoBase):
    """
    Model representing an iiko supplier.
    
    Maps to internal Supplier model.
    """
    
    name: str
    code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_id: Optional[str] = None
    is_active: bool = True
    contact_person: Optional[str] = None


class IikoInvoiceItem(BaseModel):
    """Model representing an item in an iiko invoice."""
    
    product_id: str
    product_name: str
    quantity: float
    unit_name: str
    unit_price: float
    total_price: float
    vat: Optional[float] = None


class IikoInvoice(IikoBase):
    """
    Model representing an iiko invoice.
    
    Maps to internal Invoice model.
    """
    
    number: str
    supplier_id: str
    department_id: str  # References iiko restaurant/department
    date: datetime
    due_date: Optional[datetime] = None
    total_amount: float
    currency: str = "USD"
    status: str
    comment: Optional[str] = None
    items: List[IikoInvoiceItem] = Field(default_factory=list)


class IikoConnectionStatus(BaseModel):
    """Model representing iiko connection status."""
    
    account_id: UUID
    is_connected: bool
    last_connected_at: Optional[datetime] = None
    connection_error: Optional[str] = None
    integration_type: str = "iiko"


class IikoCredentials(BaseModel):
    """Model for iiko integration credentials."""
    
    username: str
    password: str
    base_url: Optional[str] = None


class SyncJobResponse(BaseModel):
    """Response model for sync job operations."""
    
    account_id: UUID
    entity_type: str
    job_id: str
    status: str
    message: Optional[str] = None