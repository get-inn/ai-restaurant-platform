# GET INN Restaurant Platform

GET INN is the world's first platform that creates self-operating restaurants using AI agents. This platform provides an intuitive and powerful interface for restaurant owners and managers to automate critical operations, from procurement and kitchen management to staff management and menu optimization.

## Overview

The GET INN Restaurant Platform consists of three AI-powered modules:

1. **AI Supplier:** Management interface for procurement, reconciliation, and inventory tracking.
2. **AI Labor:** Interface for staff management, focused on onboarding processes.
3. **AI Chef:** Tools for menu analysis, recipe management, and insights.

The platform integrates with restaurant back-office systems and uses Azure OpenAI services for intelligent document processing and analysis.

## Repository Structure

This repository contains both the backend and frontend components of the GET INN Restaurant Platform:

- **/backend:** FastAPI-based backend service with AI integration
- **/frontend:** React-based frontend application with Vite and shadcn/ui

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Backend Setup

To set up the backend development environment:

```bash
# Start services with migrations and database initialization
./backend/start-dev.sh --build --migrate --init-db
```

When the server is running:
- API documentation will be available at http://localhost:8000/docs
- Database admin interface (Adminer) will be available at http://localhost:8080
  - System: PostgreSQL
  - Server: db
  - Username: postgres
  - Password: postgres
  - Database: restaurant

For more information on the backend, see the [Backend README](backend/README.md).

### Frontend Setup

To set up the frontend development environment:

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

When the development server is running:
- Frontend application will be available at http://localhost:5173

For more information on the frontend, see the [Frontend README](frontend/README.md).

## Architecture

The GET INN Restaurant Platform follows a modern, layered architecture:

- **Frontend Layer:** React application with Vite and shadcn/ui components
- **API Layer:** FastAPI for handling HTTP requests and WebSockets
- **Service Layer:** Business logic implementation
- **Data Access Layer:** Database operations with PostgreSQL via SQLAlchemy
- **Background Worker Layer:** Celery for asynchronous processing

For detailed architectural information, see the [Architecture Document](backend/docs/architecture.md).

## Project Status

The GET INN platform includes both backend and frontend implementations:

### Backend
- Complete database models and relationships
- RESTful API endpoints with documentation
- Authentication and authorization system
- WebSocket integration for real-time updates
- Bot management system
- Integration with AI services

### Frontend
- React-based UI with shadcn/ui component library
- Responsive dashboard interface
- Module-based architecture (Dashboard, AI Supplier, AI Labor, AI Chef)
- TanStack Query for data fetching and state management
- Theme system with light/dark mode support

## Development

For detailed development instructions, refer to the respective documentation:

- [Backend Development Guide](backend/docs/getting-started/development-environment.md)
- [Frontend Development Guide](frontend/docs/getting-started/development-environment.md)

## API and UI Documentation

When running the application:

### Backend API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Frontend UI
- **Development UI**: http://localhost:5173

## Documentation

### Backend Documentation

Detailed backend documentation is available in the [backend/docs](backend/docs/) directory:

- [Main Documentation Index](backend/docs/README.md) - Overview and navigation
- [Architecture](backend/docs/architecture/project-structure.md) - System structure and patterns
- [API Structure](backend/docs/architecture/api-structure.md) - API design and endpoints
- [Bot Management](backend/docs/modules/bot-management/overview.md) - Bot and messaging integration
- [Database Migrations](backend/docs/guides/database-migrations.md) - Working with database changes

### Frontend Documentation

Frontend documentation is available in the [frontend/docs](frontend/docs/) directory:

- [Main Documentation Index](frontend/docs/README.md) - Overview and navigation
- [Project Structure](frontend/docs/architecture/project-structure.md) - Frontend code organization
- [Component Library](frontend/docs/modules/ui-components/component-library.md) - UI component documentation
- [Core Modules](frontend/docs/modules/modules/dashboard.md) - Main application modules
- [Integration with Backend](frontend/docs/guides/integration-with-backend.md) - API integration

## License

MIT License

Copyright (c) 2023-2025 GET INN Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contact

- **Email**: anton@getinn.co
- **Website**: [www.getinn.co](https://www.getinn.co)