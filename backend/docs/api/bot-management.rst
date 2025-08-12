Bot Management API ✅
==================

.. note::
   **Implementation Status: Production Ready**
   
   All bot management features are fully implemented and battle-tested. This API powers the complete bot lifecycle including instance management, scenario execution, multi-platform support, dialog state tracking, and media handling.

The Bot Management API provides comprehensive tools for creating, configuring, and managing conversational bots across multiple messaging platforms. This API enables restaurant operators to automate customer interactions, staff onboarding, and operational workflows through intelligent chatbots.

.. grid:: 3
   :gutter: 2

   .. grid-item-card:: 🤖 Bot Instances
      :class-header: bg-primary text-white
      
      Create and manage bot instances with multi-platform support.
      
      **Key Features:**
      
      - Account-level organization
      - Platform credential management
      - Activation states
      - Usage analytics
      
   .. grid-item-card:: 📝 Scenarios
      :class-header: bg-success text-white
      
      Design conversation flows with conditional logic and variable collection.
      
      **Capabilities:**
      
      - JSON-based scenario definitions
      - Conditional branching
      - Variable substitution
      - Media and button support
      
   .. grid-item-card:: 💬 Dialog Management
      :class-header: bg-info text-white
      
      Handle active conversations with state persistence and history tracking.
      
      **Features:**
      
      - Real-time state management
      - Conversation history
      - Cross-platform continuity
      - Analytics and insights

Quick Reference
==============

.. tabs::

   .. tab:: Core Endpoints

      .. code-block:: text

         # Bot Management
         POST   /accounts/{account_id}/bots
         GET    /accounts/{account_id}/bots
         GET    /bots/{bot_id}
         PUT    /bots/{bot_id}
         DELETE /bots/{bot_id}
         
         # Scenarios
         POST   /bots/{bot_id}/scenarios
         GET    /bots/{bot_id}/scenarios
         PUT    /scenarios/{scenario_id}
         
         # Dialogs
         GET    /bots/{bot_id}/dialogs
         GET    /bots/{bot_id}/dialogs/{platform}/{chat_id}
         PUT    /bots/{bot_id}/dialogs/{platform}/{chat_id}

   .. tab:: Authentication

      All endpoints require JWT authentication:

      .. code-block:: bash

         curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
              https://api.getinn.com/v1/bots/{bot_id}

   .. tab:: Rate Limits

      .. list-table::
         :header-rows: 1

         * - Operation
           - Rate Limit
         * - Bot Creation
           - 10/min
         * - Scenario Updates
           - 20/min
         * - Dialog Operations
           - 100/min
         * - Webhook Processing
           - 1000/min

.. currentmodule:: bot_manager

Core Components
---------------

Dialog Manager
~~~~~~~~~~~~~~

The DialogManager is the central orchestration component for handling bot conversations across multiple platforms.

**DialogManager Class**

The DialogManager is the central orchestration component that coordinates between scenario processing, state management, and platform adapters. It serves as the main entry point for handling bot conversations across multiple platforms including Telegram and WhatsApp.

**Key Responsibilities:**
- Message routing and processing through platform adapters
- Dialog state management and persistence
- Scenario execution and flow control
- Media handling and fallback strategies
- Auto-transition processing with loop prevention
- Command handling (/start, /help, /reset)

**Constructor:**

``__init__(db: AsyncSession, platform_adapters: Dict[str, PlatformAdapter] = None, state_repository: StateRepository = None, scenario_processor: ScenarioProcessor = None)``

- ``db: AsyncSession`` - Database session for data operations
- ``platform_adapters: Dict[str, PlatformAdapter]`` - Optional dictionary mapping platform names to adapter instances
- ``state_repository: StateRepository`` - Optional custom state repository instance
- ``scenario_processor: ScenarioProcessor`` - Optional custom scenario processor instance

Initializes the dialog manager with database session and optional components. Creates default instances if not provided.

Key Methods
^^^^^^^^^^^

**async process_incoming_message(bot_id, platform, platform_chat_id, update_data)**

Main entry point for processing incoming messages from platform webhooks. Handles message routing, dialog state management, and response generation.

**Parameters:**
- ``bot_id`` (UUID): The bot instance identifier
- ``platform`` (str): Platform name (e.g., "telegram", "whatsapp")
- ``platform_chat_id`` (str): Chat identifier from the platform
- ``update_data`` (Dict[str, Any]): Raw webhook data from the platform

**Returns:**
- ``Optional[Dict[str, Any]]``: Response information or None if processing failed

**Processing Flow:**
1. Validates bot instance and platform adapter availability
2. Extracts message content through platform adapter
3. Retrieves or creates dialog state
4. Routes to appropriate handler (text, button, command)
5. Processes response and manages state transitions
6. Logs all operations for debugging

**Usage Example:**

.. code-block:: python

   dialog_manager = DialogManager(db, platform_adapters)
   response = await dialog_manager.process_incoming_message(
       bot_id=UUID("12345678-1234-1234-1234-123456789012"),
       platform="telegram",
       platform_chat_id="123456789",
       update_data={"message": {"text": "Hello", "from": {"id": "user123"}}}
   )

**async handle_text_message(bot_id, platform, platform_chat_id, text, dialog_state)**

Processes text messages through the dialog service and manages scenario execution.

**Parameters:**
- ``bot_id`` (UUID): Bot instance identifier
- ``platform`` (str): Platform identifier
- ``platform_chat_id`` (str): Platform chat identifier
- ``text`` (str): Text message content from user
- ``dialog_state`` (Optional[Dict[str, Any]]): Current dialog state

**Returns:**
- ``Optional[Dict[str, Any]]``: Response data with message content and state updates

**Processing Features:**
- Handles media content within text messages
- Manages auto-transitions between scenario steps
- Processes variable collection and validation
- Supports conditional scenario branching
- Implements loop prevention for transitions

**async handle_button_click(bot_id, platform, platform_chat_id, button_value, dialog_state)**

Processes button interactions from inline keyboards and reply markup.

**Parameters:**
- ``bot_id`` (UUID): Bot instance identifier
- ``platform`` (str): Platform identifier
- ``platform_chat_id`` (str): Platform chat identifier
- ``button_value`` (str): Value of the clicked button
- ``dialog_state`` (Optional[Dict[str, Any]]): Current dialog state

**Returns:**
- ``Optional[Dict[str, Any]]``: Response data with updated state

**async handle_command(bot_id, platform, platform_chat_id, command, dialog_state)**

Handles special bot commands like /start, /help, /reset.

**Parameters:**
- ``bot_id`` (UUID): Bot instance identifier
- ``platform`` (str): Platform identifier
- ``platform_chat_id`` (str): Platform chat identifier
- ``command`` (str): Command string (with / prefix)
- ``dialog_state`` (Optional[Dict[str, Any]]): Current dialog state

**Returns:**
- ``Optional[Dict[str, Any]]``: Response data

