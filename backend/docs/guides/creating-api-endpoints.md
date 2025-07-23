# Creating API Endpoints

This guide explains how to add new API endpoints to the GET INN Restaurant Platform.

## Overview

The platform follows a structured approach to API endpoints with clear separation of concerns:

1. **Pydantic Schemas**: Define request and response data models
2. **Routers**: Handle HTTP requests and responses
3. **Services**: Implement business logic
4. **Models**: Define database structure

This guide will walk you through creating a complete API endpoint, from schema definition to implementation and testing.

## Step 1: Create Pydantic Schemas

First, define the data models for your API endpoint using Pydantic:

1. Create or update schema file in the appropriate module:

```python
# src/api/schemas/module_name/feature_schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List

class FeatureBase(BaseModel):
    """Base schema with common fields"""
    name: str
    description: Optional[str] = None

class FeatureCreate(FeatureBase):
    """Schema for creating a new feature"""
    category_id: UUID

class FeatureUpdate(BaseModel):
    """Schema for updating an existing feature"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class FeatureResponse(FeatureBase):
    """Schema for feature responses"""
    id: UUID
    category_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # For Pydantic V2 (replaces orm_mode)
```

2. Update the `__init__.py` file in the schema directory to expose your new schemas:

```python
# src/api/schemas/module_name/__init__.py
from src.api.schemas.module_name.feature_schemas import (
    FeatureBase,
    FeatureCreate,
    FeatureUpdate,
    FeatureResponse,
)
```

## Step 2: Create Router File

Next, create a new router file or update an existing one:

```python
# src/api/routers/module_name/feature.py
from fastapi import APIRouter, Depends, Path, Query, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from uuid import UUID

from src.api.dependencies.db import get_db
from src.api.dependencies.auth import get_current_user, check_role
from src.api.schemas.auth_schemas import UserRole
from src.api.schemas.module_name import (
    FeatureCreate,
    FeatureUpdate,
    FeatureResponse,
)
from src.api.services.module_name.feature_service import FeatureService

router = APIRouter()

@router.post("", response_model=FeatureResponse, status_code=201)
async def create_feature(
    feature_data: FeatureCreate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new feature.
    
    Creates a feature with the provided data, associated with the current user's account.
    """
    service = FeatureService(db)
    return service.create_feature(feature_data, current_user["account_id"])

@router.get("", response_model=List[FeatureResponse])
async def list_features(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    List all features.
    
    Returns a paginated list of features associated with the current user's account.
    """
    service = FeatureService(db)
    return service.list_features(current_user["account_id"], skip=skip, limit=limit)

@router.get("/{feature_id}", response_model=FeatureResponse)
async def get_feature(
    feature_id: UUID = Path(..., description="The ID of the feature to retrieve"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific feature by ID.
    
    Returns the feature with the specified ID if it exists and belongs to the current user's account.
    """
    service = FeatureService(db)
    feature = service.get_feature(feature_id, current_user["account_id"])
    if feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature

@router.put("/{feature_id}", response_model=FeatureResponse)
async def update_feature(
    feature_id: UUID = Path(..., description="The ID of the feature to update"),
    feature_data: FeatureUpdate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a specific feature by ID.
    
    Updates the feature with the specified ID with the provided data.
    """
    service = FeatureService(db)
    feature = service.update_feature(feature_id, feature_data, current_user["account_id"])
    if feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature

@router.delete("/{feature_id}", status_code=204)
async def delete_feature(
    feature_id: UUID = Path(..., description="The ID of the feature to delete"),
    current_user: dict = Depends(check_role([UserRole.ADMIN, UserRole.MANAGER])),
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete a specific feature by ID.
    
    Deletes the feature with the specified ID. This operation requires admin or manager role.
    """
    service = FeatureService(db)
    success = service.delete_feature(feature_id, current_user["account_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Feature not found")
    return None
```

## Step 3: Create Service

Implement the business logic in a service class:

