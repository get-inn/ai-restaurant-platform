from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    INVOICE = "invoice"
    STATEMENT = "statement"
    RECONCILIATION_REPORT = "reconciliation_report"
    OTHER = "other"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


class DocumentBase(BaseModel):
    account_id: UUID4
    document_type: DocumentType
    file_name: str
    restaurant_id: Optional[UUID4] = None
    store_id: Optional[UUID4] = None
    supplier_id: Optional[UUID4] = None


class DocumentCreate(DocumentBase):
    # Additional fields for document creation
    pass


class DocumentUpdate(BaseModel):
    document_type: Optional[DocumentType] = None
    restaurant_id: Optional[UUID4] = None
    store_id: Optional[UUID4] = None
    supplier_id: Optional[UUID4] = None


class DocumentResponse(DocumentBase):
    id: UUID4
    file_type: str
    storage_path: str
    upload_date: datetime
    uploaded_by: UUID4
    status: DocumentStatus
    error_message: Optional[str] = None
    doc_metadata: Optional[dict] = None  # Renamed from metadata because it's a reserved name in SQLAlchemy
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    id: UUID4
    file_name: str
    document_type: DocumentType
    status: DocumentStatus
    message: str