**Supported Commands:**
- ``/start``: Initializes or restarts conversation
- ``/help``: Provides help information
- ``/reset``: Resets dialog state to beginning

**async send_message(bot_id, platform, platform_chat_id, message, buttons)**

Universal message sending method that handles text, media, and interactive elements.

**Parameters:**
- ``bot_id`` (UUID): Bot instance identifier
- ``platform`` (str): Platform identifier
- ``platform_chat_id`` (str): Platform chat identifier
- ``message`` (Union[str, DialogMessage, Dict[str, Any]]): Message content in various formats
- ``buttons`` (Optional[List[Dict[str, str]]]): Optional interactive buttons

**Returns:**
- ``bool``: True if message sent successfully

**Features:**
- Supports plain text, rich text, and media messages
- Handles media groups (albums) with proper ordering
- Implements fallback strategies for failed media uploads
- Manages button layouts and interactions
- Provides comprehensive error handling and logging

**async register_platform_adapter(platform, adapter)**

Registers a platform adapter for message handling.

**Parameters:**
- ``platform`` (str): Platform identifier (telegram, whatsapp, etc.)
- ``adapter`` (PlatformAdapter): Platform adapter instance

**Returns:**
- ``bool``: True if registration successful

**async get_platform_adapter(platform)**

Retrieves the registered adapter for a specific platform.

**Parameters:**
- ``platform`` (str): Platform identifier

**Returns:**
- ``Optional[PlatformAdapter]``: Adapter instance or None if not found

Scenario Processor
~~~~~~~~~~~~~~~~~~

The ScenarioProcessor handles dialog scenario execution and conversation flow logic.

**ScenarioProcessor Class**

The ScenarioProcessor processes bot dialog scenarios and manages conversation flow logic. It handles variable substitution, conditional branching, input validation, and step transitions within bot conversations.

**Key Responsibilities:**
- Processing scenario steps with message generation
- Variable substitution in messages and conditions
- Conditional logic evaluation for flow control
- User input validation against defined rules
- Next step determination based on conditions
- Support for custom condition evaluators

**Constructor:**

``__init__(custom_conditions: Dict[str, Callable] = None)``

- ``custom_conditions: Dict[str, Callable]`` - Optional custom condition evaluator functions

Initializes processor with optional custom condition handlers for extending evaluation capabilities.

Key Methods
^^^^^^^^^^^

**process_step(scenario_data, current_step_id, collected_data)**

Main method for processing scenario steps. Handles different step types and generates appropriate responses.

**Parameters:**
- ``scenario_data`` (Dict[str, Any]): Complete scenario definition with steps, variables, and metadata
- ``current_step_id`` (str): ID of the current step to process
- ``collected_data`` (Dict[str, Any]): User data collected so far in the conversation

**Returns:**
- ``Dict[str, Any]``: Processed step information containing:

  - ``message``: Generated message text with variable substitutions
  - ``buttons``: List of interactive buttons if defined
  - ``next_step``: ID of next step to process
  - ``expected_input``: Input validation rules
  - ``step_data``: Additional step metadata

**Step Types Supported:**
- ``message``: Simple message display with optional buttons
- ``conditional_message``: Message with conditional content based on collected data
- ``action``: Special actions like data collection or external API calls

**Usage Example:**

.. code-block:: python

   processor = ScenarioProcessor()
   result = processor.process_step(
       scenario_data={
           "steps": {
               "welcome": {
                   "type": "message",
                   "message": {"text": "Hello {{user_name}}!"},
                   "next_step": "collect_info"
               }
           }
       },
       current_step_id="welcome",
       collected_data={"user_name": "John"}
   )
   # Result: {"message": "Hello John!", "next_step": "collect_info", ...}

**validate_user_input(user_input, expected_input)**

Validates user input against defined rules and constraints.

**Parameters:**
- ``user_input`` (Any): User-provided input to validate
- ``expected_input`` (Dict[str, Any]): Input validation rules and constraints

**Returns:**
- ``Dict[str, Any]``: Validation result containing:

  - ``valid``: Boolean indicating if input is valid
  - ``error_message``: Human-readable error message if invalid
  - ``processed_value``: Cleaned/processed input value

**Supported Input Types:**
- ``text``: String validation with length limits and patterns
- ``number``: Numeric validation with min/max ranges
- ``button``: Button selection validation
- ``date``: Date format validation
- ``email``: Email format validation
- ``phone``: Phone number format validation

**Validation Features:**
- Regular expression pattern matching
- Length constraints (min_length, max_length)
- Numeric range validation (min_value, max_value)
- Required field validation
- Custom validation patterns

**Usage Example:**

.. code-block:: python

   validation_rules = {
       "type": "text",
       "min_length": 2,
       "max_length": 50,
       "pattern": "^[a-zA-Z\s]+$",
       "error_message": "Please enter a valid name (letters only)"
   }
   
   result = processor.validate_user_input("John Doe", validation_rules)
   # Result: {"valid": True, "processed_value": "John Doe"}

**_substitute_variables(text, collected_data, scenario_data)**

Replaces {{variable}} placeholders with actual values from collected data.

**Parameters:**
- ``text`` (str): Text containing variable placeholders
- ``collected_data`` (Dict[str, Any]): Variable values from user interactions
- ``scenario_data`` (Dict[str, Any]): Scenario definition with variable mappings

**Returns:**
- ``str``: Text with variables replaced by actual values

**Features:**
- Supports nested variable references
- Variable mapping through scenario configuration
- Fallback values for undefined variables
- Escaping for literal {{ }} usage

**_evaluate_condition(condition_expr, collected_data)**

Evaluates conditional expressions for scenario flow control.

**Parameters:**
- ``condition_expr`` (str): Condition expression to evaluate
- ``collected_data`` (Dict[str, Any]): Data to evaluate condition against

**Returns:**
- ``bool``: Result of condition evaluation

**Supported Operators:**
- ``==``: Equality comparison
- ``!=``: Inequality comparison
- ``>``: Greater than
- ``<``: Less than
- ``>=``: Greater than or equal
- ``<=``: Less than or equal
- ``contains``: String/list containment
- ``exists``: Variable existence check
- ``in``: Value in list check

**Usage Example:**

.. code-block:: python

   # Condition examples:
   processor._evaluate_condition("user_age >= 18", {"user_age": 25})  # True
   processor._evaluate_condition("user_name contains John", {"user_name": "John Doe"})  # True
   processor._evaluate_condition("user_role in [admin, manager]", {"user_role": "admin"})  # True

**_resolve_next_step(current_step, collected_data)**

Determines the next step based on step definition and conditional logic.

**Parameters:**
- ``current_step`` (Dict[str, Any]): Current step definition
- ``collected_data`` (Dict[str, Any]): Collected conversation data

**Returns:**
- ``Optional[str]``: Next step ID or None if conversation should end

**Resolution Logic:**
1. Checks for conditional next steps with condition evaluation
2. Falls back to default next_step if defined
3. Returns None if no next step is specified (conversation end)

