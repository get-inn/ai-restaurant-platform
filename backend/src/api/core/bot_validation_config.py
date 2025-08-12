"""
Bot Input Validation Configuration

This module provides configuration settings for the bot input validation system,
allowing customization of validation behavior across different environments.
"""

from typing import Dict, Any
from pydantic import BaseModel
import os

class InputValidationConfig(BaseModel):
    # Duplicate detection
    duplicate_window_seconds: int = 2
    duplicate_cache_ttl: int = 10
    
    # Rate limiting
    max_requests_per_minute: int = 30
    rate_limit_window_seconds: int = 60
    
    # Button validation
    strict_button_validation: bool = True
    allow_case_insensitive_buttons: bool = False
    
    # Text validation
    max_text_length: int = 4000
    min_text_length: int = 0
    
    # Error messages
    duplicate_message: str = "⚠️ Please wait a moment before clicking again."
    rate_limit_message: str = "⚠️ You're sending messages too quickly. Please slow down."
    invalid_button_message: str = "Please choose one of the available options."
    wrong_input_type_message: str = "Please provide the correct type of input."
    
    # Behavior settings
    ignore_duplicates: bool = True  # Don't respond to duplicates
    resend_step_on_invalid: bool = True
    log_validation_events: bool = True

# Default configuration
DEFAULT_VALIDATION_CONFIG = InputValidationConfig()

# Environment-specific configurations
def get_validation_config() -> InputValidationConfig:
    """
    Get validation configuration based on current environment.
    """
    environment = os.environ.get("ENVIRONMENT", "development").lower()
    
    if environment == "development":
        return InputValidationConfig(
            duplicate_window_seconds=1,
            max_requests_per_minute=60,
            log_validation_events=True
        )
    elif environment == "production":
        return InputValidationConfig(
            duplicate_window_seconds=3,
            max_requests_per_minute=20,
            strict_button_validation=True,
            ignore_duplicates=True
        )
    elif environment == "testing":
        return InputValidationConfig(
            duplicate_window_seconds=0.1,
            max_requests_per_minute=1000,
            log_validation_events=False
        )
    else:
        return DEFAULT_VALIDATION_CONFIG

# Validation error messages mapping
VALIDATION_ERROR_MESSAGES = {
    "duplicate": {
        "message": "⚠️ I got your click! Please wait a moment.",
        "action": "ignore",  # Don't resend current step
        "delay": 0
    },
    "invalid_button": {
        "message": "Please choose one of these options:",
        "action": "resend_with_buttons",
        "delay": 0
    },
    "wrong_input_type": {
        "message": "I was expecting you to click a button. Let me show you the options:",
        "action": "resend_current_step",
        "delay": 0
    },
    "state_mismatch": {
        "message": "Something seems out of sync. Let me help you continue:",
        "action": "resend_current_step",
        "delay": 0
    },
    "rate_limited": {
        "message": "⚠️ You're going too fast! Please slow down a bit.",
        "action": "ignore",
        "delay": 2
    }
}