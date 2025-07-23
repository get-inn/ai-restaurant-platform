# iiko API Integration Guide

## Overview

This document outlines the integration requirements between the GET INN Restaurant Platform and the iiko back-office system. The integration will allow our system to synchronize data with iiko, including restaurants, stores, suppliers, and invoices. This integration will primarily support the AI Supplier module by enabling automated procurement, reconciliation, and inventory tracking.

## Integration Points

### Authentication

iiko uses a token-based authentication system. The token must be retrieved before making any API calls and included in subsequent requests.

**Authentication Flow:**
1. Make a POST request to obtain the authentication token
2. Include the token in the header or as a query parameter for subsequent requests
3. Handle token expiration and renewal

### Data Synchronization Requirements

The following data entities should be synchronized:

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

### Supplier Search

**Endpoint:** `GET https://chiho-co.iiko.it/resto/api/suppliers/search`  
**Query Parameters:** 
- key - authentication token
- name - supplier name to search for  

**Response:** Matching supplier entities

## Implementation Guidelines

### Service Architecture

1. Create integration components in the existing project structure:
   - `src/integrations/pos_erp_adapters/iiko/` - Create an iiko-specific adapter folder

2. Implement the following components:
   - `iiko_auth.py` - Authentication Manager to handle token retrieval and renewal
   - `iiko_client.py` - Core HTTP client for iiko API requests
   - `iiko_adapters.py` - Data Mappers to convert between iiko data models and our internal models
   - `iiko_sync.py` - Sync Manager to orchestrate synchronization operations
   - `iiko_types.py` - Pydantic models for iiko data structures

### Data Models

Create the following data models to represent iiko entities:

1. **IikoRestaurant** - Maps to our Restaurant model
2. **IikoStore** - Maps to our Store model 
3. **IikoSupplier** - Maps to our Supplier model
4. **IikoInvoice** - Maps to our Invoice model

### Configuration

Add the following settings to the application configuration in `src/api/core/config.py` for global settings:

```python
# iiko integration settings
class Settings(BaseSettings):
    # Existing settings...
    
    # iiko integration
    IIKO_INTEGRATION_ENABLED: bool = False
    IIKO_BASE_URL: str = "https://chiho-co.iiko.it"  # Default base URL
    IIKO_TOKEN_REFRESH_INTERVAL: int = 3600  # seconds
```

### Database Model for Account Credentials

Store iiko credentials in the database per account by extending the Account model:

```python
# Add to src/api/core/models.py
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
    
    __table_args__ = (
        UniqueConstraint('account_id', 'integration_type', name='uix_account_integration_type'),
        {"schema": settings.DATABASE_SCHEMA}
    )
    
    # Relationships
    account = relationship("Account", back_populates="integration_credentials")
```

Update the Account model to include the relationship:

```python
class Account(Base):
    # Existing fields...
    
    # Relationships
    integration_credentials = relationship("AccountIntegrationCredentials", back_populates="account")
```

This approach allows each account to have its own set of credentials for iiko and other integrations.

### Sync Strategies

1. **Initial Sync** - Full data import when integration is first enabled
2. **Periodic Sync** - Scheduled background tasks using Celery to keep data updated
3. **Webhook Listeners** - If iiko provides webhooks for real-time updates
4. **Manual Sync** - Admin-triggered sync operations via API endpoints

### Error Handling

Implement robust error handling for:
- Authentication failures
- Network connectivity issues
- Rate limiting
- Data validation errors
- Conflict resolution for data discrepancies

## API Service Implementation

Implement the following components following the project's architecture:

```
/src/integrations/pos_erp_adapters/iiko/
  ├── iiko_auth.py       # Handle authentication and token management
  ├── iiko_client.py     # Core HTTP client with error handling
  ├── iiko_adapters.py   # Convert between iiko and internal data models
  ├── iiko_sync.py       # Orchestrate data synchronization 
  ├── iiko_types.py      # Pydantic models for iiko data
  └── __init__.py        # Package exports
```

Add the necessary service layer components for account-specific credentials management:

```
/src/api/services/
  └── integrations/
      ├── iiko_service.py        # Higher-level business logic for iiko integration
      ├── credentials_service.py  # Handle retrieval and storage of account-specific credentials
      └── encryption_service.py   # Handle secure encryption/decryption of credentials
```

Create Celery tasks for background processing that utilize account-specific credentials:

```
/src/worker/tasks/integrations/
  └── iiko_tasks.py  # Celery tasks for iiko data synchronization
```

