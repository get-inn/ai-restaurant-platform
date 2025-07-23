# Data Fetching

The GET INN frontend application uses TanStack Query (formerly React Query) for data fetching, caching, and state management of server data.

## Overview

TanStack Query provides a robust solution for managing server state with these key benefits:

1. Automatic caching and background updates
2. Deduplication of identical requests
3. Stale data handling with configurable refresh policies
4. Optimistic updates for improved UX
5. Automatic error handling and retry logic
6. Pagination and infinite scrolling support
7. Pre-fetching capabilities for improved performance

## Basic Implementation

### Query Setup

The application's data fetching is centralized through a custom API service combined with TanStack Query:

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/v1/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### Query Client Configuration

The TanStack Query client is configured with application-specific defaults:

```typescript
// src/lib/react-query.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 30, // 30 minutes
      refetchOnWindowFocus: true,
      refetchOnMount: true,
      refetchOnReconnect: true,
      retry: 1,
    },
  },
});
```

### Query Provider

The query client is provided at the application root:

```tsx
// src/main.tsx
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './lib/react-query';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      {import.meta.env.DEV && <ReactQueryDevtools />}
    </QueryClientProvider>
  </React.StrictMode>
);
```

## Custom Hooks

### Basic Query Hooks

Custom hooks encapsulate data fetching logic for specific resources:

```typescript
// src/hooks/queries/use-inventory-items.ts
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import type { InventoryItem } from '@/types';

export function useInventoryItems(options = {}) {
  return useQuery({
    queryKey: ['inventory', 'items'],
    queryFn: async () => {
      const { data } = await api.get('/supplier/inventory/items');
      return data as InventoryItem[];
    },
    ...options,
  });
}
```

### Query with Parameters

Queries with parameters adjust the query key accordingly:

```typescript
// src/hooks/queries/use-recipe-details.ts
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import type { Recipe } from '@/types';

export function useRecipeDetails(recipeId: string, options = {}) {
  return useQuery({
    queryKey: ['recipes', recipeId],
    queryFn: async () => {
      const { data } = await api.get(`/chef/recipes/${recipeId}`);
      return data as Recipe;
    },
    enabled: !!recipeId, // Only run query if recipeId exists
    ...options,
  });
}
```

### Mutation Hooks

Mutations for creating, updating, or deleting data:

```typescript
// src/hooks/mutations/use-create-recipe.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import type { Recipe, RecipeInput } from '@/types';

export function useCreateRecipe() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (newRecipe: RecipeInput) => {
      const { data } = await api.post('/chef/recipes', newRecipe);
      return data as Recipe;
    },
    onSuccess: (data) => {
      // Invalidate the recipes list query to refetch
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
      
      // Add the new recipe to the query cache
      queryClient.setQueryData(['recipes', data.id], data);
    },
  });
}
```

## Advanced Patterns

### Dependent Queries

Queries that depend on the results of other queries:

```typescript
// Example of dependent queries
function RecipeWithIngredients({ recipeId }) {
  // First query - get recipe details
  const recipeQuery = useRecipeDetails(recipeId);
  
  // Second query - get ingredient details for each ingredient in the recipe
  const ingredientsQuery = useQuery({
    queryKey: ['recipe', recipeId, 'ingredients'],
    queryFn: async () => {
      // Only run if we have recipe data with ingredients
      if (!recipeQuery.data || !recipeQuery.data.ingredientIds.length) {
        return [];
      }
      
      // Fetch details for each ingredient
      const ingredientPromises = recipeQuery.data.ingredientIds.map(
        (id) => api.get(`/supplier/inventory/items/${id}`)
      );
      
      const responses = await Promise.all(ingredientPromises);
      return responses.map((res) => res.data);
    },
    // Only enabled when recipe data is available
    enabled: !!recipeQuery.data,
  });
  
  // Handle loading and error states
  if (recipeQuery.isLoading) return <Spinner />;
  if (recipeQuery.isError) return <ErrorMessage error={recipeQuery.error} />;
  
  return (
    <div>
      <h1>{recipeQuery.data.name}</h1>
      <div className="ingredients">
        {ingredientsQuery.isLoading ? (
          <Spinner size="sm" />
        ) : (
          <IngredientsList ingredients={ingredientsQuery.data || []} />
        )}
      </div>
    </div>
  );
}
```

### Optimistic Updates

Updating the UI before the server confirms changes:

