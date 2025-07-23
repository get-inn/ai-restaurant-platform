"""
Supplier management models: Supplier, Invoice, Document, Reconciliation, etc.
"""
from src.api.models.base import *


class Supplier(Base):
    __tablename__ = "supplier"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    contact_info = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # External system integration fields
    external_id = Column(String, nullable=True, index=True)
    external_sync_status = Column(Enum(SyncStatus), nullable=True)
    external_system_type = Column(Enum(IntegrationType), nullable=True)
    external_last_synced_at = Column(DateTime, nullable=True)
    external_sync_error = Column(String, nullable=True)
    external_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="suppliers")
    invoices = relationship("Invoice", back_populates="supplier", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="supplier", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "document"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"), nullable=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("supplier.id"), nullable=True)
    document_type = Column(String, nullable=False)  # 'invoice', 'statement', 'reconciliation_report'
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # 'pdf', 'xlsx', etc.
    storage_path = Column(String, nullable=False)
    upload_date = Column(DateTime, default=func.now())
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)  # Maps to Supabase auth.users.id
    status = Column(String, nullable=False, default="uploaded")  # 'uploaded', 'processing', 'processed', 'error'
    error_message = Column(Text, nullable=True)
    doc_metadata = Column(JSONB, nullable=True)  # Renamed from metadata because it's a reserved name in SQLAlchemy
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="documents")
    invoices = relationship("Invoice", back_populates="document")
    reconciliations = relationship("Reconciliation", back_populates="document", cascade="all, delete-orphan")


class Reconciliation(Base):
    __tablename__ = "reconciliation"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("document.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"), nullable=True)
    status = Column(String, nullable=False, default="pending")  # 'pending', 'in_progress', 'completed', 'error'
    progress = Column(Float, nullable=False, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)  # Maps to Supabase auth.users.id
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="reconciliations")
    items = relationship("ReconciliationItem", back_populates="reconciliation", cascade="all, delete-orphan")


class ReconciliationItem(Base):
    __tablename__ = "reconciliation_item"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reconciliation_id = Column(UUID(as_uuid=True), ForeignKey("reconciliation.id"), nullable=False)
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(Date, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    status = Column(String, nullable=False)  # 'matched', 'missing_in_restaurant', 'missing_in_supplier', 'amount_mismatch'
    match_confidence = Column(Float, nullable=True)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    reconciliation = relationship("Reconciliation", back_populates="items")


class Invoice(Base):
    __tablename__ = "invoice"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("supplier.id"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"), nullable=False)
    invoice_number = Column(String, nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    document_id = Column(UUID(as_uuid=True), ForeignKey("document.id"), nullable=True)
    status = Column(String, nullable=False, default="active")  # 'active', 'paid', 'cancelled'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="invoices")
    store = relationship("Store", back_populates="invoices")
    document = relationship("Document", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_item"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoice.id"), nullable=False)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_item.id"), nullable=True)
    description = Column(String, nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    inventory_item = relationship("InventoryItem", back_populates="invoice_items")
    unit = relationship("Unit", back_populates="invoice_items")