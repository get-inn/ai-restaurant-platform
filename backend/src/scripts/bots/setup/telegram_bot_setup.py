#!/usr/bin/env python3
"""
Telegram Bot Setup Script
-------------------------
Sets up a Telegram bot instance with the GetInn platform:
- Gets authentication token from the API
- Creates or finds an account
- Creates or finds a bot instance
- Sets up Telegram platform credentials
- Configures webhook for message delivery

Usage:
    python -m src.scripts.bots.setup.telegram_bot_setup [--debug]

Requirements:
    - telegram_token.txt file containing a valid Telegram bot token
    - Running API server (default: http://localhost:8000)
    - ngrok or other tunnel for webhook setup (automatically detected)
"""
import os
import sys
import json
import requests
import logging
import time
from urllib.parse import urljoin
from argparse import ArgumentParser
from pathlib import Path

# Set up argument parser
parser = ArgumentParser(description='Telegram Bot Setup Script')
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
args = parser.parse_args()

# Set up logging
log_level = logging.DEBUG if args.debug else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Base API URL and token file
BASE_URL = "http://localhost:8000"
# Use absolute paths
ROOT_DIR = Path(os.path.dirname(os.path.realpath(__file__))).parents[3]  # 4 levels up to reach backend/
TOKEN_FILE = str(ROOT_DIR / "telegram_token.txt")

# Custom request session to log API calls
class LoggingSession(requests.Session):
    """Custom session that logs all API calls for debugging"""
    
    def request(self, method, url, *args, **kwargs):
        # Log the request
        request_data = kwargs.get('json', kwargs.get('data', None))
        logger.info(f"\n=== REQUEST ===\n{method} {url}")
        if request_data:
            logger.info(f"Request Data: {json.dumps(request_data, indent=2)}")
            
        # Generate curl command for debugging
        curl_command = f"curl -X {method} '{url}'"
        headers = kwargs.get('headers', {})
        for key, value in headers.items():
            curl_command += f" -H '{key}: {value}'"
            
        if request_data:
            if isinstance(request_data, dict):
                curl_command += f" -d '{json.dumps(request_data)}'"
            else:
                curl_command += f" -d '{request_data}'"
                
        logger.info(f"CURL Equivalent: {curl_command}")
        
        # Make the actual request
        try:
            response = super().request(method, url, *args, **kwargs)
            
            # Log the response
            logger.info(f"\n=== RESPONSE ===\nStatus Code: {response.status_code}")
            try:
                response_data = response.json()
                logger.info(f"Response Data: {json.dumps(response_data, indent=2)}")
            except:
                logger.info(f"Response Text: {response.text}")
                
            return response
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
            
# Create a session with logging
session = LoggingSession()

class APIError(Exception):
    """Custom exception for API errors"""
    pass

def check_response(response, operation_name):
    """Check API response and handle errors appropriately"""
    if response.status_code in (200, 201):
        return True
    elif response.status_code in (401, 403):
        logger.error(f"Authentication error for {operation_name}: {response.text}")
        logger.error("Please check your authentication token and permissions.")
        return False
    elif response.status_code == 404:
        logger.error(f"Endpoint not found for {operation_name}: {response.text}")
        return False
    elif response.status_code == 500:
        logger.error(f"Server error for {operation_name}: {response.text}")
        logger.error("The API server encountered an internal error. Please check the server logs.")
        return False
    else:
        logger.error(f"Error during {operation_name}: {response.status_code} - {response.text}")
        return False

def read_token_file():
    """Read telegram token from file"""
    try:
        with open(TOKEN_FILE, "r") as f:
            token = f.read().strip()
            if not token:
                logger.error(f"Token file {TOKEN_FILE} is empty")
                sys.exit(1)
            return token
    except FileNotFoundError:
        logger.error(f"Token file {TOKEN_FILE} not found")
        sys.exit(1)

def with_retry(func, *args, max_retries=3, initial_delay=2, **kwargs):
    """Execute a function with retry logic"""
    retry_count = 0
    retry_delay = initial_delay
    last_error = None
    
    while retry_count < max_retries:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Attempt {retry_count} failed: {str(e)}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"All {max_retries} attempts failed. Last error: {str(e)}")
                break
    
    # If we get here, all retries failed
    if last_error:
        raise last_error
    else:
        raise APIError(f"Failed after {max_retries} attempts")

