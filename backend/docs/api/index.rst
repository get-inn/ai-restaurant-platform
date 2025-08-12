GET INN Restaurant Platform API Reference
==========================================

Welcome to the comprehensive API documentation for the GET INN Restaurant Platform. This documentation provides detailed information about all available endpoints, data models, and integration patterns.

.. note::
   **Implementation Status Legend:**
   
   - ✅ **Production Ready**: Fully implemented and tested
   - 🚧 **In Development**: Partially implemented with basic functionality
   - 📋 **Planned**: Documented but not yet implemented
   - ⚠️ **Limited**: Basic endpoints exist but advanced features are placeholders

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: 🤖 Bot Management API ✅
      :link: bot-management
      :link-type: doc
      :class-header: bg-primary text-white
      
      Complete bot lifecycle management, conversation scenarios, and platform integrations.
      
      **Key Features:**
      
      - Bot instance management
      - Conversation scenarios 
      - Multi-platform support
      - Dialog state management
      
      **Status:** Production Ready - All features fully implemented
      
   .. grid-item-card:: 🔗 Integration APIs 🚧
      :link: integrations
      :link-type: doc
      :class-header: bg-success text-white
      
      External system integrations including POS systems, AI services, and third-party platforms.
      
      **Integrations:**
      
      - iiko POS System (basic implementation)
      - Azure OpenAI (documented)
      - Telegram & WhatsApp (Telegram ready)
      - Custom webhooks (planned)
      
      **Status:** In Development - Basic iiko integration available

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: 👥 Labor Management 📋
      :link: labor-management
      :link-type: doc
      :class-header: bg-info text-white
      
      Staff onboarding, training management, and HR workflow automation.
      
      **Features:**
      
      - Employee onboarding (planned)
      - Training workflows (planned)
      - HR automation (planned)
      - Performance tracking (planned)
      
      **Status:** Planned - Basic onboarding endpoint exists as placeholder
      
   .. grid-item-card:: 🍽️ Chef & Menu APIs ⚠️
      :link: chef-menu
      :link-type: doc
      :class-header: bg-warning text-white
      
      Recipe management, menu planning, and culinary data processing.
      
      **Capabilities:**
      
      - Recipe management (planned)
      - Menu optimization (planned)
      - Ingredient tracking (planned)
      - Nutritional analysis (planned)
      
      **Status:** Limited - Basic menu CRUD endpoints exist as placeholders

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: 🔐 Authentication & Security ✅
      :link: authentication
      :link-type: doc
      :class-header: bg-dark text-white
      
      User authentication, authorization, and security management.
      
      **Features:**
      
      - JWT token authentication
      - Role-based access control
      - Session management
      - Security monitoring
      
      **Status:** Production Ready - Full authentication system implemented
      
   .. grid-item-card:: 🏢 Account & Organization ✅
      :link: account-management
      :link-type: doc
      :class-header: bg-secondary text-white
      
      Multi-tenant account management and organizational structure.
      
      **Capabilities:**
      
      - Restaurant chain management
      - Multi-location support
      - User management
      - Settings and preferences
      
      **Status:** Production Ready - Full account hierarchy implemented

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: 🚚 Supplier Management ⚠️
      :link: supplier-management
      :link-type: doc
      :class-header: bg-purple text-white
      
      Complete supplier lifecycle management with automated invoice processing and inventory tracking.
      
      **Advanced Features:**
      
      - OCR invoice processing (planned)
      - Automated reconciliation (planned)
      - Performance analytics (planned)
      - Document management (planned)
      - Inventory tracking (planned)
      - Payment workflows (planned)
      
      **Status:** Limited - Basic supplier CRUD endpoints exist, advanced features planned
      
   .. grid-item-card:: 🔗 Webhook Management 🚧
      :link: webhooks
      :link-type: doc
      :class-header: bg-warning text-white
      
      Real-time event notifications and webhook management system.
      
      **Features:**
      
      - Telegram webhooks (production ready)
      - WhatsApp webhooks (documented)
      - Custom webhook endpoints (planned)
      - Event processing (basic)
      - Signature verification (planned)
      
      **Status:** In Development - Telegram webhooks fully functional

Quick Start Guide
=================

.. tabs::

   .. tab:: Authentication

      All API requests require JWT authentication:

      .. code-block:: bash

         curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
              -H "Content-Type: application/json" \
              https://api.getinn.com/v1/bots

   .. tab:: Rate Limits

      API rate limits per endpoint:

      .. list-table::
         :header-rows: 1

         * - Endpoint Category
           - Rate Limit
           - Time Window
         * - Bot Management
           - 100 requests
           - 1 minute
         * - Webhooks
           - 1000 requests  
           - 1 minute
         * - Media Upload
           - 50 requests
           - 1 minute

   .. tab:: Error Codes

      Standard HTTP status codes with detailed error responses:

      .. code-block:: json

         {
           "error": {
             "code": "VALIDATION_ERROR",
             "message": "Invalid request data",
             "details": {
               "field": "bot_name",
               "issue": "Name must be between 1-100 characters"
             }
           }
         }

