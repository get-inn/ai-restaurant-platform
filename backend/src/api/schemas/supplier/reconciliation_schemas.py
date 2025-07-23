from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from decimal import Decimal


class ReconciliationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class ItemStatus(str, Enum):
    MATCHED = "matched"
    MISSING_IN_RESTAURANT = "missing_in_restaurant"
    MISSING_IN_SUPPLIER = "missing_in_supplier"
    AMOUNT_MISMATCH = "amount_mismatch"


class ReconciliationBase(BaseModel):
    document_id: UUID4
    account_id: UUID4
    restaurant_id: Optional[UUID4] = None
    store_id: Optional[UUID4] = None


class ReconciliationCreate(ReconciliationBase):
    pass


class ReconciliationResponse(ReconciliationBase):
    id: UUID4
    status: ReconciliationStatus
    progress: float = Field(..., ge=0, le=100)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReconciliationItemBase(BaseModel):
    reconciliation_id: UUID4
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    amount: Decimal
    currency: str = "USD"
    status: ItemStatus
    match_confidence: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class ReconciliationItemCreate(ReconciliationItemBase):
    pass


class ReconciliationItemResponse(ReconciliationItemBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReconciliationStatusUpdate(BaseModel):
    status: ReconciliationStatus
    progress: float = Field(..., ge=0, le=100)
    message: Optional[str] = None


class ReconciliationStats(BaseModel):
    total_items: int
    matched_items: int
    missing_in_restaurant: int
    missing_in_supplier: int
    amount_mismatches: int
    total_matched_amount: Decimal
    total_unmatched_amount: Decimal