```python
# src/api/services/module_name/feature_service.py
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.api.models.module_name import Feature as FeatureDB
from src.api.schemas.module_name import FeatureCreate, FeatureUpdate, FeatureResponse

class FeatureService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_feature(self, data: FeatureCreate, account_id: UUID) -> Dict[str, Any]:
        """Create a new feature."""
        db_feature = FeatureDB(
            name=data.name,
            description=data.description,
            category_id=data.category_id,
            account_id=account_id
        )
        self.db.add(db_feature)
        self.db.commit()
        self.db.refresh(db_feature)
        
        return FeatureResponse.model_validate(db_feature)
    
    def get_feature(self, feature_id: UUID, account_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a specific feature by ID."""
        db_feature = self.db.query(FeatureDB).filter(
            FeatureDB.id == feature_id,
            FeatureDB.account_id == account_id
        ).first()
        
        if db_feature is None:
            return None
        
        return FeatureResponse.model_validate(db_feature)
    
    def list_features(self, account_id: UUID, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List features for an account."""
        db_features = self.db.query(FeatureDB).filter(
            FeatureDB.account_id == account_id
        ).offset(skip).limit(limit).all()
        
        return [FeatureResponse.model_validate(db_feature) for db_feature in db_features]
    
    def update_feature(self, feature_id: UUID, data: FeatureUpdate, account_id: UUID) -> Optional[Dict[str, Any]]:
        """Update a specific feature."""
        db_feature = self.db.query(FeatureDB).filter(
            FeatureDB.id == feature_id,
            FeatureDB.account_id == account_id
        ).first()
        
        if db_feature is None:
            return None
        
        # Update fields if provided
        if data.name is not None:
            db_feature.name = data.name
        if data.description is not None:
            db_feature.description = data.description
        if data.is_active is not None:
            db_feature.is_active = data.is_active
        
        self.db.commit()
        self.db.refresh(db_feature)
        
        return FeatureResponse.model_validate(db_feature)
    
    def delete_feature(self, feature_id: UUID, account_id: UUID) -> bool:
        """Delete a specific feature."""
        db_feature = self.db.query(FeatureDB).filter(
            FeatureDB.id == feature_id,
            FeatureDB.account_id == account_id
        ).first()
        
        if db_feature is None:
            return False
        
        self.db.delete(db_feature)
        self.db.commit()
        
        return True
```

## Step 4: Create Database Model

If you need a new database model, add it to the appropriate models file:

```python
# src/api/models/module_name.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.api.core.database import Base
from src.api.core.config import settings

class Feature(Base):
    __tablename__ = "feature"
    __table_args__ = {"schema": settings.DATABASE_SCHEMA}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.DATABASE_SCHEMA}.category.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.DATABASE_SCHEMA}.account.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="features")
    account = relationship("Account", back_populates="features")
```

## Step 5: Create Database Migration

Generate a migration for your new model:

```bash
# Using Docker
./backend/start-dev.sh --exec backend alembic revision -m "add feature table"

# Using local virtual environment
cd backend
python -m alembic revision -m "add feature table"
```

Then edit the generated migration file:

```python
# migrations/versions/xxxxxxxxxxxx_add_feature_table.py
def upgrade():
    op.create_table(
        'feature',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey(f'{settings.DATABASE_SCHEMA}.category.id'), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey(f'{settings.DATABASE_SCHEMA}.account.id'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema=settings.DATABASE_SCHEMA
    )
    op.create_index(op.f('ix_feature_account_id'), 'feature', ['account_id'], unique=False, schema=settings.DATABASE_SCHEMA)
    op.create_index(op.f('ix_feature_category_id'), 'feature', ['category_id'], unique=False, schema=settings.DATABASE_SCHEMA)

def downgrade():
    op.drop_index(op.f('ix_feature_category_id'), table_name='feature', schema=settings.DATABASE_SCHEMA)
    op.drop_index(op.f('ix_feature_account_id'), table_name='feature', schema=settings.DATABASE_SCHEMA)
    op.drop_table('feature', schema=settings.DATABASE_SCHEMA)
```

Apply the migration:

```bash
# Using Docker
./backend/start-dev.sh --exec backend alembic upgrade head

# Using local virtual environment
cd backend
python -m alembic upgrade head
```

## Step 6: Register the Router

Update the `__init__.py` in the module's router directory:

```python
# src/api/routers/module_name/__init__.py
from fastapi import APIRouter

from src.api.routers.module_name.feature import router as feature_router
# Import other routers in this module

router = APIRouter()
router.include_router(feature_router, prefix="/features", tags=["features"])
# Include other routers in this module
```

Then register the module router in the main application:

```python
# src/api/main.py
from src.api.routers import module_name

# Add the module router
app.include_router(
    module_name.router,
    prefix=f"{settings.API_V1_STR}/module-name",
    tags=["module-name"],
)
```

## Step 7: Write Tests

### Unit Tests

Create unit tests for the service:

