# Frontend Technical Specification v2: GET INN Platform

## 1. Platform Overview

### 1.1. Introduction

**GET INN** is the world's first platform that creates self-operating restaurants using AI agents. This specification provides comprehensive guidance for developing the frontend of the platform, which will provide an intuitive and powerful interface for restaurant owners and managers to automate critical operations, from procurement and kitchen management to staff management and menu optimization.

### 1.2. Core Modules

The platform offers three AI-powered modules:

1. **AI Supplier:** Management interface for procurement, reconciliation, and inventory tracking.
2. **AI Labor:** Interface for staff management, focused on onboarding processes.
3. **AI Chef:** Tools for menu analysis, recipe management, and insights.

## 2. Technology Stack

### 2.1. Frontend Technologies

- **Framework:** Next.js (App Router)
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui
- **Language:** TypeScript
- **State Management:** React Context API + React Query for server state
- **Deployment:** Vercel

### 2.2. Communication with Backend

- **API Protocol:** REST
- **Real-time Updates:** WebSockets
- **Authentication:** JWT via custom auth backend
- **File Uploads:** Multi-part form data

## 3. Authentication & Authorization

### 3.1. User Authentication

- **Authentication Provider:** Custom backend auth system
- **Methods:** Email/password
- **Token Storage:** HttpOnly cookies / localStorage

### 3.2. Role-Based Access Control

The application will support the following roles:

- **Admin:** Full access to all features and data
- **Account Manager:** Access to specific account and its restaurants/stores
- **Restaurant Manager:** Access limited to specific restaurant(s)
- **Chef:** Access to AI Chef module for specific restaurant(s)
- **Staff:** Limited access to labor/tasks for a specific restaurant

### 3.3. Authentication Flows

#### 3.3.1. Login Flow

1. User enters credentials on login page
2. Frontend sends authentication request to backend auth endpoint
3. On success, JWT token is received and stored
4. User is redirected to dashboard
5. Backend API endpoints are called with JWT in Authorization header

**API Endpoint:** `POST /v1/api/auth/login`

#### 3.3.2. Logout Flow

1. User clicks logout button
2. Frontend sends logout request to backend
3. Frontend clears stored tokens and auth state
4. User is redirected to login page

**API Endpoint:** `POST /v1/api/auth/logout`

#### 3.3.3. Token Refresh

1. Frontend detects token expiration
2. Silent refresh attempt is made using refresh token
3. If failed, user is prompted to login again

**API Endpoint:** `POST /v1/api/auth/refresh`

## 4. Navigation Structure

### 4.1. Main Navigation

The platform features a sidebar navigation for seamless access to all modules:

- **Dashboard**
- **AI Supplier**
  - Documents
  - Invoices
  - Reconciliation
  - Inventory
- **AI Labor**
  - Onboarding
- **AI Chef**
  - Menu Analysis
  - Recipes
  - Menu Management
- **Settings**
  - Account
  - Restaurants
  - Stores
  - Users
  - Suppliers
  - Units

### 4.2. Secondary Navigation Elements

- **Breadcrumb Bar:** Shows current location in app hierarchy
- **Account/Restaurant Selector:** Allows switching between accounts/restaurants
- **Notification Center:** Bell icon with dropdown for system notifications
- **User Menu:** Access to profile, preferences, and logout

## 5. Global Components

### 5.1. Layout Components

- **AppLayout:** Main application layout with sidebar, header, and content area
- **AuthLayout:** Layout for authentication pages
- **PageLayout:** Standard page layout with header, actions, and content

### 5.2. Common UI Components

- **DataTable:** Reusable table with sorting, filtering, and pagination
- **FilterBar:** Search and filter controls for list views
- **ActionMenu:** Context menu for item actions
- **StatusBadge:** Visual indicator for various status types
- **ConfirmDialog:** Confirmation modal for destructive actions
- **NotificationToast:** Transient notification display
- **EmptyState:** Placeholder for empty lists or sections
- **LoadingState:** Loading indicators for async operations

### 5.3. Form Components

- **FormFields:** Enhanced form inputs with validation
- **MultiSelect:** Dropdown with multiple selection support
- **DateRangePicker:** Date range selection component
- **FileUpload:** Drag and drop file upload with preview
- **SearchableSelect:** Dropdown with search functionality
- **AutocompleteInput:** Text input with autocomplete suggestions

## 6. Core Module Specifications

### 6.1. Dashboard

#### 6.1.1. Main Dashboard

**Description:** Central hub showing key metrics and recent activity across all modules.