```typescript
// Example of optimistic update
function InventoryAdjustment({ itemId }) {
  const queryClient = useQueryClient();
  const { data: item } = useInventoryItem(itemId);
  
  const updateMutation = useMutation({
    mutationFn: async ({ id, quantity }) => {
      const { data } = await api.patch(`/supplier/inventory/items/${id}`, { quantity });
      return data;
    },
    onMutate: async (newItem) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['inventory', 'items', itemId] });
      
      // Snapshot the previous value
      const previousItem = queryClient.getQueryData(['inventory', 'items', itemId]);
      
      // Optimistically update to the new value
      queryClient.setQueryData(['inventory', 'items', itemId], {
        ...previousItem,
        quantity: newItem.quantity
      });
      
      // Return context with the previous value
      return { previousItem };
    },
    onError: (err, newItem, context) => {
      // If the mutation fails, use the context to roll back
      queryClient.setQueryData(
        ['inventory', 'items', itemId], 
        context.previousItem
      );
    },
    onSettled: () => {
      // Always refetch after error or success to ensure cache consistency
      queryClient.invalidateQueries({ queryKey: ['inventory', 'items', itemId] });
    },
  });
  
  const handleQuantityChange = (newQuantity) => {
    updateMutation.mutate({ 
      id: itemId,
      quantity: newQuantity
    });
  };
  
  return (
    <div>
      <h2>{item?.name}</h2>
      <QuantityAdjuster
        value={item?.quantity || 0}
        onChange={handleQuantityChange}
        isLoading={updateMutation.isPending}
      />
    </div>
  );
}
```

### Infinite Queries

Handling paginated data with infinite scrolling:

```typescript
// Example of infinite query for activity feed
function ActivityFeed() {
  const {
    data,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
  } = useInfiniteQuery({
    queryKey: ['activities'],
    queryFn: async ({ pageParam = 1 }) => {
      const { data } = await api.get('/dashboard/activities', {
        params: { page: pageParam, limit: 20 }
      });
      return data;
    },
    getNextPageParam: (lastPage) => {
      return lastPage.nextPage ?? undefined;
    },
  });
  
  // Handle intersection observer for infinite scrolling
  const observerRef = useRef(null);
  
  const lastItemRef = useCallback(
    (node) => {
      if (isFetchingNextPage) return;
      
      if (observerRef.current) observerRef.current.disconnect();
      
      observerRef.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasNextPage) {
          fetchNextPage();
        }
      });
      
      if (node) observerRef.current.observe(node);
    },
    [isFetchingNextPage, fetchNextPage, hasNextPage]
  );
  
  return (
    <div className="activity-feed">
      <h2>Recent Activity</h2>
      
      {status === 'pending' ? (
        <Spinner />
      ) : status === 'error' ? (
        <ErrorMessage error={error} />
      ) : (
        <>
          {data.pages.map((page, i) => (
            <React.Fragment key={i}>
              {page.activities.map((activity, index) => (
                <ActivityItem 
                  key={activity.id} 
                  activity={activity}
                  ref={
                    i === data.pages.length - 1 && 
                    index === page.activities.length - 1
                      ? lastItemRef
                      : undefined
                  }
                />
              ))}
            </React.Fragment>
          ))}
          
          <div className="loading-more">
            {isFetchingNextPage ? <Spinner size="sm" /> : null}
          </div>
        </>
      )}
    </div>
  );
}
```

## Error Handling

### Global Error Handling

Centralized error handling for API requests:

```typescript
// src/services/api.ts
// Add global error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
      // Clear auth tokens
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      
      // Redirect to login page
      window.location.href = '/login';
    }
    
    // Handle 403 Forbidden errors
    if (error.response?.status === 403) {
      // Show permission denied toast
      toast.error('Permission denied. You do not have access to this resource.');
    }
    
    // Handle 5xx server errors
    if (error.response?.status >= 500) {
      // Show server error toast
      toast.error('Server error. Please try again later.');
    }
    
    return Promise.reject(error);
  }
);
```

### Query-Specific Error Handling

Custom error handling for specific queries:

```typescript
function InventoryPage() {
  const { data, error, isError, isLoading } = useInventoryItems({
    onError: (error) => {
      // Custom error handling for this specific query
      if (error.response?.status === 404) {
        toast.error('Inventory data not found. Please contact support.');
      }
    }
  });
  
  if (isLoading) return <LoadingState />;
  
  if (isError) {
    return (
      <ErrorState
        message="Failed to load inventory data"
        details={error.message}
        retry={() => queryClient.invalidateQueries({ queryKey: ['inventory', 'items'] })}
      />
    );
  }
  
  return <InventoryTable items={data} />;
}
```

