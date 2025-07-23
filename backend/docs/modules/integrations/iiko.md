# iiko Integration Guide

This document provides comprehensive information about the iiko POS/ERP system integration with the GET INN Restaurant Platform.

## Overview

The integration with iiko allows for synchronizing data between iiko and our platform, including:

- Restaurants/Departments
- Stores
- Suppliers
- Invoices/Purchase Orders

This integration primarily supports the AI Supplier module by enabling automated procurement, reconciliation, and inventory tracking.

## Architecture

The integration is designed with flexibility in mind, supporting potential future integrations with other POS/ERP systems:

1. **Core Models** - Generic external system fields in our data models
2. **Account-Level Credentials** - Secure storage of integration credentials at account level
3. **Service Layer** - Business logic for managing integrations
4. **Adapter Pattern** - Conversion between external and internal data models

## Integration Points

### Authentication

iiko uses a token-based authentication system. The token must be retrieved before making any API calls and included in subsequent requests.

**Authentication Flow:**
1. Make a POST request to obtain the authentication token
2. Include the token in the header or as a query parameter for subsequent requests
3. Handle token expiration and renewal

### Data Synchronization

The following data entities can be synchronized:

1. **Restaurants** (iiko "departments") - List of restaurants in the network
2. **Stores** - Physical inventory storage locations
3. **Suppliers** - Vendors providing goods to restaurants
4. **Invoices** - Purchase documents for goods received from suppliers

## API Endpoints

### Authentication

**Endpoint:** `POST https://chiho-co.iiko.it/resto/api/auth`  
**Headers:** Content-Type: application/x-www-form-urlencoded  
**Body Parameters:** 
- login - username credential
- pass - password credential  

**Response:** Authentication token (string)

### Restaurants (Departments)

**Endpoint:** `GET https://chiho-co.iiko.it/resto/api/corporation/departments`  
**Query Parameters:** 
- key - authentication token
- revisionFrom - data revision number (-1 for all)  

**Response:** List of restaurant entities

### Stores

**Endpoint:** `GET https://chiho-co.iiko.it/resto/api/corporation/stores`  
**Query Parameters:** 
- key - authentication token
- revisionFrom - data revision number (-1 for all)  

**Response:** List of store entities

### Invoices

**Endpoint:** `GET https://chiho-co.iiko.it/api/invoices`  
**Headers:** Authorization: Bearer {token}  
**Query Parameters:** 
- type - document type (arrival for purchase invoices)
- organizationId - restaurant/entity ID
- from - start date (format: YYYY-MM-DDThh:mm:ss)
- to - end date (format: YYYY-MM-DDThh:mm:ss)  

**Response:** List of invoice documents

### Suppliers

**Endpoint:** `GET https://chiho-co.iiko.it/resto/api/suppliers`  
**Query Parameters:** 
- key - authentication token  

**Response:** List of supplier entities

## Configuration

### Environment Variables

```env
# Optional: Enable/disable all integrations
INTEGRATIONS_ENABLED=True

# Credential encryption (required if storing credentials in DB)
CREDENTIAL_ENCRYPTION_KEY=your-32-byte-encryption-key
CREDENTIAL_ENCRYPTION_NONCE=your-12-byte-nonce
```

### Account Integration Credentials

Credentials are stored at the account level using the `AccountIntegrationCredentials` model:

```json
{
    "username": "your-iiko-username",
    "password": "your-iiko-password",
    "base_url": "https://your-iiko-instance.iiko.it" // Optional
}
```

## Implementation

### Service Architecture

1. Integration components in the project structure:
   - `src/integrations/pos_erp_adapters/iiko/` - iiko-specific adapter folder

2. Key components:
   - `iiko_auth.py` - Authentication Manager to handle token retrieval and renewal
   - `iiko_client.py` - Core HTTP client for iiko API requests
   - `iiko_adapters.py` - Data Mappers to convert between iiko data models and our internal models
   - `iiko_sync.py` - Sync Manager to orchestrate synchronization operations
   - `iiko_types.py` - Pydantic models for iiko data structures

### Database Models