def get_auth_token():
    """Get a test authentication token"""
    url = urljoin(BASE_URL, "/v1/api/auth/test-token")
    try:
        response = session.post(url, json={}, timeout=5)
        
        if not check_response(response, "get_auth_token"):
            logger.error("Failed to get authentication token")
            sys.exit(1)
        
        token = response.json().get("access_token")
        if not token:
            logger.error("Auth token not found in the response")
            sys.exit(1)
            
        session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info("Successfully obtained auth token")
        return token
    except Exception as e:
        logger.error(f"Error getting authentication token: {str(e)}")
        sys.exit(1)

def get_direct_token():
    """Get a fresh authentication token using direct request"""
    try:
        auth_response = requests.post(
            urljoin(BASE_URL, "/v1/api/auth/test-token"),
            json={},
            timeout=5
        )
        
        if auth_response.status_code != 200:
            return None
            
        return auth_response.json().get("access_token")
    except Exception:
        return None

def get_account_by_name(account_name="Test Account"):
    """Get account with the specified name - if API fails, use default account ID"""
    try:
        url = urljoin(BASE_URL, "/v1/api/accounts")
        response = session.get(url, timeout=5)
        
        if not check_response(response, "get_accounts"):
            logger.warning("Failed to get accounts, using default account")
            return {"id": "00000000-0000-0000-0000-000000000001", "name": "Test Account"}
        
        accounts = response.json()
        for account in accounts:
            if account.get("name") == account_name:
                logger.info(f"Found account with name '{account_name}'")
                return account
        
        # If no account found with the name, create one
        logger.info(f"No account found with name '{account_name}', creating one")
        return create_account(account_name)
    except Exception as e:
        logger.warning(f"Could not get or create account: {e}")
        logger.info("Using default test account")
        return {"id": "00000000-0000-0000-0000-000000000001", "name": "Test Account"}

def create_account(name):
    """Create a new account with the specified name - handle errors gracefully"""
    try:
        url = urljoin(BASE_URL, "/v1/api/accounts")
        account_data = {
            "name": name,
            "description": "Created by Python API script"
        }
        
        response = session.post(url, json=account_data, timeout=5)
        
        if not check_response(response, "create_account"):
            logger.warning("Failed to create account, using default account")
            return {"id": "00000000-0000-0000-0000-000000000001", "name": "Test Account"}
            
        logger.info(f"Successfully created account '{name}'")
        return response.json()
    except Exception as e:
        logger.warning(f"Error creating account: {e}")
        logger.info("Using default test account")
        return {"id": "00000000-0000-0000-0000-000000000001", "name": "Test Account"}

def get_bot_instance(account_id):
    """Get bot instance for the specified account - handle API errors gracefully"""
    # First try with direct API call to handle connection issues
    logger.info("Getting a fresh authentication token for bot query...")
    direct_token = get_direct_token()
    
    if direct_token:
        logger.info("Successfully obtained direct authentication token for bot query")
        try:
            # Use direct requests call with fresh token
            headers = {"Authorization": f"Bearer {direct_token}"}
            bot_url = urljoin(BASE_URL, f"/v1/api/bots")
            direct_response = requests.get(
                bot_url, 
                params={"account_id": account_id}, 
                headers=headers,
                timeout=5
            )
            
            if direct_response.status_code == 200:
                bot_instances = direct_response.json()
                logger.info(f"Successfully got bots via direct API call. Found {len(bot_instances)} bot instance(s)")
                
                # Look for a bot named "Telegram Test Bot" or "Test Telegram Bot"
                for bot in bot_instances:
                    if bot.get("name") == "Telegram Test Bot" or bot.get("name") == "Test Telegram Bot":
                        logger.info(f"Found existing Telegram Test Bot with ID: {bot.get('id')}")
                        return bot
                
                # If no specifically named bot found but we have bots, return the first one
                if bot_instances:
                    logger.info(f"Using existing bot: {bot_instances[0].get('name')} ({bot_instances[0].get('id')})")
                    return bot_instances[0]
        except Exception as direct_e:
            logger.warning(f"Error with direct bot query: {direct_e}")
    
    # Fall back to original method if direct call fails
    try:
        url = urljoin(BASE_URL, f"/v1/api/bots")
        response = session.get(url, params={"account_id": account_id}, timeout=5)
        
        if not check_response(response, "get_bot_instances"):
            logger.warning("Failed to get bot instances")
            return None
            
        bot_instances = response.json()
        if not bot_instances:
            logger.info(f"No bot instances found for account {account_id}")
            return None
            
        logger.info(f"Found {len(bot_instances)} bot instance(s) for account {account_id}")
        
        # Look for a bot named "Telegram Test Bot" or "Test Telegram Bot"
        for bot in bot_instances:
            if bot.get("name") == "Telegram Test Bot" or bot.get("name") == "Test Telegram Bot":
                logger.info(f"Found existing Telegram Test Bot with ID: {bot.get('id')}")
                return bot
                
        # If no specifically named bot found, return first one
        return bot_instances[0]
    except Exception as e:
        logger.warning(f"Error getting bot instances: {e}")
        return None

