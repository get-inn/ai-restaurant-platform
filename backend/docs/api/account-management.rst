Account Management API ✅
=====================

.. note::
   **Implementation Status: Production Ready**
   
   The account management system is fully implemented with complete CRUD operations for accounts, restaurants, stores, and suppliers. Multi-tenant data isolation and role-based access control are production-ready.

The Account Management API provides comprehensive tools for managing restaurant organizations, locations, stores, and user accounts within the GET INN platform. This API serves as the foundation for multi-tenant restaurant operations.

.. grid:: 3
   :gutter: 2

   .. grid-item-card:: 🏢 Account Management
      :class-header: bg-primary text-white
      
      Manage restaurant chains and organizations with multi-tenant support.
      
      **Features:**
      
      - Restaurant chain management
      - Multi-location support
      - Account-level settings
      - Usage analytics
      
   .. grid-item-card:: 🏪 Restaurant Management
      :class-header: bg-success text-white
      
      Individual restaurant location management and configuration.
      
      **Capabilities:**
      
      - Location details and settings
      - Timezone management
      - Contact information
      - Integration configurations
      
   .. grid-item-card:: 📦 Store Management
      :class-header: bg-info text-white
      
      Inventory storage locations and warehouse management.
      
      **Features:**
      
      - Storage location tracking
      - Inventory organization
      - Store-specific settings
      - Access control

Quick Reference
===============

.. tabs::

   .. tab:: Core Endpoints

      .. code-block:: text

         # Account Management
         POST   /v1/api/accounts
         GET    /v1/api/accounts/{account_id}
         PUT    /v1/api/accounts/{account_id}
         DELETE /v1/api/accounts/{account_id}
         
         # Restaurant Management
         POST   /v1/api/accounts/{account_id}/restaurants
         GET    /v1/api/accounts/{account_id}/restaurants
         PUT    /v1/api/restaurants/{restaurant_id}
         DELETE /v1/api/restaurants/{restaurant_id}
         
         # Store Management
         POST   /v1/api/restaurants/{restaurant_id}/stores
         GET    /v1/api/restaurants/{restaurant_id}/stores
         PUT    /v1/api/stores/{store_id}
         DELETE /v1/api/stores/{store_id}

   .. tab:: Authentication

      All endpoints require JWT authentication:

      .. code-block:: bash

         curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
              https://api.getinn.com/v1/api/accounts/{account_id}

   .. tab:: Permissions

      .. list-table::
         :header-rows: 1

         * - Operation
           - Required Role
         * - Create Account
           - Admin
         * - Manage Account
           - Admin/Owner
         * - Manage Restaurants
           - Admin/Manager
         * - Manage Stores
           - Manager/Staff

API Endpoints
=============

Account Management
------------------

.. list-table:: Account Management Endpoints
   :header-rows: 1
   :widths: 10 25 15 15 35

   * - Method
     - Endpoint
     - Auth Required
     - Rate Limit
     - Description
   * - POST
     - ``/v1/api/accounts``
     - ✅ Admin
     - 5/min
     - Create new restaurant account
   * - GET
     - ``/v1/api/accounts/{account_id}``
     - ✅ Yes
     - 100/min
     - Get account details
   * - PUT
     - ``/v1/api/accounts/{account_id}``
     - ✅ Admin/Owner
     - 20/min
     - Update account information
   * - DELETE
     - ``/v1/api/accounts/{account_id}``
     - ✅ Admin
     - 1/min
     - Delete account (with safeguards)

Create Account
~~~~~~~~~~~~~~

Create a new restaurant account in the platform.

**Endpoint:** ``POST /v1/api/accounts``

**Request Schema:**

.. code-block:: json

   {
     "name": "Delicious Pizza Chain",
     "description": "Premium pizza restaurants with multiple locations",
     "contact": {
       "email": "admin@deliciouspizza.com",
       "phone": "+1-555-123-4567",
       "address": {
         "street": "123 Business Ave",
         "city": "New York",
         "state": "NY",
         "zip": "10001",
         "country": "USA"
       }
     },
     "settings": {
       "timezone": "America/New_York",
       "currency": "USD",
       "language": "en"
     }
   }

**Success Response (201 Created):**

.. code-block:: json

   {
     "success": true,
     "data": {
       "id": "123e4567-e89b-12d3-a456-426614174000",
       "name": "Delicious Pizza Chain",
       "description": "Premium pizza restaurants with multiple locations",
       "contact": {
         "email": "admin@deliciouspizza.com",
         "phone": "+1-555-123-4567",
         "address": {
           "street": "123 Business Ave",
           "city": "New York",
           "state": "NY",
           "zip": "10001",
           "country": "USA"
         }
       },
       "settings": {
         "timezone": "America/New_York",
         "currency": "USD",
         "language": "en"
       },
       "is_active": true,
       "created_at": "2023-01-15T10:30:00Z",
       "updated_at": "2023-01-15T10:30:00Z",
       "stats": {
         "restaurants_count": 0,
         "active_bots": 0,
         "total_users": 1
       }
     }
   }

