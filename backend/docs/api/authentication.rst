Authentication API ✅
==================

.. note::
   **Implementation Status: Production Ready**
   
   The authentication system is fully implemented with JWT tokens, role-based access control, account-level data isolation, and refresh token support. All endpoints are production-ready and actively used throughout the platform.

The Authentication API handles user login, token management, and access control for the GET INN Restaurant Platform. All API endpoints (except authentication itself) require valid JWT tokens obtained through this API.

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: 🔐 User Authentication
      :class-header: bg-primary text-white
      
      Secure login with JWT token generation and refresh capabilities.
      
      **Features:**
      
      - Email/password authentication
      - JWT token generation
      - Token refresh mechanism
      - Role-based access control
      
   .. grid-item-card:: 🛡️ Security Features
      :class-header: bg-success text-white
      
      Enterprise-grade security with comprehensive protection.
      
      **Capabilities:**
      
      - Bcrypt password hashing
      - Token expiration
      - Rate limiting protection
      - Account lockout prevention

Authentication Endpoints
=======================

.. list-table:: Authentication API Endpoints
   :header-rows: 1
   :widths: 10 30 15 15 30

   * - Method
     - Endpoint
     - Auth Required
     - Rate Limit
     - Description
   * - POST
     - ``/v1/api/auth/login``
     - ❌ No
     - 10/min
     - User login with credentials
   * - POST
     - ``/v1/api/auth/refresh``
     - 🔄 Refresh Token
     - 20/min
     - Refresh expired access token

User Login
----------

Authenticate users and obtain access tokens for API operations.

**Endpoint:** ``POST /v1/api/auth/login``

**Request Schema:**

.. code-block:: json

   {
     "email": "user@restaurant.com",
     "password": "secure_password123"
   }

**Success Response (200 OK):**

.. code-block:: json

   {
     "success": true,
     "data": {
       "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
       "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
       "token_type": "bearer",
       "expires_in": 3600,
       "user": {
         "id": "123e4567-e89b-12d3-a456-426614174000",
         "email": "user@restaurant.com",
         "full_name": "John Smith",
         "role": "manager",
         "account_id": "456e7890-e89b-12d3-a456-426614174000",
         "is_active": true,
         "created_at": "2023-01-15T10:30:00Z"
       }
     },
     "meta": {
       "timestamp": "2023-01-15T14:20:00Z",
       "request_id": "req_abc123"
     }
   }

**Error Responses:**

.. tabs::

   .. tab:: Invalid Credentials (401)

      .. code-block:: json

         {
           "success": false,
           "error": {
             "code": "INVALID_CREDENTIALS",
             "message": "Invalid email or password",
             "details": {
               "suggestion": "Check your email and password and try again"
             }
           }
         }

   .. tab:: Account Disabled (403)

      .. code-block:: json

         {
           "success": false,
           "error": {
             "code": "ACCOUNT_DISABLED",
             "message": "User account is disabled",
             "details": {
               "contact": "Contact your administrator to reactivate your account"
             }
           }
         }

   .. tab:: Rate Limited (429)

      .. code-block:: json

         {
           "success": false,
           "error": {
             "code": "RATE_LIMIT_EXCEEDED",
             "message": "Too many login attempts",
             "details": {
               "retry_after": 300,
               "suggestion": "Wait 5 minutes before trying again"
             }
           }
         }

Token Refresh
-------------

Refresh expired access tokens using a valid refresh token.

**Endpoint:** ``POST /v1/api/auth/refresh``

**Request Headers:**

.. code-block:: text

   Authorization: Bearer REFRESH_TOKEN_HERE

**Success Response (200 OK):**

.. code-block:: json

   {
     "success": true,
     "data": {
       "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
       "token_type": "bearer",
       "expires_in": 3600
     }
   }

**Error Response (401 Unauthorized):**

.. code-block:: json

   {
     "success": false,
     "error": {
       "code": "INVALID_REFRESH_TOKEN",
       "message": "Refresh token is invalid or expired",
       "details": {
         "suggestion": "Please log in again to obtain new tokens"
       }
     }
   }

SDK Examples
============

.. tabs::

   .. tab:: Python

      .. code-block:: python

         from getinn_api import GetInnClient

         # Initialize client
         client = GetInnClient(base_url="https://api.getinn.com/v1")

         # Login
         auth_response = client.auth.login(
             email="user@restaurant.com",
             password="secure_password123"
         )

         # Set access token for future requests
         client.set_access_token(auth_response.access_token)

         # Refresh token when needed
         new_token = client.auth.refresh(auth_response.refresh_token)

   .. tab:: JavaScript/Node.js

      .. code-block:: javascript

         const { GetInnClient } = require('@getinn/api-client');

         const client = new GetInnClient({
           baseUrl: 'https://api.getinn.com/v1'
         });

         // Login
         const authResponse = await client.auth.login({
           email: 'user@restaurant.com',
           password: 'secure_password123'
         });

         // Set access token
         client.setAccessToken(authResponse.access_token);

         // Refresh token
         const newToken = await client.auth.refresh(authResponse.refresh_token);

   .. tab:: cURL

      .. code-block:: bash

         # Login
         curl -X POST https://api.getinn.com/v1/api/auth/login \\
           -H "Content-Type: application/json" \\
           -d '{
             "email": "user@restaurant.com",
             "password": "secure_password123"
           }'

         # Refresh token
         curl -X POST https://api.getinn.com/v1/api/auth/refresh \\
           -H "Authorization: Bearer REFRESH_TOKEN_HERE"

Token Usage
===========

Include the access token in the Authorization header for all API requests:

.. code-block:: text

   Authorization: Bearer ACCESS_TOKEN_HERE

**Token Properties:**

- **Access Token**: Short-lived (1 hour) token for API access
- **Refresh Token**: Long-lived (30 days) token for obtaining new access tokens
- **Scope**: Tokens include user role and permissions
- **Security**: Tokens are signed with HS256 algorithm

Security Best Practices
======================

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: 🔒 Token Storage
      :class-header: bg-warning text-white
      
      **Secure Storage:**
      
      - Store tokens in secure, HTTP-only cookies
      - Never store tokens in localStorage
      - Use secure, same-site cookie attributes
      - Implement token rotation
      
   .. grid-item-card:: 🛡️ API Security
      :class-header: bg-danger text-white
      
      **Request Security:**
      
      - Always use HTTPS for API calls
      - Implement CSRF protection
      - Use rate limiting for auth endpoints
      - Monitor for suspicious login patterns

Error Handling
==============

The Authentication API uses standard HTTP status codes with detailed error information:

.. list-table:: Authentication Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Status Code
     - Error Code
     - Description
   * - 400
     - VALIDATION_ERROR
     - Invalid request format or missing fields
   * - 401
     - INVALID_CREDENTIALS
     - Incorrect email or password
   * - 401
     - INVALID_TOKEN
     - Access token is invalid or expired
   * - 401
     - INVALID_REFRESH_TOKEN
     - Refresh token is invalid or expired
   * - 403
     - ACCOUNT_DISABLED
     - User account is deactivated
   * - 429
     - RATE_LIMIT_EXCEEDED
     - Too many authentication attempts
   * - 500
     - INTERNAL_ERROR
     - Server error during authentication