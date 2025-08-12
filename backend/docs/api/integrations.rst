Integration APIs 🚧
===============

.. note::
   **Implementation Status: In Development - Mixed Implementation**
   
   **Currently Available:**
   - iiko POS integration endpoints (``/v1/api/accounts/{account_id}/integrations/iiko/connect``, ``/status``)
   - Basic integration framework
   - Account-level integration credentials support
   
   **Documented But Not Fully Implemented:**
   - Azure OpenAI integration (endpoints documented but may not be fully functional)
   - Comprehensive menu synchronization
   - Advanced data transformation
   - Custom webhook management for integrations
   
   **Fully Functional:**
   - Telegram platform integration (via bot management system)
   
   The comprehensive features described in this documentation represent the planned integration capabilities.

The Integration APIs provide seamless connectivity with external systems including POS systems, AI services, payment processors, and third-party platforms. These APIs enable restaurant operators to connect their existing tools and services with the GET INN platform.

.. grid:: 3
   :gutter: 2

   .. grid-item-card:: 🍽️ POS Systems
      :class-header: bg-primary text-white
      
      Connect with popular Point of Sale systems for menu and order synchronization.
      
      **Supported Systems:**
      
      - iiko Restaurant Management (basic)
      - Square POS (planned)
      - Toast POS (planned)
      - Resy POS (planned)
      
   .. grid-item-card:: 🤖 AI Services
      :class-header: bg-success text-white
      
      Leverage artificial intelligence for enhanced restaurant operations.
      
      **AI Capabilities:**
      
      - Azure OpenAI integration (planned)
      - Document processing (OCR) (planned)
      - Natural language processing (planned)
      - Predictive analytics (planned)
      
   .. grid-item-card:: 💳 Payment Systems
      :class-header: bg-info text-white
      
      Integrate with payment processors and financial services.
      
      **Payment Partners:**
      
      - Stripe payments (planned)
      - PayPal integration (planned)
      - Banking APIs (planned)
      - Accounting systems (planned)

Quick Reference
===============

.. tabs::

   .. tab:: Available Endpoints

      .. code-block:: text

         # iiko POS Integration (Basic Implementation)
         POST   /v1/api/accounts/{account_id}/integrations/iiko/connect
         GET    /v1/api/accounts/{account_id}/integrations/iiko/status

   .. tab:: Authentication

      Integration endpoints require account-level API keys:

      .. code-block:: bash

         curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
              https://api.getinn.com/v1/api/accounts/{account_id}/integrations/iiko/status

   .. tab:: Rate Limits

      .. list-table::
         :header-rows: 1

         * - Integration Type
           - Rate Limit
         * - POS Systems
           - 100/hour
         * - AI Services
           - 50/hour (planned)
         * - Webhooks
           - 200/hour (planned)
         * - Payment APIs
           - 50/hour (planned)

Currently Available Endpoints
=============================

iiko POS Integration
--------------------

.. list-table:: iiko Integration Endpoints (Basic Implementation)
   :header-rows: 1
   :widths: 10 30 15 15 30

   * - Method
     - Endpoint
     - Auth Required
     - Status
     - Description
   * - POST
     - ``/v1/api/accounts/{account_id}/integrations/iiko/connect``
     - ✅ Yes
     - Available
     - Connect iiko integration for account
   * - GET
     - ``/v1/api/accounts/{account_id}/integrations/iiko/status``
     - ✅ Yes
     - Available
     - Get iiko integration status

Basic iiko Integration
~~~~~~~~~~~~~~~~~~~~~~

**Connect iiko Integration:** ``POST /v1/api/accounts/{account_id}/integrations/iiko/connect``

**Get Integration Status:** ``GET /v1/api/accounts/{account_id}/integrations/iiko/status``

These endpoints provide basic iiko POS system integration capabilities. The current implementation supports connecting an account to iiko services and checking the integration status.

Usage Examples
==============

.. tabs::

   .. tab:: cURL

      .. code-block:: bash

         # Connect iiko integration
         curl -X POST https://api.getinn.com/v1/api/accounts/{account_id}/integrations/iiko/connect \
           -H "Authorization: Bearer YOUR_JWT_TOKEN" \
           -H "Content-Type: application/json" \
           -d '{
             "api_login": "your_iiko_login",
             "api_password": "your_iiko_password",
             "organization_id": "your_org_id"
           }'

         # Check integration status
         curl -X GET https://api.getinn.com/v1/api/accounts/{account_id}/integrations/iiko/status \
           -H "Authorization: Bearer YOUR_JWT_TOKEN"

   .. tab:: Response Format

      Basic integration status response:

      .. code-block:: json

         {
           "success": true,
           "data": {
             "integration_type": "iiko",
             "status": "connected",
             "connected_at": "2023-01-15T10:30:00Z",
             "last_sync": "2023-01-15T12:00:00Z",
             "organization_id": "your_org_id"
           }
         }

Telegram Integration (Production Ready)
=======================================

The Telegram integration is fully functional and production-ready through the Bot Management system:

**Available Features:**
- Complete bot management via ``/v1/api/bots`` endpoints
- Real-time message processing via ``/v1/api/webhooks/telegram/{bot_id}``
- Media handling and file uploads
- Dialog state management
- Scenario-based conversation flows

**Integration Status:** ✅ Production Ready

Refer to the `Bot Management API <bot-management.html>`_ and `Webhook Management API <webhooks.html>`_ documentation for complete Telegram integration details.

Future Development
==================

Planned Integration Capabilities
--------------------------------

**POS System Integrations:**
- Advanced menu synchronization with real-time updates
- Order management and processing
- Inventory level monitoring
- Customer data synchronization
- Payment processing integration

**AI Service Integrations:**
- Azure OpenAI API integration for customer service
- Document processing with OCR capabilities
- Natural language processing for menu analysis
- Predictive analytics for demand forecasting
- Intelligent recommendation systems

**Payment System Integrations:**
- Stripe payment processing
- PayPal integration
- Banking API connectivity
- Accounting system synchronization (QuickBooks, Xero)
- Multi-currency support

**Third-Party Platform Integrations:**
- WhatsApp Business API
- Social media platforms
- Delivery service APIs (DoorDash, Uber Eats)
- Review platform integrations (Google, Yelp)
- Marketing automation platforms

Integration Configuration Framework
----------------------------------

The platform will support a unified integration configuration system:

- **Account-level credential management**
- **Webhook endpoint registration**
- **Data transformation rules**
- **Sync frequency configuration**
- **Error handling and retry policies**
- **Integration health monitoring**

Error Handling
==============

.. list-table:: Integration API Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Status Code
     - Error Code
     - Description
   * - 400
     - INVALID_CREDENTIALS
     - Integration credentials are invalid or expired
   * - 403
     - INTEGRATION_DISABLED
     - Integration is disabled for this account
   * - 404
     - INTEGRATION_NOT_FOUND
     - Requested integration does not exist
   * - 422
     - CONNECTION_FAILED
     - Failed to establish connection with external service
   * - 429
     - RATE_LIMIT_EXCEEDED
     - Integration rate limit exceeded
   * - 502
     - EXTERNAL_SERVICE_ERROR
     - External service (iiko, etc.) returned an error
   * - 503
     - INTEGRATION_UNAVAILABLE
     - Integration service is temporarily unavailable
   * - 504
     - INTEGRATION_TIMEOUT
     - Request to external service timed out