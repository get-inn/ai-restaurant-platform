# GET INN Frontend Developer Guide

## Project Overview

GET INN is an AI-Native Restaurant Operating System designed to optimize restaurant operations through artificial intelligence. The frontend application provides an intuitive interface for restaurant managers to monitor and manage their operations across multiple locations.

## Tech Stack

### Core Technologies
- **Vite**: Fast build tool and dev server optimized for React
- **React 18**: UI library with hooks and concurrent rendering features
- **TypeScript**: Static typing for better code quality and developer experience
- **React Router v6**: Declarative routing for React applications
- **TanStack Query**: Data fetching, caching, and state management

### UI & Styling
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Component library built on Radix UI primitives
- **Radix UI**: Unstyled, accessible UI primitives
- **Lucide React**: Icon library
- **CSS Variables**: Used for theming (light/dark mode)

### Developer Tools
- **ESLint**: Static code analysis
- **TypeScript**: Type checking
- **Bun**: JavaScript runtime and package manager

## Project Structure

```
frontend_v2/
├── public/                   # Static assets
│   ├── favicon.ico
│   └── uploads/      # Uploaded images
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── layout/           # Layout-specific components
│   │   │   ├── AppSidebar.tsx
│   │   │   └── Header.tsx
│   │   └── ui/               # shadcn/ui components
│   ├── contexts/             # React context providers
│   │   ├── ThemeContext.tsx  # Theme management
│   │   └── TranslationContext.tsx # i18n support
│   ├── hooks/                # Custom React hooks
│   │   ├── use-mobile.tsx    # Mobile detection
│   │   └── use-toast.ts      # Toast notifications
│   ├── lib/                  # Utility functions
│   │   └── utils.ts          # Utility functions (cn)
│   ├── pages/                # Application pages by feature
│   │   ├── Dashboard.tsx     # Main dashboard
│   │   ├── NotFound.tsx      # 404 page
│   │   ├── chef/             # AI Chef features
│   │   ├── labor/            # AI Labor features
│   │   ├── settings/         # Application settings
│   │   └── supplier/         # AI Supplier features
│   ├── services/             # API communication
│   │   └── mockApi.ts        # Mock API service
│   ├── App.css               # Global application styles
│   ├── App.tsx               # Main application component
│   ├── index.css             # Global CSS and Tailwind imports
│   ├── main.tsx              # Application entry point
│   └── vite-env.d.ts         # Vite type definitions
├── .eslintrc.js              # ESLint configuration
├── bun.lockb                 # Bun lockfile
├── components.json           # shadcn/ui components config
├── package.json              # Project dependencies
├── tailwind.config.ts        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
└── vite.config.ts            # Vite configuration
```

## Main Features

### Dashboard
- Restaurant chain overview with real-time status monitoring
- Key performance indicators and metrics
- Quick access to main modules

### AI Supplier Module
- **Reconciliation**: Automated invoice reconciliation with suppliers
  - Document upload and processing
  - Multi-step workflow with status tracking
  - Discrepancy identification and resolution
- **Inventory**: Real-time inventory management
  - Stock level monitoring
  - Low inventory alerts
  - Usage analytics and reporting

### AI Labor Module
- **Onboarding**: Staff onboarding and training tracking
  - Progress tracking for new employees
  - Training schedule management
  - Certification tracking

### AI Chef Module
- **Menu**: Menu analysis and optimization
  - ABC analysis for menu items
  - Popularity and profitability tracking
  - Data-driven menu recommendations

### Settings
- User preferences and profile management
- Company-wide configuration
- Subscription management

## Theme System

### Theme Implementation
- Theme context (`ThemeContext.tsx`) manages light/dark mode
- CSS variables in `index.css` define color schemes
- Dynamic class application to `html` element
- Local storage persistence for user preference

### Color System
- Primary brand color: Purple (#6B64B4)
- Restaurant brand accent: Dark red (#b91c1c)
- Semantic colors for status indicators:
  - Healthy (green)
  - Warning (orange)
  - Critical (red)
- Tailwind extends configuration in `tailwind.config.ts`

## Data Flow

### State Management
- React Query for server state management
- React Context for global UI state (theme, translations)
- Local component state for UI interactions

### API Communication
- `mockApi.ts` provides mock data for development
- Simulated API requests with timeouts
- Structured data interfaces for type safety

### Data Flow Example
1. Component mounts and triggers data fetch with React Query
2. Loading state shown while request is pending
3. Data received and rendered in component
4. Error handling for failed requests

## Component Usage

### Layout Components
- `AppSidebar.tsx`: Main navigation sidebar
  - Collapsible menu groups
  - Mobile responsive design
  - Active state tracking
  
- `Header.tsx`: Application header
  - User profile and settings access
  - Theme toggle
  - Notification center

### UI Components
- Built on shadcn/ui library
- Extended for application-specific needs
- Consistent styling and behavior
- Examples:
  - `Button`: Primary interaction element
  - `Card`: Content containers
  - `StatusBadge`: Visual indicator for health status

## Development Workflow

### Getting Started
1. Install dependencies: `npm install` or `bun install`
2. Start development server: `npm run dev` or `bun run dev`
3. Build for production: `npm run build` or `bun run build`

### Creating New Pages
1. Create new `.tsx` file in appropriate directory under `/pages`
2. Add route in `App.tsx`
3. Update sidebar navigation if needed

### Adding New Features
1. Design component structure and data flow
2. Implement UI components
3. Connect to data source (mock API or real backend)
4. Add to relevant navigation
5. Test across viewport sizes

### Best Practices
- Follow existing component patterns and naming conventions
- Use TypeScript interfaces for props and data structures
- Implement responsive design for all components
- Maintain accessibility standards
- Leverage Tailwind utility classes for styling
- Use React Query for data fetching and caching