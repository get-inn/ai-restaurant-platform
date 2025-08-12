Webhook Management API 🚧
====================

.. note::
   **Implementation Status: In Development - Telegram Production Ready**
   
   **Currently Available & Production Ready:**
   - Telegram webhook handler (``POST /v1/api/webhooks/telegram/{bot_id}``)
   - Telegram bot message processing
   - Dialog state management via webhooks
   - Media upload handling through webhooks
   
   **Documented But Not Fully Implemented:**
   - WhatsApp webhook handlers
   - Generic webhook management endpoints
   - Custom webhook creation and configuration
   - Webhook testing and monitoring tools
   - HMAC signature verification for custom webhooks
   - Retry mechanisms for failed deliveries
   
   The Telegram webhook system is battle-tested and handles all bot interactions in production.

The Webhook Management API enables real-time event notifications and integrations with external systems. Webhooks allow your applications to receive instant notifications when events occur in the GET INN platform, enabling responsive and automated workflows.

.. grid:: 3
   :gutter: 2

   .. grid-item-card:: 🔗 Telegram Webhooks ✅
      :class-header: bg-primary text-white
      
      Production-ready Telegram webhook processing for bot interactions.
      
      **Features:**
      
      - Real-time message processing
      - Dialog state management
      - Media file handling
      - Automatic bot responses
      
   .. grid-item-card:: 📨 Event Processing
      :class-header: bg-success text-white
      
      Process and route incoming webhook events with intelligent handling.
      
      **Features:**
      
      - Event validation (basic)
      - Message routing (Telegram)
      - Dialog updates (Telegram)
      - Response generation (planned)
      
   .. grid-item-card:: 🛡️ Security & Reliability
      :class-header: bg-info text-white
      
      Basic security and reliability for webhook processing.
      
      **Security:**
      
      - Platform authentication (Telegram)
      - Bot ID validation
      - Basic request validation
      - Error handling (planned)

Quick Reference
===============

.. tabs::

   .. tab:: Available Endpoints

      .. code-block:: text

         # Platform Webhooks (Production Ready)
         POST   /v1/api/webhooks/telegram/{bot_id}

   .. tab:: Event Types

      **Current Bot Events:**
      - Message received from user
      - Button/keyboard interactions
      - Media files uploaded
      - Dialog state changes
      
      **Planned System Events:**
      - Order events (planned)
      - Menu updates (planned)
      - Integration sync events (planned)

   .. tab:: Security

      **Current Webhook Security:**
      
      - Telegram platform authentication
      - Bot ID validation and authorization
      - Request format validation
      - Basic error handling

Currently Available Endpoints
=============================

Platform Webhooks (Production Ready)
------------------------------------

.. list-table:: Available Webhook Endpoints
   :header-rows: 1
   :widths: 10 25 15 15 35

   * - Method
     - Endpoint
     - Auth Required
     - Status
     - Description
   * - POST
     - ``/v1/api/webhooks/telegram/{bot_id}``
     - 🔐 Platform Auth
     - ✅ Production
     - Telegram webhook handler - fully functional

Telegram Webhook Handler
~~~~~~~~~~~~~~~~~~~~~~~~

Process incoming Telegram bot updates including messages, button clicks, and media uploads.

**Endpoint:** ``POST /v1/api/webhooks/telegram/{bot_id}``

**Authentication:** Telegram platform authentication via bot token validation

**Functionality:**
- Processes all Telegram update types (messages, callbacks, media)
- Updates dialog state based on bot scenarios
- Triggers appropriate bot responses
- Handles media file uploads and storage
- Manages conversation flow and transitions

**Request Body (Telegram Update Object):**

.. code-block:: json

   {
     "update_id": 123456789,
     "message": {
       "message_id": 1234,
       "from": {
         "id": 987654321,
         "is_bot": false,
         "first_name": "John",
         "last_name": "Doe",
         "username": "johndoe"
       },
       "chat": {
         "id": 987654321,
         "first_name": "John",
         "last_name": "Doe",
         "username": "johndoe",
         "type": "private"
       },
       "date": 1674567890,
       "text": "Hello, I'd like to place an order"
     }
   }

**Success Response (200 OK):**

.. code-block:: json

   {
     "success": true,
     "data": {
       "update_id": 123456789,
       "processed_at": "2023-01-15T14:30:00Z",
       "bot_id": "123e4567-e89b-12d3-a456-426614174000",
       "platform_chat_id": "987654321",
       "event_type": "message.received",
       "processing_time_ms": 156,
       "response_sent": true
     }
   }

Usage Examples
==============

.. tabs::

   .. tab:: Telegram Configuration

      .. code-block:: bash

         # Set up Telegram webhook (done automatically by platform)
         # The platform configures this webhook URL with Telegram:
         # https://api.getinn.com/v1/api/webhooks/telegram/{bot_id}

         # Telegram will POST updates to this endpoint
         # No manual configuration required - handled by bot management system

   .. tab:: Response Handling

      The webhook automatically processes incoming updates:

      .. code-block:: json

         {
           "webhook_url": "https://api.getinn.com/v1/api/webhooks/telegram/bot-uuid",
           "processing": {
             "message_received": "Dialog state updated automatically",
             "response_generated": "Based on current scenario step",
             "next_action": "Determined by bot scenario logic"
           }
         }

Integration with Bot Management
===============================

The Telegram webhook system is tightly integrated with the Bot Management API:

**Automatic Setup:**
- Webhooks are automatically configured when bots are activated
- Bot credentials are used for webhook authentication
- Dialog states are managed through webhook processing

**Scenario Execution:**
- Incoming messages trigger scenario step evaluation
- Bot responses are generated based on current dialog state
- Media handling is processed through webhook events

**For Complete Bot Management:**
Refer to the `Bot Management API <bot-management.html>`_ documentation for:
- Bot instance creation and management
- Scenario configuration and upload
- Dialog state monitoring
- Media file management

Future Development
==================

Planned Webhook Features
------------------------

**Generic Webhook Management:**
- Custom webhook endpoint creation and management
- Webhook testing and validation tools
- Event subscription management
- Webhook delivery monitoring and logs

**Additional Platform Support:**
- WhatsApp Business API webhook handlers
- Custom platform webhook adapters
- Multi-platform event routing

**Enhanced Security:**
- HMAC signature verification for custom webhooks
- IP whitelisting and rate limiting
- Webhook authentication tokens
- Request signing and validation

**Advanced Event Processing:**
- Event filtering and transformation
- Custom event types and payloads
- Batch event processing
- Event replay and recovery

**Monitoring and Analytics:**
- Webhook delivery success rates
- Performance metrics and latency tracking
- Error monitoring and alerting
- Usage analytics and reporting

Error Handling
==============

.. list-table:: Webhook Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Status Code
     - Error Code
     - Description
   * - 400
     - INVALID_UPDATE_FORMAT
     - Webhook payload format is invalid
   * - 401
     - INVALID_BOT_TOKEN
     - Bot authentication failed
   * - 404
     - BOT_NOT_FOUND
     - Bot does not exist or is inactive
   * - 422
     - PROCESSING_FAILED
     - Failed to process webhook update
   * - 500
     - INTERNAL_ERROR
     - Server error during webhook processing