## Performance Optimizations

### Query Key Structure

Consistent query key structure for effective caching:

```typescript
// Query key structure patterns

// Collection queries
['inventory', 'items'] // All inventory items
['inventory', 'items', { status: 'low' }] // Filtered inventory items
['recipes'] // All recipes
['recipes', { category: 'appetizer' }] // Filtered recipes

// Entity queries
['inventory', 'items', itemId] // Specific inventory item
['recipes', recipeId] // Specific recipe
['recipes', recipeId, 'details'] // Specific aspect of an entity

// Nested resources
['restaurants', restaurantId, 'menu'] // Menu for a specific restaurant
['suppliers', supplierId, 'invoices'] // Invoices for a specific supplier
```

### Selective Loading

Using `select` to transform and filter data:

```typescript
// Example of data transformation with select
function LowStockItems() {
  const { data } = useInventoryItems({
    select: (items) => {
      return items
        .filter(item => item.quantity < item.reorderLevel)
        .sort((a, b) => {
          // Sort by criticality (how far below reorder level)
          const aCriticality = a.reorderLevel - a.quantity;
          const bCriticality = b.reorderLevel - b.quantity;
          return bCriticality - aCriticality;
        });
    }
  });
  
  return <LowStockTable items={data || []} />;
}
```

### Prefetching

Preloading data for improved user experience:

```typescript
// Example of prefetching recipe details on hover
function RecipeList() {
  const queryClient = useQueryClient();
  const { data: recipes } = useRecipes();
  
  const prefetchRecipe = useCallback((recipeId) => {
    queryClient.prefetchQuery({
      queryKey: ['recipes', recipeId],
      queryFn: async () => {
        const { data } = await api.get(`/chef/recipes/${recipeId}`);
        return data;
      },
      staleTime: 1000 * 60 * 5, // 5 minutes
    });
  }, [queryClient]);
  
  return (
    <ul className="recipe-list">
      {recipes?.map((recipe) => (
        <li 
          key={recipe.id}
          onMouseEnter={() => prefetchRecipe(recipe.id)}
        >
          <Link to={`/recipes/${recipe.id}`}>{recipe.name}</Link>
        </li>
      ))}
    </ul>
  );
}
```

### Query Cancellation

Cancelling stale queries to prevent race conditions:

```typescript
// Example of query cancellation with AbortController
function useSearchRecipes(searchTerm) {
  return useQuery({
    queryKey: ['recipes', 'search', searchTerm],
    queryFn: async ({ signal }) => {
      if (!searchTerm || searchTerm.length < 2) {
        return [];
      }
      
      const { data } = await api.get('/chef/recipes/search', {
        params: { q: searchTerm },
        signal, // Pass the AbortController signal
      });
      
      return data;
    },
    enabled: searchTerm.length >= 2,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
```

## Best Practices

### 1. Query Key Management

- Use consistent query key patterns
- Include necessary parameters in query keys
- Structure keys hierarchically for related data

### 2. Custom Query Hooks

- Encapsulate query logic in custom hooks
- Provide sensible defaults for query options
- Allow overriding options when needed

### 3. Data Transformation

- Use `select` for client-side transformations
- Keep raw data in the cache, transform for display

### 4. Error Handling

- Implement global error handling for common cases
- Add query-specific error handling for special cases
- Provide retry mechanisms for transient errors

### 5. Loading States

- Always handle loading and error states in the UI
- Use skeleton loaders for better UX during loading

### 6. Query Invalidation

- Invalidate related queries after mutations
- Use specific query keys for targeted invalidation
- Consider optimistic updates for better UX

### 7. Background Updates

- Configure appropriate `staleTime` for different data types
- Use background fetching for frequently changing data

## Debugging

The application includes React Query Devtools in development mode:

```tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// In App component or provider setup
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppRoutes />
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
```

The devtools provide:

- Real-time view of query cache
- Query status monitoring
- Manual refetching of queries
- Query invalidation testing
- Cache inspection

## Additional Resources

- [TanStack Query Documentation](https://tanstack.com/query/latest/docs/react/overview)
- [TanStack Query Examples](https://tanstack.com/query/latest/docs/react/examples/basic)
- [Axios Documentation](https://axios-http.com/docs/intro)