**Components:**
- KPI Cards showing key metrics
- Recent reconciliations widget
- Inventory status overview
- Onboarding progress summary
- Menu performance highlights

**API Endpoints:**
- `GET /v1/api/dashboard/summary` - Get dashboard summary data
- `GET /v1/api/dashboard/recent-activity` - Get recent activity

### 6.2. AI Supplier Module

#### 6.2.1. Document Management

**Description:** Interface for uploading, viewing, and managing supplier documents.

**Pages & Routes:**
- **Document List:** `/supplier/documents`
- **Document Upload:** `/supplier/documents/upload`
- **Document Details:** `/supplier/documents/[id]`

**Key Features:**
- Document upload with drag-and-drop
- Document type classification
- Searchable document list with filters
- Document preview for PDF/Excel files
- Document metadata display

**API Endpoints:**
- `POST /v1/api/supplier/documents` - Upload new document
- `GET /v1/api/supplier/documents` - Get list of documents
- `GET /v1/api/supplier/documents/{id}` - Get document details
- `GET /v1/api/supplier/documents/{id}/download` - Download document
- `DELETE /v1/api/supplier/documents/{id}` - Delete document

**UI Components:**
- DocumentUploader
- DocumentList
- DocumentPreview
- DocumentMetadata
- DocumentFilterBar

#### 6.2.2. Invoice Management

**Description:** Interface for viewing and managing supplier invoices.

**Pages & Routes:**
- **Invoice List:** `/supplier/invoices`
- **Invoice Entry:** `/supplier/invoices/new`
- **Invoice Details:** `/supplier/invoices/[id]`

**Key Features:**
- Manual invoice entry
- Invoice line item management
- Link invoices to suppliers and inventory items
- Invoice listing with filtering by supplier, date range
- Invoice details view with line items

**API Endpoints:**
- `POST /v1/api/supplier/invoices` - Create new invoice
- `GET /v1/api/supplier/invoices` - Get list of invoices
- `GET /v1/api/supplier/invoices/{id}` - Get invoice details
- `PUT /v1/api/supplier/invoices/{id}` - Update invoice
- `DELETE /v1/api/supplier/invoices/{id}` - Delete invoice

**UI Components:**
- InvoiceForm
- InvoiceLineItemEditor
- InvoiceList
- InvoiceDetail
- SupplierSelector
- InventoryItemSelector

#### 6.2.3. Reconciliation

**Description:** Interface for reconciling supplier documents with system records.

**Pages & Routes:**
- **Reconciliation Overview:** `/supplier/reconciliation`
- **Upload & Start Reconciliation:** `/supplier/reconciliation/upload`
- **Reconciliation Details:** `/supplier/reconciliation/[id]`
- **Reconciliation History:** `/supplier/reconciliation/history`

**Key Features:**
- Document upload for reconciliation
- Real-time reconciliation progress tracking via WebSocket
- Detailed reconciliation results with categorized items
- Matched/unmatched items display
- Excel export of reconciliation results
- Historical reconciliation records

**API Endpoints:**
- `POST /v1/api/supplier/reconciliation` - Start reconciliation process
- `GET /v1/api/supplier/reconciliation` - List reconciliations
- `GET /v1/api/supplier/reconciliation/{id}` - Get reconciliation details
- `GET /v1/api/supplier/reconciliation/{id}/status` - Get reconciliation status
- `GET /v1/api/supplier/reconciliation/{id}/matched` - Get matched items
- `GET /v1/api/supplier/reconciliation/{id}/missing-restaurant` - Get items missing in restaurant
- `GET /v1/api/supplier/reconciliation/{id}/missing-supplier` - Get items missing in supplier document
- `GET /v1/api/supplier/reconciliation/{id}/mismatches` - Get mismatched items
- `GET /v1/api/supplier/reconciliation/{id}/export` - Export reconciliation results

**WebSocket:**
- `WS /ws/supplier/reconciliation/{reconciliation_id}` - Real-time reconciliation updates

**UI Components:**
- ReconciliationUploader
- ReconciliationProgressTracker
- ReconciliationResultTabs
- MatchedItemsTable
- UnmatchedItemsTable
- MismatchedItemsTable
- ExportButton
- ReconciliationHistory

#### 6.2.4. Inventory

**Description:** Interface for managing inventory items and tracking price changes.

**Pages & Routes:**
- **Inventory Overview:** `/supplier/inventory`
- **Inventory Items:** `/supplier/inventory/items`
- **Item Details:** `/supplier/inventory/items/[id]`
- **Price History:** `/supplier/inventory/prices`

