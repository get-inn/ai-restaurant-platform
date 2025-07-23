# Database Schema

This document describes the database schema used in the GET INN Restaurant Platform.

## Overview

The platform uses PostgreSQL with SQLAlchemy as the ORM (Object-Relational Mapping) layer. All tables are created in a dedicated `getinn_ops` schema rather than the default `public` schema to isolate application tables.

## Schema Organization

### Core Entities

- **Account**: Represents restaurant chains or organizations
- **User**: User accounts with authentication information
- **Restaurant**: Individual restaurant locations
- **Store**: Physical inventory storage locations

### Feature-specific Entities

- **Bot Management**: Bot instances, platform credentials, scenarios, and dialog states
- **Supplier Management**: Suppliers, invoices, and procurement data
- **Labor Management**: Staff records and onboarding information
- **Chef Tools**: Menu items, recipes, and culinary data

## Database Tables

### Core Tables

#### Account

```sql
CREATE TABLE getinn_ops.account (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);
```

#### User

```sql
CREATE TABLE getinn_ops.user (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR NOT NULL UNIQUE,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    account_id UUID NOT NULL REFERENCES getinn_ops.account(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_superuser BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);
```

#### Restaurant

```sql
CREATE TABLE getinn_ops.restaurant (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES getinn_ops.account(id),
    name VARCHAR NOT NULL,
    address TEXT,
    phone VARCHAR,
    email VARCHAR,
    timezone VARCHAR,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    iiko_id VARCHAR,
    iiko_sync_status VARCHAR,
    iiko_last_synced_at TIMESTAMP WITHOUT TIME ZONE,
    iiko_sync_error VARCHAR
);
```

### Bot Management Tables

#### BotInstance

```sql
CREATE TABLE getinn_ops.bot_instance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES getinn_ops.account(id),
    name VARCHAR NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);
```

#### BotPlatformCredential

```sql
CREATE TABLE getinn_ops.bot_platform_credential (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_id UUID NOT NULL REFERENCES getinn_ops.bot_instance(id),
    platform VARCHAR NOT NULL,
    credentials JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    webhook_url VARCHAR,
    webhook_last_checked TIMESTAMP WITHOUT TIME ZONE,
    webhook_auto_refresh BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);
```

#### BotScenario

```sql
CREATE TABLE getinn_ops.bot_scenario (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_id UUID NOT NULL REFERENCES getinn_ops.bot_instance(id),
    name VARCHAR NOT NULL,
    description TEXT,
    scenario_data JSONB NOT NULL,
    version VARCHAR NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);
```

#### BotDialogState

```sql
CREATE TABLE getinn_ops.bot_dialog_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_id UUID NOT NULL REFERENCES getinn_ops.bot_instance(id),
    platform VARCHAR NOT NULL,
    platform_chat_id VARCHAR NOT NULL,
    current_step VARCHAR NOT NULL,
    collected_data JSONB NOT NULL DEFAULT '{}',
    last_interaction_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);
```

### Integration Tables

#### AccountIntegrationCredentials

```sql
CREATE TABLE getinn_ops.account_integration_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES getinn_ops.account(id),
    integration_type VARCHAR NOT NULL,
    credentials JSONB NOT NULL,
    base_url VARCHAR,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    last_connected_at TIMESTAMP WITHOUT TIME ZONE,
    connection_status VARCHAR,
    connection_error VARCHAR,
    CONSTRAINT uix_account_integration_type UNIQUE (account_id, integration_type)
);
```

## Entity Relationships

### Account-Related Relationships

```
Account
│
├── User (many)
│   
├── Restaurant (many)
│   
├── BotInstance (many)
│   
└── AccountIntegrationCredentials (many)
```

### Bot Management Relationships

```
BotInstance
│
├── BotPlatformCredential (many)
│
├── BotScenario (many)
│
└── BotDialogState (many)
```

## SQLAlchemy Models

### Core Models

```python
# src/api/models/core.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.api.core.database import Base
from src.api.core.config import settings

class Account(Base):
    __tablename__ = "account"
    __table_args__ = {"schema": settings.DATABASE_SCHEMA}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="account")
    restaurants = relationship("Restaurant", back_populates="account")
    bots = relationship("BotInstance", back_populates="account")
    integration_credentials = relationship("AccountIntegrationCredentials", back_populates="account")
```

### Bot Management Models

