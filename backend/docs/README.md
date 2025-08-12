# GET INN Restaurant Platform Documentation

Welcome to the GET INN Restaurant Platform documentation. This repository contains comprehensive documentation for the backend services that power the AI-driven restaurant management platform.

## Documentation Structure

### Getting Started
- [Installation Guide](getting-started/installation.md) - Setup and installation instructions
- [Development Environment](getting-started/development-environment.md) - Local development configuration
- [Testing](getting-started/testing.md) - Testing strategy and commands

### Architecture
- [Project Structure](architecture/project-structure.md) - Overview of the codebase organization
- [Database Schema](architecture/database-schema.md) - Database models and relationships
- [API Structure](architecture/api-structure.md) - API design and patterns

### Modules

#### Bot Management
- [Overview](modules/bot-management/overview.md) - Comprehensive bot management system overview and architecture
- [MediaManager](modules/bot-management/media-manager.md) - Dedicated media processing component (NEW)
- [Input Validation Overview](modules/bot-management/input-validation-overview.md) - User-friendly overview of input validation features (NEW)
- [Input Validation Spec](modules/bot-management/input-validation-spec.md) - Technical specification for input validation system (NEW)
- [Refactoring Plan](modules/bot-management/refactoring-plan.md) - System refactoring achievements and status
- [API Reference](modules/bot-management/api-reference.md) - Complete API documentation for bot management
- [Scenario Format](modules/bot-management/scenario-format.md) - Bot scenario specification and examples
- [Auto-Transitions](modules/bot-management/auto-transitions.md) - Automatic conversation flow control
- [Media System](modules/bot-management/media-system.md) - Rich media handling and processing
- [Webhook Management](modules/bot-management/webhook-management.md) - Platform webhook integration
- [Conversation Logging](modules/bot-management/conversation-logging.md) - Logging and debugging system

#### AI Tools
- [Azure OpenAI](modules/ai-tools/azure-openai.md) - Azure OpenAI integration
- [Document Processing](modules/ai-tools/document-processing.md) - AI document processing pipeline

#### Integrations
- [iiko Integration](modules/integrations/iiko.md) - iiko POS/ERP system integration
- [Telegram Integration](modules/integrations/telegram.md) - Telegram bot platform integration

### Development Guides
- [Creating API Endpoints](guides/creating-api-endpoints.md) - How to add new API endpoints
- [Database Migrations](guides/database-migrations.md) - Working with database migrations
- [Adding Bot Features](guides/adding-bot-features.md) - Implementing new bot functionality

## Recent Improvements (2025)

The bot management system has undergone comprehensive refactoring with significant architectural improvements:

- ✅ **MediaManager Extraction**: Dedicated media processing component extracted from DialogManager
- ✅ **Code Reduction**: DialogManager reduced by 37% (1,403 → 882 lines)
- ✅ **Input Validation System**: Comprehensive validation preventing duplicate clicks and invalid inputs with Redis-backed rate limiting
- ✅ **Shared Utilities**: Permission system, error handlers, and validation utilities eliminate 200+ lines of duplicate code
- ✅ **Enhanced Architecture**: Better separation of concerns and improved maintainability
- ✅ **Production Stability**: All critical bugs fixed and full test coverage maintained

For complete details, see the [Bot Management Refactoring Plan](modules/bot-management/refactoring-plan.md).

## Additional Resources

- [Documentation Refactoring Plan](documentation_refactoring_plan.md) - Plan for the documentation restructuring

---

**Note:** This documentation is under active development and continuously updated to reflect the latest architectural improvements.