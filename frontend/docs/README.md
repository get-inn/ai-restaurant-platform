# GET INN Frontend Documentation

Welcome to the GET INN Frontend documentation. This repository contains comprehensive documentation for the frontend application that powers the AI-driven restaurant management platform.

## Documentation Structure

### Getting Started
- [Installation Guide](getting-started/installation.md) - Setup and installation instructions
- [Development Environment](getting-started/development-environment.md) - Local development configuration
- [Running Tests](getting-started/testing.md) - Testing strategy and commands

### Architecture
- [Project Structure](architecture/project-structure.md) - Overview of the codebase organization
- [Tech Stack](architecture/tech-stack.md) - Frontend technologies and libraries
- [Theming System](architecture/theming.md) - Theme implementation and customization

### Modules

#### UI Components
- [Component Library](modules/ui-components/component-library.md) - shadcn/ui component system
- [Layout Components](modules/ui-components/layout.md) - Header, sidebar, and layout structure
- [Custom Components](modules/ui-components/custom.md) - Custom application-specific components

#### Core Modules
- [AI Supplier](modules/modules/supplier.md) - Reconciliation and inventory management
- [AI Labor](modules/modules/labor.md) - Staff onboarding and management
- [AI Chef](modules/modules/chef.md) - Menu analysis and optimization
- [Dashboard](modules/modules/dashboard.md) - Main dashboard functionality

#### State Management
- [Data Fetching](modules/state-management/data-fetching.md) - React Query implementation
- [Context Providers](modules/state-management/context.md) - React context usage
- [Forms Management](modules/state-management/forms.md) - React Hook Form patterns

### Development Guides
- [Creating New Pages](guides/creating-new-pages.md) - How to add new application pages
- [Adding API Endpoints](guides/adding-api-endpoints.md) - Connecting to backend services
- [Integration with Backend](guides/integration-with-backend.md) - Working with backend services
- [Responsive Design](guides/responsive-design.md) - Mobile-first development approach
- [Accessibility](guides/accessibility.md) - Ensuring accessible interface

## Tech Stack Overview

The GET INN Frontend is built using the following core technologies:

- **Vite**: Fast build tool and dev server optimized for React
- **React 18**: UI library with hooks and concurrent rendering
- **TypeScript**: Type-safe JavaScript
- **React Router v6**: Client-side routing
- **TanStack Query**: Data fetching and state management
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Accessible component library built on Radix UI
- **Zod**: Schema validation
- **React Hook Form**: Form state management

## Getting Started

To start development:

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Additional Resources

- [Archive Documentation](archive/) - Previous documentation versions
- [Backend Documentation](../../backend/docs/) - Documentation for the backend services

## Backend Integration

The frontend application communicates with the backend services through RESTful APIs and WebSockets. For detailed information about the backend services, refer to the [Backend Documentation](../../backend/docs/).

Key backend integration points include:

- Authentication and authorization
- API endpoints for all core modules
- WebSocket connections for real-time updates
- Document processing and file uploads

---

**Note:** This documentation is under active development. Some sections may be incomplete or in progress.