def create_bot_instance(account_id):
    """Create a new bot instance for the account - handle errors gracefully"""
    # Double-check for existing bots before creating a new one
    logger.info("Double-checking for existing bots before creating new one...")
    direct_token = get_direct_token()
    
    if direct_token:
        try:
            # Use direct requests call with fresh token
            headers = {"Authorization": f"Bearer {direct_token}"}
            bot_url = urljoin(BASE_URL, f"/v1/api/bots")
            direct_response = requests.get(
                bot_url,
                params={"account_id": account_id},
                headers=headers,
                timeout=5
            )
            
            if direct_response.status_code == 200:
                bot_instances = direct_response.json()
                if bot_instances:
                    logger.info(f"Found existing bots via direct check - not creating a duplicate")
                    # Look for a Telegram Test Bot
                    for bot in bot_instances:
                        if bot.get("name") == "Telegram Test Bot" or bot.get("name") == "Test Telegram Bot":
                            logger.info(f"Found existing Telegram Test Bot with ID: {bot.get('id')}")
                            return bot
                    
                    # Return the first bot if no specific name match
                    logger.info(f"Using first available bot (ID: {bot_instances[0].get('id')}) instead of creating new one")
                    return bot_instances[0]
        except Exception as direct_e:
            logger.warning(f"Error with direct bot check: {direct_e}")
    
    # If we reach here, we need to create a new bot
    bot_data = {
        "name": "Telegram Test Bot",
        "description": "Test bot created via Python API script",
        "account_id": account_id
    }
    
    # Try with primary endpoint first
    try:
        url = urljoin(BASE_URL, f"/v1/api/accounts/{account_id}/bots")
        response = session.post(url, json=bot_data, timeout=5)
        
        if response.status_code in (200, 201):
            logger.info("Successfully created new bot instance")
            return response.json()
            
        # If primary endpoint fails, try alternative
        logger.warning(f"Failed with primary endpoint: {response.text}")
        logger.info("Trying alternative endpoint...")
        
        alt_url = urljoin(BASE_URL, f"/v1/api/bots")
        response = session.post(alt_url, json=bot_data, timeout=5)
        
        if response.status_code in (200, 201):
            logger.info("Successfully created new bot instance using alternative endpoint")
            return response.json()
        
        logger.error("Failed to create bot instance")
        return {"id": "placeholder-bot-id", "name": "Telegram Test Bot"}
    except Exception as e:
        logger.error(f"Failed to create bot instance: {str(e)}")
        return {"id": "placeholder-bot-id", "name": "Telegram Test Bot"}

def get_platform_credentials(bot_id):
    """Get platform credentials for the bot instance - handle API errors gracefully"""
    try:
        url = urljoin(BASE_URL, f"/v1/api/bots/{bot_id}/platforms")
        response = session.get(url, timeout=5)
        
        if not check_response(response, "get_platform_credentials"):
            logger.warning("Failed to get platform credentials")
            return None
            
        platform_credentials = response.json()
        telegram_credentials = next((p for p in platform_credentials if p.get("platform") == "telegram"), None)
        
        if telegram_credentials:
            logger.info("Found existing Telegram credentials")
        else:
            logger.info("No Telegram credentials found")
            
        return telegram_credentials
    except Exception as e:
        logger.warning(f"Error getting platform credentials: {e}")
        return None

def create_telegram_credentials(bot_id, token):
    """Create Telegram credentials for the bot - handle API errors gracefully"""
    try:
        url = urljoin(BASE_URL, f"/v1/api/bots/{bot_id}/platforms")
        cred_data = {
            "platform": "telegram",
            "credentials": {
                "token": token
            },
            "is_active": True
        }
        
        response = session.post(url, json=cred_data, timeout=5)
        
        if not check_response(response, "create_telegram_credentials"):
            logger.warning("Failed to create Telegram credentials")
            return {"id": "placeholder-platform-id"}
            
        logger.info("Successfully created Telegram credentials")
        return response.json()
    except Exception as e:
        logger.warning(f"Error creating Telegram credentials: {e}")
        return {"id": "placeholder-platform-id"}

