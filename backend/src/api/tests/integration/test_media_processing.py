"""
Integration test for media processing in bot dialogs.
Tests the flow of media from scenario to platform adapter.
"""
import pytest
import os
import requests
import json
import tempfile
from typing import Dict, Any
from uuid import UUID

from src.api.tests.base import BaseAPITest
from src.api.core.config import get_settings

settings = get_settings()


@pytest.mark.bots
class TestMediaProcessing(BaseAPITest):
    """
    Tests for media processing in bot dialogs.
    """
    
    # Get API base URL from environment variable or use default
    api_base_url = os.environ.get("API_TEST_URL", "http://localhost:8000")
    
    # Use fixed account ID from auth_service.py for tests
    test_account_id = "00000000-0000-0000-0000-000000000001"
    
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
    
    def create_test_media_file(self, file_name="test_media.png", bot_id=None):
        """
        Create a test media file directly in the database.
        """
        # Minimal valid PNG file (1x1 pixel, black)
        image_content = bytes.fromhex('89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000D4944415478DAE3626000000006000105D4378F0000000049454E44AE426082')
        
        if not bot_id:
            # Create a test bot first if bot_id not provided
            bot_data = {
                "name": "Media Test Bot",
                "description": "Bot for testing media processing",
                "account_id": self.test_account_id,
                "is_active": True,
                "platform_credentials": []
            }
            
            url = f"{self.api_base_url}/v1/api/accounts/{self.test_account_id}/bots"
            response = requests.post(url, json=bot_data, headers=self.headers)
            assert response.status_code == 201, f"Failed to create bot: {response.text}"
            bot_id = response.json()["id"]
        
        # Upload directly to the API
        files = {'file': (file_name, image_content, 'image/png')}
        url = f"{self.api_base_url}/v1/api/bots/{bot_id}/media"
        response = requests.post(url, files=files, headers=self.headers)
        
        assert response.status_code == 201, f"Failed to upload media file: {response.text}"
        media_data = response.json()
        media_id = media_data["media_id"]
        
        # Extract file_id from file name (without extension)
        file_id = os.path.splitext(file_name)[0]
        
        # Register platform file_id
        platform_data = {
            "platform": "telegram",
            "file_id": file_id
        }
        url = f"{self.api_base_url}/v1/api/media/{media_id}/platform-id"
        response = requests.post(url, json=platform_data, headers=self.headers)
        
        assert response.status_code == 200, f"Failed to register platform file ID: {response.text}"
        
        print(f"Created test media file in database with ID: {media_id}, file_id: {file_id}")
        return file_id, media_id

    def create_test_bot_with_scenario(self):
        """
        Create a test bot with a scenario that includes media.
        """
        # Create test bot data
        bot_data = {
            "name": "Media Test Bot",
            "description": "Bot for testing media processing",
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
        
        # Create a simple scenario with media
        file_id = "test_media_image"
        file_id, media_id = self.create_test_media_file(f"{file_id}.png", bot_id)
        
        scenario_data = {
            "name": "Media Test Scenario",
            "version": "1.0",
            "start_step": "welcome",
            "steps": {
                "welcome": {
                    "type": "message",
                    "message": {
                        "text": "Welcome to the media test bot!",
                        "media": [
                            {
                                "type": "image",
                                "description": "Test image",
                                "file_id": file_id
                            }
                        ]
                    },
                    "next_step": "end"
                },
                "end": {
                    "type": "message",
                    "message": {
                        "text": "Thanks for testing!"
                    }
                }
            }
        }
        
        scenario_create_data = {
            "name": "Media Test Scenario",
            "description": "A scenario for testing media processing",
            "scenario_data": scenario_data,
            "is_active": True
        }
        
        # Create the scenario
        url = f"{self.api_base_url}/v1/api/bots/{bot_id}/scenarios"
        response = requests.post(url, json=scenario_create_data, headers=self.headers)
        
        assert response.status_code == 201, f"Failed to create scenario: {response.text}"
        created_scenario = response.json()
        
        return {
            "bot_id": bot_id,
            "scenario_id": created_scenario["id"],
            "file_id": file_id,
            "media_id": media_id
        }
    
    def test_media_in_dialog_step(self):
        """
        Test that media is properly included in dialog step responses.
        """
        # Create a test bot with media scenario
        test_data = self.create_test_bot_with_scenario()
        bot_id = test_data["bot_id"]
        
        # Set up test parameters
        platform = "telegram"
        chat_id = "123456789"
        
        # Create a dialog state
        dialog_create_data = {
            "platform": platform,
            "platform_chat_id": chat_id,
            "current_step": "welcome",
            "collected_data": {}
        }
        
        url = f"{self.api_base_url}/v1/api/bots/{bot_id}/dialogs"
        response = requests.post(url, json=dialog_create_data, headers=self.headers)
        
        assert response.status_code == 201, f"Failed to create dialog state: {response.text}"
        dialog_state = response.json()
        
        # Process the current step to get the response with media
        url = f"{self.api_base_url}/v1/api/bots/{bot_id}/dialogs/{platform}/{chat_id}/process"
        process_data = {
            "input": "/start"
        }
        
        response = requests.post(url, json=process_data, headers=self.headers)
        
        # Assert successful dialog processing
        assert response.status_code == 200, f"Failed to process dialog: {response.text}"
        dialog_response = response.json()
        
        # Check that media is included in the response
        assert "message" in dialog_response, "No message in dialog response"
        message = dialog_response["message"]
        
        assert "media" in message, "No media in message"
        media = message["media"]
        
        assert isinstance(media, list), "Media is not a list"
        assert len(media) > 0, "Media list is empty"
        
        # Check first media item
        media_item = media[0]
        assert "type" in media_item, "No type in media item"
        assert "file_id" in media_item, "No file_id in media item"
        assert media_item["type"] == "image", f"Unexpected media type: {media_item['type']}"
        assert media_item["file_id"] == test_data["file_id"], f"Unexpected file_id: {media_item['file_id']}"
        
        # Clean up database test entries
        try:
            url = f"{self.api_base_url}/v1/api/media/{test_data['media_id']}"
            delete_response = requests.delete(url, headers=self.headers)
            print(f"Cleaned up test media file from database: {test_data['media_id']}")
        except Exception as e:
            print(f"Warning: Failed to clean up test media: {str(e)}")
            
        # Note: In a real test, we would actually test sending the message with media
        # to a real platform, but that requires a mock platform adapter