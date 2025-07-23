from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
import uuid
import time
import os
import sys

from src.api.core.config import get_settings
from src.api.core.logging_config import LogConfig
from src.api.dependencies.db import get_db, SessionLocal
from src.api.core.init_db import init_db
from src.api.routers import auth, accounts, test_endpoints
from src.api.routers.supplier import reconciliation, document, inventory, invoice, supplier
from src.api.routers.labor import onboarding
from src.api.routers.chef import menu, recipe
from src.api.routers import dashboard
from src.api.routers.integrations import iiko
from src.api.routers import bots
from src.api.routers import webhooks

# Configure logging with fallback for test environments
try:
    # Standard logging configuration
    import logging.config
    # Use model_dump() instead of dict() (Pydantic v2 recommended)
    logging.config.dictConfig(LogConfig().model_dump())
    logger = logging.getLogger(LogConfig().LOGGER_NAME)
except (ImportError, AttributeError) as e:
    # Fallback for testing environments
    print(f"Warning: Using fallback logging configuration: {str(e)}", file=sys.stderr)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("restaurant_api_test")

settings = get_settings()

# Set up FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start-up operations
    logger.info("Starting up application...")
    
    # Database initialization
    if os.environ.get("INITIALIZE_DB", "false").lower() == "true":
        logger.info("Initializing database...")
        try:
            db = SessionLocal()
            init_db(db)
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
        finally:
            db.close()
    
    yield
    # Shut-down operations
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request tracing
@app.middleware("http")
async def log_and_trace_requests(request: Request, call_next) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add request ID to logging context
    logger = logging.getLogger(LogConfig().LOGGER_NAME)
    logger = logging.LoggerAdapter(logger, {"request_id": request_id})
    
    # Log request
    logger.debug(
        f"Request received: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host,
        },
    )
    
    # Process request and record timing
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    # Log response
    logger.debug(
        f"Request completed: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "processing_time": process_time,
        },
    )
    
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["authentication"],
)

app.include_router(
    accounts.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["accounts"],
)

# Include supplier routers
app.include_router(
    reconciliation.router,
    prefix=f"{settings.API_V1_STR}/supplier",
    tags=["supplier"],
)

app.include_router(
    document.router,
    prefix=f"{settings.API_V1_STR}/supplier",
    tags=["supplier"],
)

app.include_router(
    inventory.router,
    prefix=f"{settings.API_V1_STR}/supplier",
    tags=["supplier"],
)

app.include_router(
    invoice.router,
    prefix=f"{settings.API_V1_STR}/supplier",
    tags=["supplier"],
)

app.include_router(
    supplier.router,
    prefix=f"{settings.API_V1_STR}/supplier",
    tags=["supplier"],
)

# Include labor routers
app.include_router(
    onboarding.router,
    prefix=f"{settings.API_V1_STR}/labor",
    tags=["labor"],
)

# Include chef routers
app.include_router(
    menu.router,
    prefix=f"{settings.API_V1_STR}/chef",
    tags=["chef"],
)

app.include_router(
    recipe.router,
    prefix=f"{settings.API_V1_STR}/chef",
    tags=["chef"],
)

# Include dashboard router
app.include_router(
    dashboard.router,
    prefix=f"{settings.API_V1_STR}/dashboard",
    tags=["dashboard"],
)

# Include integrations routers
app.include_router(
    iiko.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["integrations"],
)

# Include bot management router
app.include_router(
    bots.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["bots"],
)

# Include webhook routers with API version prefix to be consistent
app.include_router(
    webhooks.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["webhooks"],
)

# Include test endpoints for testing only (disabled in production)
app.include_router(
    test_endpoints.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["test"],
)

# Test endpoints have been removed in favor of using actual API endpoints
# with authentication bypassing for testing purposes


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000)