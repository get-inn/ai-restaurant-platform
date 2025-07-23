# Testing Guide

This document describes the testing strategy and practices for the GET INN Restaurant Platform backend.

## Testing Philosophy

The platform follows a comprehensive testing approach with multiple test types:

- **Unit Tests**: Testing individual components in isolation
- **Integration Tests**: Testing interactions between components
- **API Tests**: Testing API endpoints through HTTP requests
- **Standalone Tests**: Self-contained tests for specific features

## Test Directory Structure

Tests are organized in a structured manner:

```
/backend/src/api/tests/
├── fixtures/             # Test fixtures and shared resources
├── integration/          # Integration tests (interact with multiple components)
│   ├── bots/
│   ├── chef/
│   ├── labor/
│   ├── supplier/
│   └── ...
├── simplified/           # Simplified tests for common patterns
├── standalone/           # Self-contained tests for specific features
└── unit/                 # Unit tests (test single components)
    ├── bots/
    ├── chef/
    ├── labor/
    ├── supplier/
    └── ...
```

## Running Tests

### Using the Run Tests Script

The `run_tests.sh` script provides a convenient way to run tests:

```bash
# Run all tests in Docker
./backend/run_tests.sh

# Run tests locally using the virtual environment
./backend/run_tests.sh -l

# Run tests with coverage report
./backend/run_tests.sh -l -c

# Run specific test modules or classes
./backend/run_tests.sh -l -k "auth_flow"
```

#### Common Options

- `-l`, `--local`: Run tests locally using the virtual environment
- `-v`, `--verbose`: Show verbose output
- `-c`, `--coverage`: Generate coverage report
- `-k "pattern"`: Only run tests matching the given pattern
- `--cov-report=html`: Generate HTML coverage report

### Running Tests Manually

Tests can also be run directly with pytest:

```bash
# Activate virtual environment
source backend/venv/bin/activate

# Run all tests
cd backend
pytest

# Run specific tests
pytest src/api/tests/unit/test_auth.py

# Run tests with specific markers
pytest -m "slow"
```

## Writing Tests

### Unit Tests

Unit tests should focus on testing a single component in isolation:

```python
# src/api/tests/unit/services/bots/test_instance_service.py
import pytest
from unittest.mock import Mock, patch

from src.api.services.bots.instance_service import BotInstanceService

@pytest.fixture
def mock_db():
    return Mock()

def test_create_bot(mock_db):
    # Arrange
    service = BotInstanceService(mock_db)
    bot_data = {"name": "Test Bot", "description": "Test description"}
    
    # Act
    result = service.create_bot(bot_data)
    
    # Assert
    assert result["name"] == "Test Bot"
    assert mock_db.add.called_once()
    assert mock_db.commit.called_once()
```

### Integration Tests

Integration tests verify interactions between components:

```python
# src/api/tests/integration/test_bot_api.py
import pytest
from fastapi.testclient import TestClient

from src.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_create_bot(client, test_token):
    # Arrange
    headers = {"Authorization": f"Bearer {test_token}"}
    bot_data = {"name": "Test Bot", "description": "Test description"}
    
    # Act
    response = client.post("/v1/api/bots", json=bot_data, headers=headers)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Bot"
    assert "id" in data
```

### Test Fixtures

Fixtures are reusable components that set up test dependencies:

```python
# src/api/tests/fixtures/db.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.core.database import Base, get_db
from src.api.main import app

@pytest.fixture
def test_db():
    # Create test database engine
    engine = create_engine("sqlite:///./test.db")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Override dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal()
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
```

## Test Categories

### API Tests

For testing API endpoints and their integration:

```python
def test_create_bot_api(client, test_token):
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.post(
        "/v1/api/bots",
        json={"name": "Test Bot"},
        headers=headers
    )
    assert response.status_code == 201
```

### Database Tests

For testing database interactions:

```python
def test_bot_creation_in_db(test_db):
    # Create a bot
    bot = BotInstanceDB(name="Test Bot", description="Test")
    test_db.add(bot)
    test_db.commit()
    
    # Query it back
    db_bot = test_db.query(BotInstanceDB).filter_by(name="Test Bot").first()
    assert db_bot is not None
    assert db_bot.name == "Test Bot"
```

### Bot Conversation Tests

For testing bot dialog flows:

```python
@pytest.mark.asyncio
async def test_bot_dialog_flow(dialog_manager, test_bot_id):
    # Initialize dialog
    dialog_id = await dialog_manager.start_dialog(bot_id=test_bot_id, platform="test")
    
    # Send a message
    response = await dialog_manager.process_message(
        dialog_id=dialog_id,
        message_text="Hello",
    )
    
    # Check response
    assert "Welcome" in response["text"]
```

## Testing External Integrations

### Mocking External Services

Use mocks for external services:

```python
@patch("src.integrations.ai_tools.azure_openai.azure_openai_client_v2.AzureOpenAIClientV2")
def test_document_processing(mock_client):
    # Configure mock
    mock_client.return_value.chat_completion.return_value = {
        "choices": [{
            "message": {
                "content": '{"document_type": "invoice"}'
            }
        }]
    }
    
    # Test with the mock
    pipeline = DocumentRecognitionPipelineV2(mock_client)
    result = pipeline.process_document("test.pdf")
    
    assert result["document_type"] == "invoice"
```

### Integration Test with Real Services

For testing with real external services:

```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("AZURE_OPENAI_ENABLED"), reason="Azure OpenAI not enabled")
def test_azure_openai_integration():
    client = AzureOpenAIClientV2()
    response = client.chat_completion(
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    assert "choices" in response
```

## Test Coverage

To generate a coverage report:

```bash
./backend/run_tests.sh -l -c --cov-report=html
```

This generates an HTML report in the `htmlcov` directory. Open `htmlcov/index.html` in your browser to view it.

## Debugging Tests

For debugging failing tests:

```bash
# Run with verbose output
./backend/run_tests.sh -l -v -k "failing_test"

# Run with PDB debugger
./backend/run_tests.sh -l --pdb -k "failing_test"
```

## Bot Conversation Logs

Bot conversation tests generate detailed logs in the `logs/` directory with the format `bot_conversations_*.log`. You can view these logs using:

```bash
python -m scripts.bots.utils.view_bot_logs --source file --file logs/bot_conversations_latest.log
```

## CI/CD Integration

Tests are automatically run in the CI/CD pipeline:

1. **Pull Requests**: All tests are run when a PR is created or updated
2. **Merge to Main**: All tests are run before merging to the main branch
3. **Deployments**: Tests are run before deployment to any environment

## Best Practices

1. **Use meaningful test names** that describe what's being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Test one thing per test** function
4. **Mock external dependencies** to keep tests fast and reliable
5. **Use fixtures** for common setup and teardown
6. **Prefer API tests** over direct database access when possible
7. **Ensure tests are idempotent** and can be run multiple times
8. **Maintain test isolation** so tests don't affect each other

## Troubleshooting Common Test Issues

### Tests Failing in Docker but Passing Locally

- Check environment variable differences
- Verify database configuration
- Look for file path or permission issues

### Slow Tests

- Identify slow tests with `--durations=10` option
- Consider marking slow tests with `@pytest.mark.slow`
- Use appropriate mocking to avoid external service calls

### Database Errors

- Make sure test databases are being properly created and cleaned up
- Check for transaction handling issues
- Verify that fixtures are properly isolated