```python
class AccountIntegrationCredentials(Base):
    __tablename__ = "account_integration_credentials"
    __table_args__ = {"schema": settings.DATABASE_SCHEMA}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey(f"{settings.DATABASE_SCHEMA}.accounts.id"), nullable=False)
    integration_type = Column(String, nullable=False)  # 'iiko', 'r_keeper', etc.
    credentials = Column(JSONB, nullable=False)  # Encrypted credentials
    base_url = Column(String, nullable=True)  # Optional custom URL
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_connected_at = Column(DateTime, nullable=True)
    connection_status = Column(String, nullable=True)
    connection_error = Column(String, nullable=True)
```

### Integration-specific Fields

```python
class Restaurant(Base):
    # Existing fields...
    iiko_id = Column(String, nullable=True, index=True)
    iiko_sync_status = Column(Enum('pending', 'synced', 'error', name='sync_status_enum'), nullable=True)
    iiko_last_synced_at = Column(DateTime, nullable=True)
    iiko_sync_error = Column(String, nullable=True)
```

### Handling XML Responses

iiko API returns XML responses for most endpoints. The integration includes a robust XML parser:

```python
def xml_to_dict(element):
    """Convert XML element to dictionary recursively."""
    result = {}
    
    # Add element attributes
    for key, value in element.attrib.items():
        result[f"@{key}"] = value
    
    # Handle text content
    if element.text and element.text.strip():
        if not result:
            return element.text.strip()
        else:
            result["#text"] = element.text.strip()
    
    # Process children recursively
    for child in element:
        child_result = xml_to_dict(child)
        if child.tag in result:
            if type(result[child.tag]) is list:
                result[child.tag].append(child_result)
            else:
                result[child.tag] = [result[child.tag], child_result]
        else:
            result[child.tag] = child_result
    
    return result
```

### Sync Strategies

1. **Initial Sync** - Full data import when integration is first enabled
2. **Periodic Sync** - Scheduled background tasks using Celery to keep data updated
3. **Webhook Listeners** - For real-time updates (if supported by iiko)
4. **Manual Sync** - Admin-triggered sync operations via API endpoints

## Management API Endpoints

### Connect iiko

```
POST /v1/api/accounts/{account_id}/integrations/iiko/connect
```

Request body:
```json
{
    "username": "your-iiko-username",
    "password": "your-iiko-password",
    "base_url": "https://your-iiko-instance.iiko.it" // Optional
}
```

Response:
```json
{
    "account_id": "uuid",
    "is_connected": true,
    "last_connected_at": "2023-06-29T12:00:00Z",
    "connection_error": null,
    "integration_type": "iiko"
}
```

### Synchronize Data

```
POST /v1/api/accounts/{account_id}/integrations/iiko/sync/restaurants
```

Response:
```json
{
    "total": 10,
    "created": 5,
    "updated": 5,
    "errors": 0,
    "error_details": []
}
```

Similar endpoints exist for `/sync/stores`, `/sync/suppliers`, and `/sync/invoices`.

## Testing

To test the integration:

1. Run the Docker container:
   ```bash
   docker-compose -f docker/docker-compose.dev.yml up -d
   ```

2. Copy test script to container:
   ```bash
   docker-compose -f docker/docker-compose.dev.yml cp docker_iiko_test.py backend:/app/
   ```

3. Execute test:
   ```bash
   docker-compose -f docker/docker-compose.dev.yml exec backend python3 /app/docker_iiko_test.py
   ```

## Security Considerations

1. **Credential Management**
   - Use strong encryption (AES-256-GCM) to protect sensitive credentials
   - Store encryption key in secure environment variables, not in the database
   - Implement automatic rotation of encryption keys

2. **Permission Control**
   - Ensure only authorized users can access or modify integration credentials
   - Limit access based on user roles and account relationships

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify credentials are correct
   - Check that the iiko server is accessible
   - Ensure proper network connectivity from your Docker container

2. **XML Parsing Errors**
   - Check for changes in iiko API response format
   - Update XML parser if needed
   - Enable debug logging to see raw responses

3. **Data Synchronization Errors**
   - Ensure required fields are present in both systems
   - Check field mappings in adapter functions
   - Review error details in sync results

## Future Enhancements

1. Two-way synchronization (write back to iiko)
2. Real-time integration via webhooks if supported
3. Support for additional iiko entities (menu items, recipes, etc.)
4. Integration with AI-driven inventory forecasting
5. Integration with the AI Chef module for recipe and menu synchronization