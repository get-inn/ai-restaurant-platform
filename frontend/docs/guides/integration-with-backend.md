# Integration with Backend

This guide provides information on integrating the frontend application with the GET INN backend services.

## Overview

The frontend application communicates with the backend through RESTful API endpoints and WebSocket connections. Understanding how to properly integrate with these services is essential for developing new features.

## API Integration

### Base Configuration

API communication is centralized through the API service in `src/services/api.ts`, which configures Axios with common settings:

```typescript
// Example API service configuration
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/v1/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Authentication interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
      // Redirect to login or refresh token
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Using React Query

The application uses TanStack Query (React Query) for data fetching, caching, and state management:

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../services/api';

// Example query hook
export function useInventoryItems() {
  return useQuery({
    queryKey: ['inventory', 'items'],
    queryFn: async () => {
      const { data } = await api.get('/supplier/inventory/items');
      return data;
    },
  });
}

// Example mutation hook
export function useCreateInventoryItem() {
  return useMutation({
    mutationFn: async (newItem) => {
      const { data } = await api.post('/supplier/inventory/items', newItem);
      return data;
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['inventory', 'items'] });
    },
  });
}
```

## WebSocket Integration

Real-time updates are handled through WebSocket connections, particularly for long-running processes like document reconciliation.

### WebSocket Service

```typescript
// Example WebSocket service
export class WebSocketService {
  private socket: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  
  constructor(url: string) {
    this.url = url;
  }
  
  connect() {
    if (this.socket?.readyState === WebSocket.OPEN) return;
    
    this.socket = new WebSocket(this.url);
    
    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };
    
    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const { type, payload } = data;
        
        if (this.listeners.has(type)) {
          this.listeners.get(type)?.forEach(listener => listener(payload));
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    this.socket.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
      }
    };
  }
  
  subscribe(type: string, listener: (data: any) => void) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)?.add(listener);
  }
  
  unsubscribe(type: string, listener: (data: any) => void) {
    this.listeners.get(type)?.delete(listener);
  }
  
  disconnect() {
    this.socket?.close();
    this.socket = null;
  }
}
```

### Using WebSockets with Hooks

```typescript
// Example WebSocket hook for reconciliation progress
export function useReconciliationProgress(reconciliationId: string | null) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'pending' | 'in_progress' | 'completed' | 'error'>('pending');
  const [message, setMessage] = useState<string>('');
  
  useEffect(() => {
    if (!reconciliationId) return;
    
    const wsUrl = `${import.meta.env.VITE_WEBSOCKET_URL}/supplier/reconciliation/${reconciliationId}`;
    const socket = new WebSocket(wsUrl);
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.progress || 0);
      setStatus(data.status);
      setMessage(data.message || '');
    };
    
    return () => {
      socket.close();
    };
  }, [reconciliationId]);
  
  return { progress, status, message };
}
```

## Backend API Reference

All API endpoints follow the pattern `/v1/api/[domain]/[resource]` where:
- `v1` represents the API version
- `api` is a fixed part of the path
- `domain` represents the functional domain
- `resource` represents the specific resource within that domain

### API Domains

The API is organized into the following primary domains:

| Domain | Description | Base Path |
|--------|-------------|-----------|  
| Authentication | User authentication and authorization | `/v1/api/auth` |
| Accounts | Account management | `/v1/api/accounts` |
| Bots | Bot management and conversation | `/v1/api/bots` |
| Chef | Menu and recipe management | `/v1/api/chef` |
| Labor | Staff management | `/v1/api/labor` |
| Supplier | Supplier and procurement | `/v1/api/supplier` |
| Webhooks | External system notifications | `/v1/api/webhooks` |
| Integrations | External system connections | `/v1/api/integrations` |

### Common Endpoints by Domain

#### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/api/auth/login` | User login, returns JWT tokens |
| POST | `/v1/api/auth/logout` | User logout |
| POST | `/v1/api/auth/refresh` | Refresh authentication token |
| GET | `/v1/api/auth/me` | Get current user information |

#### Supplier Module

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/api/supplier/documents` | Upload new document |
| GET | `/v1/api/supplier/documents` | Get list of documents |
| GET | `/v1/api/supplier/documents/{id}` | Get document details |
| POST | `/v1/api/supplier/reconciliation` | Start reconciliation process |
| GET | `/v1/api/supplier/reconciliation` | List reconciliations |
| GET | `/v1/api/supplier/reconciliation/{id}` | Get reconciliation details |
| GET | `/v1/api/supplier/inventory/items` | List inventory items |
| GET | `/v1/api/supplier/inventory/price-changes` | Get price changes |

#### Labor Module

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/api/labor/onboarding` | List staff onboarding processes |
| GET | `/v1/api/labor/onboarding/{id}` | Get onboarding details |
| POST | `/v1/api/labor/onboarding` | Create onboarding process |
| PUT | `/v1/api/labor/onboarding/{id}` | Update onboarding process |

#### Chef Module

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/api/chef/menu/abc-analysis` | Get ABC analysis of menu items |
| GET | `/v1/api/chef/recipes` | List recipes |
| GET | `/v1/api/chef/recipes/{id}` | Get recipe details |

#### Bot Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/api/bots` | List bot instances |
| POST | `/v1/api/bots` | Create bot instance |
| GET | `/v1/api/bots/{id}` | Get bot instance details |
| GET | `/v1/api/bots/{id}/scenarios` | Get bot scenarios |

### WebSocket Endpoints

| WebSocket URL | Description |
|---------------|-------------|
| `/ws/supplier/reconciliation/{reconciliation_id}` | Real-time reconciliation updates |
| `/ws/chain/updates` | Real-time aggregate chain-level updates |

For a complete reference of available endpoints and their parameters, refer to the [Backend API Structure](../../backend/docs/architecture/api-structure.md) documentation.

## Common Integration Patterns

### Authentication Flow

1. User submits login credentials
2. Frontend sends POST request to `/v1/api/auth/login`
3. Backend returns JWT tokens (access and refresh)
4. Frontend stores tokens securely
5. Frontend includes access token in subsequent requests
6. When access token expires, frontend uses refresh token to get a new one

### Data Loading with Loading States

```tsx
function InventoryPage() {
  const { data, isLoading, isError, error } = useInventoryItems();
  
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  if (isError) {
    return <ErrorDisplay message={error.message} />;
  }
  
  return (
    <InventoryTable items={data.items} />
  );
}
```

### File Upload

```tsx
async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', 'invoice');
  
  try {
    const response = await api.post('/supplier/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / (progressEvent.total || 100)
        );
        // Update progress state
      },
    });
    
    return response.data;
  } catch (error) {
    // Handle error
    throw error;
  }
}
```

## Troubleshooting Integration Issues

### CORS Issues

If you encounter CORS errors:
1. Check that the backend has CORS properly configured
2. Verify the frontend is using the correct API URL
3. Ensure authentication headers are properly formatted

### Authentication Failures

If authentication fails:
1. Check token expiration and refresh logic
2. Verify tokens are being stored correctly
3. Confirm that authentication headers are included in requests

### WebSocket Connection Issues

If WebSocket connections fail:
1. Verify the WebSocket URL is correct
2. Check that the backend WebSocket server is running
3. Confirm that authentication is properly handled for WebSocket connections

## Further Reading

For more detailed information about the backend services, refer to:

- [Backend API Structure](../../backend/docs/architecture/api-structure.md)
- [Backend Authentication](../../backend/docs/modules/authentication.md)
- [WebSocket Implementation](../../backend/docs/modules/websockets.md)