```python
# src/api/tests/unit/services/module_name/test_feature_service.py
import pytest
from unittest.mock import Mock, patch
from uuid import UUID, uuid4
from datetime import datetime

from src.api.services.module_name.feature_service import FeatureService
from src.api.schemas.module_name import FeatureCreate, FeatureUpdate

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def service(mock_db):
    return FeatureService(mock_db)

def test_create_feature(service, mock_db):
    # Arrange
    account_id = uuid4()
    category_id = uuid4()
    data = FeatureCreate(name="Test Feature", description="Test Description", category_id=category_id)
    mock_db_feature = Mock(
        id=uuid4(),
        name="Test Feature",
        description="Test Description",
        category_id=category_id,
        account_id=account_id,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    # Act
    with patch('src.api.schemas.module_name.feature_schemas.FeatureResponse.model_validate', return_value={"id": mock_db_feature.id, "name": mock_db_feature.name}):
        result = service.create_feature(data, account_id)
    
    # Assert
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    assert result["name"] == "Test Feature"
```

### Integration Tests

Create integration tests for the API:

```python
# src/api/tests/integration/module_name/test_feature_api.py
import pytest
from fastapi.testclient import TestClient
from uuid import UUID, uuid4

from src.api.main import app
from src.api.models.module_name import Feature as FeatureDB
from src.api.core.database import SessionLocal

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_create_feature(client, db, test_token, test_account_id, test_category_id):
    # Arrange
    headers = {"Authorization": f"Bearer {test_token}"}
    feature_data = {
        "name": "Test Feature",
        "description": "Test Description",
        "category_id": str(test_category_id)
    }
    
    # Act
    response = client.post(
        "/v1/api/module-name/features",
        json=feature_data,
        headers=headers
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Feature"
    assert data["description"] == "Test Description"
    assert "id" in data
    
    # Verify in DB
    db_feature = db.query(FeatureDB).filter(FeatureDB.id == UUID(data["id"])).first()
    assert db_feature is not None
    assert db_feature.name == "Test Feature"
    assert db_feature.account_id == test_account_id
```

## Best Practices

1. **Follow Standard Patterns**:
   - Use consistent naming conventions
   - Maintain the same structure as existing endpoints
   - Use Pydantic for validation

2. **Proper Authorization**:
   - Always include authentication dependencies
   - Use account-based filtering for multi-tenancy
   - Implement role-based access control for sensitive operations

3. **Input Validation**:
   - Use Pydantic models for all requests
   - Add field validators for complex validations
   - Use FastAPI Query and Path parameters for additional validation

4. **Error Handling**:
   - Raise appropriate HTTPException with status codes
   - Use descriptive error messages
   - Handle edge cases properly

5. **Documentation**:
   - Add clear docstrings to all functions
   - Document parameters and return values
   - Include examples where appropriate

6. **Testing**:
   - Write unit tests for services
   - Write integration tests for API endpoints
   - Test error conditions and edge cases

7. **Performance**:
   - Use pagination for list endpoints
   - Add indexes to frequently queried columns
   - Optimize database queries

8. **Security**:
   - Validate permissions for each operation
   - Never expose sensitive information
   - Sanitize and validate all inputs

## Example: Complete API Implementation

### Router Implementation

```python
@router.get("/{feature_id}/details", response_model=FeatureDetailResponse)
async def get_feature_details(
    feature_id: UUID = Path(..., description="The ID of the feature to get details for"),
    include_stats: bool = Query(False, description="Include usage statistics"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get detailed information for a specific feature.
    
    This endpoint returns detailed information about a feature, including its relationships and optionally usage statistics.
    """
    service = FeatureService(db)
    feature = service.get_feature_details(feature_id, current_user["account_id"], include_stats)
    if feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature
```

### Service Implementation

```python
def get_feature_details(self, feature_id: UUID, account_id: UUID, include_stats: bool = False) -> Optional[Dict[str, Any]]:
    """Get detailed information for a specific feature."""
    query = self.db.query(FeatureDB).filter(
        FeatureDB.id == feature_id,
        FeatureDB.account_id == account_id
    )
    
    # Add relationships
    query = query.options(
        joinedload(FeatureDB.category),
        joinedload(FeatureDB.related_items)
    )
    
    db_feature = query.first()
    if db_feature is None:
        return None
    
    # Convert to response
    result = FeatureDetailResponse.model_validate(db_feature)
    
    # Add statistics if requested
    if include_stats:
        result.usage_stats = self._get_usage_stats(feature_id)
    
    return result
```

### Test Implementation

```python
def test_get_feature_details(client, db, test_token, test_feature_id):
    # Arrange
    headers = {"Authorization": f"Bearer {test_token}"}
    
    # Act
    response = client.get(
        f"/v1/api/module-name/features/{test_feature_id}/details?include_stats=true",
        headers=headers
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_feature_id)
    assert "category" in data
    assert "usage_stats" in data
```

## Conclusion

Creating new API endpoints in the platform follows a consistent pattern that separates concerns and promotes maintainable code. By following these steps and best practices, you can add new functionality to the platform while maintaining its architecture and quality standards.