**Key Features:**
- Inventory item list with filtering and search
- Item creation and editing
- Price change tracking with volatility indicators
- Price history charts
- Menu impact analysis for price changes

**API Endpoints:**
- `POST /v1/api/supplier/inventory/items` - Create inventory item
- `GET /v1/api/supplier/inventory/items` - List inventory items
- `GET /v1/api/supplier/inventory/items/{id}` - Get item details
- `PUT /v1/api/supplier/inventory/items/{id}` - Update item
- `DELETE /v1/api/supplier/inventory/items/{id}` - Delete item
- `GET /v1/api/supplier/inventory/price-changes` - Get price changes
- `GET /v1/api/supplier/inventory/price-history/{id}` - Get price history
- `GET /v1/api/supplier/inventory/impacted-menus/{id}` - Get affected menus
- `POST /v1/api/supplier/inventory/stock-adjustments` - Adjust stock
- `GET /v1/api/supplier/inventory/stock/store/{store_id}` - Get store stock

**UI Components:**
- InventoryList
- InventoryItemForm
- PriceChangeTable
- PriceHistoryChart
- VolatilityIndicator
- StockAdjustmentForm
- MenuImpactAnalysis

#### 6.2.5. Units Management

**Description:** Interface for managing units of measure and conversions.

**Pages & Routes:**
- **Units List:** `/supplier/units`
- **Unit Conversions:** `/supplier/units/conversions`

**Key Features:**
- Units list with categories
- Unit creation and editing
- Standard unit conversion management
- Item-specific conversion management

**API Endpoints:**
- `POST /v1/api/supplier/units` - Create unit
- `GET /v1/api/supplier/units` - List units
- `PUT /v1/api/supplier/units/{id}` - Update unit
- `DELETE /v1/api/supplier/units/{id}` - Delete unit
- `POST /v1/api/supplier/unit-conversions` - Create conversion
- `GET /v1/api/supplier/unit-conversions` - List conversions
- `DELETE /v1/api/supplier/unit-conversions/{id}` - Delete conversion
- `POST /v1/api/supplier/item-specific-conversions` - Create item conversion
- `GET /v1/api/supplier/item-specific-conversions` - List item conversions

**UI Components:**
- UnitsList
- UnitForm
- ConversionForm
- ItemSpecificConversionForm
- UnitCategorySelector

### 6.3. AI Labor Module

#### 6.3.1. Onboarding

**Description:** Interface for tracking and managing staff onboarding processes.

**Pages & Routes:**
- **Onboarding Overview:** `/labor/onboarding`
- **Onboarding Details:** `/labor/onboarding/details`
- **Staff Profile:** `/labor/onboarding/[id]`

**Key Features:**
- Staff onboarding overview by restaurant
- Staff list with status indicators
- Onboarding progress tracking
- Step completion management
- Notes and documentation for each step

**API Endpoints:**
- `POST /v1/api/labor/onboarding` - Create staff onboarding
- `GET /v1/api/labor/onboarding` - List all onboarding staff
- `GET /v1/api/labor/onboarding/restaurant/{restaurant_id}` - Staff by restaurant
- `GET /v1/api/labor/onboarding/{id}` - Get onboarding details
- `PUT /v1/api/labor/onboarding/{id}` - Update onboarding
- `DELETE /v1/api/labor/onboarding/{id}` - Delete onboarding record
- `POST /v1/api/labor/onboarding/{id}/steps` - Add onboarding step
- `PUT /v1/api/labor/onboarding/{id}/steps/{step_id}` - Update step

**UI Components:**
- OnboardingDashboard
- StaffList
- OnboardingProgressBar
- StepCompletionForm
- OnboardingTimeline
- StaffProfileCard

### 6.4. AI Chef Module

#### 6.4.1. Menu Analysis

**Description:** Interface for analyzing menu performance using ABC analysis.

**Pages & Routes:**
- **Menu ABC Analysis:** `/chef/menu`
- **Item Performance:** `/chef/menu/item/[id]`
- **Menu Insights:** `/chef/menu/insights`

**Key Features:**
- ABC analysis visualization (quadrant chart)
- Performance metrics for menu items
- Filtering by date range and categories
- Drill-down item analysis
- AI-generated insights and recommendations

**API Endpoints:**
- `GET /v1/api/chef/menu/abc-analysis` - Get ABC analysis
- `GET /v1/api/chef/menu/item/{id}/performance` - Get item performance
- `GET /v1/api/chef/menu/insights` - Get AI-generated insights
- `GET /v1/api/chef/reports/menu-abc-analysis` - Generate report

