"""
Functional tests for Telegram webhook management API endpoints.
These tests use the real HTTP API to create, get and update records.
"""
import pytest
import os
import requests
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.api.tests.base import BaseAPITest
from src.api.tests.fixtures.webhook_fixtures import webhook_fixtures, test_bot_with_credentials
from src.api.core.config import get_settings


@pytest.mark.webhooks
class TestTelegramWebhookAPI(BaseAPITest):
    """
    Integration tests for Telegram webhook management endpoints.
    Uses the real HTTP API to test webhook functionality.
    """
    
    # Get API base URL from environment variable or use default
    api_base_url = os.environ.get("API_TEST_URL", "http://localhost:8000")
    
    # Use fixed account ID for tests
    test_account_id = "00000000-0000-0000-0000-000000000001"

    @pytest.fixture(autouse=True)
    def setup_telegram_mocks(self):
        """
        Mock the Telegram Bot API calls to avoid making real external API calls.
        We still use the real internal API to test our webhook management.
        """
        # Mock the telegram.Bot class to avoid making external API calls
        with patch('telegram.Bot') as mock_bot_class:
            # Create an instance that will be returned when telegram.Bot() is called
            mock_bot = mock_bot_class.return_value
            
            # Mock set_webhook method
            mock_bot.set_webhook = pytest.mock.AsyncMock(return_value=True)
            
            # Mock webhook info with a realistic response structure
            mock_webhook_info = pytest.mock.MagicMock(
                url="https://example.com/webhook/test",
                has_custom_certificate=False,
                pending_update_count=0,
                ip_address="127.0.0.1",
                last_error_date=None,
                last_error_message=None,
                max_connections=40,
                allowed_updates=["message", "callback_query"]
            )
            mock_bot.get_webhook_info = pytest.mock.AsyncMock(return_value=mock_webhook_info)
            
            # Mock delete_webhook method
            mock_bot.delete_webhook = pytest.mock.AsyncMock(return_value=True)
            
            yield mock_bot
    
    @pytest.fixture(autouse=True)
    def setup_test_bot(self, webhook_fixtures, test_bot_with_credentials):
        """Setup test data for each test method"""
        # Get the test bot and credentials
        self.bot_id, data = test_bot_with_credentials
        self.bot_data = data["bot"]
        self.credential_data = data["credentials"]
        
        # Get authentication headers from the fixture
        self.headers = webhook_fixtures.headers
        if not self.headers:
            webhook_fixtures.get_auth_token()
            self.headers = webhook_fixtures.headers
    
    def test_set_webhook(self, setup_telegram_mocks):
        """
        Test setting a webhook for a Telegram bot.
        """
        # Prepare webhook configuration
        webhook_config = {
            "drop_pending_updates": True,
            "max_connections": 40,
            "allowed_updates": ["message", "callback_query"]
        }
        
        # Call the real API to set the webhook
        response = requests.post(
            f"{self.api_base_url}/v1/api/webhooks/telegram/{self.bot_id}/set",
            json=webhook_config,
            headers=self.headers
        )
        
        # Assert the response
        assert response.status_code == 200, f"Failed to set webhook: {response.text}"
        data = response.json()
        
        # Check that the response contains expected fields
        assert "url" in data
        assert data["url"] == "https://example.com/webhook/test"  # From our mock
        assert "pending_update_count" in data
        assert data["pending_update_count"] == 0
        
        # Verify the mock was called with expected arguments
        mock_bot = setup_telegram_mocks
        mock_bot.set_webhook.assert_called_once()
        
        # Check that the call args match our config
        call_kwargs = mock_bot.set_webhook.call_args.kwargs
        assert call_kwargs["drop_pending_updates"] is True
        assert call_kwargs["max_connections"] == 40
        assert call_kwargs["allowed_updates"] == ["message", "callback_query"]
    
    def test_get_webhook_status(self, setup_telegram_mocks):
        """
        Test getting webhook status for a Telegram bot.
        """
        # Call the real API to get webhook status
        response = requests.get(
            f"{self.api_base_url}/v1/api/webhooks/telegram/{self.bot_id}/status",
            headers=self.headers
        )
        
        # Assert the response
        assert response.status_code == 200, f"Failed to get webhook status: {response.text}"
        data = response.json()
        
        # Check that the response contains expected fields from our mock
        assert "url" in data
        assert data["url"] == "https://example.com/webhook/test"
        assert "pending_update_count" in data
        assert data["pending_update_count"] == 0
        assert "ip_address" in data
        assert data["ip_address"] == "127.0.0.1"
        assert "max_connections" in data
        assert data["max_connections"] == 40
        assert "allowed_updates" in data
        assert data["allowed_updates"] == ["message", "callback_query"]
        
        # Verify the mock was called
        mock_bot = setup_telegram_mocks
        mock_bot.get_webhook_info.assert_called_once()
    
    def test_delete_webhook(self, setup_telegram_mocks):
        """
        Test deleting a webhook for a Telegram bot.
        """
        # Call the real API to delete the webhook
        response = requests.post(
            f"{self.api_base_url}/v1/api/webhooks/telegram/{self.bot_id}/delete",
            headers=self.headers
        )
        
        # Assert the response
        assert response.status_code == 200, f"Failed to delete webhook: {response.text}"
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        
        # Verify the mock was called
        mock_bot = setup_telegram_mocks
        mock_bot.delete_webhook.assert_called_once()
    
    def test_webhook_operations_sequence(self, setup_telegram_mocks):
        """
        Test a sequence of webhook operations to verify they work together properly.
        """
        # 1. First set the webhook
        set_response = requests.post(
            f"{self.api_base_url}/v1/api/webhooks/telegram/{self.bot_id}/set",
            json={"drop_pending_updates": True},
            headers=self.headers
        )
        assert set_response.status_code == 200, f"Failed to set webhook: {set_response.text}"
        
        # 2. Check the status
        status_response = requests.get(
            f"{self.api_base_url}/v1/api/webhooks/telegram/{self.bot_id}/status",
            headers=self.headers
        )
        assert status_response.status_code == 200, f"Failed to get webhook status: {status_response.text}"
        
        # 3. Delete the webhook
        delete_response = requests.post(
            f"{self.api_base_url}/v1/api/webhooks/telegram/{self.bot_id}/delete",
            headers=self.headers
        )
        assert delete_response.status_code == 200, f"Failed to delete webhook: {delete_response.text}"
        
        # 4. Check status again to verify deletion
        mock_bot = setup_telegram_mocks
        
        # Update the mock to show webhook was deleted
        empty_webhook_info = pytest.mock.MagicMock(
            url="",  # Empty URL indicates webhook has been deleted
            has_custom_certificate=False,
            pending_update_count=0,
            ip_address=None,
            last_error_date=None,
            last_error_message=None,
            max_connections=None,
            allowed_updates=None
        )
        mock_bot.get_webhook_info = pytest.mock.AsyncMock(return_value=empty_webhook_info)
        
        status_response2 = requests.get(
            f"{self.api_base_url}/v1/api/webhooks/telegram/{self.bot_id}/status",
            headers=self.headers
        )
        assert status_response2.status_code == 200, f"Failed to get webhook status after deletion: {status_response2.text}"
        
        # Should reflect the new mock
        status_data = status_response2.json()
        assert status_data["url"] == ""