State Repository
~~~~~~~~~~~~~~~~

The StateRepository manages dialog state persistence and conversation history.

**StateRepository Class**

The StateRepository manages dialog state persistence and retrieval with intelligent caching strategies. It provides the data layer for conversation state management, including creation, updates, history tracking, and performance optimization.

**Key Responsibilities:**
- Dialog state persistence in database
- In-memory caching for performance optimization
- Conversation history tracking and retrieval
- State lifecycle management (create, update, delete)
- Cache invalidation and consistency management
- Transaction management for data integrity

**Constructor:**

``__init__(db: AsyncSession)``

- ``db: AsyncSession`` - Database session for state operations

Initializes repository with database session and creates in-memory cache for frequently accessed states.

Key Methods
^^^^^^^^^^^

**async get_dialog_state(bot_id, platform, platform_chat_id)**

Retrieves dialog state with cache-first strategy for optimal performance.

**Parameters:**
- ``bot_id`` (UUID): Bot instance identifier
- ``platform`` (str): Platform identifier (telegram, whatsapp, etc.)
- ``platform_chat_id`` (str): Platform-specific chat identifier

**Returns:**
- ``Optional[Dict[str, Any]]``: Dialog state dictionary containing:

  - ``id``: Unique dialog state identifier
  - ``current_step``: Current scenario step ID
  - ``collected_data``: User data collected during conversation
  - ``created_at``: State creation timestamp
  - ``last_interaction_at``: Last interaction timestamp
  - ``metadata``: Additional state metadata

**Caching Strategy:**
1. Checks in-memory cache first for fast access
2. Falls back to database query if not cached
3. Caches retrieved state for subsequent requests
4. Implements cache TTL for memory management

**Usage Example:**

.. code-block:: python

   repository = StateRepository(db)
   state = await repository.get_dialog_state(
       bot_id=UUID("12345678-1234-1234-1234-123456789012"),
       platform="telegram",
       platform_chat_id="123456789"
   )
   if state:
       current_step = state["current_step"]
       collected_data = state["collected_data"]

**async create_dialog_state(bot_id, platform, platform_chat_id, current_step, collected_data)**

Creates new dialog state in database and cache with proper initialization.

**Parameters:**
- ``bot_id`` (UUID): Bot instance identifier
- ``platform`` (str): Platform identifier
- ``platform_chat_id`` (str): Platform-specific chat identifier
- ``current_step`` (str): Initial scenario step ID
- ``collected_data`` (Dict[str, Any]): Initial collected data (defaults to empty dict)

**Returns:**
- ``Dict[str, Any]``: Created dialog state with all fields populated

**Initialization Process:**
1. Creates database record with unique ID
2. Sets initial timestamps (created_at, last_interaction_at)
3. Initializes collected_data structure
4. Adds to cache for immediate access
5. Returns complete state dictionary

**Usage Example:**

.. code-block:: python

   state = await repository.create_dialog_state(
       bot_id=bot_uuid,
       platform="telegram",
       platform_chat_id="123456789",
       current_step="welcome",
       collected_data={"user_language": "en"}
   )

**async update_dialog_state(state_id, update_data)**

Updates existing dialog state and maintains cache consistency.

**Parameters:**
- ``state_id`` (UUID): Dialog state identifier to update
- ``update_data`` (Dict[str, Any]): Fields to update in the state

**Returns:**
- ``Optional[Dict[str, Any]]``: Updated state dictionary or None if not found

**Update Process:**
1. Validates state exists in database
2. Applies updates to database record
3. Automatically updates last_interaction_at timestamp
4. Invalidates and updates cache entry
5. Returns updated state dictionary

**Common Update Fields:**
- ``current_step``: Update scenario progression
- ``collected_data``: Add/modify user data
- ``metadata``: Update conversation metadata

**Example:**

.. code-block:: python

   updated_state = await repository.update_dialog_state(
       state_id=state_uuid,
       update_data={
           "current_step": "collect_name",
           "collected_data": {"user_age": 25, "user_name": "John"}
       }
   )

**async delete_dialog_state(state_id)**

Deletes dialog state and associated history with cleanup.

**Parameters:**
- ``state_id`` (UUID): Dialog state identifier to delete

**Returns:**
- ``bool``: True if deletion successful, False if state not found

**Deletion Process:**
1. Removes associated dialog history entries
2. Deletes main dialog state record
3. Removes from cache
4. Handles referential integrity

**async add_to_history(dialog_state_id, message_type, message_data)**

Adds entry to conversation history for tracking and analysis.

**Parameters:**
- ``dialog_state_id`` (UUID): Associated dialog state identifier
- ``message_type`` (str): Type of message ('user', 'bot', 'system')
- ``message_data`` (Dict[str, Any]): Message content and metadata

**Returns:**
- ``Optional[Dict[str, Any]]``: Created history entry with timestamp

**History Entry Structure:**
- ``message_type``: Categorizes message source
- ``message_data``: Contains message content, media, buttons
- ``timestamp``: When message was recorded
- ``metadata``: Additional tracking information

**async get_dialog_history(dialog_state_id, limit, offset)**

Retrieves conversation history with pagination support.

**Parameters:**
- ``dialog_state_id`` (UUID): Dialog state identifier
- ``limit`` (int): Maximum entries to return (default: 50)
- ``offset`` (int): Number of entries to skip (default: 0)

**Returns:**
- ``List[Dict[str, Any]]``: History entries ordered by timestamp (newest first)

**Features:**
- Pagination for large conversation histories
- Chronological ordering (newest first)
- Efficient database queries with proper indexing
- Support for filtering by message type

**clear_cache()**

Clears in-memory cache of dialog states for memory management.

**Usage:**
- Called during high-memory situations
- Used for testing and development
- Triggered by cache size limits
- Manual cleanup operations

Conversation Logger
~~~~~~~~~~~~~~~~~~~

The ConversationLogger provides comprehensive logging for bot conversations and debugging.

**ConversationLogger Class**

The ConversationLogger provides detailed, structured logging specifically designed for bot conversations. It offers context-aware logging with thread-local storage, specialized methods for different conversation events, and comprehensive debugging support.

**Key Features:**
- Context-aware logging with thread-local storage
- Specialized methods for conversation events
- Structured JSON output for log analysis
- Event type classification for filtering
- Media operation logging with detailed metadata
- State transition tracking
- Variable update monitoring
- Condition evaluation debugging
- Auto-transition event logging

**Constructor:**

``__init__(bot_id=None, dialog_id=None, platform=None, platform_chat_id=None)``

**Parameters:**
- ``bot_id`` (Optional[Union[UUID, str]]): Bot identifier for context
- ``dialog_id`` (Optional[Union[UUID, str]]): Dialog identifier for context
- ``platform`` (Optional[str]): Platform name for context (telegram, whatsapp)
- ``platform_chat_id`` (Optional[str]): Platform chat identifier for context

