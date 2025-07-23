from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from decimal import Decimal


class InvoiceStatus(str, Enum):
    ACTIVE = "active"
    PAID = "paid"
    CANCELLED = "cancelled"


class InvoiceBase(BaseModel):
    supplier_id: UUID4
    store_id: UUID4
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    total_amount: Decimal
    currency: str = "USD"
    document_id: Optional[UUID4] = None
    status: InvoiceStatus = InvoiceStatus.ACTIVE


class InvoiceCreate(InvoiceBase):
    line_items: List["InvoiceItemCreate"]


class InvoiceUpdate(BaseModel):
    supplier_id: Optional[UUID4] = None
    store_id: Optional[UUID4] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    document_id: Optional[UUID4] = None
    status: Optional[InvoiceStatus] = None


class InvoiceResponse(InvoiceBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceItemBase(BaseModel):
    invoice_id: UUID4
    description: str
    quantity: Decimal
    unit_id: UUID4
    unit_price: Decimal
    line_total: Decimal
    inventory_item_id: Optional[UUID4] = None


class InvoiceItemCreate(BaseModel):
    description: str
    quantity: Decimal
    unit_id: UUID4
    unit_price: Decimal
    line_total: Decimal
    inventory_item_id: Optional[UUID4] = None


class InvoiceItemUpdate(BaseModel):
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_id: Optional[UUID4] = None
    unit_price: Optional[Decimal] = None
    line_total: Optional[Decimal] = None
    inventory_item_id: Optional[UUID4] = None


class InvoiceItemResponse(InvoiceItemBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceDetailResponse(InvoiceResponse):
    line_items: List[InvoiceItemResponse]


# Update forward references
InvoiceCreate.update_forward_refs()