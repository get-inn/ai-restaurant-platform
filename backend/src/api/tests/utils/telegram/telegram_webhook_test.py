#!/usr/bin/env python3
"""
Integration test for Telegram webhook functionality.

This script provides a simple way to validate the webhook service without
the complexity of unit test mocks. It performs basic operations against
the actual Telegram API to ensure everything is working correctly.

Usage:
    python telegram_webhook_test.py [--token TOKEN] [--bot-id BOT_ID]

Arguments:
    --token      Telegram bot token (will use token from file if not provided)
    --bot-id     Bot ID to use for webhook testing
"""
import os
import sys
import json
import requests
import argparse
import logging
from uuid import UUID
from datetime import datetime
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Parse arguments
parser = argparse.ArgumentParser(description="Telegram Webhook Test")
parser.add_argument("--token", help="Telegram bot token")
parser.add_argument("--bot-id", help="Bot ID to use for webhook testing")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

# Set log level based on debug flag
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

# Constants
BASE_URL = "http://localhost:8000"
TOKEN_FILE = "telegram_token.txt"


def read_token_file():
    """Read token from file if not provided as argument."""
    if args.token:
        return args.token
        
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Token file {TOKEN_FILE} not found")
        sys.exit(1)


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


def get_ngrok_url():
    """Get ngrok tunnel URL."""
    logger.info("Getting ngrok tunnel URL...")
    
    try:
        ngrok_response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if ngrok_response.status_code != 200:
            logger.error(f"Failed to get ngrok tunnels: {ngrok_response.status_code}")
            sys.exit(1)
            
        tunnels = ngrok_response.json().get("tunnels", [])
        if not tunnels:
            logger.error("No ngrok tunnels found")
            sys.exit(1)
            
        # Find HTTPS tunnel
        https_tunnel = next((t for t in tunnels if t.get("proto") == "https"), None)
        if not https_tunnel:
            logger.error("No HTTPS ngrok tunnel found")
            sys.exit(1)
            
        public_url = https_tunnel.get("public_url")
        logger.info(f"Using ngrok tunnel: {public_url}")
        return public_url
    except Exception as e:
        logger.error(f"Error getting ngrok URL: {e}")
        sys.exit(1)


def get_bot_id(auth_token):
    """Get bot ID if not provided as argument."""
    if args.bot_id:
        return args.bot_id
        
    logger.info("Getting bot ID...")
    
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
            
        bot_id = bots[0]["id"]
        logger.info(f"Using bot ID: {bot_id}")
        return bot_id
    except Exception as e:
        logger.error(f"Error getting bot ID: {e}")
        sys.exit(1)


def test_telegram_api(token):
    """Test Telegram API connectivity."""
    logger.info("Testing Telegram API connectivity...")
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        
        if response.status_code != 200:
            logger.error(f"Failed to connect to Telegram API: {response.status_code} {response.text}")
            return False
            
        data = response.json()
        if not data.get("ok"):
            logger.error(f"Telegram API returned error: {data}")
            return False
            
        bot_info = data.get("result", {})
        logger.info(f"Connected to Telegram bot: @{bot_info.get('username')}")
        return True
    except Exception as e:
        logger.error(f"Error connecting to Telegram API: {e}")
        return False


def test_webhook_service(auth_token, bot_id, token):
    """Test webhook service functionality."""
    logger.info("Testing webhook service...")
    
    try:
        # Get ngrok URL for webhook
        ngrok_url = get_ngrok_url()
        webhook_url = f"{ngrok_url}/v1/api/webhook/telegram"
        
        # Test 1: Set webhook using the service
        logger.info("Test 1: Setting webhook...")
        
        set_response = requests.post(
            urljoin(BASE_URL, f"/v1/api/webhooks/telegram/{bot_id}/set"),
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"url": webhook_url, "drop_pending_updates": True},
            timeout=10
        )
        
        if set_response.status_code != 200:
            logger.error(f"Failed to set webhook: {set_response.status_code} {set_response.text}")
            return False
            
        logger.info("Successfully set webhook")
        
        # Test 2: Get webhook status
        logger.info("Test 2: Getting webhook status...")
        
        status_response = requests.get(
            urljoin(BASE_URL, f"/v1/api/webhooks/telegram/{bot_id}/status"),
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=5
        )
        
        if status_response.status_code != 200:
            logger.error(f"Failed to get webhook status: {status_response.status_code} {status_response.text}")
            return False
            
        status_data = status_response.json()
        current_url = status_data.get("url")
        logger.info(f"Current webhook URL: {current_url}")
        
        # Test 3: Delete webhook
        logger.info("Test 3: Deleting webhook...")
        
        delete_response = requests.delete(
            urljoin(BASE_URL, f"/v1/api/webhooks/telegram/{bot_id}"),
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=5
        )
        
        if delete_response.status_code != 204:
            logger.error(f"Failed to delete webhook: {delete_response.status_code} {delete_response.text}")
            return False
            
        logger.info("Successfully deleted webhook")
        
        # Test 4: Verify webhook was deleted
        logger.info("Test 4: Verifying webhook deletion...")
        
        status_after_delete = requests.get(
            urljoin(BASE_URL, f"/v1/api/webhooks/telegram/{bot_id}/status"),
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=5
        )
        
        if status_after_delete.status_code != 200:
            logger.error(f"Failed to get webhook status after deletion: {status_after_delete.status_code}")
            return False
            
        status_data = status_after_delete.json()
        current_url = status_data.get("url")
        
        if current_url:
            logger.warning(f"Webhook URL still present after deletion: {current_url}")
        else:
            logger.info("Webhook successfully deleted")
        
        return True
    except Exception as e:
        logger.error(f"Error in webhook service test: {e}")
        return False


def main():
    """Main function."""
    # Get token
    token = read_token_file()
    logger.info(f"Using token: {token[:5]}...{token[-4:]}")
    
    # Test Telegram API connectivity
    if not test_telegram_api(token):
        logger.error("Telegram API connectivity test failed")
        sys.exit(1)
    
    # Get authentication token
    auth_token = get_auth_token()
    
    # Get bot ID
    bot_id = get_bot_id(auth_token)
    
    # Test webhook service
    if test_webhook_service(auth_token, bot_id, token):
        logger.info("All webhook service tests passed!")
    else:
        logger.error("Webhook service tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()