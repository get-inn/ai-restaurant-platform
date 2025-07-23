"""
Simple integration test for bot endpoints using direct API calls.
This is a minimalistic test to verify our authentication approach works.
"""
import pytest
import os
import requests
from typing import Dict, Any
from uuid import uuid4

from src.api.tests.base import BaseAPITest
from src.api.core.config import get_settings

settings = get_settings()


@pytest.mark.bots
class TestSimpleBotAPI(BaseAPITest):
    """
    Simple test for bot management endpoints.
    """
    
    # Get API base URL from environment variable or use default
    api_base_url = os.environ.get("API_TEST_URL", "http://localhost:8000")
    
    @classmethod
    def setup_class(cls):
        """Setup once for all tests in the class"""
        # We rely on initialize_users in auth_service.py being called when we request a token
        # This happens automatically when we make our first API call with authentication
        print(f"Test class setup - will initialize test data via auth_service.py when getting tokens")
    
    def setup_method(self):
        """Setup for each test method"""
        # Get a test token directly from the API
        url = f"{self.api_base_url}/v1/api/auth/test-token"
        print(f"Getting test token from: {url}")
        
        response = requests.post(url)
        assert response.status_code == 200, f"Failed to get test token: {response.text}"
        
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Print debug info
        print(f"Token obtained successfully: {self.token[:20]}...")
    
    def test_create_bot(self):
        """
        Test creating a new bot instance.
        """
        import json
        
        # Get test account ID - we know it's this fixed UUID from our auth_service.py
        account_id = "00000000-0000-0000-0000-000000000001"
        
        # Create test bot data
        bot_data = {
            "name": "Test Bot",
            "description": "Bot for API testing",
            "account_id": account_id,
            "is_active": True
        }
        
        # First check if the API endpoints are correctly mounted
        # Get API docs to check if the bot endpoints are registered
        docs_url = f"{self.api_base_url}/docs/openapi.json"
        print(f"Checking API endpoints at: {docs_url}")
        try:
            docs_response = requests.get(docs_url)
            print(f"API docs response status: {docs_response.status_code}")
            if docs_response.status_code == 200:
                openapi = docs_response.json()
                # Search for the bot creation endpoint in the paths
                for path, methods in openapi.get("paths", {}).items():
                    if "/accounts/" in path and "/bots" in path and "post" in methods:
                        print(f"Found bot creation endpoint: {path}")
        except Exception as e:
            print(f"Error fetching API docs: {str(e)}")
        
        # Make request using direct API - the URL has a double "api" prefix
        # This is because the router includes "/api" in the path and main.py adds "/v1"
        # First try with single "api"
        url = f"{self.api_base_url}/v1/api/accounts/{account_id}/bots"
        print(f"Trying bot creation with URL (single api): {url}")
        print(f"Headers: {self.headers}")
        print(f"Request data: {json.dumps(bot_data, indent=2)}")
        
        response = requests.post(url, json=bot_data, headers=self.headers)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        # If that fails, try with double "api"
        if response.status_code != 201:
            url = f"{self.api_base_url}/v1/api/api/accounts/{account_id}/bots"
            print(f"Trying bot creation with URL (double api): {url}")
            response = requests.post(url, json=bot_data, headers=self.headers)
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
        
        # Assert successful bot creation
        assert response.status_code == 201, f"Failed to create bot: {response.text}"
        data = response.json()
        
        # Verify response data
        assert "id" in data
        assert data["name"] == bot_data["name"]
        assert data["description"] == bot_data["description"]
        assert data["account_id"] == bot_data["account_id"]
        assert data["is_active"] == bot_data["is_active"]
        assert "created_at" in data
        
        # Print success message
        print(f"Bot created successfully with ID: {data['id']}")
        return data["id"]