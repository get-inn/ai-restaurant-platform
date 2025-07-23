# Technical Specification: GET INN Backend v2

## 1. Introduction

### 1.1. Purpose

This technical specification outlines the requirements and architecture for developing the Python backend for GET INN, the world's first platform that creates self-operating restaurants. The backend will support AI-driven automation for restaurant operations across three key modules: AI Supplier (procurement and inventory), AI Labor (staff management), and AI Chef (menu optimization).

### 1.2. System Overview

GET INN empowers restaurant founders to run scalable, self-operating restaurants using AI agents. The backend will provide robust APIs for the frontend to deliver an intuitive interface for automating critical operations like procurement, kitchen management, staff management, and menu optimization. The system is designed to support multiple restaurant chains, individual restaurants, and their respective stores.

### 1.3. Development Goals

- Build a scalable, maintainable Python backend using FastAPI
- Implement secure API endpoints with proper authentication and authorization
- Develop core services for AI Supplier, AI Labor, and AI Chef modules
- Provide real-time updates using WebSockets for long-running processes
- Create a robust document processing pipeline for financial reconciliation
- Implement comprehensive inventory, menu, and recipe management
- Support AI-driven data analysis for restaurant operations

## 2. Architecture Overview

### 2.1. High-Level Architecture

The backend follows a modern, layered architecture:

1. **API Layer**: FastAPI for handling HTTP requests and WebSockets
2. **Service Layer**: Business logic implementation
3. **Data Access Layer**: Database operations with Supabase PostgreSQL
4. **Integration Layer**: Connections to external systems and AI services
5. **Background Worker Layer**: Celery for asynchronous processing

### 2.2. Technology Stack

- **Framework**: FastAPI + Pydantic
- **Database**: PostgreSQL via Supabase
- **Authentication**: Supabase Auth with JWT
- **Task Queue**: Celery with Redis
- **Document Processing**: PyPDF2, pandas, OpenAI
- **Storage**: Supabase Storage (S3-compatible)
- **Containerization**: Docker + Docker Compose
- **WebSockets**: FastAPI's native WebSocket support

### 2.3. Deployment Architecture

- Docker-based containerization
- Microservice architecture for scalable components
- Separate containers for API, workers, and specialized services
- Horizontal scaling for high-availability

## 3. Core Modules

### 3.1. AI Supplier Module

The AI Supplier module handles procurement, reconciliation, and inventory management.

#### 3.1.1. Document Management

- Upload, store, and process supplier documents (PDF/Excel)
- Extract text and structured data from documents
- Classify documents by type and associate with the correct supplier/restaurant

#### 3.1.2. Reconciliation System

- Match supplier documents against restaurant system records
- Track reconciliation progress in real-time
- Generate detailed reports with matched/unmatched items
- Export reconciliation results in various formats

#### 3.1.3. Inventory Management

- Track ingredient price changes across restaurants
- Monitor price volatility and generate alerts
- Analyze impact of price changes on menus and sales
- Generate inventory valuation reports

### 3.2. AI Labor Module

The AI Labor module handles staff management with a focus on onboarding.

#### 3.2.1. Staff Onboarding

- Track and manage onboarding of new staff across restaurants
- Monitor onboarding progress and completion status
- Aggregate staff data at restaurant level

### 3.3. AI Chef Module

The AI Chef module provides menu analysis and optimization.

#### 3.3.1. Menu Analysis

- Implement ABC analysis for menu items based on profitability and sales volume
- Generate insights and recommendations for menu optimization
- Track menu performance metrics over time

## 4. Database Schema

### 4.1. Core Entities

#### 4.1.1. Account & Restaurant Management

```python
class Account(Base):
    __tablename__ = "account"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Restaurant(Base):
    __tablename__ = "restaurant"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Store(Base):
    __tablename__ = "store"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Supplier(Base):
    __tablename__ = "supplier"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    contact_info = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### 4.1.2. User Management

```python
class UserProfile(Base):
    __tablename__ = "user_profile"
    
    id = Column(UUID(as_uuid=True), primary_key=True)  # Maps to Supabase auth.users.id
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=True)
    role = Column(String, nullable=False)  # 'admin', 'account_manager', 'restaurant_manager', 'chef'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### 4.1.3. Document Management

