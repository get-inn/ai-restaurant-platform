# Bot Management System Overview

## Introduction

The bot management system enables creation and management of conversational interfaces across multiple messaging platforms. It provides a unified system for defining, deploying, and monitoring chat bots that can interact with users via Telegram and other platforms, integrated with the GET INN Restaurant Platform backend.

## Core Architecture

The bot management system is built on the following core components:

### 1. Bot Core Management System
FastAPI application that manages all bots, providing RESTful APIs for bot lifecycle management, configuration, and monitoring.

### 2. Dialog Manager
Module responsible for storing and executing conversation scenarios, handling dialog flow control, state transitions, and user interaction processing.

### 3. Platform Adapters
Integrations with different messaging platforms (Telegram, WhatsApp, etc.) that abstract platform-specific API differences while providing unified functionality.

### 4. Dialog State Storage
Ensuring dialog persistence across conversations, maintaining user context, collected data, and conversation history.

### 5. Media System
Comprehensive media handling for images, videos, documents, and other file types with support for multiple media items and platform-specific optimizations.

### 6. Auto-Transition System
Advanced conversation flow control allowing automatic progression through scenario steps with configurable delays and chaining capabilities.

### 7. Conversation Logging
Detailed logging system for debugging, monitoring, and analytics with specialized event types and structured data.

## Architecture Diagram

```{mermaid}
graph TB
    subgraph "GET INN Backend"
        BACKEND[GET INN Backend APIs]
        AUTH[Authentication]
        DB[(PostgreSQL Database)]
    end
    
    subgraph "Bot Management System"
        subgraph "Core Components"
            BOT_MGR[Bot Manager]
            DIALOG_MGR[Dialog Manager]
            MEDIA_MGR[Media Manager]
        end
        
        subgraph "Support Services"
            PLATFORM_ADAPT[Platform Adapters]
            STATE_REPO[State Repository]
            CONV_LOG[Conversation Logger]
        end
        
        subgraph "Processing Layer"
            SCENARIO_PROC[Scenario Processor]
            AUTO_TRANS[Auto-Transition System]
        end
    end
    
    subgraph "External Platforms"
        TELEGRAM[Telegram Bot API]
        WHATSAPP[WhatsApp Business API]
        OTHER[Other Messaging APIs]
    end
    
    subgraph "Storage & Cache"
        REDIS[(Redis Cache)]
        MEDIA_STORE[Media Storage]
    end
    
    %% Backend connections
    BACKEND <--> BOT_MGR
    AUTH --> BOT_MGR
    DB <--> STATE_REPO
    
    %% Core component relationships
    BOT_MGR --> DIALOG_MGR
    DIALOG_MGR --> SCENARIO_PROC
    DIALOG_MGR --> AUTO_TRANS
    DIALOG_MGR --> MEDIA_MGR
    DIALOG_MGR --> STATE_REPO
    DIALOG_MGR --> CONV_LOG
    
    %% Platform connections
    PLATFORM_ADAPT --> TELEGRAM
    PLATFORM_ADAPT --> WHATSAPP
    PLATFORM_ADAPT --> OTHER
    DIALOG_MGR --> PLATFORM_ADAPT
    
    %% Storage connections
    STATE_REPO <--> REDIS
    MEDIA_MGR <--> MEDIA_STORE
    
    %% Webhook flow
    TELEGRAM -.->|Webhooks| PLATFORM_ADAPT
    WHATSAPP -.->|Webhooks| PLATFORM_ADAPT
    OTHER -.->|Webhooks| PLATFORM_ADAPT
```

## Database Schema

### Bot Management Tables