**UI Components:**
- ABCQuadrantChart
- MenuItemList
- PerformanceMetricsCards
- InsightsList
- DateRangeFilter
- CategoryFilter
- PerformanceTrend

#### 6.4.2. Recipe Management

**Description:** Interface for creating and managing recipes.

**Pages & Routes:**
- **Recipe List:** `/chef/recipes`
- **Recipe Editor:** `/chef/recipes/[id]/edit`
- **Recipe Details:** `/chef/recipes/[id]`

**Key Features:**
- Recipe creation with ingredients and instructions
- Ingredient selection from inventory
- Portion and yield calculation
- Cost calculation based on ingredient prices
- Recipe categorization and search

**API Endpoints:**
- `POST /v1/api/chef/recipes` - Create recipe
- `GET /v1/api/chef/recipes` - List recipes
- `GET /v1/api/chef/recipes/{id}` - Get recipe details
- `PUT /v1/api/chef/recipes/{id}` - Update recipe
- `DELETE /v1/api/chef/recipes/{id}` - Delete recipe
- `POST /v1/api/chef/recipes/{recipe_id}/ingredients` - Add ingredient
- `DELETE /v1/api/chef/recipes/{recipe_id}/ingredients/{ingredient_id}` - Remove ingredient

**UI Components:**
- RecipeList
- RecipeForm
- IngredientSelector
- IngredientList
- CostCalculator
- InstructionEditor
- YieldCalculator

#### 6.4.3. Menu Management

**Description:** Interface for creating and managing restaurant menus.

**Pages & Routes:**
- **Menu List:** `/chef/menus`
- **Menu Builder:** `/chef/menus/[id]/edit`
- **Menu Item Editor:** `/chef/menu-items/[id]/edit`

**Key Features:**
- Menu creation and editing
- Menu item organization by category
- Menu item creation with recipe linking
- Pricing management
- Menu publishing and versioning

**API Endpoints:**
- `POST /v1/api/chef/menus` - Create menu
- `GET /v1/api/chef/menus` - List menus
- `GET /v1/api/chef/menus/{id}` - Get menu details
- `PUT /v1/api/chef/menus/{id}` - Update menu
- `DELETE /v1/api/chef/menus/{id}` - Delete menu
- `POST /v1/api/chef/menu-items` - Create menu item
- `GET /v1/api/chef/menu-items` - List menu items
- `GET /v1/api/chef/menu-items/{id}` - Get item details
- `PUT /v1/api/chef/menu-items/{id}` - Update item
- `DELETE /v1/api/chef/menu-items/{id}` - Delete item
- `POST /v1/api/chef/menus/{menu_id}/items` - Add item to menu

**UI Components:**
- MenuList
- MenuBuilder
- MenuItemForm
- CategoryManager
- RecipeSelector
- PricingForm
- MenuPreview

## 7. Settings Module

### 7.1. Account Management

**Description:** Interface for managing restaurant chains.

**Pages & Routes:**
- **Account List:** `/settings/accounts` (Admin only)
- **Account Details:** `/settings/accounts/[id]`

**API Endpoints:**
- `POST /v1/api/accounts` - Create account
- `GET /v1/api/accounts` - List accounts
- `GET /v1/api/accounts/{id}` - Get account details
- `PUT /v1/api/accounts/{id}` - Update account
- `DELETE /v1/api/accounts/{id}` - Delete account

### 7.2. Restaurant Management

**Description:** Interface for managing restaurants within accounts.

**Pages & Routes:**
- **Restaurant List:** `/settings/restaurants`
- **Restaurant Details:** `/settings/restaurants/[id]`

**API Endpoints:**
- `POST /v1/api/accounts/{account_id}/restaurants` - Create restaurant
- `GET /v1/api/accounts/{account_id}/restaurants` - List restaurants
- `GET /v1/api/restaurants/{id}` - Get restaurant details
- `PUT /v1/api/restaurants/{id}` - Update restaurant
- `DELETE /v1/api/restaurants/{id}` - Delete restaurant

### 7.3. Store Management

**Description:** Interface for managing stores within restaurants.

**Pages & Routes:**
- **Store List:** `/settings/restaurants/[id]/stores`
- **Store Details:** `/settings/stores/[id]`

**API Endpoints:**
- `POST /v1/api/restaurants/{restaurant_id}/stores` - Create store
- `GET /v1/api/restaurants/{restaurant_id}/stores` - List stores
- `GET /v1/api/stores/{id}` - Get store details
- `PUT /v1/api/stores/{id}` - Update store
- `DELETE /v1/api/stores/{id}` - Delete store

