"""
Fixtures for Telegram webhook tests.
"""
import os
import pytest
import requests
import uuid
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class WebhookTestFixtures:
    """Helper class for creating and managing webhook test fixtures."""
    
    def __init__(self, api_base_url=None, test_account_id=None):
        """Initialize with API base URL and test account ID."""
        self.api_base_url = api_base_url or os.environ.get("API_TEST_URL", "http://localhost:8000")
        self.test_account_id = test_account_id or "00000000-0000-0000-0000-000000000001"
        self.token = None
        self.headers = None
    
    def get_auth_token(self) -> str:
        """Get a test authentication token."""
        response = requests.post(f"{self.api_base_url}/v1/api/auth/test-token")
        if response.status_code != 200:
            raise Exception(f"Failed to get test token: {response.text}")
        
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        print(f"Auth token set: {self.token[:20]}...")
        return self.token
    
    def create_test_bot(self, name_prefix="Webhook Test Bot") -> Tuple[str, Dict[str, Any]]:
        """Create a test bot and return its ID and data."""
        if not self.headers:
            self.get_auth_token()
        
        bot_name = f"{name_prefix} {uuid.uuid4()}"
        bot_data = {
            "name": bot_name,
            "description": "Bot for testing webhook functionality",
            "account_id": self.test_account_id,
            "is_active": True,
            "platform_credentials": []
        }
        
        response = requests.post(
            f"{self.api_base_url}/v1/api/accounts/{bot_data['account_id']}/bots", 
            json=bot_data,
            headers=self.headers
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create test bot: {response.text}")
        
        bot_response = response.json()
        bot_id = bot_response["id"]
        logger.info(f"Created test bot with ID: {bot_id}")
        
        return bot_id, bot_response
    
    def add_telegram_credentials(self, bot_id: str, token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ") -> Dict[str, Any]:
        """Add Telegram credentials to a bot."""
        if not self.headers:
            self.get_auth_token()
        
        credential_data = {
            "platform": "telegram",
            "credentials": {
                "token": token,
            },
            "is_active": True
        }
        
        response = requests.post(
            f"{self.api_base_url}/v1/api/bots/{bot_id}/platforms",
            json=credential_data,
            headers=self.headers
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to add Telegram credential: {response.text}")
        
        logger.info(f"Added Telegram credentials to bot {bot_id}")
        return response.json()
    
    def delete_test_bot(self, bot_id: str) -> bool:
        """Delete a test bot."""
        if not self.headers:
            self.get_auth_token()
        
        response = requests.delete(
            f"{self.api_base_url}/v1/api/bots/{bot_id}",
            headers=self.headers
        )
        
        success = response.status_code == 204
        if success:
            logger.info(f"Successfully deleted test bot {bot_id}")
        else:
            logger.warning(f"Failed to delete test bot {bot_id}: {response.status_code} {response.text}")
        
        return success
    
    def create_bot_with_telegram_credentials(self) -> Tuple[str, Dict[str, Any]]:
        """Create a bot with Telegram credentials in one step."""
        bot_id, bot_data = self.create_test_bot()
        credentials = self.add_telegram_credentials(bot_id)
        return bot_id, {"bot": bot_data, "credentials": credentials}


@pytest.fixture
def webhook_fixtures():
    """Fixture that provides webhook test helpers."""
    return WebhookTestFixtures()


@pytest.fixture
def test_bot_with_credentials(webhook_fixtures):
    """Create a test bot with Telegram credentials and clean up after the test."""
    bot_id, data = webhook_fixtures.create_bot_with_telegram_credentials()
    
    yield bot_id, data
    
    # Clean up after the test
    webhook_fixtures.delete_test_bot(bot_id)