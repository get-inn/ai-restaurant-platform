# Legal Entities Implementation Specification

## Overview

This specification describes the implementation of legal entities within the GET INN Restaurant Platform. Legal entities represent formal business organizations (such as LLCs, Sole Proprietorships, etc.) that own and operate restaurants. Each account in the system can have multiple legal entities, and each restaurant is associated with exactly one legal entity.

## Domain Model

### Legal Entity

A legal entity represents a formally registered business organization that can own one or more restaurants.

**Attributes:**
- `id`: UUID - Primary identifier for the legal entity
- `name`: String - Official registered name of the legal entity (e.g., "ООО Чихо", "ИП Иванов")
- `tax_id`: String - Tax identification number (ИНН) - unique government-issued identifier
- `type`: Enum - Type of legal entity (LLC, Sole Proprietor, etc.)
- `account_id`: UUID - Reference to the account that owns this legal entity
- `active`: Boolean - Whether the legal entity is currently active
- `external_id`: String (optional) - ID reference in external systems (e.g., iiko)
- `created_at`: DateTime - When the record was created
- `updated_at`: DateTime - When the record was last updated

### Relationship to Account and Restaurant

1. **Account to Legal Entity**: One-to-Many (One account can have multiple legal entities)
2. **Legal Entity to Restaurant**: One-to-Many (One legal entity can own multiple restaurants)

## Database Schema

### Legal Entity Table

```
Table: legal_entity
Schema: getinn_ops

Columns:
- id UUID PRIMARY KEY
- name VARCHAR(255) NOT NULL
- tax_id VARCHAR(20) NOT NULL
- type VARCHAR(50) NOT NULL
- account_id UUID NOT NULL REFERENCES account(id)
- active BOOLEAN NOT NULL DEFAULT true
- external_id VARCHAR(100)
- created_at TIMESTAMP NOT NULL DEFAULT now()
- updated_at TIMESTAMP NOT NULL DEFAULT now()

Indexes:
- account_id
- tax_id (unique per account_id)
- external_id (unique if not null)
```

### Restaurant Table (Updated)

```
Table: restaurant
Schema: getinn_ops

Additional Column:
- legal_entity_id UUID NOT NULL REFERENCES legal_entity(id)

Additional Index:
- legal_entity_id
```

## API Endpoints

### Legal Entity Management

#### List Legal Entities

```
GET /v1/api/legal-entities
```

Returns a list of legal entities for the authenticated user's account.

**Query Parameters:**
- `active` (optional): Boolean - Filter by active status
- `skip` (optional): Integer - Pagination offset
- `limit` (optional): Integer - Pagination limit

**Response:**
```json
{
  "total": 2,
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "ООО Чихо",
      "tax_id": "7704123456", 
      "type": "LLC",
      "active": true,
      "external_id": "12345",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    },
    {
      "id": "8c22e34a-e67c-4ea8-8c9c-83870b9a88e6",
      "name": "ИП Иванов",
      "tax_id": "770412345678",
      "type": "SOLE_PROPRIETOR",
      "active": true,
      "external_id": "67890",
      "created_at": "2023-01-02T12:00:00Z",
      "updated_at": "2023-01-02T12:00:00Z"
    }
  ]
}
```

#### Get Legal Entity

```
GET /v1/api/legal-entities/{legal_entity_id}
```

Returns a specific legal entity by ID.

**Response:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "ООО Чихо",
  "tax_id": "7704123456",
  "type": "LLC",
  "active": true,
  "external_id": "12345",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z",
  "restaurants": [
    {
      "id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
      "name": "Чихо на Тверской",
      "external_id": "rest-123"
    },
    {
      "id": "7q8r9s0t-1u2v-3w4x-5y6z-7a8b9c0d1e2f",
      "name": "Чихо в Сокольниках",
      "external_id": "rest-456"
    }
  ]
}
```

#### Create Legal Entity

```
POST /v1/api/legal-entities
```

Creates a new legal entity.

**Request Body:**
```json
{
  "name": "ООО Новый Ресторан",
  "tax_id": "7704987654",
  "type": "LLC",
  "active": true,
  "external_id": "ext-789"
}
```

**Response:** The created legal entity object.

#### Update Legal Entity

```
PUT /v1/api/legal-entities/{legal_entity_id}
```

Updates an existing legal entity.

**Request Body:**
```json
{
  "name": "ООО Новый Ресторан Обновленное",
  "tax_id": "7704987654", 
  "type": "LLC",
  "active": false
}
```

**Response:** The updated legal entity object.

#### Delete Legal Entity

```
DELETE /v1/api/legal-entities/{legal_entity_id}
```

Marks a legal entity as inactive (soft delete).

### Integration with Restaurant Systems

#### Sync Legal Entities and Restaurants from iiko

```
POST /v1/api/integrations/iiko/sync-legal-entities
```

Synchronizes legal entities and restaurants from the iiko back-office system.

**Request Body:**
```json
{
  "sync_restaurants": true
}
```

**Response:**
```json
{
  "status": "success",
  "legal_entities_created": 1,
  "legal_entities_updated": 2,
  "restaurants_created": 3,
  "restaurants_updated": 5
}
```

## Integration with External Systems

### iiko Integration

The system will fetch legal entities and restaurants from the iiko back-office API. The following mapping will be used:

1. iiko "department" corresponds to our "restaurant"
2. iiko "corporation" corresponds to our "legal entity"

**API Endpoint:**
```
GET https://{iiko-domain}/resto/api/corporation/departments?key={api-key}&revisionFrom=-1
```

**Sample Response Processing:**
- Departments with `type=1` are legal entities 
- Departments with `type=0` are restaurants
- Restaurants have a `parentId` that references their legal entity
- The `taxpayerIdNumber` field will be mapped to our `tax_id`

**Implementation Notes:**
1. Create a synchronization service that will:
   - Fetch data from iiko API
   - Process the hierarchical structure to identify legal entities and their restaurants
   - Reconcile the data with our existing records (update, insert as needed)
   - Maintain external_id references to preserve relationships

2. The sync can be triggered:
   - Manually through the API
   - On a scheduled basis (e.g., daily)
   - On specific events (account creation, user request)

## Security Considerations

1. Legal entity operations should be restricted to admin users or designated roles
2. Cross-account access to legal entities should be prevented
3. Validation for tax IDs should follow country-specific formats

## Implementation Timeline

1. Database schema updates
2. API endpoint implementation
3. iiko integration service
4. UI components for legal entity management

## Open Questions

1. Should we support multiple restaurant management systems beyond iiko?
2. Do we need to store additional legal entity information (address, registration details, etc.)?
3. How should we handle legal entity mergers or ownership transfers?