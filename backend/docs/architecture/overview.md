# Architecture Overview

This section provides an overview of the GET INN Restaurant Platform architecture and design principles.

## System Architecture

The GET INN Restaurant Platform is built on a modern, microservices-inspired architecture designed for scalability, maintainability, and restaurant operations efficiency.

```{mermaid}
graph TB
    subgraph "Frontend Layer"
        WEB[Web Dashboard]
        MOBILE[Mobile Apps]
        BOTS[Chat Bots]
    end
    
    subgraph "API Gateway"
        FASTAPI[FastAPI Backend]
    end
    
    subgraph "Core Services"
        BOT[Bot Management]
        LABOR[Labor Management]
        SUPPLIER[Supplier Management]
        INTEGRATIONS[Integration Layer]
    end
    
    subgraph "External Services"
        TELEGRAM[Telegram]
        WHATSAPP[WhatsApp]
        IIKO[iiko POS]
        AZURE[Azure OpenAI]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis Cache)]
        CELERY[Celery Workers]
    end
    
    WEB --> FASTAPI
    MOBILE --> FASTAPI
    BOTS --> FASTAPI
    
    FASTAPI --> BOT
    FASTAPI --> LABOR
    FASTAPI --> SUPPLIER
    FASTAPI --> INTEGRATIONS
    
    BOT --> TELEGRAM
    BOT --> WHATSAPP
    INTEGRATIONS --> IIKO
    INTEGRATIONS --> AZURE
    
    FASTAPI --> POSTGRES
    FASTAPI --> REDIS
    FASTAPI --> CELERY
```

## Key Design Principles

**Domain-Driven Design**
: The codebase is organized around business domains (bots, labor, supplier) rather than technical layers.

**API-First Architecture**
: All functionality is exposed through well-defined REST APIs with comprehensive documentation.

**Asynchronous Processing**
: Background tasks and external integrations use async patterns for better performance.

**Multi-Platform Support**
: Bot system designed to work across multiple messaging platforms with unified interfaces.

**Modular Integration Layer**
: External systems (POS, AI services) integrated through pluggable adapters.

## Technology Stack

**Backend Framework**
- FastAPI with Python 3.9+
- SQLAlchemy ORM for database operations
- Pydantic for data validation

**Database & Caching**
- PostgreSQL for primary data storage
- Redis for caching and session management

**Background Processing**
- Celery for async task processing
- Redis as message broker

**External Integrations**
- Azure OpenAI for AI capabilities
- Telegram Bot API
- WhatsApp Business API
- iiko POS system integration

**Development & Deployment**
- Docker for containerization
- Alembic for database migrations
- Pytest for testing