# Installation Guide

This guide provides instructions for setting up the GET INN Frontend application for development and deployment.

## Prerequisites

Before installing the frontend application, ensure you have the following prerequisites:

- **Node.js**: v18.x or later
- **npm**: v9.x or later (or **bun** for faster installation)
- **Git**: For version control

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-restaurant-platform/frontend
```

### 2. Install Dependencies

Using npm:

```bash
npm install
```

Using bun (faster):

```bash
bun install
```

### 3. Configure Environment Variables

Create a `.env` file in the root of the frontend directory:

```
VITE_API_BASE_URL=http://localhost:8000/v1/api
VITE_WEBSOCKET_URL=ws://localhost:8000/ws
```

For different environments, you can create:
- `.env.development` - Development settings
- `.env.production` - Production settings

### 4. Start the Development Server

```bash
npm run dev
```

This will start the Vite development server, typically on port 5173. You can access the application at `http://localhost:5173`.

## Production Build

To create a production build:

```bash
npm run build
```

This will generate optimized files in the `dist/` directory, which can be deployed to any static hosting service.

## Docker Deployment

For containerized deployment, use the provided Dockerfile:

```bash
# Build the Docker image
docker build -t getinn-frontend -f Dockerfile .

# Run the container
docker run -p 80:80 getinn-frontend
```

## Troubleshooting Common Issues

### Module Resolution Issues

If you encounter module resolution issues:

1. Delete the `node_modules` directory
2. Clear the npm cache: `npm cache clean --force`
3. Reinstall dependencies: `npm install`

### API Connection Issues

If the application cannot connect to the backend API:

1. Check that the backend server is running
2. Verify that CORS is properly configured on the backend
3. Confirm that the `VITE_API_BASE_URL` environment variable is correctly set

## Next Steps

After installation:

- Review the [Development Environment](development-environment.md) guide
- Explore the project structure in the [Architecture](../architecture/project-structure.md) documentation
- Learn about available UI components in the [Component Library](../modules/ui-components/component-library.md) section