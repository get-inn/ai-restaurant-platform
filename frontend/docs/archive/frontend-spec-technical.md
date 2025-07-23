# Technical Specification: GET INN Frontend

## 1. Introduction

### 1.1. Purpose

This technical specification outlines the requirements and architecture for developing the frontend for GET INN, the world's first platform that creates self-operating restaurants. The frontend will provide an intuitive and responsive user interface supporting the three AI-driven modules: AI Supplier (procurement and inventory), AI Labor (staff management), and AI Chef (menu optimization).

### 1.2. System Overview

GET INN empowers restaurant founders to run scalable, self-operating restaurants using AI agents. The frontend will provide a modern, responsive interface that connects to the backend API to deliver critical operations like procurement, kitchen management, staff management, and menu optimization. The system is designed to support multiple restaurant chains, individual restaurants, and their respective stores.

### 1.3. Development Goals

- Build a responsive, intuitive user interface using modern frontend technologies
- Implement secure authentication and authorization flows
- Develop core UI components for AI Supplier, AI Labor, and AI Chef modules
- Provide real-time updates using WebSockets for long-running processes
- Create a comprehensive document management interface for financial reconciliation
- Implement interactive dashboards for inventory, menu, and recipe management
- Support both light and dark themes for user preference

## 2. Architecture Overview

### 2.1. High-Level Architecture

The frontend follows a modern component-based architecture:

1. **UI Layer**: React components for rendering the interface
2. **State Management**: Redux for global state, React Context for component-specific state
3. **API Layer**: Axios for HTTP requests, Socket.io for WebSockets
4. **Routing Layer**: React Router for navigation
5. **Theming Layer**: Styled Components for styling with theme support

### 2.2. Technology Stack

- **Framework**: React.js with TypeScript
- **State Management**: Redux + Redux Toolkit
- **UI Library**: Material-UI (MUI) or Tailwind CSS
- **API Communication**: Axios
- **WebSockets**: Socket.io-client
- **Forms**: React Hook Form + Yup validation
- **Charts**: Chart.js or D3.js
- **Authentication**: JWT tokens with secure storage
- **Build Tools**: Vite or Create React App

### 2.3. Deployment Architecture

- Docker-based containerization
- Static file hosting on CDN
- Environment-based configuration
- CI/CD pipeline for automated deployments

## 3. User Interface Design

### 3.1. Branding and Theme

- **Primary Color**: #6B64B4
- **Spacing**: Strategic use of white space for readability
- **Depth**: Subtle shadows and rounded corners

### 3.2. Theme Support

- **Light Theme**: Default theme with light background and dark text
- **Dark Theme**: Alternative theme with dark background and light text for low-light environments
- **Theme Switcher**: Allow users to toggle between themes

### 3.3. Layout Structure

#### 3.3.1. Header Component

- GET INN App logo (center)
- Restaurant chain logo (left)
- Theme switcher (right)
- User profile menu (right)

#### 3.3.2. Sidebar Navigation Component

The sidebar provides access to the core modules with expandable sub-menus:

- Dashboard
- AI Supplier
  - Reconciliation
  - Inventory
- AI Labor
  - Onboarding
- AI Chef
  - Menu
- Settings
  - User Settings
  - Company Settings
  - Subscription

#### 3.3.3. Main Content Area

- Content header with breadcrumbs
- Module-specific content
- Responsive design for different screen sizes

#### 3.3.4. Common UI Elements

- Cards for content grouping
- Data tables with sorting and filtering
- Status indicators (green, orange, red)
- Modal dialogs for forms
- Toast notifications for feedback

## 4. Core Modules UI

### 4.1. AI Supplier Module

#### 4.1.1. Reconciliation

The Reconciliation interface includes three tabs:

1. **Overview Tab**:
   - List of restaurants with reconciliation status indicators (green/orange/red)
   - Summary statistics for reconciliation status across the chain

2. **Documents Tab**:
   - Document upload interface with drag-and-drop support
   - Document list with status and progress indicators
   - Search and filter functionality   
   - 8-step reconciliation process visualization
   - Action buttons for processing documents

3. **History Tab**:
   - Table of past reconciliations with details
   - Search and filter functionality
   - Export options for reconciliation reports

#### 4.1.2. Inventory

The Inventory interface includes three tabs:

1. **Overview Tab**:
   - High-level inventory status view for all restaurants (up to 50 restaurants)
   - Status indicators (green/orange/red) showing inventory health
   - Summary charts for inventory levels and alerts

