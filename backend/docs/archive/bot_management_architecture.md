# Bot Management System Architecture

## 1. Architecture Overview

The bot management system is built on the following core components:

1. **Bot Core Management System** - FastAPI application that manages all bots
2. **Dialog Manager** - module responsible for storing and executing scenarios
3. **Messenger Adapters** - integrations with different platforms (Telegram, WhatsApp, etc.)
4. **Dialog State Storage** - ensuring dialog persistence
5. **Media Storage** - for working with images and videos
6. **LLM Integration Component** - for future expansion of capabilities

## 2. Database Schema

### 2.1. Bot Management

```python
class BotInstance(Base):
    __tablename__ = "bot_instance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)  # Links to account (restaurant chain)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BotPlatformCredential(Base):
    __tablename__ = "bot_platform_credential"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    platform = Column(String, nullable=False)  # 'telegram', 'whatsapp', 'viber', etc.
    credentials = Column(JSONB, nullable=False)  # tokens and platform-specific settings
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BotScenario(Base):
    __tablename__ = "bot_scenario"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    scenario_data = Column(JSONB, nullable=False)  # full scenario structure
    version = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 2.2. Dialog State Management

```python
class BotDialogState(Base):
    __tablename__ = "bot_dialog_state"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    platform = Column(String, nullable=False)  # 'telegram', 'whatsapp', 'viber', etc.
    platform_chat_id = Column(String, nullable=False)  # Chat ID in the specific platform
    current_step = Column(String, nullable=False)  # current scenario step
    collected_data = Column(JSONB, nullable=False, default={})  # collected data
    last_interaction_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BotDialogHistory(Base):
    __tablename__ = "bot_dialog_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dialog_state_id = Column(UUID(as_uuid=True), ForeignKey("bot_dialog_state.id"), nullable=False)
    message_type = Column(String, nullable=False)  # 'user', 'bot'
    message_data = Column(JSONB, nullable=False)  # message content and metadata
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
```

### 2.3. Media Management

```python
class BotMediaFile(Base):
    __tablename__ = "bot_media_file"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    file_type = Column(String, nullable=False)  # 'image', 'video', etc.
    file_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    platform_file_ids = Column(JSONB, nullable=True)  # Map of platform -> file_id
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

## 3. API Endpoints

```
# Bot Management
GET /api/accounts/{account_id}/bots
POST /api/accounts/{account_id}/bots
GET /api/bots/{id}
PUT /api/bots/{id}
DELETE /api/bots/{id}
POST /api/bots/{id}/activate
POST /api/bots/{id}/deactivate

# Bot Platform Credentials
GET /api/bots/{bot_id}/platforms
POST /api/bots/{bot_id}/platforms
GET /api/bots/{bot_id}/platforms/{platform}
PUT /api/bots/{bot_id}/platforms/{platform}
DELETE /api/bots/{bot_id}/platforms/{platform}

# Scenario Management
GET /api/bots/{bot_id}/scenarios
POST /api/bots/{bot_id}/scenarios
GET /api/scenarios/{id}
PUT /api/scenarios/{id}
DELETE /api/scenarios/{id}
POST /api/scenarios/{id}/activate

# Dialog Management
GET /api/bots/{bot_id}/dialogs
GET /api/bots/{bot_id}/platforms/{platform}/dialogs
GET /api/dialogs/{id}
DELETE /api/dialogs/{id}
GET /api/dialogs/{id}/history

# Media Files
GET /api/bots/{bot_id}/media
POST /api/bots/{bot_id}/media
GET /api/media/{id}
DELETE /api/media/{id}

# Platform Webhooks
POST /api/webhook/{platform}/{bot_id}
```

## 4. Dialog Scenario Storage and Processing

Dialog scenarios are stored in JSON format in the `bot_scenario` table. Example scenario structure:

```json
{
  "version": "1.0",
  "steps": [
    {
      "id": "welcome",
      "message": {
        "text": "Hello! What's your name?",
        "media": []
      },
      "expected_input": {
        "type": "text",
        "variable": "first_name"
      },
      "next_step": "ask_lastname"
    },
    {
      "id": "ask_lastname",
      "message": {
        "text": "Please enter your last name"
      },
      "expected_input": {
        "type": "text",
        "variable": "last_name"
      },
      "next_step": "ask_position"
    },
    {
      "id": "ask_position",
      "message": {
        "text": "What's your position in the company?"
      },
      "buttons": [
        {"text": "Food Guide", "value": "food-guide"},
        {"text": "Cook", "value": "cook"},
        {"text": "Manager", "value": "manager"},
        {"text": "Office Worker 🤓", "value": "office"}
      ],
      "expected_input": {
        "type": "button",
        "variable": "position"
      },
      "next_step": "ask_project"
    }
  ],
  "conditions": [
    {
      "if": "citizenship == 'РФ'",
      "then": "show_rf_docs",
      "else": "show_sng_docs"
    }
  ]
}
```

## 5. Multi-Platform Dialog Management

- A single bot can interact with users across multiple messaging platforms
- Each bot has platform-specific credentials stored in `bot_platform_credential` table
- Dialog state includes both the bot ID and platform information
- The Dialog Manager abstracts away platform-specific differences
- Platform adapters handle the translation between the unified format and platform-specific features

## 6. Media File Handling

1. Upload media files through API endpoint
2. Files are saved locally or to cloud storage (using existing Supabase Storage)
3. Metadata and file paths are stored in the database
4. When sending messages, the bot uploads files to each platform and stores platform-specific IDs
5. `platform_file_ids` stores a JSON map of platform -> file_id for efficient reuse

## 7. Platform Integration Architecture

```
┌───────────────┐    ┌────────────────────┐    ┌────────────────┐
│ Messaging     │◄───┤ Platform Webhook   │◄───┤ Bot Manager    │
│ Platforms     │    │ Controllers        │    └────────────────┘
│ (Telegram,    │    └────────────────────┘           ▲
│  WhatsApp,    │              ▲                      │
│  Viber)       │              │                      │
└───────────────┘     ┌────────────────────┐    ┌────────────────┐
                      │ Platform Adapters  │◄───┤ Dialog Manager │
                      └────────────────────┘    └────────────────┘
                                                      ▲
                                                      │
                                               ┌────────────────┐
                                               │ Dialog State   │
                                               │ Repository     │
                                               └────────────────┘
```

- Platform-agnostic core system
- Adapters for each supported messaging platform (Telegram, WhatsApp, Viber)
- Common dialog flow regardless of platform
- Platform-specific rendering for optimal native experience

## 8. LLM Integration (Future Expansion)

1. Abstract interface for LLM interaction
2. Integration through API with chosen LLM provider
3. Mechanism for inserting LLM-generated responses into the scenario
4. Result caching to optimize LLM requests
5. Potential for dynamic conversation flow adjustments based on LLM understanding

## 9. Testing Strategy

1. **Unit tests**: for individual system components
2. **Integration tests**: for checking interactions between components
3. **Platform API mocks**: for testing without real platform requests
4. **Scenario tests**: for verifying the correct execution of scenarios
5. **Cross-platform tests**: for verifying consistent behavior across platforms
6. **Load tests**: for performance testing under high loads

## 10. Integration with Existing Backend

```
┌───────────────────────────────────────────────────────────────┐
│                   Existing GET INN Backend                     │
└──────────────────────┬────────────────────────────────────────┘
                       │
                       │ Direct DB access + API integration
                       ▼
┌───────────────────────────────────────────────────────────────┐
│                     Bot Management System                     │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  Bot Manager │    │Dialog Manager│    │Media Manager │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Platform     │    │ State        │    │ LLM          │     │
│  │ Adapters     │    │ Repository   │    │ Integration  │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└───────────┬──────────────────┬──────────────────┬─────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Telegram API  │    │ WhatsApp API  │    │  Viber API    │
└───────────────┘    └───────────────┘    └───────────────┘
```

- Authentication through existing mechanism (Supabase Auth)
- Shared models for accounts and users
- Integration with existing database
- Using existing storage solutions for media files
- Data collected from bot dialogs can be synced with the main system (e.g., onboarding data to staff tables)
- Common dialog flow for all platforms with platform-specific rendering

## 11. Project Structure

