"""
Test configuration for API tests.
"""
import pytest
import asyncio
from typing import Dict, Any, Generator
from uuid import uuid4

from src.api.schemas.auth_schemas import UserRole

# Import fixtures from base.py
from src.api.tests.base import db_session, test_client, authorized_client

@pytest.fixture
def test_user() -> Dict[str, Any]:
    """
    Returns a test user for authentication tests.
    """
    return {
        "id": str(uuid4()),
        "email": "test@example.com",
        "password": "password",
        "is_active": True,
        "role": UserRole.ADMIN
    }

@pytest.fixture
def test_account() -> Dict[str, Any]:
    """
    Returns a test account data.
    """
    return {
        "name": "Test Account",
        "account_type": "restaurant"
    }

@pytest.fixture
def test_restaurant() -> Dict[str, Any]:
    """
    Returns test restaurant data.
    """
    return {
        "name": "Test Restaurant",
        "location": "123 Test Street",
        "contact_info": {
            "phone": "+1234567890",
            "email": "restaurant@example.com"
        }
    }

@pytest.fixture
def test_store() -> Dict[str, Any]:
    """
    Returns test store data.
    """
    return {
        "name": "Test Store",
        "address": "456 Test Avenue",
        "contact_info": {
            "phone": "+0987654321",
            "email": "store@example.com"
        }
    }

@pytest.fixture
def test_supplier() -> Dict[str, Any]:
    """
    Returns test supplier data.
    """
    return {
        "name": "Test Supplier",
        "contact_info": {
            "phone": "+1122334455",
            "email": "supplier@example.com"
        }
    }

@pytest.fixture
def test_bot_instance() -> Dict[str, Any]:
    """
    Returns test bot instance data.
    """
    return {
        "name": "Test Bot",
        "description": "A bot for testing",
        "account_id": str(uuid4()),
        "is_active": True
    }

@pytest.fixture
def test_bot_scenario() -> Dict[str, Any]:
    """
    Returns test bot scenario data.
    """
    return {
        "name": "Test Scenario",
        "description": "A scenario for testing",
        "version": "1.0",
        "steps": [
            {
                "id": "welcome",
                "message": "Welcome to the test bot!",
                "next_step": "question"
            },
            {
                "id": "question",
                "message": "This is a test question?",
                "next_step": "end"
            },
            {
                "id": "end",
                "message": "Thank you for testing!",
                "next_step": None
            }
        ]
    }

# Add more fixtures as needed for specific test suites