2. **Ingredients Tab**:
   - Ingredient-level analysis table with:
     - Ingredient name
     - Price change percentage
     - Dish usage count
     - Percentage of total sales
   - Sorting and filtering options
   - Detailed view for individual ingredients

3. **Settings Tab**:
   - Interface to define percentage thresholds for status indicators
   - Configure recommended inventory levels for each ingredient
   - Set up alerts and notifications

### 4.2. AI Labor Module

#### 4.2.1. Onboarding

The Onboarding interface includes two tabs:

1. **Overview Tab**:
   - Summary dashboard showing number of staff onboarding in each location
   - Status breakdown by location and position
   - Charts visualizing onboarding progress across the chain

2. **Details Tab**:
   - Staff list with:
     - Name
     - Location
     - Onboarding starting date
     - Planned final exam date
     - Current status
   - Filtering by location, status, and date range
   - Detailed view for individual staff members

### 4.3. AI Chef Module

#### 4.3.1. Menu

The Menu interface includes the ABC-Menu analysis tab:

- Menu performance metrics visualization
- ABC categorization of menu items based on profitability and sales
- Interactive charts showing item performance
- Filtering by date range, category, and restaurant
- Detailed analysis view for individual menu items

## 5. Feature Details

### 5.1. User Settings

The User Settings interface allows users to personalize their experience:

- Theme Switcher toggle between Light and Dark themes
- Account Details management (name, email, password)
- Notification Preferences customization
- Language Preferences selection
- Security Settings including two-factor authentication

### 5.2. Company Settings

The Company Settings interface allows configuration of restaurant-specific preferences:

- Business Information (company name, contact information, hours)
- Payment Methods configuration
- Integrations with third-party systems
- Branding & Customization options
- Employee Management interface


## 6. API Integration

### 6.1. Authentication Endpoints

```
POST /v1/api/auth/login - User login
POST /v1/api/auth/logout - User logout
POST /v1/api/auth/refresh - Refresh authentication token
GET /v1/api/auth/me - Get current user information
```

### 6.2. AI Supplier Module Endpoints

```
# Document Management
POST /v1/api/supplier/documents - Upload new document
GET /v1/api/supplier/documents - Get list of documents
GET /v1/api/supplier/documents/{id} - Get document details

# Reconciliation
POST /v1/api/supplier/reconciliation - Start reconciliation process
GET /v1/api/supplier/reconciliation/chain-status - Get chain-wide status
GET /v1/api/supplier/reconciliation/{id}/status - Get specific status
GET /v1/api/supplier/reconciliation/{id}/matched - Get matched items
GET /v1/api/supplier/reconciliation/{id}/missing-restaurant - Get missing restaurant items
GET /v1/api/supplier/reconciliation/{id}/missing-supplier - Get missing supplier items

# Inventory
GET /v1/api/supplier/inventory/items - List inventory items
GET /v1/api/supplier/inventory/price-changes - Get price changes
GET /v1/api/supplier/inventory/price-history/{id} - Get price history
```

### 6.3. AI Labor Module Endpoints

```
GET /v1/api/labor/onboarding/chain-status - List onboarding status across restaurants
GET /v1/api/labor/onboarding/restaurant/{restaurant_id} - Staff by restaurant
GET /v1/api/labor/onboarding/{id} - Get specific onboarding details
```

### 6.4. AI Chef Module Endpoints

```
GET /v1/api/chef/menu/abc-analysis - Get ABC analysis
GET /v1/api/chef/menu/item/{id}/performance - Get item performance
GET /v1/api/chef/menu/insights - Get AI-generated insights
GET /v1/api/chef/menu/performance/chain-status - Get menu performance status
GET /v1/api/chef/recipes - List recipes
GET /v1/api/chef/recipes/{id} - Get recipe details
GET /v1/api/chef/recipes/adherence/chain-status - Get recipe adherence status
```

### 6.5. WebSocket Endpoints

```
WS /ws/supplier/reconciliation/{reconciliation_id} - Real-time reconciliation updates
WS /ws/chain/updates - Real-time aggregate chain-level updates
```

## 7. Data Flow Examples

### 7.1. Reconciliation Flow

1. **User Action**: User uploads a supplier document for reconciliation
   - Frontend sends `POST /v1/api/supplier/documents` with file data
   - Backend returns document ID