def get_ngrok_url():
    """Get the current ngrok tunnel URL"""
    try:
        ngrok_info = json.loads(requests.get("http://localhost:4040/api/tunnels", timeout=5).text)
        for tunnel in ngrok_info.get("tunnels", []):
            if tunnel.get("proto") == "https":
                return tunnel.get("public_url")
    except Exception as e:
        logger.warning(f"Failed to get ngrok URL: {e}")
    
    return None

def set_telegram_webhook_direct(bot_token, webhook_url):
    """Set webhook directly with Telegram API - with rate limiting support"""
    telegram_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    telegram_data = {
        "url": webhook_url,
        "drop_pending_updates": True,
        "allowed_updates": ["message", "callback_query"]
    }
    
    # Try with retries for rate limiting
    max_retries = 3
    current_retry = 0
    
    while current_retry < max_retries:
        telegram_response = requests.post(telegram_url, json=telegram_data, timeout=10)
        
        # Check if successful
        if telegram_response.status_code == 200 and telegram_response.json().get("ok"):
            logger.info("Successfully set webhook via direct Telegram API call")
            return {
                "webhook_url": webhook_url,
                "status": "success",
                "message": "Set via direct Telegram API",
                "telegram_response": telegram_response.json()
            }
        
        # Check for rate limiting
        if telegram_response.status_code == 429:
            retry_after = 1
            try:
                response_data = telegram_response.json()
                if "parameters" in response_data and "retry_after" in response_data["parameters"]:
                    retry_after = response_data["parameters"]["retry_after"]
            except Exception:
                pass
            
            logger.warning(f"Rate limited by Telegram API. Waiting {retry_after} seconds before retry {current_retry + 1}/{max_retries}")
            time.sleep(retry_after + 0.5)  # Add a small buffer
            current_retry += 1
            continue
        
        # Other error - log and break
        logger.error(f"Direct Telegram API call failed: {telegram_response.status_code} - {telegram_response.text}")
        break
    
    return {
        "webhook_url": webhook_url,
        "status": "error",
        "message": "Failed to set webhook via direct Telegram API after retries"
    }

def set_ngrok_webhook(bot_id, platform_id, token):
    """Set ngrok webhook for the bot - handle API errors gracefully with fallback to direct Telegram API"""
    try:
        # Get ngrok URL for the webhook
        ngrok_url = get_ngrok_url()
        if not ngrok_url:
            logger.error("Failed to get webhook URL from ngrok")
            return {"webhook_url": "Error: No ngrok URL", "status": "error"}
        
        webhook_url = f"{ngrok_url}/v1/api/webhooks/telegram/{bot_id}"
        # Keep the simplified URL for reference, but we won't use it
        simple_webhook_url = f"{ngrok_url}/telegram"  # Simplified URL for direct Telegram API
        
        logger.info(f"Setting webhook URL to: {webhook_url}")
        
        # Try to set webhook using the API server endpoint
        url = urljoin(BASE_URL, f"/v1/api/webhooks/telegram/{bot_id}/set")
        webhook_data = {
            "url": webhook_url,
            "drop_pending_updates": True
        }
        
        response = session.post(url, json=webhook_data, timeout=10)
        api_server_success = response.status_code in [200, 201]
        
        # If API server call failed, try direct Telegram API call
        if not api_server_success:
            logger.info("API server webhook setup failed. Trying direct Telegram API call...")
            # Use the full API path instead of simplified one
            full_webhook_url = f"{ngrok_url}/v1/api/webhooks/telegram/{bot_id}"
            logger.info(f"Setting direct Telegram webhook to: {full_webhook_url}")
            
            return set_telegram_webhook_direct(token, full_webhook_url)
            
        # If API server was successful
        logger.info("Successfully set ngrok webhook via API server")
        result = response.json() if response.text and response.text != "null" else {}
        result["webhook_url"] = webhook_url
        result["status"] = "success"
        return result
            
    except Exception as e:
        logger.warning(f"Error setting webhook: {e}")
        return {"webhook_url": "Error setting webhook", "status": "error", "error": str(e)}

