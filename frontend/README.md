# GET INN Frontend

Welcome to the GET INN Frontend project - the user interface for the AI-driven restaurant management platform.

## Project Overview

GET INN is an AI-Native Restaurant Operating System designed to optimize restaurant operations through artificial intelligence. The frontend application provides an intuitive interface for restaurant managers to monitor and manage their operations across multiple locations.

**Production URL**: https://getinn.ai

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Main Documentation Index](docs/README.md)
- [Installation Guide](docs/getting-started/installation.md)
- [Project Structure](docs/architecture/project-structure.md)

### Core Modules

- [Dashboard](docs/modules/modules/dashboard.md) - Main dashboard functionality
- [AI Supplier](docs/modules/modules/supplier.md) - Reconciliation and inventory management
- [AI Labor](docs/modules/modules/labor.md) - Staff onboarding and management
- [AI Chef](docs/modules/modules/chef.md) - Menu analysis and optimization

### Development Resources

- [Component Library](docs/modules/ui-components/component-library.md) - UI component documentation
- [Data Fetching](docs/modules/state-management/data-fetching.md) - TanStack Query implementation
- [Integration with Backend](docs/guides/integration-with-backend.md) - Working with backend services

## Development Setup

There are several ways of editing your application.

**Development**

You can make changes to this project by using your preferred IDE and working locally.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## Tech Stack

This project is built with:

- **Vite**: Fast build tool and development server
- **React 18**: UI library with hooks and concurrent rendering features
- **TypeScript**: Static typing for improved code quality and developer experience
- **React Router v6**: Declarative routing for React applications
- **TanStack Query**: Data fetching, caching, and state management
- **shadcn/ui**: Component library built on Radix UI primitives
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Flexible charting library for data visualization

## Architecture

The application follows a modern component-based architecture:

- **UI Layer**: React components for rendering the interface
- **State Management**: TanStack Query for server state, React Context for local state
- **API Layer**: Axios for HTTP requests, WebSockets for real-time updates
- **Routing Layer**: React Router for navigation
- **Theming Layer**: Tailwind CSS for styling with theme support

## Project Structure

The project follows a feature-based organization pattern. For detailed information about the project structure, refer to the [Project Structure](docs/architecture/project-structure.md) documentation.

## Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Build for development
npm run build:dev

# Run linting
npm run lint

# Preview production build
npm run preview
```

## Need Help?

- Refer to the [documentation](docs/README.md) for detailed guides and API references
- Check the [Integration Guide](docs/guides/integration-with-backend.md) for backend integration
- Reach out to the GET INN team for technical support
