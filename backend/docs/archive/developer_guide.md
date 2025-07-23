# GET INN Restaurant Platform - Developer Guide

This guide provides instructions for common development tasks on the GET INN Restaurant Platform backend. It is intended to help new developers get up to speed quickly with our development practices and patterns.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Adding New API Endpoints](#adding-new-api-endpoints)
- [Working with Database Models](#working-with-database-models)
- [Creating Pydantic Schemas](#creating-pydantic-schemas)
- [API Documentation](#api-documentation)
- [Authentication and Authorization](#authentication-and-authorization)
- [WebSocket Development](#websocket-development)
- [Background Tasks](#background-tasks)
- [Testing](#testing)

## Environment Setup

### Initial Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ai-restaurant-platform
   ```

2. Start the development environment:
   ```bash
   ./backend/start-dev.sh --build --migrate --init-db
   ```

3. Access the API documentation at http://localhost:8000/docs

### Development Workflow

- Use `./backend/start-dev.sh --logs` to see running logs
- Use `./backend/start-dev.sh --down` to stop containers
- Use `./backend/start-dev.sh --exec backend <command>` to run commands in the backend container

## Adding New API Endpoints

### Step 1: Create Pydantic Schemas

1. First, create or update schemas in `backend/src/api/schemas/`:
   ```python
   # backend/src/api/schemas/module_name/feature_schemas.py
   from pydantic import BaseModel
   from datetime import datetime
   from uuid import UUID
   from typing import Optional, List

   class FeatureBase(BaseModel):
       name: str
       description: Optional[str] = None

   class FeatureCreate(FeatureBase):
       # Fields required for creation
       category_id: UUID

   class FeatureUpdate(BaseModel):
       # Optional fields for updates
       name: Optional[str] = None
       description: Optional[str] = None

   class FeatureResponse(FeatureBase):
       id: UUID
       created_at: datetime
       updated_at: datetime

       class Config:
           orm_mode = True
   ```

2. Update the `__init__.py` file in the schema directory to expose your new schemas:
   ```python
   # backend/src/api/schemas/module_name/__init__.py
   from backend.src.api.schemas.module_name.feature_schemas import (
       FeatureBase,
       FeatureCreate,
       FeatureUpdate,
       FeatureResponse,
   )
   ```

### Step 2: Create Router File

1. Create a new router file or update an existing one in `backend/src/api/routers/`:
   ```python
   # backend/src/api/routers/module_name/feature.py
   from fastapi import APIRouter, Depends, Path, Query, HTTPException, Body
   from sqlalchemy.orm import Session
   from typing import List, Optional, Any
   from uuid import UUID

   from backend.src.api.dependencies.db import get_db
   from backend.src.api.dependencies.auth import get_current_user, check_role
   from backend.src.api.schemas.auth_schemas import UserRole
   from backend.src.api.schemas.module_name import (
       FeatureCreate,
       FeatureUpdate,
       FeatureResponse,
   )

   router = APIRouter()

   @router.post("", response_model=FeatureResponse, status_code=201)
   async def create_feature(
       feature_data: FeatureCreate = Body(...),
       current_user: dict = Depends(get_current_user),
       db: Session = Depends(get_db),
   ) -> Any:
       """
       Create a new feature.
       """
       # Implementation will be added in service layer
       # Example placeholder implementation:
       return {
           "id": "00000000-0000-0000-0000-000000000001",
           "name": feature_data.name,
           "description": feature_data.description,
           "created_at": "2023-01-01T00:00:00",
           "updated_at": "2023-01-01T00:00:00",
       }

   @router.get("", response_model=List[FeatureResponse])
   async def list_features(
       skip: int = Query(0, ge=0),
       limit: int = Query(100, ge=1, le=100),
       current_user: dict = Depends(get_current_user),
       db: Session = Depends(get_db),
   ) -> Any:
       """
       List all features.
       """
       # Implementation will be added in service layer
       return []

   @router.get("/{feature_id}", response_model=FeatureResponse)
   async def get_feature(
       feature_id: UUID = Path(..., description="The ID of the feature to retrieve"),
       current_user: dict = Depends(get_current_user),
       db: Session = Depends(get_db),
   ) -> Any:
       """
       Get a specific feature by ID.
       """
       # Implementation will be added in service layer
       return {
           "id": feature_id,
           "name": "Sample Feature",
           "description": "This is a sample feature",
           "created_at": "2023-01-01T00:00:00",
           "updated_at": "2023-01-01T00:00:00",
       }
   ```

2. Update the module's `__init__.py` to expose your router:
   ```python
   # backend/src/api/routers/module_name/__init__.py
   from backend.src.api.routers.module_name.feature import router as feature_router
   ```

### Step 3: Register the Router in main.py

1. Import the new router in `backend/src/api/main.py`:
   ```python
   from backend.src.api.routers.module_name import feature
   ```

2. Include the router in the FastAPI app:
   ```python
   app.include_router(
       feature.router,
       prefix=f"{settings.API_V1_STR}/module-name",
       tags=["module-name"],
   )
   ```

## Working with Database Models

### Adding a New Model

1. Define your SQLAlchemy model in `backend/src/api/core/models.py`:
   ```python
   class Feature(Base):
       __tablename__ = "feature"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       name = Column(String, nullable=False)
       description = Column(Text, nullable=True)
       category_id = Column(UUID(as_uuid=True), ForeignKey("category.id"), nullable=False)
       created_at = Column(DateTime, default=func.now())
       updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
       
       # Relationships
       category = relationship("Category", back_populates="features")
   ```

2. Update any related models that might have relationships with your new model.

### Creating a Database Migration

1. Generate a new migration file:
   ```bash
   ./backend/start-dev.sh --exec backend alembic revision -m "add feature table"
   ```

2. Edit the generated migration file in `backend/migrations/versions/`:
   ```python
   def upgrade():
       op.create_table(
           'feature',
           sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
           sa.Column('name', sa.String(), nullable=False),
           sa.Column('description', sa.Text(), nullable=True),
           sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('category.id'), nullable=False),
           sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
           sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
           sa.PrimaryKeyConstraint('id')
       )

   def downgrade():
       op.drop_table('feature')
   ```

3. Apply the migration:
   ```bash
   ./backend/start-dev.sh --exec backend alembic upgrade head
   ```

### Modifying an Existing Model

1. Update the model in `backend/src/api/core/models.py` with your new field:
   ```python
   class Feature(Base):
       # Existing fields...
       is_active = Column(Boolean, nullable=False, default=True)
   ```

2. Generate a migration:
   ```bash
   ./backend/start-dev.sh --exec backend alembic revision -m "add is_active to feature"
   ```

3. Edit the migration file:
   ```python
   def upgrade():
       op.add_column('feature', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))

   def downgrade():
       op.drop_column('feature', 'is_active')
   ```

4. Apply the migration:
   ```bash
   ./backend/start-dev.sh --exec backend alembic upgrade head
   ```

## Creating Pydantic Schemas

### Best Practices for Schema Design

1. Create a base schema with common fields:
   ```python
   class FeatureBase(BaseModel):
       name: str
       description: Optional[str] = None
   ```

2. Create a schema for creation requests:
   ```python
   class FeatureCreate(FeatureBase):
       category_id: UUID
   ```

3. Create a schema for update requests:
   ```python
   class FeatureUpdate(BaseModel):
       name: Optional[str] = None
       description: Optional[str] = None
       is_active: Optional[bool] = None
   ```

4. Create a schema for responses:
   ```python
   class FeatureResponse(FeatureBase):
       id: UUID
       category_id: UUID
       is_active: bool
       created_at: datetime
       updated_at: datetime

       class Config:
           orm_mode = True  # Enables ORM mode for direct use with SQLAlchemy models
   ```

### Adding Validation

Use Pydantic's validation capabilities:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class FeatureCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    priority: int = Field(..., ge=1, le=5)
    
    @validator('name')
    def name_must_not_contain_special_chars(cls, v):
        if not all(c.isalnum() or c.isspace() or c == '-' for c in v):
            raise ValueError('Name must only contain alphanumeric characters, spaces, or hyphens')
        return v
```

## API Documentation

### Documenting Endpoints

Use docstrings in your endpoint functions for automatic API documentation:

```python
@router.post("", response_model=FeatureResponse, status_code=201)
async def create_feature(
    feature_data: FeatureCreate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new feature.

    This endpoint allows users to create a new feature with the provided data.
    The user must be authenticated to access this endpoint.

    Parameters:
    - **feature_data**: The data needed to create a new feature
    
    Returns:
    - **FeatureResponse**: The created feature with its ID and timestamps
    """
    # Implementation
```

### Customizing OpenAPI Documentation

Add tags and descriptions in `main.py`:

```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="API for the GET INN Restaurant Platform",
    version="1.0.0",
)

# Add tag metadata
app.openapi_tags = [
    {
        "name": "module-name",
        "description": "Operations related to feature management",
        "externalDocs": {
            "description": "Feature management documentation",
            "url": "https://docs.example.com/features/",
        },
    },
]
```

## Authentication and Authorization

### Adding Authentication to an Endpoint

Use the `get_current_user` dependency:

```python
from backend.src.api.dependencies.auth import get_current_user

@router.get("", response_model=List[FeatureResponse])
async def list_features(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """List all features."""
    # Implementation
```

### Role-Based Authorization

Use the `check_role` dependency:

```python
from backend.src.api.dependencies.auth import check_role
from backend.src.api.schemas.auth_schemas import UserRole

@router.post("", response_model=FeatureResponse, status_code=201)
async def create_feature(
    feature_data: FeatureCreate = Body(...),
    current_user: dict = Depends(check_role([UserRole.ADMIN, UserRole.MANAGER])),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new feature."""
    # Implementation
```

## WebSocket Development

### Creating a WebSocket Endpoint

1. Define the WebSocket endpoint in your router file:
   ```python
   @router.websocket("/ws/{client_id}")
   async def websocket_endpoint(
       websocket: WebSocket,
       client_id: str,
   ):
       connection_manager = get_connection_manager()
       await connection_manager.connect(websocket, f"client_{client_id}")
       
       try:
           # Send initial message
           await websocket.send_json({"status": "connected", "client_id": client_id})
           
           # Keep connection and handle messages
           while True:
               data = await websocket.receive_text()
               # Process received data
               await websocket.send_json({"status": "message_received", "data": data})
       except WebSocketDisconnect:
           connection_manager.disconnect(websocket, f"client_{client_id}")
   ```

### Broadcasting Messages

Use the connection manager to broadcast messages to clients:

```python
# In a service function or API endpoint
async def notify_feature_update(feature_id: str, data: dict):
    connection_manager = get_connection_manager()
    await connection_manager.broadcast(
        f"feature_{feature_id}",
        {"event": "feature_updated", "data": data}
    )
```

## Background Tasks

### Creating a Celery Task

1. Define the task in `backend/src/worker/tasks/`:
   ```python
   # backend/src/worker/tasks/module_name/feature_tasks.py
   from celery import shared_task
   from backend.src.worker.celery_app import app

   @app.task
   def process_feature(feature_id: str):
       # Task implementation
       return {"status": "completed", "feature_id": feature_id}
   ```

### Triggering Tasks from API Endpoints

```python
@router.post("/{feature_id}/process")
async def process_feature(
    feature_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Start processing a feature."""
    # Trigger background task
    from backend.src.worker.tasks.module_name.feature_tasks import process_feature
    task = process_feature.delay(str(feature_id))
    
    return {"status": "processing_started", "task_id": task.id}
```

## Testing

### Writing Unit Tests

Create test files in `backend/tests/unit/`:

```python
# backend/tests/unit/test_feature.py
import pytest
from uuid import uuid4
from backend.src.api.schemas.module_name import FeatureCreate, FeatureResponse
# Import the service you want to test

def test_create_feature():
    # Arrange
    feature_data = FeatureCreate(name="Test Feature", category_id=uuid4())
    
    # Act
    # Call your service function
    
    # Assert
    # Check the result
```

### Running Tests

```bash
# Run all tests
./backend/start-dev.sh --exec backend pytest

# Run specific test file
./backend/start-dev.sh --exec backend pytest tests/unit/test_feature.py

# Run with coverage
./backend/start-dev.sh --exec backend pytest --cov=backend
```

## Common Issues and Solutions

### Database Migration Issues

- **Issue**: Migration fails with "Table already exists"
  **Solution**: Make sure your migration isn't trying to create a table that already exists. Check previous migrations.

- **Issue**: Changes not reflected in database
  **Solution**: Make sure you've run `alembic upgrade head` after creating your migration.

### API Endpoint Issues

- **Issue**: 422 Unprocessable Entity errors
  **Solution**: Check your request body against the Pydantic schema. Ensure all required fields are provided and in the correct format.

- **Issue**: 401 Unauthorized errors
  **Solution**: Ensure your authentication token is valid and properly included in the Authorization header.

### Docker Issues

- **Issue**: Changes not reflected in the running container
  **Solution**: In development mode, the code should auto-reload. If not, try restarting the container: `./backend/start-dev.sh --build`

- **Issue**: Database connection errors
  **Solution**: Check that the database container is running and that the connection settings are correct.