API Architecture Overview
========================

.. mermaid::

   graph TB
       subgraph "Client Applications"
           WEB[Web Dashboard]
           MOBILE[Mobile Apps]
           CLI[CLI Tools]
       end
       
       subgraph "API Gateway Layer"
           AUTH[Authentication]
           RATE[Rate Limiting]
           VALID[Validation]
       end
       
       subgraph "Core API Services"
           BOTS[Bot Management]
           LABOR[Labor Management]
           CHEF[Chef Tools]
           SUPPLIER[Supplier Management]
       end
       
       subgraph "External Integrations"
           TELEGRAM[Telegram API]
           WHATSAPP[WhatsApp API]
           IIKO[iiko POS]
           AZURE[Azure OpenAI]
       end
       
       subgraph "Data Layer"
           POSTGRES[(PostgreSQL)]
           REDIS[(Redis Cache)]
           MEDIA[Media Storage]
       end
       
       WEB --> AUTH
       MOBILE --> AUTH
       CLI --> AUTH
       
       AUTH --> RATE
       RATE --> VALID
       
       VALID --> BOTS
       VALID --> LABOR
       VALID --> CHEF
       VALID --> SUPPLIER
       
       BOTS --> TELEGRAM
       BOTS --> WHATSAPP
       LABOR --> AZURE
       SUPPLIER --> IIKO
       
       BOTS --> POSTGRES
       LABOR --> POSTGRES
       CHEF --> POSTGRES
       SUPPLIER --> POSTGRES
       
       BOTS --> REDIS
       BOTS --> MEDIA

Core API Components
==================

Database Models
---------------

The platform uses SQLAlchemy ORM with PostgreSQL for data persistence:

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: **Bot Models**
      :class-header: bg-primary text-white
      
      - ``BotInstance``: Bot configuration and metadata
      - ``BotScenario``: Conversation flow definitions
      - ``BotDialogState``: Active conversation states
      - ``BotPlatformCredential``: Platform authentication
      
   .. grid-item-card:: **Core Models**
      :class-header: bg-secondary text-white
      
      - ``Account``: Organization/restaurant chain
      - ``User``: Platform user accounts
      - ``Restaurant``: Individual locations
      - ``Store``: Inventory storage locations

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: **Labor Models**
      :class-header: bg-info text-white
      
      - ``Employee``: Staff member profiles
      - ``OnboardingFlow``: Training workflows
      - ``TaskAssignment``: Work assignments
      - ``PerformanceMetric``: KPI tracking
      
   .. grid-item-card:: **Integration Models**
      :class-header: bg-warning text-white
      
      - ``AccountIntegrationCredentials``: External service auth
      - ``WebhookEndpoint``: Event notification configs
      - ``SyncStatus``: Data synchronization state
      - ``ApiUsageMetric``: API consumption tracking

API Dependencies
---------------

The dependency injection system provides shared services across all endpoints:

.. code-block:: python

   from api.dependencies.auth import get_current_user
   from api.dependencies.db import get_async_db
   
   @router.get("/bots/{bot_id}")
   async def get_bot(
       bot_id: UUID,
       current_user: User = Depends(get_current_user),
       db: AsyncSession = Depends(get_async_db)
   ):
       # Endpoint implementation
       pass

**Key Dependencies:**

- **Authentication** (``api.dependencies.auth``): JWT validation, user context, permissions
- **Database** (``api.dependencies.async_db``): Async database session management  
- **Cache** (``api.dependencies.cache``): Redis caching for performance
- **Rate Limiting** (``api.dependencies.rate_limit``): Request throttling
- **Validation** (``api.dependencies.validation``): Input sanitization

Actually Implemented Endpoints Summary
=======================================

✅ Production Ready APIs
------------------------

