# Project Structure

This document describes the overall structure of the GET INN Restaurant Platform backend codebase.

## Directory Structure

```
/backend/
├── docker/                # Docker configuration files
├── docs/                  # Project documentation
├── logs/                  # Log output directory
├── migrations/            # Database migration files
│   └── versions/          # Individual migration scripts
├── src/                   # Source code
│   ├── api/               # FastAPI application
│   │   ├── core/          # Core functionality and models
│   │   │   └── seed/      # Database seed data
│   │   ├── dependencies/  # FastAPI dependencies
│   │   ├── models/        # Database models
│   │   ├── routers/       # API route definitions
│   │   │   ├── bots/      # Bot management endpoints
│   │   │   ├── chef/      # Chef module endpoints
│   │   │   ├── integrations/ # Integration endpoints
│   │   │   ├── labor/     # Labor management endpoints
│   │   │   ├── supplier/  # Supplier module endpoints
│   │   │   └── webhooks/  # Webhook handlers
│   │   ├── schemas/       # Pydantic schemas for data validation
│   │   ├── services/      # Business logic services
│   │   ├── tests/         # API tests
│   │   │   ├── fixtures/  # Test fixtures
│   │   │   ├── integration/ # Integration tests
│   │   │   ├── simplified/ # Simplified tests
│   │   │   ├── standalone/ # Standalone tests
│   │   │   └── unit/      # Unit tests
│   │   └── utils/         # Utility functions
│   ├── bot_manager/       # Bot management system
│   ├── integrations/      # External integrations
│   │   ├── ai_tools/      # AI service integrations
│   │   │   └── azure_openai/ # Azure OpenAI integration
│   │   ├── llm/           # Language model abstractions
│   │   ├── platforms/     # Messaging platform adapters
│   │   └── pos_erp_adapters/ # POS/ERP system adapters
│   └── worker/            # Background worker processes
│       └── tasks/         # Celery tasks
└── tests/                 # Project-level tests
```

## Key Components

### API Layer (`src/api/`)

The API layer is built with FastAPI and follows a structured approach:

- **core/**: Core functionality including configuration, database models, and application setup
- **dependencies/**: FastAPI dependency injection for database sessions, authentication, etc.
- **models/**: SQLAlchemy ORM models for database tables
- **routers/**: API endpoints organized by domain/feature
- **schemas/**: Pydantic models for request/response validation
- **services/**: Business logic implementation
- **tests/**: Test suite organized by test type
- **utils/**: Helper functions and utilities

### Bot Management System (`src/bot_manager/`)

The bot management system handles chat bot interactions across multiple messaging platforms:

- Dialog management
- State management
- Scenario execution
- Cross-platform adapters

### Integrations (`src/integrations/`)

Integrations with external systems and services:

- **ai_tools/**: AI services like Azure OpenAI
- **llm/**: Language model abstractions and interfaces
- **platforms/**: Messaging platform adapters (Telegram, etc.)
- **pos_erp_adapters/**: POS/ERP system integrations (iiko, etc.)

### Background Worker (`src/worker/`)

Celery-based background task processing:

- **tasks/**: Organized task definitions
- Scheduled jobs
- Asynchronous processing

## Domain Organization

The codebase is organized by domain/feature areas:

- **bots/**: Bot management and conversation interfaces
- **chef/**: Restaurant chef tools and menu management
- **labor/**: Staff management and onboarding
- **supplier/**: Procurement, reconciliation, and inventory
- **integrations/**: External system connections
- **webhooks/**: Webhook handlers for real-time updates

Each domain typically has corresponding routers, schemas, services, and tests that follow the same naming convention.

## Testing Structure

Tests are organized by type:

- **unit/**: Testing individual components in isolation
- **integration/**: Testing interactions between components
- **simplified/**: Streamlined tests for common patterns
- **standalone/**: Self-contained tests for specific features
- **fixtures/**: Reusable test fixtures and data

## Database Migrations

Database schema changes are managed with Alembic:

- `migrations/versions/`: Individual migration scripts
- Schema changes are version-controlled
- Migrations can be applied or rolled back

## Docker Configuration

The application uses Docker for development, testing, and deployment:

- `docker/`: Contains Docker-related configuration files
- `docker-compose.yml`: Main Docker Compose configuration
- Custom Dockerfiles for specific environments