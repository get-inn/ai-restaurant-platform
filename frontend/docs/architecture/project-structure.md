# Project Structure

This document outlines the organization of the GET INN Frontend codebase, explaining key directories and files.

## Directory Structure

```
frontend/
├── public/                   # Static assets
│   ├── favicon.ico
│   └── uploads/              # Uploaded images
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
│   │   └── api.ts            # API service
│   ├── App.css               # Global application styles
│   ├── App.tsx               # Main application component
│   ├── index.css             # Global CSS and Tailwind imports
│   ├── main.tsx              # Application entry point
│   └── vite-env.d.ts         # Vite type definitions
├── .eslintrc.js              # ESLint configuration
├── package.json              # Project dependencies
├── tailwind.config.ts        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
└── vite.config.ts            # Vite configuration
```

## Key Directories and Files

### `src/components/`

Contains reusable UI components organized by purpose:

- **`layout/`**: Components for application structure
  - `AppSidebar.tsx`: Main navigation sidebar
  - `Header.tsx`: Application header with user menu and controls
  
- **`ui/`**: shadcn/ui components and extensions
  - Generated and customized UI primitives from the shadcn/ui library
  - Custom extensions of these components for application-specific needs

### `src/contexts/`

Contains React Context providers:

- **`ThemeContext.tsx`**: Manages theme switching (light/dark mode)
- **`TranslationContext.tsx`**: Provides internationalization capabilities

### `src/hooks/`

Custom React hooks that encapsulate reusable logic:

- **`use-mobile.tsx`**: Detects mobile viewport
- **`use-toast.ts`**: Provides toast notification functionality
- **`use-api.ts`**: Custom hook for API calls

### `src/lib/`

Utility functions and helpers:

- **`utils.ts`**: General utility functions including the `cn` utility for class name merging

### `src/pages/`

Application pages organized by feature module:

- **`Dashboard.tsx`**: Main dashboard view
- **`chef/`**: AI Chef module pages
- **`labor/`**: AI Labor module pages
- **`settings/`**: Application settings pages
- **`supplier/`**: AI Supplier module pages

### `src/services/`

API communication and external service integration:

- **`api.ts`**: Core API service for communication with backend
- Service modules for specific API endpoints

## File Naming Conventions

- React components use **PascalCase**: `Header.tsx`, `Dashboard.tsx`
- Hooks use **camelCase** with `use-` prefix: `use-mobile.tsx`
- Utility files use **camelCase**: `utils.ts`
- Context providers use **PascalCase** with `Context` suffix: `ThemeContext.tsx`

## Code Organization Principles

1. **Feature-based organization**: Code is primarily organized by feature/module
2. **Component reusability**: Components are designed to be reusable across the application
3. **Separation of concerns**: UI components, business logic, and API communication are separated
4. **Consistent patterns**: Similar features follow consistent patterns for better maintainability

## Module Dependencies

The codebase follows a clear dependency hierarchy:

1. **UI Components**: Have minimal dependencies, primarily on styling utilities
2. **Pages**: Depend on components, contexts, and services
3. **Services**: Depend on utility functions, but not on components or pages
4. **Contexts**: Provide shared state accessible to components and pages
5. **Hooks**: Encapsulate reusable logic for components and pages

## Build Configuration

- **`vite.config.ts`**: Configures the Vite build tool with plugins and settings
- **`tsconfig.json`**: TypeScript configuration including path aliases
- **`tailwind.config.ts`**: Tailwind CSS configuration with theme settings
- **`eslintrc.js`**: ESLint configuration for code quality