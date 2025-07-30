#!/usr/bin/env python3
"""
Test Telegram Button Click
-------------------------
Tests the "Оки" button in the documents_button step by simulating
a Telegram callback_query webhook event.

This script:
1. Gets the bot_id from the API
2. Simulates a button click webhook event
3. Sends it to the webhook endpoint
4. Verifies the response

Usage:
    python -m src.api.tests.utils.telegram.test_telegram_button [--chat-id CHAT_ID] [--button-value VALUE]
"""
import os
import sys
import json
import requests
import argparse
import logging
import uuid
from datetime import datetime
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Parse arguments
parser = argparse.ArgumentParser(description="Test Telegram Button Click")
parser.add_argument("--bot-id", help="Bot ID to use for the test")
parser.add_argument("--chat-id", default="12345", help="Chat ID to use for the test")
parser.add_argument("--button-value", default="ok", help="Button value to simulate")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

# Set log level based on debug flag
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

# Constants
BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token from API."""
    logger.info("Getting authentication token...")
    
    try:
        response = requests.post(
            urljoin(BASE_URL, "/v1/api/auth/test-token"),
            json={},
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get auth token: {response.status_code} {response.text}")
            sys.exit(1)
            
        token = response.json().get("access_token")
        if not token:
            logger.error("Auth token not found in response")
            sys.exit(1)
            
        logger.info("Successfully obtained auth token")
        return token
    except Exception as e:
        logger.error(f"Error getting auth token: {e}")
        sys.exit(1)

def get_bot_id(auth_token):
    """Get bot ID from API or use the provided one."""
    # Check if bot ID was provided as argument
    if args.bot_id:
        logger.info(f"Using provided bot ID: {args.bot_id}")
        return args.bot_id
        
    # Otherwise try to get from API
    logger.info("Getting bot ID from API...")
    
    try:
        response = requests.get(
            urljoin(BASE_URL, "/v1/api/bots"),
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get bots: {response.status_code} {response.text}")
            sys.exit(1)
            
        bots = response.json()
        if not bots:
            logger.error("No bots found")
            sys.exit(1)
        
        # Look for a bot named "Telegram Test Bot" or "Test Telegram Bot"
        for bot in bots:
            if bot.get("name") == "Telegram Test Bot" or bot.get("name") == "Test Telegram Bot":
                bot_id = bot.get("id")
                logger.info(f"Found Telegram Test Bot with ID: {bot_id}")
                return bot_id
                
        # If no specific bot found, use the first one
        bot_id = bots[0]["id"]
        logger.info(f"Using first available bot with ID: {bot_id}")
        return bot_id
    except Exception as e:
        logger.error(f"Error getting bot ID: {e}")
        sys.exit(1)

def simulate_button_click(bot_id, chat_id, button_value):
    """Simulate a button click by sending a webhook event."""
    logger.info(f"Simulating button click: value={button_value}, chat_id={chat_id}")
    
    # Create callback_query webhook payload
    update_id = int(datetime.now().timestamp())
    message_id = int(datetime.now().timestamp() % 10000)
    callback_query_id = str(uuid.uuid4())
    
    webhook_payload = {
        "update_id": update_id,
        "callback_query": {
            "id": callback_query_id,
            "from": {
                "id": int(chat_id),
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser"
            },
            "message": {
                "message_id": message_id,
                "from": {
                    "id": 987654321,
                    "is_bot": True,
                    "first_name": "TestBot",
                    "username": "test_bot"
                },
                "chat": {
                    "id": int(chat_id),
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser",
                    "type": "private"
                },
                "date": int(datetime.now().timestamp()),
                "text": "Изучи этот список и нажми кнопку, когда будешь готов продолжить."
            },
            "chat_instance": str(uuid.uuid4().int)[:10],
            "data": button_value
        }
    }
    
    # Log the payload
    if args.debug:
        logger.debug(f"Webhook payload: {json.dumps(webhook_payload, indent=2)}")
    
    # Send webhook to API
    webhook_url = urljoin(BASE_URL, f"/v1/api/webhooks/telegram/{bot_id}")
    logger.info(f"Sending webhook to: {webhook_url}")
    
    try:
        response = requests.post(webhook_url, json=webhook_payload, timeout=10)
        
        logger.info(f"Response status code: {response.status_code}")
        
        # Log the full response in debug mode
        if args.debug:
            logger.debug(f"Response body: {response.text}")
        
        # Check response
        if response.status_code == 200:
            logger.info("✓ Button click simulation successful")
            return True
        else:
            logger.error(f"✗ Button click simulation failed: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending webhook: {e}")
        return False

def main():
    """Main function."""
    try:
        # Get auth token
        auth_token = get_auth_token()
        
        # Get bot ID
        bot_id = get_bot_id(auth_token)
        
        # Simulate button click
        success = simulate_button_click(
            bot_id=bot_id,
            chat_id=args.chat_id,
            button_value=args.button_value
        )
        
        # Display result
        print("\n=== TEST RESULTS ===")
        if success:
            print("✓ Button click simulation SUCCESSFUL")
            print("✓ The webhook was processed correctly")
            print(f"✓ The scenario should now have moved to the next step")
        else:
            print("✗ Button click simulation FAILED")
            print("✗ See error logs above for details")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()