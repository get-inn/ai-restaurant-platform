# Backend API Enhancements for ЧиХо Onboarding Bot

This document outlines the necessary enhancements to the existing GET INN backend API to support the Telegram onboarding bot functionality.

## 1. Overview

The current backend architecture includes basic labor/onboarding functionality, but requires specific extensions to fully support the Telegram bot integration. These enhancements will focus on:

1. New API endpoints specific to the Telegram bot workflow
2. Database model extensions to support additional data requirements
3. Service layer modifications to handle Telegram-specific functionality

## 2. Database Model Extensions

### 2.1. StaffOnboarding Model Extensions

Add the following fields to the existing `StaffOnboarding` model:

```python
# Extend db/models/labor/onboarding.py

class StaffOnboarding(Base):
    """Staff onboarding record"""
    __tablename__ = "staff_onboarding"
    
    # Existing fields...
    
    # New fields
    telegram_id = Column(String, nullable=True, index=True)  # Telegram user ID
    phone_number = Column(String, nullable=True)  # Contact phone number
    first_shift_datetime = Column(DateTime, nullable=True)  # First shift date and time
    citizenship = Column(String, nullable=True)  # Citizenship status
    onboarding_progress = Column(Integer, default=0)  # Progress percentage through onboarding
    last_interaction = Column(DateTime, default=func.now())  # Last bot interaction time
```

### 2.2. New OnboardingMaterial Model

Create a new model for storing onboarding materials:

```python
# Add to db/models/labor/onboarding.py

class MaterialType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    LINK = "link"

class OnboardingMaterial(Base):
    """Materials used in the onboarding process"""
    __tablename__ = "onboarding_materials"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    material_type = Column(Enum(MaterialType), nullable=False)
    file_path = Column(String, nullable=True)  # For stored files
    url = Column(String, nullable=True)  # For external resources
    content_category = Column(String, nullable=False)  # e.g., 'ideology', 'responsibilities'
    telegram_file_id = Column(String, nullable=True)  # Telegram's file_id for reuse
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 2.3. New SupportRequest Model

Create a model to track support requests:

```python
# Add to db/models/labor/onboarding.py

class SupportRequestStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

class SupportRequest(Base):
    """Support requests from onboarding employees"""
    __tablename__ = "support_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    staff_onboarding_id = Column(UUID(as_uuid=True), ForeignKey("staff_onboarding.id"), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum(SupportRequestStatus), default=SupportRequestStatus.PENDING)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    staff_onboarding = relationship("StaffOnboarding")
    assignee = relationship("User", foreign_keys=[assigned_to])
```

### 2.4. Menu System Model

Add model for the bot's menu system:

```python
# Add to db/models/labor/onboarding.py

class BotMenuOption(Base):
    """Menu options for the onboarding bot"""
    __tablename__ = "bot_menu_options"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("bot_menu_options.id"), nullable=True)
    action_type = Column(String, nullable=False)  # 'material', 'function', 'submenu'
    action_data = Column(JSONB, nullable=True)  # Content or function reference
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    parent = relationship("BotMenuOption", remote_side=[id], backref="children")
```

## 3. New API Endpoints

### 3.1. Telegram Onboarding Endpoints

#### 3.1.1. Create Onboarding from Telegram

```python
# In api/labor/onboarding.py

@router.post("/telegram", response_model=StaffOnboardingResponse)
async def create_telegram_onboarding(
    onboarding_data: TelegramOnboardingCreate,
    current_user: User = Depends(get_telegram_bot_user)
):
    """
    Create a new staff onboarding record from Telegram data.
    
    Parameters:
    - **onboarding_data**: Staff information collected via Telegram
    - **current_user**: Authenticated bot user (automatically injected)
    
    Returns:
    - **StaffOnboardingResponse**: Created staff onboarding record
    """
    # Implementation...
    return staff_onboarding
```

#### 3.1.2. Update Onboarding Progress

```python
@router.put("/telegram/{telegram_id}/progress", response_model=StaffOnboardingResponse)
async def update_onboarding_progress(
    telegram_id: str,
    progress_data: OnboardingProgressUpdate,
    current_user: User = Depends(get_telegram_bot_user)
):
    """Update onboarding progress for a Telegram user"""
    # Implementation...
    return updated_staff_onboarding