2. **User Action**: User starts reconciliation process
   - Frontend sends `POST /v1/api/supplier/reconciliation` with document ID
   - Backend returns reconciliation ID and creates background task

3. **Frontend**: Establishes WebSocket connection for real-time updates
   - Connects to `WS /ws/supplier/reconciliation/{reconciliation_id}`
   - Shows progress indicator in the UI

4. **Backend**: Processing occurs with progress updates via WebSocket
   - Frontend updates the UI to reflect current step and progress

5. **Frontend**: Receives final result notification via WebSocket
   - Fetches detailed results using REST endpoints
   - Displays matched/missing items in tabular format

6. **User Action**: User can export reconciliation results
   - Frontend sends `GET /v1/api/supplier/reconciliation/{id}/export`
   - Downloads and offers to save the Excel report

### 7.2. Menu ABC Analysis Flow

1. **User Action**: User requests menu ABC analysis
   - Frontend sends `GET /v1/api/chef/menu/abc-analysis` with parameters
   - Backend returns categorized menu items

2. **Frontend**: Processes and visualizes the data
   - Renders color-coded sections for A, B, C categories
   - Shows performance metrics in charts and tables
   - Provides interactive filtering options

3. **User Action**: User drills down into item details
   - Frontend sends `GET /v1/api/chef/menu/item/{id}/performance`
   - Displays detailed performance metrics and trends

## 8. Component Structure

```
/src
├── assets/               # Static assets
│   ├── images/           # Image files
│   ├── icons/            # Icon SVGs
│   └── fonts/            # Font files
├── components/           # Reusable UI components
│   ├── common/           # Shared components
│   │   ├── Header/       # App header component
│   │   ├── Sidebar/      # Navigation sidebar
│   │   ├── Table/        # Reusable data table
│   │   ├── Card/         # Content card component
│   │   ├── Modal/        # Modal dialog component
│   │   └── StatusBadge/  # Status indicator component
│   ├── supplier/         # AI Supplier module components
│   │   ├── ReconciliationOverview/
│   │   ├── DocumentUpload/
│   │   ├── InventoryStatus/
│   │   └── PriceHistory/
│   ├── labor/            # AI Labor module components
│   │   ├── OnboardingDashboard/
│   │   └── StaffList/
│   └── chef/             # AI Chef module components
│       ├── MenuAnalysis/
│       └── ItemPerformance/
├── hooks/                # Custom React hooks
│   ├── useAuth.ts        # Authentication hook
│   ├── useWebSocket.ts   # WebSocket connection hook
│   └── useFetch.ts       # Data fetching hook
├── pages/                # Application pages
│   ├── Dashboard/        # Main dashboard
│   ├── supplier/         # AI Supplier pages
│   ├── labor/            # AI Labor pages
│   ├── chef/             # AI Chef pages
│   └── settings/         # Settings pages
├── services/             # API service layer
│   ├── api.ts            # API configuration
│   ├── auth.service.ts   # Authentication service
│   ├── supplier.service.ts
│   ├── labor.service.ts
│   └── chef.service.ts
├── store/                # Redux store configuration
│   ├── index.ts
│   ├── slices/           # Redux slices
│   │   ├── authSlice.ts
│   │   ├── supplierSlice.ts
│   │   ├── laborSlice.ts
│   │   └── chefSlice.ts
│   └── selectors/        # Redux selectors
├── types/                # TypeScript definitions
│   ├── api.types.ts      # API response types
│   └── domain.types.ts   # Domain model types
├── utils/                # Utility functions
│   ├── formatters.ts     # Data formatting utilities
│   ├── validators.ts     # Validation functions
│   └── theme.ts          # Theme configuration
└── App.tsx               # Main application component
```

## 9. Mockup Data Structure

For the initial development phase, mock API endpoints should return realistic test data. Below are examples of the data structures for key endpoints:

### 9.1. Reconciliation Chain Status

```typescript
interface ReconciliationStatusItem {
  restaurant_id: string;
  restaurant_name: string;
  status: 'green' | 'orange' | 'red';
  last_reconciliation_date: string;
  pending_documents: number;
  processed_documents: number;
}

interface ChainReconciliationStatus {
  total_restaurants: number;
  green_count: number;
  orange_count: number;
  red_count: number;
  restaurants: ReconciliationStatusItem[];
}
```

### 9.2. Inventory Item

