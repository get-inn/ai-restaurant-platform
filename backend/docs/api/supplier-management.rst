Supplier Management API ⚠️
=======================

.. warning::
   **Implementation Status: Limited - Basic Endpoints Only**
   
   **Currently Available:**
   - Basic supplier CRUD operations (``GET``, ``POST`` with account ID)
   - Simple supplier profile management
   - Account-level supplier listing
   
   **Planned Features (Not Yet Implemented):**
   - OCR invoice processing
   - Document management system
   - Automated reconciliation
   - Performance analytics
   - Inventory tracking
   - Payment workflows
   
   The advanced features described in this documentation represent the planned functionality and are not currently available in the API.

The Supplier Management API provides comprehensive tools for managing supplier relationships, processing invoices, handling document management, and maintaining inventory tracking. This API streamlines the entire supplier workflow from onboarding to payment reconciliation.

.. grid:: 4
   :gutter: 2

   .. grid-item-card:: 🏢 Supplier Management
      :class-header: bg-primary text-white
      
      Complete supplier lifecycle management with detailed profiles.
      
      **Features:**
      
      - Supplier onboarding
      - Contact management
      - Performance tracking
      - Contract management
      
   .. grid-item-card:: 📄 Invoice Processing
      :class-header: bg-success text-white
      
      Automated invoice processing with smart reconciliation.
      
      **Capabilities:**
      
      - OCR document processing
      - Automated data extraction
      - Approval workflows
      - Payment tracking
      
   .. grid-item-card:: 📂 Document Management
      :class-header: bg-info text-white
      
      Secure document storage and management system.
      
      **Features:**
      
      - File upload and storage
      - Document categorization
      - Version control
      - Access permissions
      
   .. grid-item-card:: 📦 Inventory Tracking
      :class-header: bg-warning text-white
      
      Real-time inventory management and tracking.
      
      **Capabilities:**
      
      - Stock level monitoring
      - Automated reordering
      - Expiration tracking
      - Usage analytics

Quick Reference
===============

.. tabs::

   .. tab:: Core Endpoints

      .. code-block:: text

         # Supplier Management
         POST   /v1/api/accounts/{account_id}/suppliers
         GET    /v1/api/accounts/{account_id}/suppliers
         PUT    /v1/api/suppliers/{supplier_id}
         DELETE /v1/api/suppliers/{supplier_id}
         
         # Invoice Management
         POST   /v1/api/suppliers/{supplier_id}/invoices
         GET    /v1/api/suppliers/{supplier_id}/invoices
         PUT    /v1/api/invoices/{invoice_id}
         POST   /v1/api/invoices/{invoice_id}/reconcile
         
         # Document Management
         POST   /v1/api/suppliers/{supplier_id}/documents
         GET    /v1/api/suppliers/{supplier_id}/documents
         GET    /v1/api/documents/{document_id}
         DELETE /v1/api/documents/{document_id}

   .. tab:: Workflow

      **Typical Supplier Workflow:**

      1. Create supplier profile
      2. Upload contracts and documents
      3. Process incoming invoices
      4. Reconcile against purchase orders
      5. Track inventory levels
      6. Generate performance reports

   .. tab:: Integration

      **External System Integration:**

      - Accounting software (QuickBooks, Xero)
      - ERP systems (SAP, Oracle)
      - Payment processors
      - OCR services for document processing

Actually Implemented Endpoints
===============================

Supplier Management
-------------------

.. list-table:: Currently Available Supplier Endpoints
   :header-rows: 1
   :widths: 10 25 15 15 35

   * - Method
     - Endpoint
     - Auth Required
     - Status
     - Description
   * - POST
     - ``/v1/api/accounts/{account_id}/suppliers``
     - ✅ Yes
     - Available
     - Create new supplier (basic implementation)
   * - GET
     - ``/v1/api/accounts/{account_id}/suppliers``
     - ✅ Yes
     - Available
     - List account suppliers
   * - GET
     - ``/v1/api/suppliers/{supplier_id}``
     - ✅ Yes
     - Available
     - Get supplier details

Basic Supplier Operations
~~~~~~~~~~~~~~~~~~~~~~~~~

The current implementation provides basic supplier management with simple CRUD operations. The actual endpoints use placeholder implementations and return basic JSON responses.

**Available Operations:**
- Create supplier with basic information
- List suppliers for an account
- Get supplier details by ID

.. note::
   **Current Implementation Note:**
   
   The supplier management endpoints currently exist as placeholder implementations. They accept basic supplier data and return simple responses, but do not include the advanced features like invoice processing, document management, or inventory tracking shown in the planned features above.

Usage Examples
==============

.. tabs::

   .. tab:: cURL

      .. code-block:: bash

         # Create supplier (basic implementation)
         curl -X POST https://api.getinn.com/v1/api/accounts/{account_id}/suppliers \
           -H "Authorization: Bearer YOUR_JWT_TOKEN" \
           -H "Content-Type: application/json" \
           -d '{
             "name": "Fresh Produce Co.",
             "contact": {
               "email": "orders@freshproduce.com",
               "phone": "+1-555-123-4567"
             }
           }'

         # List suppliers for account
         curl -X GET https://api.getinn.com/v1/api/accounts/{account_id}/suppliers \
           -H "Authorization: Bearer YOUR_JWT_TOKEN"

         # Get supplier details
         curl -X GET https://api.getinn.com/v1/api/suppliers/{supplier_id} \
           -H "Authorization: Bearer YOUR_JWT_TOKEN"

   .. tab:: Response Format

      Basic supplier response format:

      .. code-block:: json

         {
           "success": true,
           "data": {
             "id": "supplier-uuid",
             "account_id": "account-uuid",
             "name": "Fresh Produce Co.",
             "contact": {
               "email": "orders@freshproduce.com",
               "phone": "+1-555-123-4567"
             },
             "created_at": "2023-01-15T10:30:00Z",
             "updated_at": "2023-01-15T10:30:00Z"
           }
         }

Error Handling
==============

.. list-table:: Basic Supplier Management Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Status Code
     - Error Code
     - Description
   * - 400
     - VALIDATION_ERROR
     - Invalid supplier data provided
   * - 404
     - SUPPLIER_NOT_FOUND
     - Supplier does not exist or user lacks access
   * - 404
     - ACCOUNT_NOT_FOUND
     - Account does not exist or user lacks access
   * - 409
     - DUPLICATE_SUPPLIER
     - Supplier with this name already exists for account

Future Development
==================

The following features are planned for future releases:

- **Invoice Processing**: OCR-based invoice data extraction and processing
- **Document Management**: Secure document storage and version control
- **Performance Analytics**: Comprehensive supplier performance tracking
- **Inventory Integration**: Real-time inventory level monitoring
- **Payment Workflows**: Automated payment processing and reconciliation
- **Compliance Tracking**: Regulatory compliance monitoring and reporting