.. list-table:: Bot Management (Fully Implemented)
   :header-rows: 1
   :widths: 10 30 15 40

   * - Method
     - Endpoint
     - Auth Required
     - Description
   * - POST
     - ``/v1/api/accounts/{account_id}/bots``
     - ✅ Yes
     - Create new bot instance
   * - GET
     - ``/v1/api/accounts/{account_id}/bots``
     - ✅ Yes
     - List account bots with pagination
   * - GET
     - ``/v1/api/bots/{bot_id}``
     - ✅ Yes
     - Get bot details and statistics
   * - PUT
     - ``/v1/api/bots/{bot_id}``
     - ✅ Yes
     - Update bot configuration
   * - DELETE
     - ``/v1/api/bots/{bot_id}``
     - ✅ Admin
     - Delete bot and all data
   * - POST
     - ``/v1/api/bots/{bot_id}/scenarios``
     - ✅ Yes
     - Create conversation scenario
   * - POST
     - ``/v1/api/bots/{bot_id}/scenarios/upload``
     - ✅ Yes
     - Upload JSON scenario file
   * - POST
     - ``/v1/api/webhooks/telegram/{bot_id}``
     - 🔐 Platform
     - Telegram webhook handler (production ready)

.. list-table:: Authentication & Account Management (Fully Implemented)
   :header-rows: 1
   :widths: 10 30 15 40

   * - Method
     - Endpoint
     - Auth Required
     - Description
   * - POST
     - ``/v1/api/auth/login``
     - ❌ No
     - User login with email/password
   * - POST
     - ``/v1/api/auth/refresh``
     - ✅ Yes
     - Refresh access token
   * - GET
     - ``/v1/api/auth/me``
     - ✅ Yes
     - Get current user info
   * - POST
     - ``/v1/api/accounts``
     - ✅ Admin
     - Create new account
   * - GET
     - ``/v1/api/accounts/{account_id}``
     - ✅ Yes
     - Get account details
   * - POST
     - ``/v1/api/accounts/{account_id}/restaurants``
     - ✅ Manager
     - Create restaurant for account
   * - GET
     - ``/v1/api/accounts/{account_id}/suppliers``
     - ✅ Yes
     - List account suppliers

🚧 Limited Implementation APIs
------------------------------

.. list-table:: Basic Endpoints Available
   :header-rows: 1
   :widths: 15 30 15 40

   * - API Module
     - Endpoint
     - Status
     - Description
   * - **iiko Integration**
     - ``/v1/api/accounts/{id}/integrations/iiko/connect``
     - Available
     - Connect iiko integration
   * - **iiko Integration**
     - ``/v1/api/accounts/{id}/integrations/iiko/status``
     - Available
     - Get integration status
   * - **Chef & Menu**
     - ``/v1/api/chef`` (CRUD operations)
     - Placeholder
     - Basic menu management placeholders
   * - **Supplier Management**
     - ``/v1/api/accounts/{id}/suppliers`` (Basic CRUD)
     - Placeholder
     - Basic supplier CRUD operations
   * - **Labor Management**
     - ``/v1/api/labor/onboarding``
     - Placeholder
     - Basic onboarding placeholder

SDK and Client Libraries
=======================

.. tabs::

   .. tab:: Python

      Install the official Python client:

      .. code-block:: bash

         pip install getinn-api-client

      Basic usage:

      .. code-block:: python

         from getinn_api import GetInnClient
         
         client = GetInnClient(
             api_key="your-api-key",
             base_url="https://api.getinn.com/v1"
         )
         
         # Create a bot
         bot = client.bots.create(
             account_id="account-uuid",
             name="My Bot",
             description="Automated assistant"
         )
         
         # List scenarios
         scenarios = client.scenarios.list(bot_id=bot.id)

   .. tab:: JavaScript/Node.js

      Install the Node.js client:

      .. code-block:: bash

         npm install @getinn/api-client

      Basic usage:

      .. code-block:: javascript

         const { GetInnClient } = require('@getinn/api-client');
         
         const client = new GetInnClient({
           apiKey: 'your-api-key',
           baseUrl: 'https://api.getinn.com/v1'
         });
         
         // Create a bot
         const bot = await client.bots.create({
           accountId: 'account-uuid',
           name: 'My Bot',
           description: 'Automated assistant'
         });
         
         // List scenarios
         const scenarios = await client.scenarios.list({ botId: bot.id });

   .. tab:: cURL

      Direct HTTP requests using cURL:

      .. code-block:: bash

         # Create a bot
         curl -X POST https://api.getinn.com/v1/accounts/{account_id}/bots \\
           -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
           -H "Content-Type: application/json" \\
           -d '{
             "name": "My Bot",
             "description": "Automated assistant"
           }'
         
         # Get bot details
         curl -X GET https://api.getinn.com/v1/bots/{bot_id} \\
           -H "Authorization: Bearer YOUR_JWT_TOKEN"

Detailed API Reference
=====================

For comprehensive documentation of each API endpoint, including request/response schemas, examples, and error handling:

.. toctree::
   :maxdepth: 2
   :caption: API Modules

   authentication
   account-management
   bot-management
   supplier-management
   integrations
   webhooks
   labor-management
   chef-menu