Initializes logger with optional context that will be included in all log messages. Context is stored using thread-local storage for thread safety.

**Context Management Methods:**

**set_context(**kwargs)**

Sets or updates context values for all subsequent log messages in the current thread.

**Parameters:**
- ``**kwargs``: Context key-value pairs to set

**Usage Example:**

.. code-block:: python

   logger = ConversationLogger()
   logger.set_context(
       bot_id="12345",
       platform="telegram",
       platform_chat_id="987654321",
       user_id="user123",
       scenario_id="onboarding_v1"
   )

**clear_context(*keys)**

Clears specific context values or all context if no keys specified.

**Parameters:**
- ``*keys``: Specific keys to clear from context

**General Logging Methods:**

**debug(event_type, message, data=None)**

Logs debug-level messages with event type classification.

**Parameters:**
- ``event_type`` (LogEventType): Classification of the event being logged
- ``message`` (str): Human-readable log message
- ``data`` (Optional[Dict[str, Any]]): Additional structured data

**info(event_type, message, data=None)**

Logs info-level messages with event type classification.

**warning(event_type, message, data=None)**

Logs warning-level messages with event type classification.

**error(event_type, message, data=None, exc_info=None)**

Logs error-level messages with optional exception information.

**Parameters:**
- ``exc_info``: Exception information for stack traces

**Specialized Conversation Logging Methods:**

**incoming_message(message, data=None)**

Logs incoming messages from users with INCOMING event type.

**Parameters:**
- ``message`` (str): User message content
- ``data`` (Optional[Dict[str, Any]]): Additional message metadata

**Usage Example:**

.. code-block:: python

   logger.incoming_message(
       "Hello, I need help",
       data={
           "message_type": "text",
           "user_id": "123456",
           "timestamp": "2023-01-01T12:00:00Z"
       }
   )

**outgoing_message(message, data=None)**

Logs outgoing messages to users with OUTGOING event type.

**Parameters:**
- ``message`` (str): Bot response message
- ``data`` (Optional[Dict[str, Any]]): Response metadata

**media_processing(operation, media_type, data=None)**

Logs media processing operations with detailed information.

**Parameters:**
- ``operation`` (str): Operation being performed (upload, download, send, resize, etc.)
- ``media_type`` (str): Type of media (image, video, audio, document, sticker)
- ``data`` (Optional[Dict[str, Any]]): Media operation details

**Usage Example:**

.. code-block:: python

   logger.media_processing(
       operation="upload",
       media_type="image",
       data={
           "file_size": 1048576,
           "file_name": "photo.jpg",
           "mime_type": "image/jpeg",
           "upload_duration_ms": 1250
       }
   )

**webhook_received(platform, data=None)**

Logs webhook events from messaging platforms.

**Parameters:**
- ``platform`` (str): Platform that sent the webhook
- ``data`` (Optional[Dict[str, Any]]): Webhook payload information

**state_change(step_id, data=None)**

Logs dialog state changes and step transitions.

**Parameters:**
- ``step_id`` (str): New step identifier
- ``data`` (Optional[Dict[str, Any]]): State change details

**Usage Example:**

.. code-block:: python

   logger.state_change(
       step_id="collect_name",
       data={
           "previous_step": "welcome",
           "transition_reason": "user_input",
           "collected_data_count": 3
       }
   )

**variable_update(variable, value, data=None)**

Logs variable updates in collected conversation data.

**Parameters:**
- ``variable`` (str): Variable name being updated
- ``value`` (Any): New variable value
- ``data`` (Optional[Dict[str, Any]]): Update context

**condition_evaluation(condition, result, data=None)**

Logs condition evaluation results for debugging scenario logic.

**Parameters:**
- ``condition`` (str): Condition expression that was evaluated
- ``result`` (bool): Evaluation result (True/False)
- ``data`` (Optional[Dict[str, Any]]): Evaluation context

**Usage Example:**

.. code-block:: python

   logger.condition_evaluation(
       condition="user_age >= 18",
       result=True,
       data={
           "user_age": 25,
           "step_id": "age_verification",
           "evaluation_time_ms": 2
       }
   )

**auto_transition(message, data=None)**

Logs automatic step transition events with details.

**Parameters:**
- ``message`` (str): Description of the auto-transition
- ``data`` (Optional[Dict[str, Any]]): Transition details

**Factory Function:**

**get_logger(bot_id=None, dialog_id=None, platform=None, platform_chat_id=None)**

Factory function to create logger instances with initial context.

**Parameters:**
- Same as constructor parameters

**Returns:**
- ``ConversationLogger``: Logger instance with specified context

**Usage Example:**

.. code-block:: python

   # Create logger with context
   logger = get_logger(
       bot_id="bot_123",
       platform="telegram",
       platform_chat_id="chat_456"
   )
   
   # Log conversation events
   logger.incoming_message("Hello", {"message_type": "text"})
   logger.state_change("greeting")
   logger.outgoing_message("Hi! How can I help you?")
   
   # Log media processing
   logger.media_processing("send", "image", {"media_id": "img_789"})
   
   # Log condition evaluation
   logger.condition_evaluation("user_authenticated == true", True)

**Thread Safety:**
The ConversationLogger uses thread-local storage for context management, ensuring that context values are isolated between different conversation threads and concurrent operations.

**Log Event Types:**
- ``INCOMING``: Messages from users
- ``OUTGOING``: Messages to users
- ``STATE_CHANGE``: Dialog state transitions
- ``MEDIA_PROCESSING``: Media operations
- ``WEBHOOK``: Platform webhook events
- ``VARIABLE_UPDATE``: Data collection updates
- ``CONDITION_EVAL``: Conditional logic evaluation
- ``AUTO_TRANSITION``: Automatic step transitions
- ``ERROR``: Error conditions
- ``DEBUG``: Debug information

Performance and Debugging Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Structured Logging Output:**
All log entries are formatted as structured JSON with consistent fields:

.. code-block:: json

   {
       "timestamp": "2023-01-01T12:00:00.000Z",
       "level": "INFO",
       "event_type": "INCOMING",
       "message": "User message received",
       "context": {
           "bot_id": "12345",
           "platform": "telegram",
           "platform_chat_id": "987654321",
           "dialog_id": "dialog_456"
       },
       "data": {
           "message_type": "text",
           "user_id": "user123",
           "content_length": 25
       }
   }

**Log Analysis Features:**
- Event type filtering for specific analysis
- Context-based log aggregation
- Performance timing for operations
- Error tracking with stack traces
- Media operation monitoring
- State transition flow analysis

API Routers
-----------

Bot Instance Management
~~~~~~~~~~~~~~~~~~~~~~~

.. currentmodule:: api.routers.bots

The bot instances router provides comprehensive CRUD operations for managing bot instances within accounts. It handles bot lifecycle management, activation states, and account-level bot organization.

**Core Endpoints:**

**POST /accounts/{account_id}/bots** - Create Bot Instance