def check_and_set_bot_scenario(bot_id, force_reload=False):
    """Check if bot has a scenario attached and set default one if not
    
    Args:
        bot_id: The bot ID to check/update
        force_reload: If True, will reload the scenario even if one already exists
    
    Returns:
        bool: True if scenario is set successfully, False otherwise
    """
    try:
        # Check if the bot has an active scenario
        url = urljoin(BASE_URL, f"/v1/api/bots/{bot_id}/scenarios")
        logger.info(f"Checking if bot {bot_id} has an active scenario")
        
        response = session.get(url, params={"active_only": True}, timeout=5)
        
        if not check_response(response, "check_bot_scenarios"):
            logger.warning(f"Failed to check bot scenarios for bot {bot_id}")
            return False
            
        scenarios = response.json()
        
        if scenarios and len(scenarios) > 0 and not force_reload:
            logger.info(f"Bot already has {len(scenarios)} active scenario(s)")
            return True
        
        if scenarios and len(scenarios) > 0 and force_reload:
            # Deactivate existing scenarios before creating a new one
            logger.info("Deactivating existing scenarios before reload")
            for scenario in scenarios:
                scenario_id = scenario.get("id")
                deactivate_url = urljoin(BASE_URL, f"/v1/api/bots/{bot_id}/scenarios/{scenario_id}")
                deactivate_data = {"is_active": False}
                deactivate_response = session.patch(deactivate_url, json=deactivate_data, timeout=5)
                
                if not check_response(deactivate_response, "deactivate_scenario"):
                    logger.warning(f"Failed to deactivate scenario {scenario_id}")
            
            logger.info("Existing scenarios deactivated. Loading updated scenario.")
            
        # Read the onboarding scenario file
        scenario_path = ROOT_DIR / "docs" / "archive" / "onboarding_scenario.json"
        
        if not scenario_path.exists():
            logger.error(f"Scenario file not found at {scenario_path}")
            return False
            
        try:
            with open(scenario_path, "r", encoding="utf-8") as f:
                scenario_data = json.load(f)
                
            # Create a new scenario for the bot
            scenario_url = urljoin(BASE_URL, f"/v1/api/bots/{bot_id}/scenarios/upload")
            
            scenario_payload = {
                "file_content": json.dumps(scenario_data)
            }
            
            scenario_response = session.post(scenario_url, json=scenario_payload, timeout=10)
            
            if not check_response(scenario_response, "create_bot_scenario"):
                logger.warning("Failed to create default scenario")
                return False
                
            scenario_result = scenario_response.json()
            logger.info(f"Successfully created default scenario with ID: {scenario_result.get('id')}")
            return True
            
        except json.JSONDecodeError as je:
            logger.error(f"Error parsing scenario file: {je}")
            return False
        except Exception as e:
            logger.error(f"Error setting default scenario: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking/setting bot scenario: {e}")
        return False

def main():
    """Main function to run the script"""
    try:
        # Read telegram token from file
        telegram_token = read_token_file()
        logger.info("Telegram token loaded from file")
        
        # Get authentication token
        auth_token = get_auth_token()
        
        # Get account with name "Test Account"
        account = get_account_by_name()
        account_id = account["id"]
        
        # Get bot instance for this account
        bot_instance = get_bot_instance(account_id)
        
        # If no bot instance exists, create one
        if not bot_instance:
            bot_instance = create_bot_instance(account_id)
            
        bot_id = bot_instance["id"]
        
        # Check platform credentials for bot instance
        telegram_credentials = get_platform_credentials(bot_id)
        
        # If platform credentials don't exist, create them
        if not telegram_credentials:
            telegram_credentials = create_telegram_credentials(bot_id, telegram_token)
            platform_id = telegram_credentials["id"]
        else:
            platform_id = telegram_credentials["id"]
        
        # Check if bot has a scenario and set default if not, force reload the scenario to apply changes
        scenario_status = check_and_set_bot_scenario(bot_id, force_reload=True)
        
        # Set ngrok webhook for bot
        webhook_info = set_ngrok_webhook(bot_id, platform_id, telegram_token)
        
        logger.info("\n=== SUMMARY ===")
        logger.info(f"Account ID: {account_id}")
        logger.info(f"Bot ID: {bot_id}")
        logger.info(f"Platform ID: {platform_id}")
        logger.info(f"Scenario Status: {'✅ Active (Reloaded with updated documents_list step)' if scenario_status else '❌ Error setting up scenario'}")
        logger.info(f"Webhook URL: {webhook_info.get('webhook_url', 'Unknown')}")
        logger.info(f"Webhook Status: {webhook_info.get('status', 'Unknown')}")
    
    except Exception as e:
        logger.error(f"\n=== EXECUTION FAILED ===")
        logger.error(f"Error: {str(e)}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()