Get Account Details
~~~~~~~~~~~~~~~~~~~

Retrieve comprehensive account information including statistics.

**Endpoint:** ``GET /v1/api/accounts/{account_id}``

**Response includes:**
- Basic account information
- Contact details and settings
- Restaurant count and statistics
- Active integrations
- Usage metrics

Restaurant Management
---------------------

.. list-table:: Restaurant Management Endpoints
   :header-rows: 1
   :widths: 10 25 15 15 35

   * - Method
     - Endpoint
     - Auth Required
     - Rate Limit
     - Description
   * - POST
     - ``/v1/api/accounts/{account_id}/restaurants``
     - ✅ Admin/Manager
     - 10/min
     - Create new restaurant location
   * - GET
     - ``/v1/api/accounts/{account_id}/restaurants``
     - ✅ Yes
     - 100/min
     - List account restaurants
   * - GET
     - ``/v1/api/restaurants/{restaurant_id}``
     - ✅ Yes
     - 100/min
     - Get restaurant details
   * - PUT
     - ``/v1/api/restaurants/{restaurant_id}``
     - ✅ Manager
     - 20/min
     - Update restaurant information
   * - DELETE
     - ``/v1/api/restaurants/{restaurant_id}``
     - ✅ Admin
     - 5/min
     - Delete restaurant location

Create Restaurant
~~~~~~~~~~~~~~~~~

Add a new restaurant location to an account.

**Endpoint:** ``POST /v1/api/accounts/{account_id}/restaurants``

**Request Schema:**

.. code-block:: json

   {
     "name": "Downtown Pizza Palace",
     "address": {
       "street": "456 Main Street",
       "city": "New York",
       "state": "NY",
       "zip": "10002",
       "country": "USA"
     },
     "contact": {
       "phone": "+1-555-987-6543",
       "email": "downtown@deliciouspizza.com"
     },
     "settings": {
       "timezone": "America/New_York",
       "hours": {
         "monday": {"open": "11:00", "close": "22:00"},
         "tuesday": {"open": "11:00", "close": "22:00"},
         "friday": {"open": "11:00", "close": "23:00"},
         "saturday": {"open": "11:00", "close": "23:00"},
         "sunday": {"open": "12:00", "close": "21:00"}
       }
     },
     "integrations": {
       "iiko": {
         "enabled": true,
         "restaurant_id": "iiko_rest_123"
       }
     }
   }

Store Management
----------------

.. list-table:: Store Management Endpoints
   :header-rows: 1
   :widths: 10 25 15 15 35

   * - Method
     - Endpoint
     - Auth Required
     - Rate Limit
     - Description
   * - POST
     - ``/v1/api/restaurants/{restaurant_id}/stores``
     - ✅ Manager
     - 20/min
     - Create new storage location
   * - GET
     - ``/v1/api/restaurants/{restaurant_id}/stores``
     - ✅ Yes
     - 100/min
     - List restaurant stores
   * - GET
     - ``/v1/api/stores/{store_id}``
     - ✅ Yes
     - 100/min
     - Get store details
   * - PUT
     - ``/v1/api/stores/{store_id}``
     - ✅ Manager
     - 50/min
     - Update store information
   * - DELETE
     - ``/v1/api/stores/{store_id}``
     - ✅ Manager
     - 10/min
     - Delete storage location

SDK Examples
============

