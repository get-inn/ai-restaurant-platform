"""
Base test classes for API tests.
"""
import pytest
import os
import uuid
from typing import Dict, Any, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.api.main import app
from src.api.dependencies.db import get_db
from src.api.core.config import get_settings
from src.api.core.init_db import init_db
from src.api.models import Base

settings = get_settings()

# Use a test database URL, defaulting to in-memory SQLite if not specified
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "sqlite:///./test.db"
)

# Use PostgreSQL Docker container with restaurant database for tests
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/restaurant"
)

# Set JWT secret key for tests
os.environ["JWT_SECRET_KEY"] = "testsecretkey"
os.environ["JWT_ALGORITHM"] = "HS256"

# Create sync engine for the tests
engine = create_engine(TEST_DATABASE_URL, echo=True)

# Create session factory
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


def override_get_db() -> Generator:
    """
    Returns a test database session.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def db_session() -> Session:
    """
    Creates a database session for tests using the existing restaurant database.
    Uses alembic to manage the database schema.
    """
    # Get a database session
    db = TestingSessionLocal()
    
    try:
        # Set up schema if needed - in a real environment this would run migrations
        # but we're using an existing database, so we skip this step
        
        # Import here to avoid circular import
        from src.api.services.auth_service import initialize_users
        
        # Initialize default users required for testing
        try:
            # Only initialize users if they don't exist yet
            # This is safer for working with a shared database
            # For real tests, we should use a separate test schema or database
            initialize_users(db)
            db.commit()
        except Exception as e:
            print(f"Error initializing users: {e}")
            db.rollback()
        
        yield db
    finally:
        # Close the session but don't drop tables since we're using a shared DB
        db.close()


@pytest.fixture
def test_client() -> TestClient:
    """
    Create a test client using the app.
    """
    # Replace the dependency with our test DB session
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as client:
        # Test data initialization happens through auth_service.py when tokens are requested
        yield client
    
    # Clean up the dependency override after test
    app.dependency_overrides = {}


@pytest.fixture
def admin_client(test_client: TestClient, db_session) -> TestClient:
    """
    Test client with valid authentication token for admin user.
    """
    # Get test token from our test/token endpoint
    response = test_client.post("/v1/api/test/token", params={"user_id": "00000000-0000-0000-0000-000000000001"})
    assert response.status_code == 200, "Failed to get test token"
    token_data = response.json()
    
    # Add the token to the client headers
    test_client.headers["Authorization"] = f"Bearer {token_data['access_token']}"
    
    yield test_client
    
    # Clean up - remove token from headers after test completes
    test_client.headers.pop("Authorization", None)


@pytest.fixture
def manager_client(test_client: TestClient, db_session) -> TestClient:
    """
    Test client with valid authentication token for account manager user.
    """
    # Get test token from our test-token endpoint
    response = test_client.post("/v1/api/auth/test-token", params={"user_id": "00000000-0000-0000-0000-000000000002"})
    assert response.status_code == 200, "Failed to get test token"
    token_data = response.json()
    
    # Add the token to the client headers
    test_client.headers["Authorization"] = f"Bearer {token_data['access_token']}"
    
    yield test_client
    
    # Clean up - remove token from headers after test completes
    test_client.headers.pop("Authorization", None)


# For backward compatibility, keep the original name as well
@pytest.fixture
def authorized_client(test_client: TestClient, db_session) -> TestClient:
    """
    Test client with valid authentication token for admin user.
    """
    # Get test token from our test/token endpoint
    response = test_client.post("/v1/api/test/token", params={"user_id": "00000000-0000-0000-0000-000000000001"})
    assert response.status_code == 200, "Failed to get test token"
    token_data = response.json()
    
    # Add the token to the client headers
    test_client.headers["Authorization"] = f"Bearer {token_data['access_token']}"
    
    yield test_client
    
    # Clean up - remove token from headers after test completes
    test_client.headers.pop("Authorization", None)


@pytest.fixture
def test_account() -> Dict[str, Any]:
    """
    Returns test account data.
    """
    return {
        "name": f"Test Account {uuid.uuid4()}"
    }


@pytest.fixture
def test_restaurant() -> Dict[str, Any]:
    """
    Returns test restaurant data.
    """
    return {
        "name": f"Test Restaurant {uuid.uuid4()}"
    }


@pytest.fixture
def test_store() -> Dict[str, Any]:
    """
    Returns test store data.
    """
    return {
        "name": f"Test Store {uuid.uuid4()}"
    }


@pytest.fixture
def test_supplier() -> Dict[str, Any]:
    """
    Returns test supplier data.
    """
    return {
        "name": f"Test Supplier {uuid.uuid4()}",
        "contact_info": {
            "email": "supplier@example.com",
            "phone": "+1234567890"
        }
    }


class BaseAPITest:
    """
    Base class for API tests providing common utility methods.
    """
    
    @staticmethod
    def get_api_v1_url(path: str) -> str:
        """
        Returns a full API URL with version prefix.
        """
        return f"{settings.API_V1_STR}{path}"
    
    @staticmethod
    def assert_successful_response(response_data: Dict[str, Any], status_code: int = 200) -> None:
        """
        Verify a successful API response with expected status code.
        """
        assert response_data is not None
        assert status_code in [200, 201, 202, 204]
    
    @staticmethod
    def assert_error_response(response_data: Dict[str, Any], status_code: int) -> None:
        """
        Verify an error API response with expected status code and error details.
        """
        assert response_data is not None
        assert "detail" in response_data
        assert status_code >= 400