Following the existing backend structure pattern, the bot management system will be organized as follows:

```
/backend/
│
├── src/
│   ├── api/                       # FastAPI application
│   │   ├── core/
│   │   │   ├── models.py          # Database models for bots
│   │   │   └── config.py          # Configuration settings
│   │   │
│   │   ├── routers/
│   │   │   ├── bots/              # Bot management endpoints
│   │   │   │   ├── __init__.py
│   │   │   │   ├── instances.py    # Bot instance management
│   │   │   │   ├── scenarios.py    # Scenario management
│   │   │   │   ├── dialogs.py      # Dialog state management
│   │   │   │   └── media.py        # Media file management
│   │   │   │
│   │   │   └── webhooks/          # Platform webhook endpoints
│   │   │       ├── __init__.py
│   │   │       ├── telegram.py     # Telegram webhook handler
│   │   │       ├── whatsapp.py     # WhatsApp webhook handler
│   │   │       └── viber.py        # Viber webhook handler
│   │   │
│   │   ├── schemas/
│   │   │   ├── bots/              # Pydantic models for bot API
│   │   │   │   ├── __init__.py
│   │   │   │   ├── instance_schemas.py
│   │   │   │   ├── scenario_schemas.py
│   │   │   │   ├── dialog_schemas.py
│   │   │   │   └── media_schemas.py
│   │   │   │
│   │   │   └── webhooks/
│   │   │       ├── __init__.py
│   │   │       ├── telegram_schemas.py
│   │   │       ├── whatsapp_schemas.py
│   │   │       └── viber_schemas.py
│   │   │
│   │   ├── services/
│   │   │   ├── bots/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── instance_service.py   # Bot instance management
│   │   │   │   ├── scenario_service.py   # Scenario management
│   │   │   │   ├── dialog_service.py     # Dialog state management
│   │   │   │   └── media_service.py      # Media file management
│   │   │   │
│   │   │   └── llm/
│   │   │       ├── __init__.py
│   │   │       └── llm_service.py        # LLM integration service
│   │   │
│   │   └── dependencies/              # FastAPI dependencies
│   │       └── bot_auth.py            # Bot authentication
│   │
│   ├── integrations/
│   │   ├── platforms/                # Platform-specific adapters
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Base platform adapter
│   │   │   ├── telegram_adapter.py   # Telegram-specific adapter
│   │   │   ├── whatsapp_adapter.py   # WhatsApp-specific adapter
│   │   │   └── viber_adapter.py      # Viber-specific adapter
│   │   │
│   │   └── llm/                     # LLM integration components
│   │       ├── __init__.py
│   │       ├── azure_openai/         # Azure OpenAI integration
│   │       └── openai/               # OpenAI integration
│   │
│   ├── bot_manager/                 # Core bot management system
│   │   ├── __init__.py
│   │   ├── dialog_manager.py        # Dialog flow management
│   │   ├── scenario_processor.py    # Scenario execution
│   │   └── state_repository.py      # Dialog state persistence
│   │
│   └── worker/
│       ├── tasks/
│       │   └── bots/
│       │       ├── __init__.py
│       │       ├── message_tasks.py    # Async message processing
│       │       └── media_tasks.py      # Media processing tasks
│       │
│       └── celery_app.py              # Celery configuration
│
└── tests/
    ├── unit/
    │   └── bots/
    │       ├── test_dialog_manager.py
    │       ├── test_scenario_processor.py
    │       └── test_platform_adapters.py
    │
    ├── integration/
    │   └── bots/
    │       ├── test_bot_api.py
    │       ├── test_telegram_webhook.py
    │       └── test_dialog_flow.py
    │
    └── scenarios/                       # Test scenarios
        ├── test_onboarding_scenario.py
        └── test_cross_platform.py
```

This structure integrates seamlessly with the existing backend architecture while adding bot-specific components. It follows the same layered approach with API endpoints, services, and integrations, ensuring consistent development patterns across the system.

This architecture provides a flexible and scalable system for managing platform-agnostic chatbots, with a focus on reliability and the ability to expand functionality in the future. It leverages the existing account management infrastructure while adding bot-specific functionality.