```typescript
interface InventoryItem {
  id: string;
  name: string;
  description?: string;
  category: string;
  unit: {
    id: string;
    name: string;
    symbol: string;
  };
  current_price: number;
  previous_price: number;
  price_change_percentage: number;
  dish_usage_count: number;
  sales_percentage: number;
  stock_level: number;
  recommended_level: number;
  status: 'green' | 'orange' | 'red';
}

interface InventoryResponse {
  total_items: number;
  items: InventoryItem[];
}
```

### 9.3. Staff Onboarding

```typescript
interface StaffOnboarding {
  id: string;
  name: string;
  email: string;
  position: string;
  location: string;
  start_date: string;
  exam_date: string;
  progress_percentage: number;
  status: 'in_progress' | 'completed' | 'terminated';
  steps: {
    id: string;
    name: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
  }[];
}

interface OnboardingResponse {
  total_staff: number;
  by_location: {
    location_id: string;
    location_name: string;
    staff_count: number;
  }[];
  staff: StaffOnboarding[];
}
```

### 9.4. Menu ABC Analysis

```typescript
interface MenuItemAnalysis {
  id: string;
  name: string;
  category: string;
  abc_category: 'A' | 'B' | 'C' | 'D';
  profit_margin: number;
  sales_volume: number;
  revenue: number;
  cost: number;
  trend: 'up' | 'down' | 'stable';
}

interface MenuAnalysisResponse {
  analysis_date: string;
  period_start: string;
  period_end: string;
  category_distribution: {
    a_count: number;
    b_count: number;
    c_count: number;
    d_count: number;
  };
  items: MenuItemAnalysis[];
}
```

## 10. Development Guidelines

### 10.1. Component Design Standards

1. **Component Structure**:
   - Use functional components with hooks
   - Implement proper TypeScript typing
   - Follow the container/presentational pattern where appropriate

2. **Styling Approach**:
   - Use styled-components with theme support
   - Create consistent spacing and sizing using theme variables
   - Implement responsive design using media queries

3. **Error Handling**:
   - Implement proper error boundaries
   - Display user-friendly error messages
   - Log errors to monitoring service

### 10.2. State Management

1. **Global State**:
   - Use Redux for application-wide state
   - Implement Redux Toolkit for simplified Redux usage
   - Create separate slices for different modules

2. **Local State**:
   - Use React useState for component-specific state
   - Use React Context for sharing state between related components

3. **Side Effects**:
   - Use React useEffect for side effects
   - Implement custom hooks for complex logic

### 10.3. API Communication

1. **Request Structure**:
   - Use Axios for HTTP requests
   - Implement request interceptors for authentication
   - Implement response interceptors for error handling

2. **WebSocket Management**:
   - Create WebSocket service for real-time updates
   - Implement automatic reconnection
   - Handle connection state in the UI

### 10.4. Authentication & Security

1. **Token Management**:
   - Store JWT tokens securely
   - Implement token refresh mechanism
   - Clear tokens on logout

2. **Route Protection**:
   - Implement protected routes with role-based access
   - Redirect unauthenticated users to login

3. **Input Validation**:
   - Validate form inputs before submission
   - Sanitize user inputs to prevent XSS

## 11. Performance Optimizations

1. **Code Splitting**:
   - Implement route-based code splitting
   - Lazy load components where appropriate

2. **Bundle Optimization**:
   - Use tree shaking to eliminate unused code
   - Optimize asset sizes for production

3. **Rendering Optimization**:
   - Use React.memo for preventing unnecessary re-renders
   - Implement virtualized lists for long data sets

4. **API Optimization**:
   - Implement data caching
   - Use pagination for large datasets
   - Implement debouncing for search inputs

## 12. Testing Strategy

1. **Unit Testing**:
   - Test individual components in isolation
   - Mock external dependencies

2. **Integration Testing**:
   - Test component interactions
   - Test API integration with mock server

3. **End-to-End Testing**:
   - Test critical user flows
   - Test across different browsers and devices

## 13. Deployment and CI/CD

1. **Development Environment**:
   - Local development server
   - Development API integration

2. **Staging Environment**:
   - Production-like environment
   - Testing with staging API

3. **Production Environment**:
   - Optimized build
   - CDN distribution
   - Production API integration

4. **CI/CD Pipeline**:
   - Automated testing
   - Automated builds
   - Automated deployments

## 14. Future Enhancements

- Mobile responsive design optimization
- Native mobile application development
- Advanced analytics dashboard
- AI-powered recommendation widgets
- Offline mode support
- Multi-language support
- Accessibility improvements