### Credential Management

Implement secure credential storage with the following key components:

1. **Encryption Service**
   - Use strong encryption (AES-256-GCM) to protect sensitive credentials
   - Store encryption key in secure environment variables, not in the database
   - Implement automatic rotation of encryption keys

2. **Credential Service**
   - Provide methods to securely store, retrieve, and update account-specific credentials
   - Validate credentials before storage
   - Maintain audit logs of credential access and changes

3. **Permission Control**
   - Ensure only authorized users can access or modify integration credentials
   - Limit access based on user roles and account relationships

## Database Changes

1. Add integration-specific fields to the relevant models in `src/api/core/models.py`:

```python
class Restaurant(Base):
    # Existing fields...
    iiko_id = Column(String, nullable=True, index=True)
    iiko_sync_status = Column(Enum('pending', 'synced', 'error', name='sync_status_enum'), nullable=True)
    iiko_last_synced_at = Column(DateTime, nullable=True)
    iiko_sync_error = Column(String, nullable=True)

# Similar changes for Store, Supplier, and other relevant models
```

2. Create Alembic migration for these changes:

```bash
./start-dev.sh --exec backend alembic revision --autogenerate -m "add iiko integration fields"
```

## Testing Strategy

1. Create unit tests in `tests/unit/integrations/iiko/` with mocked iiko API responses
2. Implement integration tests in `tests/integration/integrations/` using a staging iiko instance
3. Create sync verification tests to ensure data integrity
4. Use the existing testing infrastructure and pytest fixtures

## Deployment Considerations

1. Ensure proper secret management for encryption keys using environment variables
2. Monitor API usage to stay within rate limits per account
3. Implement logging for all synchronization operations using the existing logging configuration in `src/api/core/logging_config.py`
4. Create alerts for sync failures or discrepancies, with account-specific notifications
5. Update docker-compose configuration to include the encryption key environment variables:

```yaml
services:
  backend:
    # Existing configuration...
    environment:
      # Existing variables...
      - CREDENTIAL_ENCRYPTION_KEY=${CREDENTIAL_ENCRYPTION_KEY}
      - CREDENTIAL_ENCRYPTION_NONCE=${CREDENTIAL_ENCRYPTION_NONCE}
```

6. Implement proper key rotation mechanisms for credential encryption keys
7. Consider using a secret management service like HashiCorp Vault for increased security

## API Endpoints

Add the following API endpoints to manage the integration with account-specific credentials:

```python
# Create in src/api/routers/integrations/iiko.py

@router.post("/connect", response_model=schemas.IikoConnectionStatus)
async def connect_iiko(
    credentials: schemas.IikoCredentials, 
    account_id: UUID = Path(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test and save iiko connection credentials for a specific account"""
    # Check if user has access to this account
    # Validate and encrypt credentials
    # Store in AccountIntegrationCredentials
    # Test connection
    # Return status

@router.get("/status", response_model=schemas.IikoConnectionStatus)
async def get_iiko_status(
    account_id: UUID = Path(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current iiko connection status for a specific account"""
    # Check if user has access to this account
    # Retrieve status from AccountIntegrationCredentials

@router.post("/sync/{entity_type}", response_model=schemas.SyncJobResponse)
async def trigger_sync(
    entity_type: str, 
    account_id: UUID = Path(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger manual sync for an entity type for a specific account"""
    # Check if user has access to this account
    # Get account credentials
    # Trigger appropriate sync task

@router.get("/logs", response_model=List[schemas.SyncLogEntry])
async def get_sync_logs(
    account_id: UUID = Path(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get iiko sync logs for a specific account"""
    # Check if user has access to this account
    # Return filtered logs
```

Create the necessary Pydantic schemas:

```python
# Add to src/api/schemas/integrations/iiko_schemas.py

class IikoCredentials(BaseModel):
    username: str
    password: str
    base_url: Optional[str] = None

class IikoConnectionStatus(BaseModel):
    account_id: UUID
    is_connected: bool
    last_connected_at: Optional[datetime] = None
    connection_error: Optional[str] = None
    integration_type: str = "iiko"
```

## Future Enhancements

1. Two-way synchronization (write back to iiko)
2. Real-time integration via webhooks if supported
3. Support for additional iiko entities (menu items, recipes, etc.)
4. Integration with AI-driven inventory forecasting
5. Integration with the AI Chef module for recipe and menu synchronization