```

#### 3.1.3. Get Onboarding Status by Telegram ID

```python
@router.get("/telegram/{telegram_id}", response_model=StaffOnboardingResponse)
async def get_onboarding_by_telegram_id(
    telegram_id: str,
    current_user: User = Depends(get_telegram_bot_user)
):
    """Get onboarding record by Telegram ID"""
    # Implementation...
    return staff_onboarding
```

### 3.2. Project and Position Data Endpoints

#### 3.2.1. List Projects

```python
@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_telegram_bot_user)
):
    """
    Get list of available projects (restaurants) for onboarding.
    
    Returns:
    - List of projects with ID and name
    """
    # Implementation...
    return projects
```

#### 3.2.2. List Positions

```python
@router.get("/positions", response_model=List[PositionResponse])
async def list_positions(
    current_user: User = Depends(get_telegram_bot_user)
):
    """
    Get list of available positions for onboarding.
    
    Returns:
    - List of positions with ID and name
    """
    # Implementation...
    return positions
```

### 3.3. Onboarding Materials Endpoints

#### 3.3.1. Get Materials by Category

```python
@router.get("/materials/{category}", response_model=List[OnboardingMaterialResponse])
async def get_materials_by_category(
    category: str,
    current_user: User = Depends(get_telegram_bot_user)
):
    """
    Get onboarding materials by category.
    
    Parameters:
    - **category**: Material category (e.g., 'ideology', 'responsibilities')
    
    Returns:
    - List of materials in the specified category
    """
    # Implementation...
    return materials
```

#### 3.3.2. Get Material by ID

```python
@router.get("/materials/item/{material_id}", response_model=OnboardingMaterialResponse)
async def get_material_by_id(
    material_id: UUID,
    current_user: User = Depends(get_telegram_bot_user)
):
    """Get specific onboarding material by ID"""
    # Implementation...
    return material
```

### 3.4. Support Request Endpoints

#### 3.4.1. Create Support Request

```python
@router.post("/support", response_model=SupportRequestResponse)
async def create_support_request(
    support_data: SupportRequestCreate,
    current_user: User = Depends(get_telegram_bot_user)
):
    """
    Create a new support request from a Telegram user.
    
    Parameters:
    - **support_data**: Support request data with telegram_id and message
    
    Returns:
    - Created support request
    """
    # Implementation...
    return support_request
```

#### 3.4.2. Get Support Request Status

```python
@router.get("/support/{request_id}", response_model=SupportRequestResponse)
async def get_support_request(
    request_id: UUID,
    current_user: User = Depends(get_telegram_bot_user)
):
    """Get status of a support request"""
    # Implementation...
    return support_request
```

### 3.5. Bot Menu System Endpoints

#### 3.5.1. Get Menu Structure

```python
@router.get("/menu", response_model=List[MenuOptionResponse])
async def get_menu_structure(
    parent_id: UUID = None,
    current_user: User = Depends(get_telegram_bot_user)
):
    """
    Get bot menu structure, optionally filtered by parent menu item.
    
    Parameters:
    - **parent_id**: Optional parent menu item ID
    
    Returns:
    - List of menu options
    """
    # Implementation...
    return menu_options
```

## 4. Schema Definitions

### 4.1. Telegram Onboarding Schemas

```python
# In schemas/labor/onboarding.py

class TelegramOnboardingCreate(BaseModel):
    telegram_id: str
    first_name: str
    last_name: str
    position: str
    project: str
    first_shift_datetime: datetime
    citizenship: str
    
    class Config:
        schema_extra = {
            "example": {
                "telegram_id": "123456789",
                "first_name": "Иван",
                "last_name": "Петров",
                "position": "Фуд-гид",
                "project": "Пятницкая",
                "first_shift_datetime": "2023-08-01T10:00:00",
                "citizenship": "РФ"
            }
        }

