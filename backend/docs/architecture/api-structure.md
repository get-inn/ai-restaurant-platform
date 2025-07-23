# API Structure

This document outlines the API structure and design patterns used in the GET INN Restaurant Platform.

## API Organization

The API follows a structured, domain-driven organization with consistent patterns.

### Base URL

The API base URL follows this pattern:

```
/v1/api/[domain]/[resource]
```

Where:
- `v1` represents the API version
- `api` is a fixed part of the path
- `domain` represents the functional domain (e.g., bots, chef, labor)
- `resource` represents the specific resource within that domain

### Domains

The API is organized into the following primary domains:

| Domain | Description | Base Path |
|--------|-------------|-----------|
| Authentication | User authentication and authorization | `/v1/api/auth` |
| Accounts | Account management | `/v1/api/accounts` |
| Bots | Bot management and conversation | `/v1/api/bots` |
| Chef | Menu and recipe management | `/v1/api/chef` |
| Labor | Staff management | `/v1/api/labor` |
| Supplier | Supplier and procurement | `/v1/api/supplier` |
| Webhooks | External system notifications | `/v1/api/webhooks` |
| Integrations | External system connections | `/v1/api/integrations` |

### Resource Patterns

Resources follow RESTful patterns with standardized endpoints:

| Method | Path | Description | Response Code |
|--------|------|-------------|---------------|
| GET | `/{resource}` | List resources | 200 |
| POST | `/{resource}` | Create resource | 201 |
| GET | `/{resource}/{id}` | Get single resource | 200 |
| PUT | `/{resource}/{id}` | Update resource | 200 |
| DELETE | `/{resource}/{id}` | Delete resource | 204 |
| POST | `/{resource}/{id}/{action}` | Perform action on resource | 200 |

### Nested Resources

For resources that are logically nested:

```
/v1/api/accounts/{account_id}/bots
/v1/api/bots/{bot_id}/platforms
/v1/api/bots/{bot_id}/scenarios
```

## API Implementation

### Router Structure

API endpoints are implemented using FastAPI routers:

```python
# src/api/routers/bots/instances.py
from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from src.api.dependencies.db import get_db
from src.api.dependencies.auth import get_current_user
from src.api.schemas.bots import BotInstanceCreate, BotInstanceResponse
from src.api.services.bots.instance_service import BotInstanceService

router = APIRouter()

@router.post("", response_model=BotInstanceResponse, status_code=201)
async def create_bot(
    bot_data: BotInstanceCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new bot instance."""
    service = BotInstanceService(db)
    return service.create_bot(bot_data, current_user["account_id"])

@router.get("", response_model=List[BotInstanceResponse])
async def list_bots(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all bot instances."""
    service = BotInstanceService(db)
    return service.list_bots(current_user["account_id"], skip=skip, limit=limit)
```

### Router Registration

Routers are registered in the main FastAPI application:

```python
# src/api/main.py
from fastapi import FastAPI
from src.api.core.config import settings
from src.api.routers import bots, chef, labor, supplier, webhooks, auth

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for the GET INN Restaurant Platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["auth"])
app.include_router(bots.router, prefix=f"{settings.API_V1_STR}/bots", tags=["bots"])
app.include_router(chef.router, prefix=f"{settings.API_V1_STR}/chef", tags=["chef"])
app.include_router(labor.router, prefix=f"{settings.API_V1_STR}/labor", tags=["labor"])
app.include_router(supplier.router, prefix=f"{settings.API_V1_STR}/supplier", tags=["supplier"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_STR}/webhooks", tags=["webhooks"])
```

## Data Models and Schemas

### Database Models

Database models use SQLAlchemy ORM:

```python
# src/api/models/bots.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.api.core.database import Base
from src.api.core.config import settings

class BotInstance(Base):
    __tablename__ = "bot_instance"
    __table_args__ = {"schema": settings.DATABASE_SCHEMA}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.DATABASE_SCHEMA}.account.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    platforms = relationship("BotPlatformCredential", back_populates="bot")
    scenarios = relationship("BotScenario", back_populates="bot")
```

### Pydantic Schemas

Request/response schemas use Pydantic:

```python
# src/api/schemas/bots/instance_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class BotInstanceBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class BotInstanceCreate(BotInstanceBase):
    account_id: Optional[UUID] = None

class BotInstanceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class BotInstanceResponse(BotInstanceBase):
    id: UUID
    account_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## API Dependencies

### Database Session

```python
# src/api/dependencies/db.py
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.database import SessionLocal, AsyncSessionLocal