### 7.4. User Management

**Description:** Interface for managing user accounts and roles.

**Pages & Routes:**
- **User List:** `/settings/users`
- **User Details:** `/settings/users/[id]`

**API Endpoints:**
- `GET /v1/api/users` - List users
- `GET /v1/api/users/{id}` - Get user details
- `PUT /v1/api/users/{id}/role` - Update user role
- `GET /v1/api/users/me` - Get current user profile

### 7.5. Supplier Management

**Description:** Interface for managing suppliers.

**Pages & Routes:**
- **Supplier List:** `/settings/suppliers`
- **Supplier Details:** `/settings/suppliers/[id]`

**API Endpoints:**
- `POST /v1/api/accounts/{account_id}/suppliers` - Create supplier
- `GET /v1/api/accounts/{account_id}/suppliers` - List suppliers
- `GET /v1/api/suppliers/{id}` - Get supplier details
- `PUT /v1/api/suppliers/{id}` - Update supplier
- `DELETE /v1/api/suppliers/{id}` - Delete supplier

## 8. Real-time Communication

### 8.1. WebSocket Implementation

For real-time updates, the application will use WebSocket connections:

```typescript
// WebSocket hook example
export function useReconciliationProgress(reconciliationId: string | null) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('pending');
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (!reconciliationId) return;
    
    const socket = new WebSocket(`${WS_URL}/ws/supplier/reconciliation/${reconciliationId}`);
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.progress);
      setStatus(data.status);
      if (data.error) setError(data.error);
    };
    
    socket.onclose = () => {
      console.log('WebSocket connection closed');
    };
    
    return () => {
      socket.close();
    };
  }, [reconciliationId]);
  
  return { progress, status, error };
}
```

### 8.2. WebSocket Endpoints

- `WS /ws/supplier/reconciliation/{reconciliation_id}` - Reconciliation progress updates

## 9. Workflow and User Experience

Drawing inspiration from modern SaaS dashboards like Monday.com, Notion, and hotel management systems, the GET INN platform will offer an intuitive and efficient user experience.

### 9.1. Core UX Principles

- **Progressive Disclosure**: Present only the most relevant information first, with details available on demand
- **Contextual Actions**: Show actions only when they're relevant to the current context
- **Visual Hierarchy**: Use size, color, and position to guide users through interfaces
- **Immediate Feedback**: Provide real-time feedback for all user interactions
- **Consistency**: Maintain consistent patterns across the platform

### 9.2. Interactive Interface

The app provides a clean and user-friendly interface with rich interactive features:

#### 9.2.1. Drag-and-Drop Features

- **Menu Builder**: Drag and drop items to arrange menu structure
- **Dashboard Widgets**: Customize dashboard layouts through dragging components
- **Reconciliation Process**: Drag items between categories during reconciliation review
- **Inventory Organization**: Drag to reorganize inventory categories

#### 9.2.2. In-line Editing

- Direct editing of text fields without modal dialogs where appropriate
- Quick-edit mode for lists and tables
- Instant saving with visual confirmation

#### 9.2.3. Progressive Loading

- Skeleton loaders for content that's being fetched
- Infinite scrolling for long lists with smart prefetching
- Chunked loading for large datasets

### 9.3. Motion and Animation

- Subtle transitions between states (200-300ms)
- Micro-interactions to provide feedback (buttons, toggles, selections)
- Purposeful animations that guide user attention
- Reduced motion option for accessibility

## 10. Form Handling & Validation

### 10.1. Form Strategy

Forms will be built using a combination of:

- React Hook Form for form state management
- Zod for validation schemas
- Custom components for field types

### 10.2. Validation Strategy

- Client-side validation for immediate feedback
- Server-side validation as final check
- Consistent error display pattern

### 10.3. Form Example

```tsx
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

// Validation schema
const inventoryItemSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  defaultUnitId: z.string().uuid("Please select a unit"),
  category: z.string().optional(),
  itemType: z.enum(["raw_ingredient", "semi_finished", "finished_product"]),
  reorderLevel: z.number().optional(),
});

// Component
function InventoryItemForm({ onSubmit, initialData }) {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(inventoryItemSchema),
    defaultValues: initialData || {},
  });
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="space-y-4">
        <div>
          <label>Name</label>
          <input {...register("name")} className="input" />
          {errors.name && <p className="error">{errors.name.message}</p>}
        </div>
        
        <div>
          <label>Description</label>
          <textarea {...register("description")} className="textarea" />
        </div>
        
        {/* Other fields */}
        
        <button type="submit" className="btn btn-primary">Save</button>
      </div>
    </form>
  );
}
```

