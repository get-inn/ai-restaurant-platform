# iiko Integration Guide

This document provides a comprehensive overview of the iiko integration with our restaurant management platform.

## Overview

The integration with iiko POS/ERP system allows for synchronizing data between iiko and our platform, including:

- Restaurants/Departments
- Stores
- Suppliers
- Invoices/Purchase Orders

## Architecture

The integration is designed with flexibility in mind, supporting potential future integrations with other POS/ERP systems:

1. **Core Models** - Generic external system fields in our data models
2. **Account-Level Credentials** - Secure storage of integration credentials at account level
3. **Service Layer** - Business logic for managing integrations
4. **Adapter Pattern** - Conversion between external and internal data models

## Configuration

### Required Environment Variables

```env
# Optional: Enable/disable all integrations
INTEGRATIONS_ENABLED=True

# Credential encryption (required if storing credentials in DB)
CREDENTIAL_ENCRYPTION_KEY=your-32-byte-encryption-key
CREDENTIAL_ENCRYPTION_NONCE=your-12-byte-nonce
```

### Account Integration Credentials

Credentials are stored at the account level using the `AccountIntegrationCredentials` model:

```python
{
    "username": "your-iiko-username",
    "password": "your-iiko-password" 
}
```

Optional: You can specify a custom `base_url` if not using the default iiko URL.

## API Endpoints

### Authentication

```
POST /api/v1/accounts/{account_id}/integrations/iiko/connect
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

### Synchronization

```
POST /api/v1/accounts/{account_id}/integrations/iiko/sync/restaurants
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

## Implementation Details

### XML Response Handling

iiko API returns XML responses for most endpoints. Our integration includes a robust XML parser that converts these responses to Python dictionaries:

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
    # ...
    
    return result
```

### Field Mappings

The integration handles differences in field names between XML and JSON responses:

```python
# Example: Restaurant name can be in "name" (JSON) or "n" (XML)
name = iiko_data.get("name", "")
if not name and "n" in iiko_data:
    name = iiko_data.get("n", "Unnamed Restaurant")
```

### Data Synchronization

The `IikoSyncManager` class orchestrates data synchronization:

1. Fetches data from iiko API
2. Converts to internal models using adapters
3. Creates or updates records in the database
4. Tracks results and handles errors

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

### Example Test Output

```
===== Testing iiko API in Docker =====

1. Testing authentication...
✅ Authentication successful - token: 22ecb2f5-1f4f-f...

2. Fetching restaurants...
Status code: 200
Content type: application/xml
✅ Found 31 restaurants

3. Fetching suppliers...
Status code: 200
Content type: application/xml
✅ Found 658 suppliers

✅ iiko API test completed successfully in Docker!
```

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

## Next Steps

1. Add support for more iiko entity types
2. Implement scheduled synchronization
3. Add conflict resolution for data discrepancies
4. Develop UI for integration management