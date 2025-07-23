"""
Simplified integration tests for the bot management API endpoints.
Uses direct API calls instead of TestClient for better test reliability.
"""
import pytest
import os
import requests
from typing import Dict, Any
from uuid import uuid4, UUID

from src.api.tests.base import BaseAPITest
from src.api.core.config import get_settings

settings = get_settings()


@pytest.mark.bots
class TestSimpleBotManagementAPI(BaseAPITest):
    """
    Simplified tests for bot management endpoints in the API.
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
    
    def test_create_bot_instance(self) -> None:
        """
        Test creating a new bot instance.
        """
        # Use fixed account ID from auth_service.py for tests
        account_id = "00000000-0000-0000-0000-000000000001"
        
        # Create test bot data
        bot_data = {
            "name": "Customer Support Bot",
            "description": "Bot for customer support automation",
            "account_id": account_id,
            "is_active": True,
            "platform_credentials": []
        }
        
        # Make request using direct API
        url = f"{self.api_base_url}/v1/api/accounts/{bot_data['account_id']}/bots"
        print(f"Creating bot with URL: {url}")
        
        response = requests.post(url, json=bot_data, headers=self.headers)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        # Assert successful bot creation
        assert response.status_code == 201, f"Failed to create bot: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"] == bot_data["name"]
        assert data["description"] == bot_data["description"]
        assert data["account_id"] == bot_data["account_id"]
        assert data["is_active"] == bot_data["is_active"]
        assert "created_at" in data
        
        bot_id = data["id"]
        print(f"Created bot with ID: {bot_id}")
        
        return bot_id
    
    def test_get_bot_by_id(self) -> None:
        """
        Test getting a bot by ID.
        """
        # First create a bot
        bot_id = self.test_create_bot_instance()
        
        # Now get the bot
        url = f"{self.api_base_url}/v1/api/bots/{bot_id}"
        print(f"Getting bot with URL: {url}")
        
        response = requests.get(url, headers=self.headers)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        # Assert successful bot retrieval
        assert response.status_code == 200, f"Failed to get bot: {response.text}"
        data = response.json()
        assert data["id"] == bot_id
        
        print(f"Successfully retrieved bot with ID: {bot_id}")
        
        return data
    
    def test_update_bot(self) -> None:
        """
        Test updating a bot.
        """
        # First create a bot
        bot_id = self.test_create_bot_instance()
        
        # Now update the bot
        update_data = {
            "name": "Updated Bot Name",
            "description": "Updated description",
            "is_active": False
        }
        
        url = f"{self.api_base_url}/v1/api/bots/{bot_id}"
        print(f"Updating bot with URL: {url}")
        
        response = requests.put(url, json=update_data, headers=self.headers)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        # Assert successful bot update
        assert response.status_code == 200, f"Failed to update bot: {response.text}"
        data = response.json()
        assert data["id"] == bot_id
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["is_active"] == update_data["is_active"]
        
        print(f"Successfully updated bot with ID: {bot_id}")
        
        return data
    
    def test_delete_bot(self) -> None:
        """
        Test deleting a bot.
        """
        # First create a bot
        bot_id = self.test_create_bot_instance()
        
        # Now delete the bot
        url = f"{self.api_base_url}/v1/api/bots/{bot_id}"
        print(f"Deleting bot with URL: {url}")
        
        response = requests.delete(url, headers=self.headers)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        # Assert successful bot deletion
        assert response.status_code == 204, f"Failed to delete bot: {response.text}"
        
        print(f"Successfully deleted bot with ID: {bot_id}")
        
        # Verify that the bot is gone
        get_response = requests.get(url, headers=self.headers)
        assert get_response.status_code == 404, "Bot should be deleted but still exists"