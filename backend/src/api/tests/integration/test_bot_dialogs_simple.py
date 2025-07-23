"""
Simplified integration tests for the bot dialog API endpoints.
Uses direct API calls instead of TestClient for better test reliability.
"""
import pytest
import os
import requests
import json
from typing import Dict, Any
from uuid import UUID

from src.api.tests.base import BaseAPITest
from src.api.core.config import get_settings

settings = get_settings()


@pytest.mark.bots
class TestSimpleBotDialogAPI(BaseAPITest):
    """
    Simplified tests for bot dialog endpoints in the API.
    """
    
    # Get API base URL from environment variable or use default
    api_base_url = os.environ.get("API_TEST_URL", "http://localhost:8000")
    
    # Use fixed account ID from auth_service.py for tests
    test_account_id = "00000000-0000-0000-0000-000000000001"
    
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
        
        # Log token acquisition (only show beginning for security)
        print(f"Token obtained successfully: {self.token[:10]}...")
    
    def create_test_bot(self):
        """
        Helper to create a test bot for dialog tests.
        Returns the bot ID if successful.
        """
        # Create test bot data
        bot_data = {
            "name": "Bot for Dialog Tests",
            "description": "Bot for testing dialog state",
            "account_id": self.test_account_id,
            "is_active": True,
            "platform_credentials": []
        }
        
        # Create the bot
        url = f"{self.api_base_url}/v1/api/accounts/{bot_data['account_id']}/bots"
        response = requests.post(url, json=bot_data, headers=self.headers)
        
        assert response.status_code == 201, f"Failed to create bot: {response.text}"
        created_bot = response.json()
        bot_id = created_bot["id"]
        
        return bot_id
        
    def test_get_dialog_state(self):
        """
        Test getting dialog state for a chat.
        """
        # First create a test bot
        bot_data = {
            "name": "Bot for Dialog State Test",
            "description": "Bot for testing dialog state",
            "account_id": self.test_account_id,
            "is_active": True,
            "platform_credentials": []
        }
        
        # Create the bot first 
        create_response = requests.post(
            f"{self.api_base_url}/v1/api/accounts/{bot_data['account_id']}/bots", 
            json=bot_data,
            headers=self.headers
        )
        
        assert create_response.status_code == 201, f"Failed to create bot: {create_response.text}"
        created_bot = create_response.json()
        bot_id = created_bot['id']
        
        # Set up test parameters
        platform = "telegram"
        chat_id = "123456789"
        
        # Get dialog state
        url = f"{self.api_base_url}/v1/api/bots/{bot_id}/dialogs/{platform}/{chat_id}"
        
        response = requests.get(url, headers=self.headers)
        
        # Assert successful dialog state retrieval
        assert response.status_code == 200, f"Failed to get dialog state: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["bot_id"] == bot_id
        assert data["platform"] == platform
        assert data["platform_chat_id"] == chat_id
        assert "current_step" in data
        assert "collected_data" in data
        assert "last_interaction_at" in data
        
        # Note: In pytest, tests should not return values
        # We're keeping this pattern consistent with other tests for now
        
    def test_update_dialog_state(self):
        """
        Test updating dialog state for a chat.
        """
        # First create a test bot
        bot_data = {
            "name": "Bot for Dialog State Update",
            "description": "Bot for testing dialog state update",
            "account_id": self.test_account_id,
            "is_active": True,
            "platform_credentials": []
        }
        
        # Create the bot
        create_response = requests.post(
            f"{self.api_base_url}/v1/api/accounts/{bot_data['account_id']}/bots", 
            json=bot_data,
            headers=self.headers
        )
        
        assert create_response.status_code == 201, f"Failed to create bot: {create_response.text}"
        created_bot = create_response.json()
        bot_id = created_bot['id']
        
        # Set up test parameters
        platform = "telegram"
        chat_id = "123456789"
        
        # First get the initial dialog state
        url = f"{self.api_base_url}/v1/api/bots/{bot_id}/dialogs/{platform}/{chat_id}"
        initial_response = requests.get(url, headers=self.headers)
        assert initial_response.status_code == 200, f"Failed to get initial dialog state: {initial_response.text}"
        initial_data = initial_response.json()
        dialog_id = initial_data["id"]
        
        # Update data
        update_data = {
            "current_step": "confirmation",
            "collected_data": {
                "name": "John Doe",
                "order_items": ["pizza", "cola"],
                "delivery_address": "123 Main St"
            }
        }
        
        # Make the update request
        response = requests.put(url, json=update_data, headers=self.headers)
        
        # Assert successful dialog state update
        assert response.status_code == 200, f"Failed to update dialog state: {response.text}"
        data = response.json()
        assert data["id"] == dialog_id
        assert data["bot_id"] == bot_id
        assert data["platform"] == platform
        assert data["platform_chat_id"] == chat_id
        assert data["current_step"] == update_data["current_step"]
        assert data["collected_data"] == update_data["collected_data"]
        assert "updated_at" in data
        
    def test_get_dialog_history(self):
        """
        Test getting dialog history for a chat.
        """
        # Create a test bot
        bot_data = {
            "name": "Bot for Dialog History",
            "description": "Bot for testing dialog history",
            "account_id": self.test_account_id,
            "is_active": True,
            "platform_credentials": []
        }
        
        # Create the bot
        create_response = requests.post(
            f"{self.api_base_url}/v1/api/accounts/{bot_data['account_id']}/bots", 
            json=bot_data,
            headers=self.headers
        )
        
        assert create_response.status_code == 201, f"Failed to create bot: {create_response.text}"
        created_bot = create_response.json()
        bot_id = created_bot['id']
        
        # Set up test parameters
        platform = "telegram"
        chat_id = "123456789"
        
        # Get dialog history
        url = f"{self.api_base_url}/v1/api/bots/{bot_id}/dialogs/{platform}/{chat_id}/history"
        
        response = requests.get(url, headers=self.headers)
        
        # Assert successful dialog history retrieval
        assert response.status_code == 200, f"Failed to get dialog history: {response.text}"
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)