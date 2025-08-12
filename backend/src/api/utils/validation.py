"""
Shared validation utilities.
Consolidates common validation patterns used across the API.
"""
import json
import re
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from fastapi import HTTPException, status

from src.api.core.exceptions import BadRequestError


def validate_uuid_string(value: str, field_name: str = "ID") -> UUID:
    """
    Validate and convert a string to UUID.
    
    Args:
        value: String to validate and convert
        field_name: Name of the field for error messages
        
    Returns:
        UUID object
        
    Raises:
        BadRequestError: If value is not a valid UUID
    """
    try:
        return UUID(value)
    except (ValueError, TypeError):
        raise BadRequestError(detail=f"Invalid {field_name} format. Must be a valid UUID.")


def validate_json_data(
    json_string: str, 
    max_size_kb: int = 100,
    required_fields: List[str] = None
) -> Dict[str, Any]:
    """
    Validate and parse JSON string with size and structure checks.
    
    Args:
        json_string: JSON string to validate
        max_size_kb: Maximum allowed size in KB
        required_fields: List of required top-level fields
        
    Returns:
        Parsed JSON data
        
    Raises:
        BadRequestError: If JSON is invalid or doesn't meet requirements
    """
    # Check size
    size_kb = len(json_string.encode('utf-8')) / 1024
    if size_kb > max_size_kb:
        raise BadRequestError(detail=f"JSON data too large. Maximum size: {max_size_kb}KB")
    
    # Parse JSON
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise BadRequestError(detail=f"Invalid JSON format: {str(e)}")
    
    # Check required fields
    if required_fields and isinstance(data, dict):
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequestError(
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
    
    return data


def validate_platform_name(platform: str) -> str:
    """
    Validate platform name format.
    
    Args:
        platform: Platform name to validate
        
    Returns:
        Validated platform name
        
    Raises:
        BadRequestError: If platform name is invalid
    """
    # Normalize to lowercase
    platform = platform.lower().strip()
    
    # Check format
    if not re.match(r'^[a-z][a-z0-9_-]*$', platform):
        raise BadRequestError(
            detail="Platform name must start with a letter and contain only lowercase letters, numbers, underscores, and hyphens"
        )
    
    # Check length
    if len(platform) < 2 or len(platform) > 50:
        raise BadRequestError(
            detail="Platform name must be between 2 and 50 characters"
        )
    
    return platform


def validate_bot_name(name: str) -> str:
    """
    Validate bot name format.
    
    Args:
        name: Bot name to validate
        
    Returns:
        Validated bot name
        
    Raises:
        BadRequestError: If bot name is invalid
    """
    name = name.strip()
    
    if not name:
        raise BadRequestError(detail="Bot name cannot be empty")
    
    if len(name) < 1 or len(name) > 100:
        raise BadRequestError(detail="Bot name must be between 1 and 100 characters")
    
    # Check for potentially problematic characters
    if re.search(r'[<>\"\'&]', name):
        raise BadRequestError(detail="Bot name contains invalid characters")
    
    return name


def validate_scenario_data(scenario_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate bot scenario data structure.
    
    Args:
        scenario_data: Scenario data to validate
        
    Returns:
        Validated scenario data
        
    Raises:
        BadRequestError: If scenario data is invalid
    """
    if not isinstance(scenario_data, dict):
        raise BadRequestError(detail="Scenario data must be a JSON object")
    
    # Check required top-level fields
    required_fields = ["steps"]
    missing_fields = [field for field in required_fields if field not in scenario_data]
    if missing_fields:
        raise BadRequestError(
            detail=f"Scenario missing required fields: {', '.join(missing_fields)}"
        )
    
    # Validate steps structure
    steps = scenario_data.get("steps", {})
    if not isinstance(steps, dict):
        raise BadRequestError(detail="Scenario 'steps' must be a JSON object")
    
    if not steps:
        raise BadRequestError(detail="Scenario must have at least one step")
    
    # Validate each step
    for step_id, step_data in steps.items():
        if not isinstance(step_data, dict):
            raise BadRequestError(detail=f"Step '{step_id}' must be a JSON object")
        
        # Check required step fields
        if "type" not in step_data:
            raise BadRequestError(detail=f"Step '{step_id}' missing required 'type' field")
        
        step_type = step_data.get("type")
        if step_type not in ["message", "conditional_message", "action"]:
            raise BadRequestError(
                detail=f"Step '{step_id}' has invalid type '{step_type}'. "
                       f"Must be one of: message, conditional_message, action"
            )
    
    return scenario_data


def validate_credentials(credentials: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """
    Validate platform credentials structure.
    
    Args:
        credentials: Credentials dictionary to validate
        platform: Platform name for platform-specific validation
        
    Returns:
        Validated credentials
        
    Raises:
        BadRequestError: If credentials are invalid
    """
    if not isinstance(credentials, dict):
        raise BadRequestError(detail="Credentials must be a JSON object")
    
    # Platform-specific validation
    if platform == "telegram":
        if "api_token" not in credentials:
            raise BadRequestError(detail="Telegram credentials must include 'api_token'")
        
        api_token = credentials.get("api_token", "").strip()
        if not api_token:
            raise BadRequestError(detail="Telegram API token cannot be empty")
        
        # Basic Telegram token format validation
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', api_token):
            raise BadRequestError(detail="Invalid Telegram API token format")
    
    return credentials


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input by removing potentially dangerous content.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        BadRequestError: If string is too long
    """
    if not isinstance(value, str):
        return str(value)
    
    # Trim whitespace
    value = value.strip()
    
    # Check length
    if len(value) > max_length:
        raise BadRequestError(detail=f"Text too long. Maximum length: {max_length} characters")
    
    # Remove control characters except newlines and tabs
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t')
    
    return value


def validate_pagination_params(skip: int, limit: int, max_limit: int = 1000) -> tuple[int, int]:
    """
    Validate pagination parameters.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        max_limit: Maximum allowed limit
        
    Returns:
        Tuple of validated (skip, limit)
        
    Raises:
        BadRequestError: If parameters are invalid
    """
    if skip < 0:
        raise BadRequestError(detail="Skip parameter cannot be negative")
    
    if limit <= 0:
        raise BadRequestError(detail="Limit parameter must be positive")
    
    if limit > max_limit:
        raise BadRequestError(detail=f"Limit parameter cannot exceed {max_limit}")
    
    return skip, limit