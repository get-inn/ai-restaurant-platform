# GET INN Restaurant Platform Backend

This is the backend service for the GET INN Restaurant Platform, a system that creates self-operating restaurants using AI agents.

## Features

- **AI Supplier**: Management interface for procurement, reconciliation, and inventory tracking
- **AI Labor**: Interface for staff management, focused on onboarding processes
- **AI Chef**: Tools for menu analysis, recipe management, and insights
- **Document Recognition**: AI-powered document processing using Azure OpenAI integration
- **Bot Management**: Conversation-based interfaces with detailed logging for debugging

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Getting Started](docs/getting-started/installation.md)**: Installation and setup guides
- **[Architecture](docs/architecture/project-structure.md)**: System architecture and design
- **[Module Documentation](docs/modules/)**: Details on specific system modules
- **[Development Guides](docs/guides/)**: How-to guides for common tasks

For a complete overview of available documentation, see the [Documentation Index](docs/README.md).

## Quick Start

### Development Environment

Use the `start-dev.sh` script to manage the development environment:

```bash
# Start all services in Docker
./start-dev.sh --build --migrate

# Run API locally with other services in Docker
./start-dev.sh --local-api

# Stop all services
./start-dev.sh --down
```

### Testing

Run tests using the `run_tests.sh` script:

```bash
# Run all tests locally
./run_tests.sh -l

# Run specific tests
./run_tests.sh -l -k "test_name"

# Run with coverage report
./run_tests.sh -l -c
```

## Key Components

### Bot Management System

The platform includes a comprehensive bot management system with:

- Multi-platform support (Telegram, etc.)
- Scenario-based dialog flows
- Automatic webhook management
- Detailed conversation logging

For bot conversation logs, use:
```bash
python -m scripts.bots.utils.view_bot_logs --bot-id BOT_ID
```

For more details, see the [Bot Management Documentation](docs/modules/bot-management/overview.md).

### Azure OpenAI Integration

The platform integrates with Azure OpenAI for document processing using a 3-stage pipeline:

1. **Classification**: Determine document type
2. **Field Extraction**: Extract structured data
3. **Validation**: Validate and enrich data

For more information, see the [Azure OpenAI Integration Guide](docs/modules/ai-tools/azure-openai.md) and [Document Processing Pipeline](docs/modules/ai-tools/document-processing.md).

### Database Schema

The application uses a dedicated PostgreSQL schema named `getinn_ops` instead of the default `public` schema:

```yaml
environment:
  - DATABASE_URL=postgresql://postgres:postgres@db:5432/restaurant
  - DATABASE_SCHEMA=getinn_ops
```

For database migration information, see the [Database Migrations Guide](docs/guides/database-migrations.md).

## Environment Variables

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_SCHEMA` | PostgreSQL schema name | `getinn_ops` |
| `AZURE_OPENAI_ENABLED` | Enable Azure OpenAI integration | `false` |
| `BOT_LOG_LEVEL` | Bot logging level | `INFO` |
| `USE_NGROK` | Use ngrok for local webhooks | `false` |

For a complete list of environment variables, see the installation guide.

## External Integrations

- **Telegram**: Bot platform for conversation interfaces
- **iiko**: POS/ERP system integration
- **Azure OpenAI**: AI service for document processing

For integration-specific details, see the respective documentation in the [Integrations Module](docs/modules/integrations/).

## Contributing

When contributing to this project:

1. Follow the project structure described in [Project Structure](docs/architecture/project-structure.md)
2. Use the [API Structure](docs/architecture/api-structure.md) guidelines for new endpoints
3. Create database migrations as described in [Database Migrations](docs/guides/database-migrations.md)
4. Update documentation when adding new features or making significant changes

## Pydantic V2 Migration

This project is being migrated from Pydantic V1 to V2. When working with Pydantic models:

1. Use `from_attributes = True` instead of `orm_mode = True` in Config classes
2. Use `model_validate()` instead of `from_orm()` for converting ORM models to Pydantic models
3. Use `model_dump()` instead of `dict()` for converting Pydantic models to dictionaries