def get_db():
    """
    Dependency for getting a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """
    Dependency for getting an async database session.
    """
    async with AsyncSessionLocal() as session:
        yield session
```

### Authentication

```python
# src/api/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from typing import Optional, List

from src.api.core.config import settings
from src.api.schemas.auth_schemas import TokenPayload, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validate access token and return current user.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return user info from token
    return {
        "id": token_data.sub,
        "email": token_data.email,
        "account_id": token_data.account_id,
        "roles": token_data.roles,
    }

def check_role(allowed_roles: List[UserRole]):
    """
    Dependency for checking user roles.
    """
    async def authorize(current_user: dict = Depends(get_current_user)):
        for role in current_user.get("roles", []):
            if role in allowed_roles:
                return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return authorize
```

## Service Layer

Services implement business logic:

```python
# src/api/services/bots/instance_service.py
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.api.models.bots import BotInstance as BotInstanceDB
from src.api.schemas.bots import BotInstanceCreate, BotInstanceUpdate, BotInstanceResponse

class BotInstanceService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_bot(self, data: BotInstanceCreate, account_id: UUID) -> Dict[str, Any]:
        """Create a new bot instance."""
        db_bot = BotInstanceDB(
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            account_id=account_id
        )
        self.db.add(db_bot)
        self.db.commit()
        self.db.refresh(db_bot)
        
        # Convert to Pydantic model
        return BotInstanceResponse.model_validate(db_bot)
    
    def list_bots(self, account_id: UUID, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List bot instances for an account."""
        db_bots = self.db.query(BotInstanceDB).filter(
            BotInstanceDB.account_id == account_id
        ).offset(skip).limit(limit).all()
        
        # Convert to Pydantic models
        return [BotInstanceResponse.model_validate(db_bot) for db_bot in db_bots]
```

## API Documentation

### OpenAPI Schema

The API documentation is automatically generated using FastAPI's built-in OpenAPI support and is available at:

```
http://localhost:8000/docs
```

### Documentation Configuration

```python
# src/api/main.py
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for the GET INN Restaurant Platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# OpenAPI Tags
app.openapi_tags = [
    {
        "name": "auth",
        "description": "Authentication and authorization operations",
    },
    {
        "name": "bots",
        "description": "Bot management operations",
    },
    # Additional tags...
]
```

### Docstrings

Endpoint functions include descriptive docstrings that are used in the OpenAPI documentation:

```python
@router.post("", response_model=BotInstanceResponse, status_code=201)
async def create_bot(
    bot_data: BotInstanceCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new bot instance.
    
    Creates a bot with the provided name and description, associated with the current user's account.
    
    Returns the created bot instance with its generated ID and timestamps.
    """
    service = BotInstanceService(db)
    return service.create_bot(bot_data, current_user["account_id"])
```

## Error Handling

### HTTP Exceptions

```python
from fastapi import HTTPException, status

# Raise a 404 Not Found exception
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Bot not found"
)

# Raise a 403 Forbidden exception
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not authorized to access this resource"
)
```

### Custom Exception Handlers

```python
# src/api/core/exceptions.py
from fastapi import Request, status
from fastapi.responses import JSONResponse

class DatabaseError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

async def database_exception_handler(request: Request, exc: DatabaseError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.detail},
    )

# Register in main.py
app.add_exception_handler(DatabaseError, database_exception_handler)
```

## WebSocket Support

For real-time communication:

```python
# src/api/routers/websockets.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict

router = APIRouter()

# Store active connections
connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    connections[client_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            # Process data
            await websocket.send_json({"message": "Received", "data": data})
    except WebSocketDisconnect:
        # Handle disconnect
        if client_id in connections:
            del connections[client_id]
```

## Best Practices

1. **Consistent Path Structure**: Use consistent path patterns for all endpoints
2. **Pydantic Models**: Use Pydantic for request/response validation
3. **Service Layer**: Implement business logic in service classes
4. **Dependency Injection**: Use FastAPI's dependency injection for common dependencies
5. **Clear Documentation**: Provide clear docstrings for all endpoints
6. **Proper Status Codes**: Use appropriate HTTP status codes for responses
7. **Consistent Response Format**: Maintain consistent response structures
8. **Pagination**: Implement pagination for list endpoints
9. **Role-Based Authorization**: Use role-based access control
10. **Input Validation**: Validate all inputs using Pydantic models