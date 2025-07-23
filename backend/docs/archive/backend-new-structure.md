# GET INN Backend - New Structure

This document outlines the new backend structure for the GET INN platform, designed from scratch to support the frontend requirements defined in the frontend specification. The structure is organized around the three core AI-powered modules: AI Supplier, AI Labor, and AI Chef.

## 1. Project Structure

```
/backend
├── src/
│   ├── main.py                     # Application entry point
│   ├── core/                       # Core components
│   │   ├── config.py               # Configuration settings
│   │   ├── logging.py              # Logging configuration
│   │   ├── security.py             # Security utilities (JWT, password hashing)
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── database.py             # Database configuration
│   ├── db/                         # Database models and migrations
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── base.py             # Base model class
│   │   │   ├── account.py          # Account-related models
│   │   │   ├── user.py             # User model
│   │   │   ├── supplier/           # AI Supplier models
│   │   │   │   ├── document.py     # Document model
│   │   │   │   ├── invoice.py      # Invoice model
│   │   │   │   ├── reconciliation.py # Reconciliation models
│   │   │   │   ├── inventory.py    # Inventory models
│   │   │   │   └── unit.py         # Unit models
│   │   │   ├── labor/              # AI Labor models
│   │   │   │   └── onboarding.py   # Onboarding models
│   │   │   └── chef/               # AI Chef models
│   │   │       ├── menu.py         # Menu models
│   │   │       ├── recipe.py       # Recipe models
│   │   │       └── analysis.py     # Analysis models
│   │   └── migrations/             # Alembic migrations
│   │       ├── env.py              # Migration environment
│   │       └── versions/           # Migration versions
│   ├── api/                        # API endpoints
│   │   ├── deps.py                 # Dependency injection
│   │   ├── auth.py                 # Authentication endpoints
│   │   ├── dashboard.py            # Dashboard endpoints
│   │   ├── supplier/               # AI Supplier endpoints
│   │   │   ├── documents.py        # Document management
│   │   │   ├── invoices.py         # Invoice management
│   │   │   ├── reconciliation.py   # Reconciliation process
│   │   │   ├── inventory.py        # Inventory management
│   │   │   └── units.py            # Unit management
│   │   ├── labor/                  # AI Labor endpoints
│   │   │   └── onboarding.py       # Staff onboarding
│   │   ├── chef/                   # AI Chef endpoints
│   │   │   ├── menu.py             # Menu analysis
│   │   │   ├── recipes.py          # Recipe management
│   │   │   └── menus.py            # Menu management
│   │   └── settings/               # Settings endpoints
│   │       ├── accounts.py         # Account management
│   │       ├── restaurants.py      # Restaurant management
│   │       ├── stores.py           # Store management
│   │       ├── users.py            # User management
│   │       └── suppliers.py        # Supplier management
│   ├── schemas/                    # Pydantic models
│   │   ├── auth.py                 # Authentication schemas
│   │   ├── common.py               # Common schemas
│   │   ├── supplier/               # AI Supplier schemas
│   │   │   ├── document.py         # Document schemas
│   │   │   ├── invoice.py          # Invoice schemas
│   │   │   ├── reconciliation.py   # Reconciliation schemas
│   │   │   ├── inventory.py        # Inventory schemas
│   │   │   └── unit.py             # Unit schemas
│   │   ├── labor/                  # AI Labor schemas
│   │   │   └── onboarding.py       # Onboarding schemas
│   │   ├── chef/                   # AI Chef schemas
│   │   │   ├── menu.py             # Menu schemas
│   │   │   ├── recipe.py           # Recipe schemas
│   │   │   └── analysis.py         # Analysis schemas
│   │   └── settings/               # Settings schemas
│   │       ├── account.py          # Account schemas
│   │       ├── restaurant.py       # Restaurant schemas
│   │       ├── store.py            # Store schemas
│   │       ├── user.py             # User schemas
│   │       └── supplier.py         # Supplier schemas
│   ├── services/                   # Business logic
│   │   ├── auth.py                 # Authentication service
│   │   ├── dashboard.py            # Dashboard service
│   │   ├── supplier/               # AI Supplier services
│   │   │   ├── document_service.py # Document management service
│   │   │   ├── invoice_service.py  # Invoice management service
│   │   │   ├── reconciliation_service.py # Reconciliation service
│   │   │   ├── inventory_service.py # Inventory service
│   │   │   └── unit_service.py     # Unit service
│   │   ├── labor/                  # AI Labor services
│   │   │   └── onboarding_service.py # Onboarding service
│   │   └── chef/                   # AI Chef services
│   │       ├── menu_service.py     # Menu analysis service
│   │       ├── recipe_service.py   # Recipe service
│   │       └── menu_management_service.py # Menu management service
│   ├── workers/                    # Background workers
│   │   ├── celery_app.py           # Celery configuration
│   │   └── tasks/                  # Background tasks
│   │       ├── supplier/           # AI Supplier tasks
│   │       │   ├── document_processing.py # Document processing
│   │       │   └── reconciliation.py # Reconciliation processing
│   │       └── chef/               # AI Chef tasks
│   │           └── analysis.py     # Menu analysis tasks
│   ├── utils/                      # Utility functions
│   │   ├── storage.py              # File storage utilities
│   │   ├── pdf_extractor.py        # PDF processing utilities
│   │   ├── excel_parser.py         # Excel processing utilities
│   │   └── websockets.py           # WebSocket utilities
│   └── websockets/                 # WebSocket handlers
│       └── supplier/               # AI Supplier WebSockets
│           └── reconciliation.py   # Reconciliation progress updates
├── tests/                          # Test suite
│   ├── conftest.py                 # Test configuration
│   ├── unit/                       # Unit tests
│   │   ├── api/                    # API tests
│   │   └── services/               # Service tests
│   └── integration/                # Integration tests
├── alembic.ini                     # Alembic configuration
├── pyproject.toml                  # Project metadata and dependencies
├── requirements.txt                # Python dependencies
└── docker/                         # Docker configuration
    ├── Dockerfile.api              # API service Dockerfile
    ├── Dockerfile.worker           # Worker service Dockerfile
    ├── docker-compose.yml          # Docker Compose configuration
    └── docker-compose.dev.yml      # Development Docker Compose configuration
```