- **Purpose**: Creates a new bot instance within a specific account
- **Request Body**: BotInstanceCreate schema with name, description, and configuration
- **Response**: Complete bot instance data with generated ID and timestamps
- **Validation**: Account ownership verification and bot name uniqueness
- **Side Effects**: Initializes default dialog state and creates audit log entry

**GET /accounts/{account_id}/bots** - List Account Bots

- **Purpose**: Retrieves all bot instances belonging to an account
- **Query Parameters**: 
  - ``limit`` (int): Maximum bots to return (default: 50)
  - ``offset`` (int): Pagination offset (default: 0)
  - ``status`` (str): Filter by activation status (active, inactive, all)
- **Response**: Paginated list of bot instances with metadata
- **Permissions**: Account owner or admin access required

**GET /bots/{bot_id}** - Get Specific Bot

- **Purpose**: Retrieves detailed information for a specific bot instance
- **Response**: Complete bot data including configuration, status, and statistics
- **Includes**: Platform credentials count, active scenarios, dialog statistics
- **Caching**: Response cached for performance optimization

**PUT /bots/{bot_id}** - Update Bot Configuration

- **Purpose**: Updates bot instance configuration and metadata
- **Request Body**: BotInstanceUpdate schema with modified fields
- **Validation**: Configuration consistency checks and permission verification
- **Side Effects**: Updates cache and triggers webhook notifications

**DELETE /bots/{bot_id}** - Delete Bot Instance

- **Purpose**: Permanently removes bot instance and associated data
- **Cascade Effects**: Removes scenarios, dialogs, credentials, and history
- **Safety**: Requires confirmation and admin privileges
- **Cleanup**: Deactivates webhooks and clears platform registrations

**POST /bots/{bot_id}/activate** - Activate Bot

- **Purpose**: Activates bot for message processing
- **Prerequisites**: Valid platform credentials and at least one active scenario
- **Side Effects**: Registers webhooks and starts message processing
- **Validation**: Platform connectivity tests before activation

**POST /bots/{bot_id}/deactivate** - Deactivate Bot

- **Purpose**: Temporarily disables bot without data deletion
- **Side Effects**: Unregisters webhooks and stops message processing
- **Preservation**: Maintains all data and configuration for reactivation

Scenario Management
~~~~~~~~~~~~~~~~~~~

The scenarios router provides comprehensive conversation scenario management with support for JSON import/export, version control, and activation management.

**Core Endpoints:**

**POST /bots/{bot_id}/scenarios** - Create Scenario

- **Purpose**: Creates new conversation scenario with step definitions
- **Request Body**: BotScenarioCreate schema with name, version, and scenario data
- **Validation**: 
  - Scenario structure validation (steps, transitions, variables)
  - Step ID uniqueness and reference integrity
  - Variable mapping consistency
  - Conditional logic syntax validation
- **Features**: Automatic version numbering and conflict detection

**POST /bots/{bot_id}/scenarios/upload** - Upload JSON Scenario

- **Purpose**: Imports scenario from JSON file with comprehensive validation
- **File Format**: Structured JSON with steps, metadata, and configuration
- **Validation Process**:
  1. JSON syntax and structure validation
  2. Scenario schema compliance checking
  3. Step reference integrity verification
  4. Variable and condition syntax validation
  5. Media reference validation
- **Error Handling**: Detailed validation error reports with line numbers
- **Import Options**: Replace existing, merge with existing, or create new version

**GET /bots/{bot_id}/scenarios** - List Bot Scenarios

- **Purpose**: Retrieves all scenarios for a specific bot with filtering
- **Query Parameters**:
  - ``active_only`` (bool): Show only active scenarios
  - ``version`` (str): Filter by scenario version
  - ``limit``, ``offset``: Pagination controls
- **Response**: Scenario list with metadata, step counts, and activation status
- **Sorting**: By creation date, last modified, or alphabetical

**GET /scenarios/{scenario_id}** - Get Specific Scenario

- **Purpose**: Retrieves complete scenario definition with all steps
- **Response Includes**:
  - Complete step definitions with transitions
  - Variable mappings and validation rules
  - Conditional logic expressions
  - Media references and button configurations
  - Usage statistics and performance metrics
- **Export Format**: Can return as JSON for backup/migration

**PUT /scenarios/{scenario_id}** - Update Scenario

- **Purpose**: Updates scenario definition with validation
- **Request Body**: BotScenarioUpdate schema with modified elements
- **Version Control**: Creates new version if major changes detected
- **Validation**: Same comprehensive checks as creation
- **Impact Analysis**: Identifies affected active dialogs

**POST /scenarios/{scenario_id}/activate** - Toggle Activation

- **Purpose**: Activates or deactivates scenario for bot conversations
- **Request Body**: BotScenarioActivate schema with activation status
- **Prerequisites**: Complete scenario validation before activation
- **Side Effects**: 
  - Updates bot routing configuration
  - Affects new conversation initialization
  - Triggers cache invalidation
- **Safety**: Active dialogs continue with current scenario version

**DELETE /scenarios/{scenario_id}** - Delete Scenario

- **Purpose**: Removes scenario with safety checks
- **Prerequisites**: Scenario must be inactive with no active dialogs
- **Cascade Effects**: Removes associated test data and analytics
- **Archive Option**: Can archive instead of permanent deletion

Dialog Management
~~~~~~~~~~~~~~~~~

The dialogs router provides comprehensive conversation state management and history tracking for active bot conversations across all platforms.

**Core Endpoints:**

**GET /bots/{bot_id}/dialogs** - List Bot Dialogs

- **Purpose**: Retrieves all active dialogs for a bot across platforms
- **Query Parameters**:
  - ``platform`` (str): Filter by specific platform
  - ``status`` (str): Filter by dialog status (active, completed, abandoned)
  - ``limit``, ``offset``: Pagination controls
  - ``from_date``, ``to_date``: Date range filtering
- **Response**: Dialog summaries with current step, last activity, and user info
- **Analytics**: Includes conversation duration and step progression metrics

**GET /bots/{bot_id}/dialogs/{platform}/{chat_id}** - Get/Create Dialog State

- **Purpose**: Retrieves existing dialog state or creates new one if not found
- **Response**: Complete dialog state with:
  - Current scenario step and collected data
  - Conversation history summary
  - User profile information
  - Platform-specific metadata
  - State timestamps and progression
- **Auto-Creation**: Creates new dialog with default scenario if none exists
- **Caching**: State cached for performance optimization

**GET /bots/{bot_id}/dialogs/{platform}/{chat_id}/history** - Get Dialog History

- **Purpose**: Retrieves complete conversation history with pagination
- **Query Parameters**:
  - ``limit`` (int): Maximum history entries (default: 50, max: 500)
  - ``offset`` (int): Pagination offset
  - ``message_type`` (str): Filter by message type (user, bot, system)
  - ``from_timestamp``, ``to_timestamp``: Time range filtering
- **Response**: Chronologically ordered conversation history
- **Format**: Each entry includes message content, metadata, and timestamps
- **Export**: Supports JSON and CSV export formats