```python
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
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### 4.1.4. Reconciliation Management

```python
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
```

#### 4.1.5. Inventory Management

```python
class UnitCategory(Base):
    __tablename__ = "unit_category"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)  # 'weight', 'volume', 'count'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Unit(Base):
    __tablename__ = "unit"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=True)  # NULL means global unit
    name = Column(String, nullable=False)  # 'kilogram', 'liter', 'piece'
    symbol = Column(String, nullable=False)  # 'kg', 'L', 'pc'
    unit_category_id = Column(UUID(as_uuid=True), ForeignKey("unit_category.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UnitConversion(Base):
    __tablename__ = "unit_conversion"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=True)
    from_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    to_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    conversion_factor = Column(Numeric(15, 6), nullable=False)  # e.g., 1000 for kg to g
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class InventoryItem(Base):
    __tablename__ = "inventory_item"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    default_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    category = Column(String, nullable=True)
    item_type = Column(String, nullable=False)  # 'raw_ingredient', 'semi_finished', 'finished_product'
    current_cost_per_unit = Column(Numeric(10, 2), nullable=True)
    reorder_level = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ItemSpecificUnitConversion(Base):
    __tablename__ = "item_specific_unit_conversion"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_item.id"), nullable=False)
    from_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    to_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    conversion_factor = Column(Numeric(15, 6), nullable=False)  # e.g., 0.91 for 1 pack = 0.91 kg
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class InventoryStock(Base):
    __tablename__ = "inventory_stock"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"), nullable=False)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_item.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class InventoryItemPriceHistory(Base):
    __tablename__ = "inventory_item_price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_item.id"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"), nullable=False)
    price_date = Column(Date, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    source = Column(String, nullable=False)  # 'invoice', 'manual_update', 'system_calculated'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### 4.1.6. Invoice Management

```python
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
```

#### 4.1.7. Recipe & Menu Management

```python
class Recipe(Base):
    __tablename__ = "recipe"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    yield_quantity = Column(Numeric(10, 2), nullable=False)
    yield_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredient"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipe.id"), nullable=False)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_item.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Menu(Base):
    __tablename__ = "menu"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(Time, nullable=True)  # NULL means all day
    end_time = Column(Time, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class MenuItem(Base):
    __tablename__ = "menu_item"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    base_price = Column(Numeric(10, 2), nullable=False)
    category = Column(String, nullable=True)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipe.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class MenuContainsMenuItem(Base):
    __tablename__ = "menu_contains_menu_item"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menu_id = Column(UUID(as_uuid=True), ForeignKey("menu.id"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_item.id"), nullable=False)
    display_order = Column(Integer, nullable=True)
    price_override = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SalesData(Base):
    __tablename__ = "sales_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_item.id"), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    sale_price = Column(Numeric(10, 2), nullable=False)
    sale_datetime = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### 4.1.8. Staff Management

```python
class StaffOnboarding(Base):
    __tablename__ = "staff_onboarding"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    position = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="in_progress")  # 'in_progress', 'completed', 'terminated'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class OnboardingStep(Base):
    __tablename__ = "onboarding_step"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_onboarding_id = Column(UUID(as_uuid=True), ForeignKey("staff_onboarding.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")  # 'pending', 'in_progress', 'completed', 'failed'
    completion_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 4.2. Key Relationships

- Users belong to Accounts and optionally to specific Restaurants
- Restaurants belong to Accounts
- Stores belong to Restaurants
- Documents belong to Accounts and optionally to Restaurants, Stores, and Suppliers
- Reconciliations are linked to Documents and the organizational hierarchy (Account/Restaurant/Store)
- Inventory Items belong to Accounts with stock tracked at Store level
- Recipes belong to Accounts and contain Inventory Items
- Menus belong to Restaurants and contain Menu Items
- Menu Items belong to Accounts and optionally link to Recipes
- Sales Data records Menu Item sales in Restaurants
- Staff Onboarding records are associated with Restaurants

## 5. API Endpoints

### 5.1. AI Supplier Module Endpoints

#### 5.1.1. Document Management

```
POST /v1/api/supplier/documents
GET /v1/api/supplier/documents
GET /v1/api/supplier/documents/{id}
GET /v1/api/supplier/documents/{id}/download
DELETE /v1/api/supplier/documents/{id}
```

#### 5.1.2. Invoice Management

```
POST /v1/api/supplier/invoices
GET /v1/api/supplier/invoices
GET /v1/api/supplier/invoices/{id}
PUT /v1/api/supplier/invoices/{id}
DELETE /v1/api/supplier/invoices/{id}
```

#### 5.1.3. Reconciliation

```
POST /v1/api/supplier/reconciliation
GET /v1/api/supplier/reconciliation
GET /v1/api/supplier/reconciliation/{id}
GET /v1/api/supplier/reconciliation/{id}/status
GET /v1/api/supplier/reconciliation/{id}/matched
GET /v1/api/supplier/reconciliation/{id}/missing-restaurant
GET /v1/api/supplier/reconciliation/{id}/missing-supplier
GET /v1/api/supplier/reconciliation/{id}/mismatches
GET /v1/api/supplier/reconciliation/{id}/export
```

#### 5.1.4. Inventory Management

```
POST /v1/api/supplier/inventory/items
GET /v1/api/supplier/inventory/items
GET /v1/api/supplier/inventory/items/{id}
PUT /v1/api/supplier/inventory/items/{id}
DELETE /v1/api/supplier/inventory/items/{id}

GET /v1/api/supplier/inventory/price-changes
GET /v1/api/supplier/inventory/price-history/{id}
GET /v1/api/supplier/inventory/impacted-menus/{id}

POST /v1/api/supplier/inventory/stock-adjustments
GET /v1/api/supplier/inventory/stock
GET /v1/api/supplier/inventory/stock/store/{store_id}
```

#### 5.1.5. Units and Conversions

```
POST /v1/api/supplier/units
GET /v1/api/supplier/units
GET /v1/api/supplier/units/{id}
PUT /v1/api/supplier/units/{id}
DELETE /v1/api/supplier/units/{id}

POST /v1/api/supplier/unit-conversions
GET /v1/api/supplier/unit-conversions
GET /v1/api/supplier/unit-conversions/{id}
PUT /v1/api/supplier/unit-conversions/{id}
DELETE /v1/api/supplier/unit-conversions/{id}

POST /v1/api/supplier/item-specific-conversions
GET /v1/api/supplier/item-specific-conversions
GET /v1/api/supplier/item-specific-conversions/{id}
PUT /v1/api/supplier/item-specific-conversions/{id}
DELETE /v1/api/supplier/item-specific-conversions/{id}
```

#### 5.1.6. Reports

```
GET /v1/api/supplier/reports/inventory-valuation
GET /v1/api/supplier/reports/cost-of-goods-sold
```

### 5.2. AI Labor Module Endpoints

#### 5.2.1. Onboarding Management

```
POST /v1/api/labor/onboarding
GET /v1/api/labor/onboarding
GET /v1/api/labor/onboarding/restaurant/{restaurant_id}
GET /v1/api/labor/onboarding/{id}
PUT /v1/api/labor/onboarding/{id}
DELETE /v1/api/labor/onboarding/{id}

POST /v1/api/labor/onboarding/{id}/steps
GET /v1/api/labor/onboarding/{id}/steps
PUT /v1/api/labor/onboarding/{id}/steps/{step_id}
DELETE /v1/api/labor/onboarding/{id}/steps/{step_id}
```

### 5.3. AI Chef Module Endpoints

#### 5.3.1. Menu Management

```
POST /v1/api/chef/menus
GET /v1/api/chef/menus
GET /v1/api/chef/menus/{id}
PUT /v1/api/chef/menus/{id}
DELETE /v1/api/chef/menus/{id}

POST /v1/api/chef/menu-items
GET /v1/api/chef/menu-items
GET /v1/api/chef/menu-items/{id}
PUT /v1/api/chef/menu-items/{id}
DELETE /v1/api/chef/menu-items/{id}

POST /v1/api/chef/menus/{menu_id}/items
GET /v1/api/chef/menus/{menu_id}/items
DELETE /v1/api/chef/menus/{menu_id}/items/{menu_item_id}
```

#### 5.3.2. Recipe Management

```
POST /v1/api/chef/recipes
GET /v1/api/chef/recipes
GET /v1/api/chef/recipes/{id}
PUT /v1/api/chef/recipes/{id}
DELETE /v1/api/chef/recipes/{id}

POST /v1/api/chef/recipes/{recipe_id}/ingredients
GET /v1/api/chef/recipes/{recipe_id}/ingredients
PUT /v1/api/chef/recipes/{recipe_id}/ingredients/{ingredient_id}
DELETE /v1/api/chef/recipes/{recipe_id}/ingredients/{ingredient_id}
```

#### 5.3.3. Menu Analytics

```
GET /v1/api/chef/menu/abc-analysis
GET /v1/api/chef/menu/item/{id}/performance
GET /v1/api/chef/menu/insights

POST /v1/api/chef/sales-data
GET /v1/api/chef/sales-data
GET /v1/api/chef/reports/menu-abc-analysis
```

### 5.4. Core Management Endpoints

#### 5.4.1. Account Management

```
POST /v1/api/accounts
GET /v1/api/accounts
GET /v1/api/accounts/{id}
PUT /v1/api/accounts/{id}
DELETE /v1/api/accounts/{id}
```

#### 5.4.2. Restaurant Management

```
POST /v1/api/accounts/{account_id}/restaurants
GET /v1/api/accounts/{account_id}/restaurants
GET /v1/api/restaurants/{id}
PUT /v1/api/restaurants/{id}
DELETE /v1/api/restaurants/{id}
```

#### 5.4.3. Store Management

```
POST /v1/api/restaurants/{restaurant_id}/stores
GET /v1/api/restaurants/{restaurant_id}/stores
GET /v1/api/stores/{id}
PUT /v1/api/stores/{id}
DELETE /v1/api/stores/{id}
```

#### 5.4.4. User Management

```
GET /v1/api/users/me
GET /v1/api/users
GET /v1/api/users/{id}
PUT /v1/api/users/{id}/role
```

#### 5.4.5. Supplier Management

```
POST /v1/api/accounts/{account_id}/suppliers
GET /v1/api/accounts/{account_id}/suppliers
GET /v1/api/suppliers/{id}
PUT /v1/api/suppliers/{id}
DELETE /v1/api/suppliers/{id}
```

### 5.5. WebSocket Endpoints

```
WS /ws/supplier/reconciliation/{reconciliation_id}
```

## 6. Authentication and Authorization

### 6.1. Authentication Flow

Authentication will be handled using Supabase Auth with the following flow:

1. Users register or log in via the frontend using Supabase client libraries
2. Upon successful authentication, Supabase issues a JWT containing user information
3. The JWT is included in the `Authorization: Bearer <token>` header for all API requests
4. The backend validates the JWT and extracts the user ID and other claims
5. User permissions are determined based on their role and associated entities

### 6.2. Authorization Model

The system implements a role-based access control model with the following roles:

1. **Admin**: Full access to all features and data
2. **Account Manager**: Full access to a specific account and its restaurants/stores
3. **Restaurant Manager**: Access limited to specific restaurant(s)
4. **Chef**: Access to AI Chef module for specific restaurant(s)
5. **Staff**: Limited access to labor/tasks for a specific restaurant

Authorization is enforced at multiple levels:
- API endpoint access control via FastAPI dependencies
- Row-level security in the database via Supabase RLS policies
- Object-level permissions checks in service layers

## 7. Detailed Implementation Components

### 7.1. Document Processing Pipeline

1. **Document Upload**: Frontend uploads document to backend
2. **Storage**: Document is stored in Supabase Storage
3. **Metadata Recording**: Document metadata saved in database
4. **Processing Queue**: Document added to Celery task queue
5. **Text Extraction**: Worker extracts text using appropriate library
6. **Data Structuring**: Raw text converted to structured data
7. **Entity Recognition**: Identify suppliers, invoices, amounts
8. **Reconciliation**: Match against existing records
9. **Result Storage**: Save reconciliation results
10. **Notification**: Inform user of completed processing

### 7.2. WebSocket Communication for Real-time Updates

The system uses WebSockets to provide real-time updates for long-running processes:

```python
# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)

    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_json(message)
```

### 7.3. Reconciliation Process

The reconciliation process follows these steps:

1. User uploads a document and initiates reconciliation
2. Backend creates a reconciliation record and starts background processing
3. Progress updates are sent via WebSockets as each step completes
4. Document text is extracted and parsed
5. Supplier is identified from document content
6. System retrieves matching invoices from the database or restaurant system
7. Invoice items are matched against document entries
8. Results are categorized as matched, missing, or mismatched
9. Final reconciliation report is generated
10. User is notified of completion

### 7.4. Menu ABC Analysis Algorithm

The ABC analysis categorizes menu items based on profitability and sales volume:

```python
def generate_menu_abc_analysis(restaurant_id, start_date, end_date):
    # Get sales data for period
    sales_data = get_sales_data(restaurant_id, start_date, end_date)
    
    # Calculate metrics for each item
    menu_items = []
    for item in sales_data:
        profit_margin = calculate_profit_margin(item)
        sales_volume = item.quantity_sold
        total_revenue = item.quantity_sold * item.sale_price
        
        # Calculate percentile ranks
        profit_percentile = calculate_percentile(profit_margin, [i.profit_margin for i in sales_data])
        volume_percentile = calculate_percentile(sales_volume, [i.quantity_sold for i in sales_data])
        
        # Determine ABC category
        category = determine_abc_category(profit_percentile, volume_percentile)
        
        menu_items.append({
            "id": item.menu_item_id,
            "name": item.name,
            "profit_margin": profit_margin,
            "sales_volume": sales_volume,
            "total_revenue": total_revenue,
            "category": category
        })
    
    return {
        "analysis_date": datetime.now(),
        "period_start": start_date,
        "period_end": end_date,
        "menu_items": menu_items
    }
```

## 8. Project Structure

```
/ai-restaurant-platform-backend
├── src/
│   ├── api/                      # FastAPI application
│   │   ├── main.py               # Application entry point
│   │   ├── routers/              # API endpoint definitions
│   │   │   ├── accounts.py       # Account management endpoints
│   │   │   ├── chef/             # AI Chef module endpoints
│   │   │   │   ├── menu.py       # Menu management
│   │   │   │   ├── recipes.py    # Recipe management
│   │   │   │   └── analytics.py  # Menu analytics
│   │   │   ├── labor/            # AI Labor module endpoints
│   │   │   │   └── onboarding.py # Staff onboarding
│   │   │   ├── supplier/         # AI Supplier module endpoints
│   │   │   │   ├── documents.py  # Document management
│   │   │   │   ├── invoices.py   # Invoice management
│   │   │   │   ├── reconciliation.py # Reconciliation process
│   │   │   │   ├── inventory.py  # Inventory management
│   │   │   │   └── units.py      # Unit management
│   │   │   ├── restaurants.py    # Restaurant management endpoints
│   │   │   ├── stores.py         # Store management endpoints
│   │   │   └── users.py          # User management endpoints
│   │   ├── dependencies/         # Endpoint dependencies
│   │   │   ├── auth.py           # Authentication and authorization
│   │   │   └── db.py             # Database session management
│   │   ├── schemas/              # Pydantic data models
│   │   │   ├── auth_schemas.py   # Authentication models
│   │   │   ├── chef/             # AI Chef schemas
│   │   │   ├── labor/            # AI Labor schemas
│   │   │   └── supplier/         # AI Supplier schemas
│   │   ├── services/             # Business logic layer
│   │   │   ├── auth_service.py   # Authentication service
│   │   │   ├── chef/             # AI Chef services
│   │   │   ├── labor/            # AI Labor services 
│   │   │   └── supplier/         # AI Supplier services
│   │   ├── core/                 # Core components
│   │   │   ├── config.py         # Configuration settings
│   │   │   ├── exceptions.py     # Custom exceptions
│   │   │   ├── logging_config.py # Logging configuration
│   │   │   ├── models.py         # Database models
│   │   │   └── unit_converter.py # Unit conversion utilities
│   │   └── utils/                # Utility functions
│   │       ├── pdf_extractor.py  # PDF processing utilities
│   │       └── excel_parser.py   # Excel/CSV processing utilities
│   ├── worker/                   # Celery worker
│   │   ├── celery_app.py         # Celery configuration
│   │   └── tasks/                # Asynchronous tasks
│   │       ├── supplier/         # AI Supplier tasks
│   │       │   ├── document_processing_tasks.py # Document processing
│   │       │   └── reconciliation_tasks.py      # Reconciliation processing
│   │       ├── labor/            # AI Labor tasks
│   │       └── chef/             # AI Chef tasks
│   └── integrations/             # External integrations
│       ├── pos_erp_adapters/     # POS/ERP system adapters
│       └── ai_tools/             # AI service integrations
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── performance/              # Performance tests
├── docker/                       # Docker configuration
│   ├── Dockerfile.backend        # API service Dockerfile
│   ├── Dockerfile.worker         # Worker service Dockerfile
│   └── docker-compose.yml        # Docker Compose configuration
└── docs/                         # Documentation
```

## 9. Data Flow Examples

### 9.1. Reconciliation Flow

1. **Frontend**: User uploads a supplier document for reconciliation
   - `POST /v1/api/supplier/documents` with file data
   - System returns document ID

2. **Frontend**: User starts reconciliation process
   - `POST /v1/api/supplier/reconciliation` with document ID and options
   - System returns reconciliation ID and creates background task

3. **Frontend**: Establishes WebSocket connection for real-time updates
   - Connect to `WS /ws/supplier/reconciliation/{reconciliation_id}`

4. **Backend**: Processing occurs with progress updates via WebSocket
   - Document validation → Text extraction → Supplier identification → 
     Data structuring → System integration → Invoice matching → 
     Result classification → Report generation

5. **Frontend**: Receives final result notification via WebSocket
   - Fetches detailed results via `GET /v1/api/supplier/reconciliation/{id}/matched`, etc.

6. **Frontend**: User can export reconciliation results
   - `GET /v1/api/supplier/reconciliation/{id}/export` to download Excel report

### 9.2. Menu ABC Analysis Flow

1. **Backend**: Collects sales data regularly from restaurant POS systems
   - Data is processed and stored in `sales_data` table

2. **Frontend**: User requests menu ABC analysis
   - `GET /v1/api/chef/menu/abc-analysis?restaurant_id=X&start_date=Y&end_date=Z`

3. **Backend**: Processes the request
   - Retrieves sales data for the specified period
   - Calculates profit margin for each menu item (using recipes and ingredient costs)
   - Analyzes sales volume and revenue metrics
   - Categorizes items using the ABC algorithm
   - Returns categorized results

4. **Frontend**: Displays results in a visual dashboard
   - A items (high value): Top performing items
   - B items: Moderate performers
   - C items: Low performers
   - D items: Underperforming items to consider removing

5. **Frontend**: User can drill down into specific item performance
   - `GET /v1/api/chef/menu/item/{id}/performance`
   - View detailed metrics, trends, and ingredient price impacts

## 10. Development and Deployment

### 10.1. Development Setup

1. Clone the repository
2. Create local environment file from template
3. Start the development environment with Docker Compose
   ```bash
   docker-compose -f docker/docker-compose.dev.yml up
   ```
4. Run database migrations
   ```bash
   docker-compose -f docker/docker-compose.dev.yml exec backend alembic upgrade head
   ```

### 10.2. Testing

1. Run unit tests
   ```bash
   docker-compose -f docker/docker-compose.dev.yml exec backend pytest tests/unit
   ```
2. Run integration tests
   ```bash
   docker-compose -f docker/docker-compose.dev.yml exec backend pytest tests/integration
   ```
3. Run performance tests (optional)
   ```bash
   docker-compose -f docker/docker-compose.dev.yml exec backend pytest tests/performance
   ```

### 10.3. Deployment

1. Build production Docker images
   ```bash
   docker-compose -f docker/docker-compose.yml build
   ```
2. Deploy with proper environment variables for production
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```
3. Run database migrations
   ```bash
   docker-compose -f docker/docker-compose.yml exec backend alembic upgrade head
   ```

## 11. Migration and Maintenance

### 11.1. Database Migrations

The project uses Alembic for database schema migrations:

1. Create a new migration
   ```bash
   alembic revision -m "description of changes"
   ```
2. Apply migrations
   ```bash
   alembic upgrade head
   ```
3. Rollback migrations
   ```bash
   alembic downgrade -1
   ```

### 11.2. Monitoring and Logging

- Structured logging with JSON format
- Log aggregation with a centralized logging system
- Metrics collection with Prometheus
- Real-time monitoring with Grafana dashboards
- Error tracking integration

## 12. Security Considerations

- All communications secured with TLS
- JWT tokens with short expiration times
- Database credentials stored as environment variables
- Input validation for all API endpoints
- Document encryption at rest
- Role-based access control
- Regular security audits and updates

## 13. Performance Considerations

- Horizontal scaling for API services
- Worker pool size tuned for document processing load
- Database connection pooling
- Result caching for frequently accessed data
- Optimized database indexes for common queries
- Pagination for large result sets
- Asynchronous processing for time-consuming tasks

## 14. Future Enhancements

- AI-driven inventory forecasting
- Automated menu recommendation system
- Staff scheduling optimization
- Supplier pricing analysis and recommendation
- Mobile application support
- Multilingual support