## 2. Database Models

### 2.1. Core Models

#### 2.1.1. Account Models (db/models/account.py)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Boolean, Table
from sqlalchemy.orm import relationship

from .base import Base

class Account(Base):
    """Restaurant chain (e.g., a restaurant group)"""
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    restaurants = relationship("Restaurant", back_populates="account")
    users = relationship("User", back_populates="account")
    suppliers = relationship("Supplier", back_populates="account")

class Restaurant(Base):
    """Individual restaurant within a chain"""
    __tablename__ = "restaurants"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    name = Column(String, nullable=False)
    location = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    account = relationship("Account", back_populates="restaurants")
    stores = relationship("Store", back_populates="restaurant")
    menus = relationship("Menu", back_populates="restaurant")

class Store(Base):
    """Inventory location or sub-entity within a restaurant (e.g., Kitchen, Bar)"""
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    restaurant = relationship("Restaurant", back_populates="stores")
    inventory_stock = relationship("InventoryStock", back_populates="store")

class Supplier(Base):
    """Supplier information"""
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    name = Column(String, nullable=False)
    contact_info = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    account = relationship("Account", back_populates="suppliers")
    invoices = relationship("Invoice", back_populates="supplier")
```

#### 2.1.2. User Model (db/models/user.py)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Boolean, Enum
from sqlalchemy.orm import relationship

from .base import Base
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    ACCOUNT_MANAGER = "account_manager"
    RESTAURANT_MANAGER = "restaurant_manager" 
    CHEF = "chef"
    STAFF = "staff"

class User(Base):
    """User account"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    account = relationship("Account", back_populates="users")
    restaurant = relationship("Restaurant")
```

### 2.2. AI Supplier Models

#### 2.2.1. Document Model (db/models/supplier/document.py)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from ..base import Base
import enum

class DocumentType(enum.Enum):
    INVOICE = "invoice"
    STATEMENT = "statement"
    RECONCILIATION_REPORT = "reconciliation_report"
    OTHER = "other"