## 11. User Experience with Themes

The platform will support multiple themes to accommodate different user preferences and working environments.

### 11.1. Theme Implementation

```typescript
// theme-config.js
module.exports = {
  themes: {
    light: {
      background: 'bg-white',
      text: 'text-gray-900',
      card: 'bg-white border border-gray-200',
      border: 'border-gray-200',
      hover: 'hover:bg-gray-50',
      sidebar: 'bg-gray-50',
      shadow: 'shadow-sm',
    },
    dark: {
      background: 'bg-gray-900',
      text: 'text-gray-100',
      card: 'bg-gray-800 border border-gray-700',
      border: 'border-gray-700',
      hover: 'hover:bg-gray-700',
      sidebar: 'bg-gray-800',
      shadow: 'shadow-md shadow-gray-900',
    },
  },
}
```

### 11.2. Theme Options

#### 11.2.1. Light Theme

The default theme is bright and minimalistic, designed for:
- Professional daytime usage
- High-contrast environments
- Maximum readability of complex data
- Clean, modern appearance with a light background and dark text

#### 11.2.2. Dark Theme

The dark theme offers a darker background with light text, designed for:
- Users who prefer lower screen brightness
- Low-light environments
- Extended usage sessions
- Reduced eye strain

### 11.3. Theme Switching

Theme switching is managed through a global context and stored in local storage for persistence:

```tsx
const ThemeContext = createContext<{
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}>({ theme: 'light', toggleTheme: () => {} });

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const savedTheme = localStorage.getItem('theme');
    return (savedTheme === 'dark' || savedTheme === 'light') ? savedTheme : 'light';
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
```

## 12. Data Fetching & State Management

### 12.1. Data Fetching Strategy

The application will use React Query for data fetching, with a custom API client:

```typescript
// API client
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// React Query hook
import { useQuery } from '@tanstack/react-query';

export function useInventoryItems(filters) {
  return useQuery({
    queryKey: ['inventory-items', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.category) params.append('category', filters.category);
      
      const { data } = await apiClient.get(`/supplier/inventory/items?${params}`);
      return data;
    },
  });
}
```

### 12.2. Global State Management

For application-wide state, we'll use React Context:

```typescript
// Auth context
import { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { apiClient } from '../lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // Check for existing session
    checkSession()
      .then(user => setUser(user))
      .finally(() => setIsLoading(false));
  }, []);
  
  const checkSession = async () => {
    try {
      const { data } = await apiClient.get('/auth/me');
      return data.user;
    } catch (error) {
      return null;
    }
  };
  
  const login = async (email, password) => {
    const { data } = await apiClient.post('/auth/login', { email, password });
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('refresh_token', data.refreshToken);
    setUser(data.user);
  };
  
  const logout = async () => {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
    }
  };
  
  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) return false;
      
      const { data } = await apiClient.post('/auth/refresh', { refreshToken });
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('refresh_token', data.refreshToken);
      return true;
    } catch (error) {
      return false;
    }
  };
  
  return (
    <AuthContext.Provider value={{ 
      user, 
      isLoading, 
      login, 
      logout,
      refreshToken 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

## 13. Error Handling

### 13.1. API Error Handling

```typescript
// API error handler
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Try token refresh on 401 errors
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      try {
        const refreshed = await authContext.refreshToken();
        if (refreshed) {
          // Retry the original request with new token
          const token = localStorage.getItem('auth_token');
          error.config.headers['Authorization'] = `Bearer ${token}`;
          return apiClient(error.config);
        }
      } catch (refreshError) {
        // Refresh failed, proceed to logout
      }
      
      // If we got here, refresh failed or wasn't available
      await authContext.logout();
      router.push('/login');
    }
    
    // Format error for consistent handling
    const formattedError = {
      status: error.response?.status,
      message: error.response?.data?.detail || 'An error occurred',
      code: error.response?.data?.code,
      data: error.response?.data?.data,
    };
    
    return Promise.reject(formattedError);
  }
);

// Component error handling
const { mutate, isError, error } = useMutation({
  mutationFn: createInventoryItem,
  onSuccess: () => {
    toast.success('Item created successfully');
    queryClient.invalidateQueries(['inventory-items']);
    router.push('/supplier/inventory');
  },
  onError: (error) => {
    toast.error(`Failed to create item: ${error.message}`);
  }
});
```

### 13.2. UI Error States

- Form validation errors
- Empty states for lists
- Error boundaries for component failures
- Toast notifications for transient errors

## 14. Responsive Design

### 14.1. Breakpoint Strategy

The application will use Tailwind's default breakpoints:

- **sm:** 640px
- **md:** 768px
- **lg:** 1024px
- **xl:** 1280px
- **2xl:** 1536px

### 14.2. Mobile-First Approach

All components will be designed mobile-first with responsive adaptations:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => (
    <ItemCard key={item.id} item={item} />
  ))}
</div>
```