class OnboardingProgressUpdate(BaseModel):
    progress: int
    last_completed_step: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "progress": 50,
                "last_completed_step": "company_history"
            }
        }
```

### 4.2. Project and Position Schemas

```python
class ProjectResponse(BaseModel):
    id: UUID
    name: str
    
    class Config:
        orm_mode = True

class PositionResponse(BaseModel):
    id: UUID
    name: str
    
    class Config:
        orm_mode = True
```

### 4.3. Onboarding Material Schemas

```python
class OnboardingMaterialResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    material_type: str
    file_path: Optional[str]
    url: Optional[str]
    content_category: str
    telegram_file_id: Optional[str]
    
    class Config:
        orm_mode = True
```

### 4.4. Support Request Schemas

```python
class SupportRequestCreate(BaseModel):
    telegram_id: str
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "telegram_id": "123456789",
                "message": "У меня проблема с доступом к информации о компании."
            }
        }

class SupportRequestResponse(BaseModel):
    id: UUID
    message: str
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True
```

### 4.5. Menu Option Schemas

```python
class MenuOptionResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    parent_id: Optional[UUID]
    action_type: str
    action_data: Optional[Dict]
    display_order: int
    has_children: bool
    
    class Config:
        orm_mode = True
```

## 5. Service Layer Enhancements

### 5.1. Onboarding Service Extensions

```python
# In services/labor/onboarding_service.py

class OnboardingService:
    # Existing methods...
    
    async def create_from_telegram(self, db: Session, telegram_data: TelegramOnboardingCreate) -> StaffOnboarding:
        """Create new staff onboarding record from Telegram data"""
        # Implementation...
        
    async def get_by_telegram_id(self, db: Session, telegram_id: str) -> Optional[StaffOnboarding]:
        """Find onboarding record by Telegram ID"""
        # Implementation...
        
    async def update_progress(self, db: Session, telegram_id: str, progress_data: OnboardingProgressUpdate) -> StaffOnboarding:
        """Update onboarding progress"""
        # Implementation...
```

### 5.2. Material Service

```python
# Add to services/labor/material_service.py

class OnboardingMaterialService:
    async def get_by_category(self, db: Session, category: str) -> List[OnboardingMaterial]:
        """Get materials by category"""
        # Implementation...
        
    async def get_by_id(self, db: Session, material_id: UUID) -> Optional[OnboardingMaterial]:
        """Get material by ID"""
        # Implementation...
```

### 5.3. Support Service

```python
# Add to services/labor/support_service.py

class SupportService:
    async def create_request(self, db: Session, support_data: SupportRequestCreate) -> SupportRequest:
        """Create support request"""
        # Implementation...
        
    async def get_request(self, db: Session, request_id: UUID) -> Optional[SupportRequest]:
        """Get support request by ID"""
        # Implementation...
        
    async def assign_request(self, db: Session, request_id: UUID, user_id: UUID) -> SupportRequest:
        """Assign support request to staff member"""
        # Implementation...
        
    async def resolve_request(self, db: Session, request_id: UUID) -> SupportRequest:
        """Mark support request as resolved"""
        # Implementation...
```

### 5.4. Menu Service

```python
# Add to services/labor/menu_service.py

class MenuService:
    async def get_menu_structure(self, db: Session, parent_id: Optional[UUID] = None) -> List[BotMenuOption]:
        """Get menu structure, optionally filtered by parent"""
        # Implementation...
        
    async def get_menu_item(self, db: Session, item_id: UUID) -> Optional[BotMenuOption]:
        """Get specific menu item"""
        # Implementation...
```

## 6. Authentication and Security

### 6.1. Telegram Bot Authentication

Create a special authentication mechanism for the Telegram bot:

```python
# In core/security.py

def get_telegram_bot_token() -> str:
    """Get the bot's API token from environment variables"""
    return settings.TELEGRAM_BOT_TOKEN