**PUT /bots/{bot_id}/dialogs/{platform}/{chat_id}** - Update Dialog State

- **Purpose**: Updates dialog state with new step or collected data
- **Request Body**: DialogStateUpdate schema with state modifications
- **Validation**:
  - Step ID exists in current scenario
  - Collected data matches expected format
  - State transition is valid
- **Side Effects**:
  - Updates cache and database
  - Logs state change event
  - Triggers analytics update
- **Concurrency**: Handles concurrent updates with optimistic locking

**DELETE /bots/{bot_id}/dialogs/{platform}/{chat_id}** - Reset Dialog

- **Purpose**: Resets dialog to initial state while preserving history
- **Safety**: Requires confirmation parameter
- **Options**: Complete reset or reset to specific checkpoint
- **History**: Previous conversation preserved in archived history

Platform Credentials
~~~~~~~~~~~~~~~~~~~~~

The platforms router provides secure credential management for bot integrations across multiple messaging platforms with encryption, validation, and webhook management.

**Core Endpoints:**

**POST /bots/{bot_id}/platforms** - Add Platform Credentials

- **Purpose**: Adds encrypted credentials for messaging platform integration
- **Request Body**: BotPlatformCredentialCreate schema with platform-specific credentials
- **Supported Platforms**:
  - **Telegram**: Bot token, webhook URL configuration
  - **WhatsApp Business API**: Phone number, access token, webhook verification
  - **Facebook Messenger**: Page access token, app secret
  - **Slack**: Bot token, signing secret
  - **Discord**: Bot token, application ID
- **Security**: All credentials encrypted at rest using AES-256 encryption
- **Validation**: Platform-specific credential format validation and connectivity testing

**GET /bots/{bot_id}/platforms** - List Platform Integrations

- **Purpose**: Retrieves all configured platform integrations for a bot
- **Response**: Platform list with status, configuration summary (no sensitive data)
- **Status Indicators**: Connection health, webhook status, last activity
- **Permissions**: Only returns platforms accessible to current user

**GET /bots/{bot_id}/platforms/{platform}** - Get Platform Details

- **Purpose**: Retrieves detailed platform configuration and status
- **Response**: 
  - Platform configuration (non-sensitive fields)
  - Webhook status and URL
  - Connection health metrics
  - Usage statistics and rate limits
  - Error logs and troubleshooting info

**PUT /bots/{bot_id}/platforms/{platform}** - Update Platform Credentials

- **Purpose**: Updates platform credentials with re-validation
- **Security**: Re-encrypts updated credentials
- **Validation**: Tests new credentials before saving
- **Webhook Management**: Updates webhook URLs if changed

**DELETE /bots/{bot_id}/platforms/{platform}** - Remove Platform

- **Purpose**: Safely removes platform integration
- **Cleanup Process**:
  1. Deactivates webhook endpoints
  2. Clears platform-specific data
  3. Removes encrypted credentials
  4. Updates bot routing configuration
- **Safety**: Requires confirmation and checks for active dialogs

**POST /bots/{bot_id}/platforms/{platform}/test** - Test Connection

- **Purpose**: Validates platform credentials and connectivity
- **Testing Process**:
  - Credential format validation
  - API connectivity testing
  - Webhook URL validation
  - Permission verification
- **Response**: Detailed test results with specific error messages

**POST /bots/{bot_id}/platforms/{platform}/webhook** - Configure Webhook

- **Purpose**: Sets up or updates webhook configuration for platform
- **Request Body**: Webhook URL, verification token, and event subscriptions
- **Platform Registration**: Registers webhook with platform API
- **Validation**: Webhook URL accessibility and SSL certificate validation
- **Event Filtering**: Configures which events to receive from platform

Webhook Management
~~~~~~~~~~~~~~~~~~

**Webhook Endpoints:**

**POST /webhooks/{platform}/{bot_id}** - Platform Webhook Handler

- **Purpose**: Receives and processes webhooks from messaging platforms
- **Security**: Validates webhook signatures and authorization tokens
- **Processing**: Routes webhook events to DialogManager for conversation handling
- **Supported Events**: Messages, button clicks, media uploads, user actions
- **Response**: Platform-specific acknowledgment format

**GET /webhooks/{platform}/{bot_id}/status** - Webhook Status

- **Purpose**: Checks webhook configuration and connectivity status
- **Response**: Webhook health, last event timestamp, error counts

Services
--------

Bot Instance Service
~~~~~~~~~~~~~~~~~~~~

.. currentmodule:: api.services.bots

The InstanceService provides comprehensive business logic for bot instance lifecycle management. It handles creation, configuration, activation states, and platform integration with full validation and error handling.

**Key Methods:**

**async create_bot_instance(db, account_id, bot_data)**

- **Purpose**: Creates a new bot instance with comprehensive validation
- **Parameters**:
  - ``db`` (AsyncSession): Database session
  - ``account_id`` (UUID): Owner account identifier
  - ``bot_data`` (BotInstanceCreate): Bot creation data
- **Returns**: ``BotInstanceResponse`` - Created bot with generated ID and timestamps
- **Validation**:
  - Account existence and ownership verification
  - Bot name uniqueness within account
  - Configuration schema validation
  - Resource quota checking
- **Side Effects**:
  - Creates default dialog state configuration
  - Initializes analytics tracking
  - Creates audit log entry

**async get_bot_instance(db, bot_id)**

- **Purpose**: Retrieves bot instance with full details and statistics
- **Parameters**:
  - ``db`` (AsyncSession): Database session
  - ``bot_id`` (UUID): Bot identifier
- **Returns**: ``Optional[BotInstanceResponse]`` - Complete bot data or None
- **Includes**:
  - Basic bot information and configuration
  - Platform integration status
  - Active scenario count
  - Dialog statistics (active, completed, abandoned)
  - Performance metrics
- **Caching**: Results cached for performance optimization

**async update_bot_instance(db, bot_id, update_data)**

- **Purpose**: Updates bot configuration with validation
- **Parameters**:
  - ``db`` (AsyncSession): Database session
  - ``bot_id`` (UUID): Bot identifier
  - ``update_data`` (BotInstanceUpdate): Update payload
- **Returns**: ``Optional[BotInstanceResponse]`` - Updated bot data
- **Validation**:
  - Configuration consistency checks
  - Name uniqueness validation
  - Impact analysis for active dialogs
- **Side Effects**: Cache invalidation and webhook notifications

**async delete_bot_instance(db, bot_id)**

- **Purpose**: Safely deletes bot instance with cascade cleanup
- **Parameters**:
  - ``db`` (AsyncSession): Database session
  - ``bot_id`` (UUID): Bot identifier
- **Returns**: ``bool`` - True if deletion successful
- **Cascade Operations**:
  - Deactivates all platform webhooks
  - Archives active dialog states
  - Removes scenarios and media
  - Cleans up analytics data