.. tabs::

   .. tab:: Python

      .. code-block:: python

         from getinn_api import GetInnClient

         client = GetInnClient(
             api_key="your-api-key",
             base_url="https://api.getinn.com/v1"
         )

         # Create account
         account = client.accounts.create(
             name="My Restaurant Chain",
             description="Family-owned restaurants",
             contact={
                 "email": "admin@myrestaurant.com",
                 "phone": "+1-555-123-4567"
             }
         )

         # Create restaurant
         restaurant = client.restaurants.create(
             account_id=account.id,
             name="Main Location",
             address={
                 "street": "123 Food Street",
                 "city": "Foodville",
                 "state": "CA",
                 "zip": "90210"
             }
         )

         # Create store
         store = client.stores.create(
             restaurant_id=restaurant.id,
             name="Main Storage",
             type="dry_storage"
         )

   .. tab:: JavaScript/Node.js

      .. code-block:: javascript

         const { GetInnClient } = require('@getinn/api-client');

         const client = new GetInnClient({
           apiKey: 'your-api-key',
           baseUrl: 'https://api.getinn.com/v1'
         });

         // Create account
         const account = await client.accounts.create({
           name: 'My Restaurant Chain',
           description: 'Family-owned restaurants',
           contact: {
             email: 'admin@myrestaurant.com',
             phone: '+1-555-123-4567'
           }
         });

         // Create restaurant
         const restaurant = await client.restaurants.create({
           accountId: account.id,
           name: 'Main Location',
           address: {
             street: '123 Food Street',
             city: 'Foodville',
             state: 'CA',
             zip: '90210'
           }
         });

   .. tab:: cURL

      .. code-block:: bash

         # Create account
         curl -X POST https://api.getinn.com/v1/api/accounts \\
           -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
           -H "Content-Type: application/json" \\
           -d '{
             "name": "My Restaurant Chain",
             "description": "Family-owned restaurants",
             "contact": {
               "email": "admin@myrestaurant.com",
               "phone": "+1-555-123-4567"
             }
           }'

         # Create restaurant
         curl -X POST https://api.getinn.com/v1/api/accounts/{account_id}/restaurants \\
           -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
           -H "Content-Type: application/json" \\
           -d '{
             "name": "Main Location",
             "address": {
               "street": "123 Food Street",
               "city": "Foodville",
               "state": "CA",
               "zip": "90210"
             }
           }'

Data Models
===========

Account Model
-------------

.. code-block:: json

   {
     "id": "uuid",
     "name": "string",
     "description": "string",
     "contact": {
       "email": "string",
       "phone": "string",
       "address": {
         "street": "string",
         "city": "string",
         "state": "string",
         "zip": "string",
         "country": "string"
       }
     },
     "settings": {
       "timezone": "string",
       "currency": "string",
       "language": "string"
     },
     "is_active": "boolean",
     "created_at": "datetime",
     "updated_at": "datetime"
   }

Restaurant Model
----------------

.. code-block:: json

   {
     "id": "uuid",
     "account_id": "uuid",
     "name": "string",
     "address": {
       "street": "string",
       "city": "string",
       "state": "string",
       "zip": "string",
       "country": "string"
     },
     "contact": {
       "phone": "string",
       "email": "string"
     },
     "settings": {
       "timezone": "string",
       "hours": "object"
     },
     "integrations": {
       "iiko": {
         "enabled": "boolean",
         "restaurant_id": "string",
         "sync_status": "string",
         "last_synced_at": "datetime"
       }
     },
     "is_active": "boolean",
     "created_at": "datetime",
     "updated_at": "datetime"
   }

Store Model
-----------

.. code-block:: json

   {
     "id": "uuid",
     "restaurant_id": "uuid",
     "name": "string",
     "type": "string",
     "description": "string",
     "location": "string",
     "capacity": "object",
     "is_active": "boolean",
     "created_at": "datetime",
     "updated_at": "datetime"
   }

Business Logic
==============

Account Hierarchy
-----------------

The platform follows a clear organizational hierarchy:

.. mermaid::

   graph TB
       ACCOUNT[Account]
       RESTAURANT[Restaurant]
       STORE[Store]
       USER[User]
       BOT[Bot Instance]
       
       ACCOUNT --> RESTAURANT
       ACCOUNT --> USER
       ACCOUNT --> BOT
       RESTAURANT --> STORE
       
       subgraph "Account Level"
           ACCOUNT
           USER
           BOT
       end
       
       subgraph "Restaurant Level"
           RESTAURANT
           STORE
       end

Integration Support
-------------------

Accounts and restaurants support various external integrations:

- **iiko POS System**: Restaurant-level integration for menu and order data
- **Payment Processors**: Account-level payment gateway configurations  
- **Third-party APIs**: Custom integration endpoints and webhooks
- **Analytics Platforms**: Data export and reporting integrations

Error Handling
==============

.. list-table:: Account Management Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Status Code
     - Error Code
     - Description
   * - 400
     - VALIDATION_ERROR
     - Invalid request data or missing required fields
   * - 403
     - INSUFFICIENT_PERMISSIONS
     - User lacks required role for operation
   * - 404
     - ACCOUNT_NOT_FOUND
     - Account does not exist or user lacks access
   * - 404
     - RESTAURANT_NOT_FOUND
     - Restaurant does not exist or user lacks access
   * - 409
     - DUPLICATE_NAME
     - Account or restaurant name already exists
   * - 422
     - BUSINESS_RULE_VIOLATION
     - Operation violates business constraints
   * - 500
     - INTERNAL_ERROR
     - Server error during account operations