### 14.3. Component Adaptations

Certain components will have different layouts on mobile:

- Sidebar collapses to bottom navigation or hamburger menu
- Tables convert to cards
- Multi-column forms stack vertically

## 15. Accessibility

### 15.1. Core Requirements

- All interactive elements must be keyboard navigable
- Proper aria attributes on custom components
- Sufficient color contrast (WCAG AA compliance)
- Screen reader support for all content

### 15.2. Implementation Examples

```tsx
// Accessible button
<button 
  onClick={handleClick}
  aria-label="Delete item"
  disabled={isLoading}
  className="btn"
>
  {isLoading ? 'Deleting...' : 'Delete'}
</button>

// Form input with label association
<div>
  <label htmlFor="name-input">Name</label>
  <input 
    id="name-input"
    type="text" 
    aria-invalid={!!errors.name}
    aria-describedby={errors.name ? "name-error" : undefined}
  />
  {errors.name && (
    <p id="name-error" className="error">
      {errors.name.message}
    </p>
  )}
</div>
```

## 16. Performance Optimization

### 16.1. Code Splitting

Next.js provides automatic code splitting by route. Additional splitting:

```typescript
// Dynamic import for heavy components
const Chart = dynamic(() => import('../components/Chart'), {
  loading: () => <div>Loading chart...</div>,
  ssr: false, // For client-side only components
});
```

### 16.2. Virtualization