async def get_telegram_bot_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Authenticate requests from the Telegram bot.
    
    This function verifies that the request is coming from the authorized bot
    and returns a service user account with appropriate permissions.
    """
    # Validate token
    try:
        payload = decode_token(token)
        if payload.get("bot_id") != settings.TELEGRAM_BOT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bot credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get bot service account
    db = SessionLocal()
    try:
        bot_user = db.query(User).filter(
            User.email == settings.TELEGRAM_BOT_SERVICE_EMAIL
        ).first()
        
        if bot_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bot service account not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return bot_user
    finally:
        db.close()
```

## 7. Configuration Updates

### 7.1. Environment Variables

Add the following environment variables to the application configuration:

```python
# In core/config.py

class Settings(BaseSettings):
    # Existing settings...
    
    # Telegram Bot settings
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_BOT_ID: str
    TELEGRAM_BOT_SERVICE_EMAIL: str = "telegram-bot@getinn.local"
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    
    # File storage for bot media
    BOT_MEDIA_STORAGE_PATH: str = "/app/media"
    
    class Config:
        env_file = ".env"
```

### 7.2. Dependency Injection Updates

Update dependency injection to include bot-specific dependencies:

```python
# In api/deps.py

def get_onboarding_service() -> OnboardingService:
    return OnboardingService()

def get_material_service() -> OnboardingMaterialService:
    return OnboardingMaterialService()

def get_support_service() -> SupportService:
    return SupportService()

def get_menu_service() -> MenuService:
    return MenuService()
```

## 8. Database Migration

Create a new Alembic migration to add the new tables and columns:

```python
"""Add Telegram bot support models

Revision ID: xyz123
Revises: abc456
Create Date: 2023-07-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

# revision identifiers, used by Alembic.
revision = 'xyz123'
down_revision = 'abc456'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add new columns to staff_onboarding table
    op.add_column('staff_onboarding', sa.Column('telegram_id', sa.String(), nullable=True, index=True))
    op.add_column('staff_onboarding', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('staff_onboarding', sa.Column('first_shift_datetime', sa.DateTime(), nullable=True))
    op.add_column('staff_onboarding', sa.Column('citizenship', sa.String(), nullable=True))
    op.add_column('staff_onboarding', sa.Column('onboarding_progress', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('staff_onboarding', sa.Column('last_interaction', sa.DateTime(), nullable=False, server_default=sa.text('now()')))
    
    # 2. Create onboarding_materials table
    op.create_table(
        'onboarding_materials',
        sa.Column('id', UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('material_type', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('content_category', sa.String(), nullable=False),
        sa.Column('telegram_file_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'))
    )
    
    # 3. Create support_requests table
    op.create_table(
        'support_requests',
        sa.Column('id', UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('staff_onboarding_id', UUID(), sa.ForeignKey('staff_onboarding.id'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('assigned_to', UUID(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'))
    )
    
    # 4. Create bot_menu_options table
    op.create_table(
        'bot_menu_options',
        sa.Column('id', UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', UUID(), sa.ForeignKey('bot_menu_options.id'), nullable=True),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('action_data', JSONB(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'))
    )


def downgrade():
    # Drop new tables
    op.drop_table('bot_menu_options')
    op.drop_table('support_requests')
    op.drop_table('onboarding_materials')
    
    # Remove columns from staff_onboarding
    op.drop_column('staff_onboarding', 'last_interaction')
    op.drop_column('staff_onboarding', 'onboarding_progress')
    op.drop_column('staff_onboarding', 'citizenship')
    op.drop_column('staff_onboarding', 'first_shift_datetime')
    op.drop_column('staff_onboarding', 'phone_number')
    op.drop_column('staff_onboarding', 'telegram_id')
```

## 9. Summary of Changes

The proposed enhancements to the backend API will provide:

1. **Telegram-Specific Endpoints**: Specialized endpoints for the Telegram bot to create and manage onboarding records
2. **Data Storage Extensions**: Additional fields and tables to store Telegram-specific data
3. **Material Management**: System for managing and retrieving onboarding media and documents
4. **Support Functionality**: Mechanism for handling user support requests
5. **Menu System**: Flexible menu structure for the bot's interface

These changes will enable seamless integration between the Telegram bot and the existing GET INN backend, ensuring proper data flow and storage for the onboarding process while maintaining the current system architecture.