- **Safety**: Requires bot to be inactive and no pending dialogs

**async activate_bot(db, bot_id)**

- **Purpose**: Activates bot for message processing with validation
- **Prerequisites**:
  - At least one valid platform credential
  - At least one active scenario
  - Webhook connectivity verification
- **Activation Process**:
  1. Validates all platform credentials
  2. Tests webhook endpoints
  3. Registers with platform APIs
  4. Updates bot status to active
  5. Starts message processing
- **Returns**: ``BotInstanceResponse`` - Updated bot with active status

**async deactivate_bot(db, bot_id)**

- **Purpose**: Deactivates bot while preserving all data
- **Deactivation Process**:
  1. Stops accepting new messages
  2. Completes processing of queued messages
  3. Unregisters platform webhooks
  4. Updates bot status to inactive
- **Data Preservation**: All dialogs, scenarios, and history maintained

**async list_account_bots(db, account_id, filters)**

- **Purpose**: Retrieves paginated list of bots for an account
- **Parameters**:
  - ``filters`` - Status, date range, search criteria
- **Returns**: Paginated bot list with summary information
- **Features**: Sorting, filtering, and search capabilities

Scenario Service
~~~~~~~~~~~~~~~~

The ScenarioService provides comprehensive scenario lifecycle management including creation, validation, version control, import/export, and activation management.

**Key Methods:**

**async create_scenario(db, bot_id, scenario_data)**

- **Purpose**: Creates new conversation scenario with comprehensive validation
- **Parameters**:
  - ``db`` (AsyncSession): Database session
  - ``bot_id`` (UUID): Owner bot identifier
  - ``scenario_data`` (BotScenarioCreate): Scenario definition
- **Returns**: ``BotScenarioResponse`` - Created scenario with validation results
- **Validation Process**:
  1. **Structure Validation**: Steps, transitions, and metadata format
  2. **Reference Integrity**: Step ID uniqueness and valid transitions
  3. **Variable Validation**: Variable mappings and data types
  4. **Condition Syntax**: Conditional logic expression validation
  5. **Media References**: Media file existence and accessibility
  6. **Button Configuration**: Button values and action validation
- **Version Control**: Automatic version numbering and conflict detection

**async validate_scenario_structure(scenario_data)**

- **Purpose**: Comprehensive scenario validation without database storage
- **Parameters**:
  - ``scenario_data`` (Dict[str, Any]): Raw scenario definition
- **Returns**: ``ScenarioValidationResult`` - Detailed validation report
- **Validation Categories**:
  - **Syntax Errors**: JSON structure and required fields
  - **Logic Errors**: Unreachable steps, infinite loops, dead ends
  - **Reference Errors**: Invalid step references, missing variables
  - **Type Errors**: Incorrect data types and format violations
- **Error Reporting**: Line numbers, specific error messages, and fix suggestions

**async import_scenario_from_json(db, bot_id, json_file, options)**

- **Purpose**: Imports scenario from JSON file with advanced processing
- **Parameters**:
  - ``json_file`` - Uploaded JSON file
  - ``options`` - Import settings (replace, merge, version handling)
- **Import Process**:
  1. File format validation and JSON parsing
  2. Schema compliance verification
  3. Scenario structure validation
  4. Conflict resolution with existing scenarios
  5. Version management and backup creation
- **Error Handling**: Detailed import reports with specific failure reasons
- **Rollback**: Automatic rollback on validation failures

**async export_scenario_to_json(db, scenario_id, format_options)**

- **Purpose**: Exports scenario to JSON with formatting options
- **Format Options**:
  - Pretty printing with indentation
  - Comment inclusion for documentation
  - Variable substitution examples
  - Test data inclusion
- **Usage**: Backup, migration, and sharing scenarios

**async activate_scenario(db, scenario_id, activation_data)**

- **Purpose**: Activates scenario for bot conversations
- **Parameters**:
  - ``activation_data`` (BotScenarioActivate): Activation configuration
- **Pre-Activation Validation**:
  - Complete scenario structure validation
  - Referenced media file verification
  - Variable mapping completeness
  - Step connectivity analysis
- **Activation Effects**:
  - Updates bot routing configuration
  - Invalidates dialog caches
  - Triggers analytics initialization

**async get_scenario_analytics(db, scenario_id, date_range)**

- **Purpose**: Retrieves scenario usage and performance analytics
- **Returns**: ``ScenarioAnalytics`` - Comprehensive usage statistics
- **Analytics Included**:
  - Step completion rates
  - User drop-off points
  - Average completion time
  - Most/least used paths
  - Error frequency by step
  - Condition evaluation statistics

**async clone_scenario(db, scenario_id, clone_options)**

- **Purpose**: Creates copy of scenario with modifications
- **Clone Options**:
  - Name and version modification
  - Step ID prefix/suffix
  - Variable name mapping
  - Selective step inclusion
- **Use Cases**: A/B testing, scenario variants, backup creation

**async get_scenario_dependencies(db, scenario_id)**

- **Purpose**: Analyzes scenario dependencies and impact
- **Returns**: Dependency graph with:
  - Referenced media files
  - Variable dependencies
  - External service integrations
  - Platform-specific features
- **Impact Analysis**: Effects of scenario changes on active dialogs

Dialog Service
~~~~~~~~~~~~~~

The DialogService provides comprehensive conversation state management with advanced features for dialog lifecycle, history tracking, analytics, and multi-platform support.

**Key Methods:**

**async process_dialog_message(db, bot_id, platform, chat_id, message_data)**

- **Purpose**: Central message processing with state management
- **Parameters**:
  - ``message_data`` (Dict[str, Any]): Structured message information
- **Returns**: ``DialogProcessingResult`` - Response data and state updates
- **Processing Pipeline**:
  1. **State Retrieval**: Gets or creates dialog state
  2. **Scenario Processing**: Executes current scenario step
  3. **Input Validation**: Validates user input against expected format
  4. **Variable Collection**: Updates collected conversation data
  5. **State Transition**: Moves to next appropriate step
  6. **Response Generation**: Creates platform-appropriate response
  7. **History Logging**: Records conversation interaction
  8. **Analytics Update**: Updates conversation metrics

**async get_or_create_dialog_state(db, bot_id, platform, chat_id)**

- **Purpose**: Retrieves existing dialog or creates new one with initialization
- **Returns**: ``DialogStateResponse`` - Complete dialog state information
- **Creation Process**:
  - Determines appropriate starting scenario
  - Initializes collected data structure
  - Sets up user profile information
  - Configures platform-specific settings
  - Creates initial history entry
- **Caching**: State cached for performance with TTL management

**async update_dialog_state(db, dialog_id, state_updates)**

- **Purpose**: Updates dialog state with validation and consistency checks
- **Parameters**:
  - ``state_updates`` (DialogStateUpdate): State modification data
- **Validation**:
  - Step ID exists in current scenario
  - Collected data format compliance
  - State transition validity
  - Concurrent update handling
