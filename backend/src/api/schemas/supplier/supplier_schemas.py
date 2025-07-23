from pydantic import BaseModel, UUID4
from typing import Optional, Dict, Any
from datetime import datetime


class SupplierBase(BaseModel):
    name: str
    account_id: UUID4
    contact_info: Optional[Dict[str, Any]] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None


class SupplierResponse(SupplierBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True