```python
class BotInstance(Base):
    __tablename__ = "bot_instance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BotPlatformCredential(Base):
    __tablename__ = "bot_platform_credential"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    platform = Column(String, nullable=False)  # 'telegram', 'whatsapp', etc.
    credentials = Column(JSONB, nullable=False)
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

### Dialog State Management

```python
class BotDialogState(Base):
    __tablename__ = "bot_dialog_state"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    platform = Column(String, nullable=False)
    platform_chat_id = Column(String, nullable=False)
    current_step = Column(String, nullable=False)
    collected_data = Column(JSONB, nullable=False, default={})
    last_interaction_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BotDialogHistory(Base):
    __tablename__ = "bot_dialog_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dialog_state_id = Column(UUID(as_uuid=True), ForeignKey("bot_dialog_state.id"))
    message_type = Column(String, nullable=False)  # 'user', 'bot'
    message_data = Column(JSONB, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
```

### Media Management

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

## API Endpoints

### Bot Management
```
GET    /api/accounts/{account_id}/bots
POST   /api/accounts/{account_id}/bots
GET    /api/bots/{id}
PUT    /api/bots/{id}
DELETE /api/bots/{id}
POST   /api/bots/{id}/activate
POST   /api/bots/{id}/deactivate
```

### Platform Credentials
```
GET    /api/bots/{bot_id}/platforms
POST   /api/bots/{bot_id}/platforms
GET    /api/bots/{bot_id}/platforms/{platform}
PUT    /api/bots/{bot_id}/platforms/{platform}
DELETE /api/bots/{bot_id}/platforms/{platform}
```

### Scenario Management
```
GET    /api/bots/{bot_id}/scenarios
POST   /api/bots/{bot_id}/scenarios
GET    /api/scenarios/{id}
PUT    /api/scenarios/{id}
DELETE /api/scenarios/{id}
POST   /api/scenarios/{id}/activate
```

### Dialog Management
```
GET    /api/bots/{bot_id}/dialogs
GET    /api/bots/{bot_id}/platforms/{platform}/dialogs
GET    /api/dialogs/{id}
DELETE /api/dialogs/{id}
GET    /api/dialogs/{id}/history
```

### Media Management
```
GET    /api/bots/{bot_id}/media
POST   /api/bots/{bot_id}/media
GET    /api/media/{id}
GET    /api/media/{id}/content
DELETE /api/media/{id}
```

### Platform Webhooks
```
POST   /api/webhook/{platform}/{bot_id}
```

## Key Features

### Multi-Platform Support
- Create bots that work across multiple messaging platforms
- Platform-specific optimizations while maintaining consistent behavior
- Unified API for managing all platforms

### Advanced Scenario System
- JSON-based scenario definitions with flexible structure
- Support for conditional branching and dynamic content
- Variable collection and manipulation
- Integration with backend services and APIs

### Auto-Transitions
- Automatic progression through conversation steps
- Configurable delays between messages
- Chain multiple auto-transitions for complex flows
- Comprehensive logging and debugging support

### Rich Media Handling
- Support for images, videos, audio, and documents
- Multiple media items in a single message
- Platform-specific media optimizations
- Media with interactive buttons

### State Management
- Persistent conversation state across sessions
- Context preservation and data collection
- User information and platform-specific metadata
- Dialog history and analytics

### Comprehensive Logging
- Detailed conversation logging for debugging
- Specialized event types for different operations
- Performance monitoring and metrics
- Structured data for analysis

## Key Concepts

### Bot Instance
A bot instance represents a single bot with its configuration, credentials, and scenarios. Features:
- Multiple platform-specific integrations
- Association with specific scenarios
- Enable/disable functionality
- Account-level organization

### Bot Platform Credentials
Platform-specific authentication and configuration:
- Secure token storage
- Platform-specific settings
- Webhook configuration
- Security and access controls

### Bot Scenarios
Defined conversation flows determining bot responses:
- Step-based message sequences
- Conditional branching logic
- Variable collection and validation
- Media and button support
- Auto-transition capabilities

### Dialog State
Conversation context persistence:
- Current scenario step tracking
- Collected user data
- Platform-specific metadata
- Interaction history

## Conversation Flow Process

```{mermaid}
sequenceDiagram
    participant User
    participant Platform as Messaging Platform
    participant Webhook as Webhook Controller
    participant DialogMgr as Dialog Manager
    participant ScenarioProc as Scenario Processor
    participant StateRepo as State Repository
    participant Logger as Conversation Logger
    
    User->>Platform: Send message
    Platform->>Webhook: Forward update via webhook
    Webhook->>DialogMgr: Process incoming message
    
    DialogMgr->>Logger: Log incoming message
    DialogMgr->>StateRepo: Get/create dialog state
    StateRepo-->>DialogMgr: Return current state
    
    DialogMgr->>ScenarioProc: Process current step
    ScenarioProc->>ScenarioProc: Evaluate conditions
    ScenarioProc->>ScenarioProc: Apply variable substitutions
    ScenarioProc-->>DialogMgr: Return processed response
    
    DialogMgr->>StateRepo: Update dialog state
    DialogMgr->>Logger: Log processing events
    
    DialogMgr->>Platform: Send response message
    Platform->>User: Deliver response
    
    alt Auto-transition enabled
        DialogMgr->>DialogMgr: Schedule auto-transition
        Note over DialogMgr: Wait for configured delay
        DialogMgr->>ScenarioProc: Process next step automatically
        DialogMgr->>Platform: Send auto-transition message
        Platform->>User: Deliver automated message
    end
```

## Platform Integration Architecture

Key principles:
- Platform-agnostic core system
- Specialized adapters for each messaging platform
- Common dialog flow regardless of platform
- Platform-specific rendering for optimal user experience
- Unified error handling and logging

## Integration Points

The bot management system integrates with:

### 1. Main Backend
- Shared authentication and authorization
- Access to business logic and data
- Common database and storage systems
- Existing account and user management

### 2. External APIs
- Platform-specific messaging APIs
- Media storage and processing services
- Third-party integrations and webhooks

### 3. Storage Systems
- PostgreSQL for structured data
- File storage for media content
- Caching for performance optimization

## Project Structure

```
/backend/src/
├── api/
│   ├── routers/
│   │   ├── bots/              # Bot management endpoints
│   │   └── webhooks/          # Platform webhook endpoints
│   ├── schemas/
│   │   ├── bots/              # Bot API schemas
│   │   └── webhooks/          # Webhook schemas
│   └── services/
│       └── bots/              # Bot business logic
├── integrations/
│   └── platforms/             # Platform-specific adapters
├── bot_manager/               # Core bot management system
│   ├── dialog_manager.py      # Dialog flow management
│   ├── scenario_processor.py  # Scenario execution
│   ├── state_repository.py    # State persistence
│   └── conversation_logger.py # Logging system
└── tests/
    ├── unit/
    ├── integration/
    └── scenarios/
```

## Testing Strategy

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing
3. **Platform API Mocks**: Testing without real platform requests
4. **Scenario Tests**: Conversation flow verification
5. **Cross-Platform Tests**: Consistent behavior validation
6. **Load Tests**: Performance under high loads

## Further Reading

For detailed information on specific components:

- [Auto-Transitions](auto-transitions.md) - Automatic conversation flow control
- [Media System](media-system.md) - Rich media handling and processing
- [Scenario Format](scenario-format.md) - Bot scenario specification
- [Webhook Management](webhook-management.md) - Platform webhook integration
- [Conversation Logging](conversation-logging.md) - Logging and debugging system

## Future Considerations

1. **LLM Integration**: AI-powered conversation capabilities
2. **Analytics Dashboard**: Conversation analytics and insights
3. **A/B Testing**: Scenario performance testing
4. **Multi-Language Support**: Internationalization capabilities
5. **Advanced Integrations**: CRM, marketing automation, etc.
6. **Performance Optimization**: Caching, load balancing, scaling