- **Side Effects**:
  - Cache invalidation and update
  - History entry creation
  - Analytics event triggering
  - Webhook notifications for external systems

**async get_dialog_history(db, dialog_id, pagination, filters)**

- **Purpose**: Retrieves conversation history with advanced filtering
- **Parameters**:
  - ``pagination`` - Limit, offset, ordering
  - ``filters`` - Message type, date range, search terms
- **Returns**: ``DialogHistoryResponse`` - Paginated conversation history
- **Features**:
  - Full-text search in message content
  - Message type filtering (user, bot, system)
  - Date range and time-based filtering
  - Export capabilities (JSON, CSV)
  - Media content inclusion

**async analyze_dialog_flow(db, dialog_id)**

- **Purpose**: Analyzes conversation flow and provides insights
- **Returns**: ``DialogFlowAnalysis`` - Comprehensive flow analysis
- **Analysis Includes**:
  - Step progression timeline
  - User engagement metrics
  - Response time analysis
  - Drop-off point identification
  - Path deviation from expected flow
  - Variable collection efficiency

**async reset_dialog_state(db, dialog_id, reset_options)**

- **Purpose**: Resets dialog to specified state while preserving history
- **Reset Options**:
  - Complete reset to beginning
  - Reset to specific checkpoint
  - Partial reset (preserve selected variables)
  - Scenario change with state migration
- **History Preservation**: Previous conversation archived but accessible

**async export_dialog_data(db, dialog_id, export_format)**

- **Purpose**: Exports complete dialog data for analysis or backup
- **Export Formats**:
  - JSON with full conversation tree
  - CSV for spreadsheet analysis
  - XML for system integration
  - PDF for human-readable reports
- **Data Included**: Messages, state changes, media, analytics

**async get_dialog_analytics(db, dialog_id)**

- **Purpose**: Provides detailed analytics for individual conversation
- **Returns**: ``DialogAnalytics`` - Comprehensive conversation metrics
- **Metrics Included**:
  - Conversation duration and response times
  - Step completion rates and timing
  - User engagement indicators
  - Error frequency and types
  - Media interaction statistics
  - Variable collection success rates

**async handle_dialog_timeout(db, dialog_id, timeout_action)**

- **Purpose**: Manages dialog timeouts and inactivity handling
- **Timeout Actions**:
  - Send reminder message
  - Reset to previous checkpoint
  - Mark as abandoned
  - Trigger follow-up workflow
- **Configuration**: Timeout thresholds and actions configurable per bot

**async merge_dialog_data(db, primary_dialog_id, secondary_dialog_id)**

- **Purpose**: Merges data from multiple dialog sessions (same user, different platforms)
- **Use Cases**: Cross-platform continuity, duplicate session handling
- **Merge Strategy**: Configurable rules for data conflicts and history combination

Media Service
~~~~~~~~~~~~~

The MediaService handles media processing, storage, and delivery for bot conversations with support for multiple formats and platforms.

**Key Methods:**

**async upload_media(db, bot_id, media_file, metadata)**

- **Purpose**: Uploads and processes media files for bot use
- **Supported Formats**: Images (JPEG, PNG, GIF), Videos (MP4, MOV), Audio (MP3, WAV), Documents (PDF, DOC)
- **Processing Pipeline**:
  1. File validation and virus scanning
  2. Format conversion and optimization
  3. Thumbnail generation for images/videos
  4. Platform-specific format preparation
  5. CDN upload and URL generation
  6. Database record creation
- **Returns**: ``MediaUploadResponse`` - Media URLs and metadata

**async get_media_by_platform(db, media_id, platform)**

- **Purpose**: Retrieves platform-optimized media URLs
- **Platform Optimization**: Different sizes, formats, and delivery methods per platform
- **Caching**: CDN caching with appropriate headers

**async process_media_group(db, media_files, group_metadata)**

- **Purpose**: Handles media groups (albums) with proper ordering
- **Features**: Maintains order, generates group thumbnails, batch processing

Webhook Service
~~~~~~~~~~~~~~~

The WebhookService manages webhook registration, validation, and event processing for all supported platforms.

**Key Methods:**

**async register_webhook(db, bot_id, platform, webhook_config)**

- **Purpose**: Registers webhook with platform API
- **Validation**: URL accessibility, SSL certificate verification
- **Configuration**: Event subscriptions, verification tokens

**async process_webhook_event(db, platform, bot_id, event_data)**

- **Purpose**: Processes incoming webhook events
- **Security**: Signature validation, token verification
- **Event Routing**: Routes to appropriate dialog processing

Data Schemas
------------

Bot Schemas
~~~~~~~~~~~

.. currentmodule:: api.schemas.bots

The bot schemas define Pydantic models for request/response validation across all bot management endpoints.

Usage Examples
--------------

Creating a Complete Bot Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   from api.services.bots.instance_service import InstanceService
   from api.services.bots.scenario_service import ScenarioService
   from api.schemas.bots.instance_schemas import BotInstanceCreate
   from api.schemas.bots.scenario_schemas import BotScenarioCreate

   async def create_complete_bot():
       # Create bot instance
       bot_data = BotInstanceCreate(
           account_id=account_uuid,
           name="Welcome Bot",
           description="Automated staff onboarding bot"
       )
       bot = await InstanceService.create_bot_instance(db, bot_data)
       
       # Add platform credentials
       credential_data = BotPlatformCredentialCreate(
           platform="telegram",
           credentials={"token": "your-bot-token"}
       )
       await InstanceService.add_platform_credential(db, bot.id, credential_data)
       
       # Create scenario
       scenario_data = BotScenarioCreate(
           bot_id=bot.id,
           name="Onboarding Scenario",
           version="1.0",
           scenario_data={
               "version": "1.0",
               "steps": {
                   "welcome": {
                       "id": "welcome",
                       "type": "message",
                       "message": {"text": "Welcome to GET INN!"},
                       "next_step": "collect_name"
                   }
               }
           }
       )
       await ScenarioService.create_scenario(db, scenario_data)

Processing Incoming Messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from bot_manager.dialog_manager import DialogManager
   from integrations.platforms.telegram import TelegramAdapter

   async def process_webhook():
       # Initialize dialog manager
       telegram_adapter = TelegramAdapter(bot_token)
       dialog_manager = DialogManager(db)
       await dialog_manager.register_platform_adapter("telegram", telegram_adapter)
       
       # Process incoming webhook
       response = await dialog_manager.process_incoming_message(
           bot_id=bot_uuid,
           platform="telegram", 
           platform_chat_id="123456789",
           update_data=telegram_update
       )
       
       return response

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from api.core.exceptions import BotNotFoundException
   
   try:
       bot = await InstanceService.get_bot_instance(db, bot_id)
   except BotNotFoundException:
       # Handle bot not found
       return {"error": "Bot not found"}
   except Exception as e:
       # Handle other errors
       logger.error(f"Error retrieving bot: {e}")
       return {"error": "Internal server error"}