```python
# src/api/models/bots.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.api.core.database import Base
from src.api.core.config import settings
from src.api.models.core import Account

class BotInstance(Base):
    __tablename__ = "bot_instance"
    __table_args__ = {"schema": settings.DATABASE_SCHEMA}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.DATABASE_SCHEMA}.account.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="bots")
    platforms = relationship("BotPlatformCredential", back_populates="bot")
    scenarios = relationship("BotScenario", back_populates="bot")
    dialog_states = relationship("BotDialogState", back_populates="bot")

class BotPlatformCredential(Base):
    __tablename__ = "bot_platform_credential"
    __table_args__ = {"schema": settings.DATABASE_SCHEMA}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.DATABASE_SCHEMA}.bot_instance.id"), nullable=False)
    platform = Column(String, nullable=False)
    credentials = Column(JSONB, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    webhook_url = Column(String, nullable=True)
    webhook_last_checked = Column(DateTime, nullable=True)
    webhook_auto_refresh = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bot = relationship("BotInstance", back_populates="platforms")
```

## Schema Migration

The platform uses Alembic for database migrations:

```python
# migrations/env.py
import os
from alembic import context
from sqlalchemy import engine_from_config, pool, MetaData

# This is the Alembic Config object
config = context.config

# Get schema name from environment variable
schema = os.environ.get("DATABASE_SCHEMA", "getinn_ops")

# Set target metadata with schema
target_metadata = MetaData(schema=schema)
```

Migration example for adding webhook fields:

```python
# migrations/versions/webhook_fields_migration.py
def upgrade():
    op.add_column('bot_platform_credential', sa.Column('webhook_url', sa.String(), nullable=True), schema='getinn_ops')
    op.add_column('bot_platform_credential', sa.Column('webhook_last_checked', sa.DateTime(), nullable=True), schema='getinn_ops')
    op.add_column('bot_platform_credential', sa.Column('webhook_auto_refresh', sa.Boolean(), nullable=False, server_default='true'), schema='getinn_ops')

def downgrade():
    op.drop_column('bot_platform_credential', 'webhook_auto_refresh', schema='getinn_ops')
    op.drop_column('bot_platform_credential', 'webhook_last_checked', schema='getinn_ops')
    op.drop_column('bot_platform_credential', 'webhook_url', schema='getinn_ops')
```

## Database Connection

Connection settings are configured via environment variables:

```python
# src/api/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from src.api.core.config import settings

# Create SQLAlchemy engines
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
async_engine = create_async_engine(settings.ASYNC_DATABASE_URL, pool_pre_ping=True)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession)

# Create base class for ORM models
Base = declarative_base()
```

## External Integration Fields

For integration with external systems like iiko, models include additional fields:

```python
# Fields added to models for iiko integration
iiko_id = Column(String, nullable=True, index=True)
iiko_sync_status = Column(String, nullable=True)
iiko_last_synced_at = Column(DateTime, nullable=True)
iiko_sync_error = Column(String, nullable=True)
```

## Data Types

### Common Data Types

| PostgreSQL Type | SQLAlchemy Type | Python Type | Description |
|----------------|-----------------|------------|-------------|
| uuid | UUID(as_uuid=True) | UUID | Unique identifiers |
| varchar | String | str | Text strings |
| text | Text | str | Longer text content |
| boolean | Boolean | bool | True/false values |
| timestamp | DateTime | datetime | Date and time values |
| jsonb | JSONB | dict | JSON data with binary storage |

### Special Types

- **JSONB**: Used for structured data storage (like bot scenario data, credentials)
- **UUID**: Used for primary keys and foreign keys
- **Enum**: Used for status fields with predefined values

## Indexes and Constraints

### Primary Keys

All tables use UUID primary keys with the uuid_generate_v4() function as the default value.

### Foreign Keys

Foreign keys enforce referential integrity between related tables.

### Unique Constraints

```sql
-- Example unique constraint
CONSTRAINT uix_account_integration_type UNIQUE (account_id, integration_type)
```

### Indexes

Indexes are created for frequently queried columns:

```sql
-- Example indexes
CREATE INDEX ix_bot_dialog_state_bot_id ON getinn_ops.bot_dialog_state(bot_id);
CREATE INDEX ix_bot_dialog_state_platform_chat_id ON getinn_ops.bot_dialog_state(platform_chat_id);
CREATE INDEX ix_restaurant_iiko_id ON getinn_ops.restaurant(iiko_id);
```

## Schema Notes

- All tables include `created_at` and `updated_at` timestamp columns for auditing
- Most tables include an `is_active` boolean flag for soft deletion
- External system IDs (like `iiko_id`) are included in relevant tables for integration
- Credentials and other sensitive data are stored in JSONB columns for flexibility