For long lists, use virtualization:

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }) {
  const parentRef = useRef(null);
  
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });
  
  return (
    <div ref={parentRef} className="h-96 overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {items[virtualItem.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 16.3. Memoization

Use memoization for expensive calculations and components:

```tsx
// Memoized component
const MemoizedTable = React.memo(function Table({ data }) {
  // Component implementation
});

// Memoized calculation
const getFilteredItems = React.useCallback(
  (items, filter) => {
    return items.filter(item => 
      item.name.toLowerCase().includes(filter.toLowerCase())
    );
  },
  []
);

function ItemList({ items }) {
  const [filter, setFilter] = useState('');
  const filteredItems = useMemo(
    () => getFilteredItems(items, filter),
    [items, filter, getFilteredItems]
  );
  
  // Render filtered items
}
```

## 17. Project Structure

```
/src
  /app                       # Next.js App Router
    /api                     # API routes
    /(auth)                  # Auth pages
      /login/page.tsx
      /signup/page.tsx
    /(dashboard)             # Protected pages
      /page.tsx              # Dashboard
      /supplier/             # AI Supplier module
        /documents/
        /invoices/
        /reconciliation/
        /inventory/
      /labor/                # AI Labor module
        /onboarding/
      /chef/                 # AI Chef module
        /menu/
        /recipes/
        /menus/
      /settings/             # Settings pages
    /layout.tsx              # Root layout
  /components                # Shared components
    /ui                      # Basic UI components
    /forms                   # Form components
    /charts                  # Data visualization
    /tables                  # Table components
    /layouts                 # Page layouts
    /modules                 # Module-specific components
      /supplier/
      /labor/
      /chef/
  /hooks                     # Custom hooks
  /lib                       # Utility libraries
    /api.ts                  # API client
    /auth.ts                 # Authentication utilities
    /validation.ts           # Validation schemas
  /providers                 # Context providers
  /styles                    # Global styles
  /types                     # TypeScript type definitions
```

## 18. Design System

### 18.1. Color Palette

```typescript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f7ff',
          100: '#e0eefe',
          200: '#bfd7f9',
          300: '#8eb6ef',
          400: '#5b8fe2',
          500: '#3a6dc5',
          600: '#2d54a7',
          700: '#244188',
          800: '#1a365d', // Deep navy blue (primary brand color)
          900: '#152a4a',
        },
        secondary: {
          50: '#edfafa',
          100: '#d5f5f6',
          200: '#a6eaec',
          300: '#6dd7db',
          400: '#40bec4',
          500: '#2c9ea3',
          600: '#2c7a7b', // Teal accent for highlights
          700: '#285e61',
          800: '#234e52',
          900: '#1d3e41',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        }
      },
    },
  },
}
```

### 18.2. Color Usage Guidelines

#### 18.2.1. Primary Color (Deep Navy Blue #1a365d)

- Main brand color representing professionalism and trustworthiness
- Used for primary buttons, navigation elements, and key UI components
- Provides strong contrast against white backgrounds

#### 18.2.2. Secondary Color (Teal #2c7a7b)

- Accent color for highlighting important information and interactive elements
- Calls to action, success states, and progress indicators
- Complements the primary color while providing visual interest

#### 18.2.3. Neutral Grays

- Forms the foundation of the UI
- Used for text, backgrounds, borders, and subtle distinctions
- Provides hierarchy through different shades

#### 18.2.4. White Space

- Strategic use of white space for readability
- Helps establish visual hierarchy
- Creates a clean, uncluttered appearance

### 18.3. Visual Depth

- Subtle shadows for layering and component distinction
- Rounded corners (border-radius) for a modern, approachable feel
- Consistent spacing system based on 4px increments

### 18.4. Typography

```typescript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['1rem', { lineHeight: '1.5rem' }],
        lg: ['1.125rem', { lineHeight: '1.75rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },
    },
  },
}
```

### 18.5. Component Variants

```tsx
// Button component with variants
type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  // other props
}

const Button = ({ 
  variant = 'primary', 
  size = 'md',
  children,
  ...props
}: ButtonProps) => {
  const variantClasses = {
    primary: 'bg-primary-600 hover:bg-primary-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
    ghost: 'bg-transparent hover:bg-gray-100 text-gray-900',
  };
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };
  
  return (
    <button
      className={`rounded-md font-medium transition-colors ${variantClasses[variant]} ${sizeClasses[size]}`}
      {...props}
    >
      {children}
    </button>
  );
};
```

## 19. Implementation Plan

### 19.1. Phase 1: Core Infrastructure

1. Setup Next.js application with TypeScript
2. Implement authentication and user management
3. Create base layout and navigation components
4. Implement core UI component library
5. Setup API client and data fetching patterns

### 19.2. Phase 2: Essential Features

1. Supplier module - Document and Reconciliation
2. Labor module - Basic onboarding
3. Chef module - ABC analysis
4. Core settings pages

### 19.3. Phase 3: Advanced Features

1. Supplier module - Advanced inventory management
2. Chef module - Recipe and menu management
3. Enhanced dashboards and reporting
4. Data import/export features

### 19.4. Phase 4: Polish & Optimization

1. Performance optimization
2. Accessibility improvements
3. Mobile responsiveness
4. Advanced data visualization

## 20. Design Artifacts

### 20.1. Design Mockups

Design mockups will be created using Figma, covering the following key screens:

- Dashboard overview for each module
- Key workflow screens (reconciliation, inventory management, menu analysis)
- Mobile and desktop variants
- Light and dark theme versions

### 20.2. Component Storybook

A comprehensive storybook will document all UI components:

- Core components with all variants
- Interactive examples
- Accessibility guidelines
- Usage examples in different contexts

### 20.3. Design Tokens

Design tokens will be exported from Figma and converted to Tailwind configuration:

- Colors and color schemes
- Typography scales
- Spacing system
- Border radiuses
- Shadow definitions

## 21. Testing Strategy

### 21.1. Unit Testing

- Test individual components and hooks
- Use React Testing Library and Jest
- Focus on component behavior, not implementation

### 21.2. Integration Testing

- Test component interactions
- Test data flow between components
- Mock API responses for consistent tests

### 21.3. End-to-End Testing

- Test complete user flows
- Use Cypress or Playwright
- Test across different browsers and devices

## 22. Additional Required Backend Endpoints

Based on the frontend requirements, the following additional backend endpoints will be needed:

### 22.1. Authentication Endpoints

```
POST /v1/api/auth/login - User login
POST /v1/api/auth/logout - User logout
POST /v1/api/auth/refresh - Refresh authentication token
GET /v1/api/auth/me - Get current user information
```

### 22.2. Dashboard Endpoints

```
GET /v1/api/dashboard/summary - Get dashboard summary data
GET /v1/api/dashboard/recent-activity - Get recent activity
```

## 23. Conclusion

This technical specification provides comprehensive guidance for developing the frontend of the GET INN platform. By following this specification, the development team will create a robust, user-friendly interface that leverages the full capabilities of the backend services to deliver an exceptional experience for restaurant operators.

The modular architecture, responsive design, and performance optimizations ensure the platform will scale effectively as features are added and user base grows. The consistent design system and component library will maintain visual coherence across the application, while the accessibility considerations ensure the platform is usable by all.