class DocumentStatus(enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"

class Document(Base):
    """Document metadata and storage reference"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)
    
    document_type = Column(Enum(DocumentType), nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # e.g., 'pdf', 'xlsx'
    storage_path = Column(String, nullable=False)
    
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    error_message = Column(Text, nullable=True)
    
    metadata = Column(JSONB, nullable=True)
    
    upload_date = Column(DateTime, default=func.now())
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    reconciliations = relationship("Reconciliation", back_populates="document")
```

#### 2.2.2. Invoice Model (db/models/supplier/invoice.py)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Numeric, Date, Enum
from sqlalchemy.orm import relationship

from ..base import Base
import enum

class InvoiceStatus(enum.Enum):
    ACTIVE = "active"
    PAID = "paid"
    CANCELLED = "cancelled"

class Invoice(Base):
    """Supplier invoice"""
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    
    invoice_number = Column(String, nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD", nullable=False)
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.ACTIVE, nullable=False)
    
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="invoices")
    store = relationship("Store")
    items = relationship("InvoiceItem", back_populates="invoice")

class InvoiceItem(Base):
    """Line item in an invoice"""
    __tablename__ = "invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=True)
    
    description = Column(String, nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    inventory_item = relationship("InventoryItem")
    unit = relationship("Unit")
```

#### 2.2.3. Reconciliation Model (db/models/supplier/reconciliation.py)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Float, Enum, Numeric, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from ..base import Base
import enum

class ReconciliationStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"

class ItemStatus(enum.Enum):
    MATCHED = "matched"
    MISSING_IN_RESTAURANT = "missing_in_restaurant"
    MISSING_IN_SUPPLIER = "missing_in_supplier"
    AMOUNT_MISMATCH = "amount_mismatch"

class Reconciliation(Base):
    """Reconciliation process information"""
    __tablename__ = "reconciliations"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=True)
    
    status = Column(Enum(ReconciliationStatus), default=ReconciliationStatus.PENDING, nullable=False)
    progress = Column(Float, default=0, nullable=False)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="reconciliations")
    items = relationship("ReconciliationItem", back_populates="reconciliation")

class ReconciliationItem(Base):
    """Individual item within a reconciliation"""
    __tablename__ = "reconciliation_items"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    reconciliation_id = Column(UUID(as_uuid=True), ForeignKey("reconciliations.id"), nullable=False)
    
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(Date, nullable=True)
    
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD", nullable=False)
    
    status = Column(Enum(ItemStatus), nullable=False)
    match_confidence = Column(Float, nullable=True)
    
    details = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    reconciliation = relationship("Reconciliation", back_populates="items")
```

#### 2.2.4. Inventory Model (db/models/supplier/inventory.py)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Numeric, Enum, Date
from sqlalchemy.orm import relationship

from ..base import Base
import enum

class ItemType(enum.Enum):
    RAW_INGREDIENT = "raw_ingredient"
    SEMI_FINISHED = "semi_finished"
    FINISHED_PRODUCT = "finished_product"

class InventoryItem(Base):
    """Inventory item (raw ingredients, semi-finished products)"""
    __tablename__ = "inventory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    default_unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    category = Column(String, nullable=True)
    item_type = Column(Enum(ItemType), nullable=False)
    
    current_cost_per_unit = Column(Numeric(10, 2), nullable=True)
    reorder_level = Column(Numeric(10, 2), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    default_unit = relationship("Unit")
    stock = relationship("InventoryStock", back_populates="inventory_item")
    price_history = relationship("InventoryItemPriceHistory", back_populates="inventory_item")
    item_specific_conversions = relationship("ItemSpecificUnitConversion", back_populates="inventory_item")

class InventoryStock(Base):
    """Stock level of an inventory item at a store"""
    __tablename__ = "inventory_stock"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    store = relationship("Store", back_populates="inventory_stock")
    inventory_item = relationship("InventoryItem", back_populates="stock")
    unit = relationship("Unit")

class InventoryItemPriceHistory(Base):
    """Price history for an inventory item"""
    __tablename__ = "inventory_item_price_history"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    
    price_date = Column(Date, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    source = Column(String, nullable=False)  # 'invoice', 'manual_update', 'system_calculated'
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    inventory_item = relationship("InventoryItem", back_populates="price_history")
    store = relationship("Store")
    unit = relationship("Unit")
```

#### 2.2.5. Unit Model (db/models/supplier/unit.py)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Numeric
from sqlalchemy.orm import relationship

from ..base import Base

class UnitCategory(Base):
    """Categories for units (e.g., weight, volume, count)"""
    __tablename__ = "unit_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    units = relationship("Unit", back_populates="category")

class Unit(Base):
    """Units of measure with conversion support"""
    __tablename__ = "units"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)  # NULL means global unit
    
    name = Column(String, nullable=False)  # 'kilogram', 'liter', 'piece'
    symbol = Column(String, nullable=False)  # 'kg', 'L', 'pc'
    
    unit_category_id = Column(UUID(as_uuid=True), ForeignKey("unit_categories.id"), nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("UnitCategory", back_populates="units")

class UnitConversion(Base):
    """Conversion factors between units of the same category"""
    __tablename__ = "unit_conversions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    
    from_unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    to_unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    conversion_factor = Column(Numeric(15, 6), nullable=False)  # e.g., 1000 for kg to g
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    from_unit = relationship("Unit", foreign_keys=[from_unit_id])
    to_unit = relationship("Unit", foreign_keys=[to_unit_id])

class ItemSpecificUnitConversion(Base):
    """Item-specific conversions between units of different categories"""
    __tablename__ = "item_specific_unit_conversions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    
    from_unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    to_unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    conversion_factor = Column(Numeric(15, 6), nullable=False)  # e.g., 0.91 for 1 pack = 0.91 kg
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    inventory_item = relationship("InventoryItem", back_populates="item_specific_conversions")
    from_unit = relationship("Unit", foreign_keys=[from_unit_id])
    to_unit = relationship("Unit", foreign_keys=[to_unit_id])
```

### 2.3. AI Labor Models

#### 2.3.1. Onboarding Model (db/models/labor/onboarding.py)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Date, Text, Enum
from sqlalchemy.orm import relationship

from ..base import Base
import enum

class OnboardingStatus(enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TERMINATED = "terminated"

class StepStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class StaffOnboarding(Base):
    """Staff onboarding record"""
    __tablename__ = "staff_onboarding"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    position = Column(String, nullable=False)
    
    start_date = Column(Date, nullable=False)
    status = Column(Enum(OnboardingStatus), default=OnboardingStatus.IN_PROGRESS, nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant")
    steps = relationship("OnboardingStep", back_populates="staff_onboarding")

class OnboardingStep(Base):
    """Individual step in the onboarding process"""
    __tablename__ = "onboarding_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    staff_onboarding_id = Column(UUID(as_uuid=True), ForeignKey("staff_onboarding.id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    status = Column(Enum(StepStatus), default=StepStatus.PENDING, nullable=False)
    completion_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    staff_onboarding = relationship("StaffOnboarding", back_populates="steps")
```

### 2.4. AI Chef Models

#### 2.4.1. Recipe Model (db/models/chef/recipe.py)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Text, Numeric
from sqlalchemy.orm import relationship

from ..base import Base

class Recipe(Base):
    """Recipe definition"""
    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    
    yield_quantity = Column(Numeric(10, 2), nullable=False)
    yield_unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    ingredients = relationship("RecipeIngredient", back_populates="recipe")
    menu_items = relationship("MenuItem", back_populates="recipe")
    yield_unit = relationship("Unit")

class RecipeIngredient(Base):
    """Ingredients required for a recipe"""
    __tablename__ = "recipe_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    inventory_item = relationship("InventoryItem")
    unit = relationship("Unit")
```

#### 2.4.2. Menu Model (db/models/chef/menu.py)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Text, Numeric, Time, Boolean, Integer
from sqlalchemy.orm import relationship

from ..base import Base

class Menu(Base):
    """Menu offered by a restaurant"""
    __tablename__ = "menus"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    start_time = Column(Time, nullable=True)  # NULL means all day
    end_time = Column(Time, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="menus")
    menu_items = relationship("MenuContainsMenuItem", back_populates="menu")

class MenuItem(Base):
    """Item on the restaurant's menu"""
    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    base_price = Column(Numeric(10, 2), nullable=False)
    category = Column(String, nullable=True)
    
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    recipe = relationship("Recipe", back_populates="menu_items")
    menu_links = relationship("MenuContainsMenuItem", back_populates="menu_item")
    sales = relationship("SalesData", back_populates="menu_item")

class MenuContainsMenuItem(Base):
    """Association between menus and menu items"""
    __tablename__ = "menu_contains_menu_item"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    menu_id = Column(UUID(as_uuid=True), ForeignKey("menus.id"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.id"), nullable=False)
    
    display_order = Column(Integer, nullable=True)
    price_override = Column(Numeric(10, 2), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    menu = relationship("Menu", back_populates="menu_items")
    menu_item = relationship("MenuItem", back_populates="menu_links")

class SalesData(Base):
    """Sales data for menu items"""
    __tablename__ = "sales_data"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.id"), nullable=False)
    
    quantity_sold = Column(Integer, nullable=False)
    sale_price = Column(Numeric(10, 2), nullable=False)
    sale_datetime = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant")
    menu_item = relationship("MenuItem", back_populates="sales")
```

## 3. API Endpoints

### 3.1. Authentication Endpoints (api/auth.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta

from ..core.security import create_access_token, get_password_hash, verify_password
from ..db.models.user import User
from ..schemas.auth import TokenResponse, LoginRequest, TokenPayload, UserCreate

router = APIRouter(prefix="/v1/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint that authenticates a user and returns access and refresh tokens.
    
    Parameters:
    - **login_request**: Email and password credentials
    
    Returns:
    - **token**: JWT access token
    - **refreshToken**: JWT refresh token for obtaining new access tokens
    - **user**: Basic user information
    
    Raises:
    - **401 Unauthorized**: If credentials are invalid
    """
    # Implementation details...
    return {"token": access_token, "refreshToken": refresh_token, "user": user_data}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint"""
    # Implementation details...
    return {"detail": "Successfully logged out"}

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token endpoint"""
    # Implementation details...
    return {"token": new_access_token, "refreshToken": new_refresh_token, "user": user_data}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    # Implementation details...
    return current_user
```

### 3.2. AI Supplier Module Endpoints

#### 3.2.1. Document Management (api/supplier/documents.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List

from ...schemas.supplier.document import DocumentResponse, DocumentCreate
from ...db.models.user import User
from ...core.security import get_current_user

router = APIRouter(prefix="/v1/api/supplier/documents", tags=["Supplier Documents"])

@router.post("/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_data: DocumentCreate = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a new document to the system.
    
    Parameters:
    - **file**: The document file (PDF, Excel)
    - **document_data**: Metadata about the document (document type, associated entities)
    - **current_user**: Authenticated user (automatically injected)
    
    Returns:
    - **DocumentResponse**: Created document with metadata
    
    Raises:
    - **400 Bad Request**: If file format is invalid or metadata is incomplete
    - **413 Request Entity Too Large**: If file exceeds maximum size
    """
    # Implementation details...
    return document

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    account_id: UUID = None,
    restaurant_id: UUID = None,
    document_type: str = None,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get list of documents"""
    # Implementation details...
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get document details"""
    # Implementation details...
    return document

@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Download original document"""
    # Implementation details...
    return document_file

@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Delete a document"""
    # Implementation details...
    return {"detail": "Document deleted successfully"}
```

#### 3.2.2. Reconciliation (api/supplier/reconciliation.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from typing import List

from ...schemas.supplier.reconciliation import (
    ReconciliationCreate, ReconciliationResponse, ReconciliationItemResponse
)
from ...db.models.user import User
from ...core.security import get_current_user
from ...websockets.supplier.reconciliation import reconciliation_manager

router = APIRouter(prefix="/v1/api/supplier/reconciliation", tags=["Supplier Reconciliation"])

@router.post("/", response_model=ReconciliationResponse)
async def start_reconciliation(
    reconciliation_data: ReconciliationCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Start a new reconciliation process for matching supplier documents with system records.
    
    Parameters:
    - **reconciliation_data**: Data needed to start reconciliation, including document ID
    - **current_user**: Authenticated user (automatically injected)
    
    Returns:
    - **ReconciliationResponse**: Created reconciliation with initial status
    
    Notes:
    - This is an asynchronous operation. Use WebSocket connection to monitor progress.
    - WebSocket: /ws/supplier/reconciliation/{reconciliation_id}
    
    Raises:
    - **404 Not Found**: If document doesn't exist
    - **400 Bad Request**: If document is not in a state that can be reconciled
    """
    # Implementation details...
    return reconciliation

@router.get("/", response_model=List[ReconciliationResponse])
async def list_reconciliations(
    account_id: UUID = None,
    restaurant_id: UUID = None,
    status: str = None,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List reconciliations"""
    # Implementation details...
    return reconciliations

@router.get("/{reconciliation_id}", response_model=ReconciliationResponse)
async def get_reconciliation(
    reconciliation_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get reconciliation details"""
    # Implementation details...
    return reconciliation

@router.get("/{reconciliation_id}/status", response_model=ReconciliationStatusResponse)
async def get_reconciliation_status(
    reconciliation_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get reconciliation status and progress"""
    # Implementation details...
    return status

@router.get("/{reconciliation_id}/matched", response_model=List[ReconciliationItemResponse])
async def get_matched_items(
    reconciliation_id: UUID,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get matched invoices"""
    # Implementation details...
    return matched_items

@router.get("/{reconciliation_id}/missing-restaurant", response_model=List[ReconciliationItemResponse])
async def get_missing_in_restaurant(
    reconciliation_id: UUID,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get entries missing in restaurant system"""
    # Implementation details...
    return missing_items

@router.get("/{reconciliation_id}/missing-supplier", response_model=List[ReconciliationItemResponse])
async def get_missing_in_supplier(
    reconciliation_id: UUID,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get entries missing in supplier document"""
    # Implementation details...
    return missing_items

@router.get("/{reconciliation_id}/mismatches", response_model=List[ReconciliationItemResponse])
async def get_mismatches(
    reconciliation_id: UUID,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get entries with amount mismatches"""
    # Implementation details...
    return mismatched_items

@router.get("/{reconciliation_id}/export")
async def export_reconciliation(
    reconciliation_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Export reconciliation results as Excel"""
    # Implementation details...
    return excel_file
```

### 3.3. WebSocket Implementation

```python
# In main.py
@app.websocket("/ws/supplier/reconciliation/{reconciliation_id}")
async def websocket_reconciliation_endpoint(websocket: WebSocket, reconciliation_id: str):
    await reconciliation_manager.connect(websocket, reconciliation_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        reconciliation_manager.disconnect(websocket, reconciliation_id)

# In websockets/supplier/reconciliation.py
class ReconciliationManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, reconciliation_id: str):
        await websocket.accept()
        if reconciliation_id not in self.active_connections:
            self.active_connections[reconciliation_id] = []
        self.active_connections[reconciliation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, reconciliation_id: str):
        if reconciliation_id in self.active_connections:
            self.active_connections[reconciliation_id].remove(websocket)
            if not self.active_connections[reconciliation_id]:
                del self.active_connections[reconciliation_id]

    async def send_progress_update(self, reconciliation_id: str, data: dict):
        if reconciliation_id in self.active_connections:
            for connection in self.active_connections[reconciliation_id]:
                await connection.send_json(data)

reconciliation_manager = ReconciliationManager()
```

## 4. Background Task Implementation

### 4.1. Document Processing Task

```python
# In workers/tasks/supplier/document_processing.py
from celery import shared_task
from uuid import UUID

from ....db.models.supplier.document import Document, DocumentStatus
from ....db.models.supplier.reconciliation import Reconciliation, ReconciliationStatus
from ....utils.pdf_extractor import extract_text_from_pdf
from ....utils.excel_parser import parse_excel
from ....websockets.supplier.reconciliation import reconciliation_manager

@shared_task
def process_document(document_id: str):
    """Process a document for text and structure extraction"""
    # Get database session
    db = SessionLocal()
    try:
        # Get document
        document = db.query(Document).filter(Document.id == UUID(document_id)).first()
        if not document:
            return {"status": "error", "message": "Document not found"}
        
        # Update document status
        document.status = DocumentStatus.PROCESSING
        db.commit()
        
        # Process document based on file type
        if document.file_type.lower() == 'pdf':
            extracted_text = extract_text_from_pdf(document.storage_path)
            # Process the extracted text...
        elif document.file_type.lower() in ('xlsx', 'xls'):
            data = parse_excel(document.storage_path)
            # Process the data...
        else:
            document.status = DocumentStatus.ERROR
            document.error_message = f"Unsupported file type: {document.file_type}"
            db.commit()
            return {"status": "error", "message": document.error_message}
        
        # Update document status to processed
        document.status = DocumentStatus.PROCESSED
        db.commit()
        
        return {"status": "success", "document_id": document_id}
    
    except Exception as e:
        # Log the error
        logging.exception(f"Error processing document {document_id}: {str(e)}")
        
        # Update document status
        document.status = DocumentStatus.ERROR
        document.error_message = str(e)
        db.commit()
        
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
```

### 4.2. Reconciliation Task

```python
# In workers/tasks/supplier/reconciliation.py
from celery import shared_task
from uuid import UUID

from ....db.models.supplier.reconciliation import Reconciliation, ReconciliationStatus
from ....websockets.supplier.reconciliation import reconciliation_manager

@shared_task
def process_reconciliation(reconciliation_id: str):
    """Process a reconciliation task"""
    # Get database session
    db = SessionLocal()
    try:
        # Get reconciliation
        reconciliation = db.query(Reconciliation).filter(Reconciliation.id == UUID(reconciliation_id)).first()
        if not reconciliation:
            return {"status": "error", "message": "Reconciliation not found"}
        
        # Update reconciliation status
        reconciliation.status = ReconciliationStatus.IN_PROGRESS
        reconciliation.started_at = datetime.now()
        reconciliation.progress = 0
        db.commit()
        
        # Send initial progress update via WebSocket
        await reconciliation_manager.send_progress_update(
            reconciliation_id,
            {
                "progress": 0,
                "status": "in_progress",
                "message": "Starting reconciliation process"
            }
        )
        
        # Define steps for the reconciliation process
        steps = [
            {"step_number": 1, "name": "Document Validation"},
            {"step_number": 2, "name": "Text Extraction"},
            {"step_number": 3, "name": "Supplier Identification"},
            {"step_number": 4, "name": "Data Structuring"},
            {"step_number": 5, "name": "Restaurant System Integration"},
            {"step_number": 6, "name": "Invoice Matching"},
            {"step_number": 7, "name": "Result Classification"},
            {"step_number": 8, "name": "Report Generation"}
        ]
        
        # Process each step
        for step in steps:
            # Update progress via WebSocket
            await reconciliation_manager.send_progress_update(
                reconciliation_id,
                {
                    "step_number": step["step_number"],
                    "status": "in_progress",
                    "progress": (step["step_number"] - 1) / len(steps) * 100,
                    "message": f"Processing {step['name']}"
                }
            )
            
            # Execute step logic based on step number
            if step["step_number"] == 1:
                # Document validation logic...
                pass
            elif step["step_number"] == 2:
                # Text extraction logic...
                pass
            # ... other steps
            
            # Update progress via WebSocket after step completion
            await reconciliation_manager.send_progress_update(
                reconciliation_id,
                {
                    "step_number": step["step_number"],
                    "status": "done",
                    "progress": step["step_number"] / len(steps) * 100,
                    "message": f"Completed {step['name']}"
                }
            )
            
            # Update reconciliation progress in database
            reconciliation.progress = step["step_number"] / len(steps) * 100
            db.commit()
        
        # Update reconciliation status to completed
        reconciliation.status = ReconciliationStatus.COMPLETED
        reconciliation.completed_at = datetime.now()
        reconciliation.progress = 100
        db.commit()
        
        # Send final progress update via WebSocket
        await reconciliation_manager.send_progress_update(
            reconciliation_id,
            {
                "progress": 100,
                "status": "completed",
                "message": "Reconciliation completed successfully"
            }
        )
        
        return {"status": "success", "reconciliation_id": reconciliation_id}
    
    except Exception as e:
        # Log the error
        logging.exception(f"Error processing reconciliation {reconciliation_id}: {str(e)}")
        
        # Update reconciliation status
        reconciliation.status = ReconciliationStatus.ERROR
        db.commit()
        
        # Send error update via WebSocket
        await reconciliation_manager.send_progress_update(
            reconciliation_id,
            {
                "status": "error",
                "error": str(e),
                "message": "An error occurred during reconciliation"
            }
        )
        
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
```

## 5. Integration and Configuration

### 5.1. Main Application Entry Point (main.py)

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from .api import auth, dashboard
from .api.supplier import documents, invoices, reconciliation, inventory, units
from .api.labor import onboarding
from .api.chef import menu, recipes, menus
from .api.settings import accounts, restaurants, stores, users, suppliers
from .websockets.supplier.reconciliation import reconciliation_manager

app = FastAPI(
    title="GET INN Backend API",
    description="Backend API for the GET INN platform that creates self-operating restaurants",
    version="1.0.0",
    docs_url=None,  # Disable default docs URL to customize it
    redoc_url=None  # Disable default redoc URL to customize it
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with actual origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Custom API documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png"
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.png"
    )

# Custom OpenAPI schema
@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

# Include routers
app.include_router(auth.router)
app.include_router(dashboard.router)

# Supplier module routers
app.include_router(documents.router)
app.include_router(invoices.router)
app.include_router(reconciliation.router)
app.include_router(inventory.router)
app.include_router(units.router)

# Labor module routers
app.include_router(onboarding.router)

# Chef module routers
app.include_router(menu.router)
app.include_router(recipes.router)
app.include_router(menus.router)

# Settings routers
app.include_router(accounts.router)
app.include_router(restaurants.router)
app.include_router(stores.router)
app.include_router(users.router)
app.include_router(suppliers.router)

# WebSocket endpoints
@app.websocket("/ws/supplier/reconciliation/{reconciliation_id}")
async def websocket_reconciliation_endpoint(websocket: WebSocket, reconciliation_id: str):
    await reconciliation_manager.connect(websocket, reconciliation_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        reconciliation_manager.disconnect(websocket, reconciliation_id)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
```

### 5.2. Security Implementation (core/security.py)

```python
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..core.config import settings
from ..db.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_token(token)
        user_id = payload["sub"]
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    finally:
        db.close()
```

## 6. API Documentation

### 6.1. Swagger UI

All API endpoints are fully documented using OpenAPI specifications and accessible through Swagger UI at `/docs`. The documentation includes:

- Detailed endpoint descriptions
- Request/response models with field descriptions
- Authentication requirements
- Example requests and responses
- Error responses and status codes

### 6.2. OpenAPI Schema

The OpenAPI schema is available at `/openapi.json` and can be imported into API client tools like Postman or Insomnia.

### 6.3. Documentation Guidelines for Developers

When adding new endpoints, follow these guidelines to maintain high-quality API documentation:

1. **Use docstrings**: All endpoint functions should have detailed docstrings that describe:
   - What the endpoint does
   - Parameters and their purpose
   - Return values
   - Possible error responses
   - Any special notes or considerations

2. **Use Pydantic models**: Define clear Pydantic models with field descriptions:

```python
class ReconciliationCreate(BaseModel):
    document_id: UUID = Field(..., description="ID of the document to reconcile")
    restaurant_ids: List[UUID] = Field(..., description="IDs of restaurants to include in reconciliation")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "restaurant_ids": ["123e4567-e89b-12d3-a456-426614174001"]
            }
        }
```

3. **Tag endpoints**: Use consistent tags to group related endpoints:

```python
router = APIRouter(prefix="/v1/api/supplier/reconciliation", tags=["Supplier Reconciliation"])
```

4. **Document response status codes**: Specify possible response status codes:

```python
@router.post("/", response_model=ReconciliationResponse, status_code=201,
            responses={
                401: {"description": "Unauthorized"},
                404: {"description": "Document not found"},
                400: {"description": "Invalid request"}
            })
```

## 7. Conclusion

This new backend structure has been designed to directly support the frontend requirements while maintaining a clean, modular organization. The architecture is centered around the three core AI modules defined in the frontend specification:

1. **AI Supplier** - Manages documents, invoices, reconciliation, inventory, and units
2. **AI Labor** - Manages staff onboarding
3. **AI Chef** - Manages menu analysis, recipes, and menu management

Key improvements over the previous structure:

- Modular organization by functional domain (supplier, labor, chef)
- Clear separation of API endpoints, schemas, and business logic
- Dedicated WebSocket implementation for real-time updates
- Comprehensive database models with proper relationships
- Background task processing for document processing and reconciliation
- Standardized API routes matching the frontend requirements
- Custom authentication and security implementation

The backend provides all necessary endpoints required by the frontend, ensuring seamless integration between frontend and backend components.