"""
iiko authentication module.

This module handles authentication with the iiko API, including token retrieval and renewal.
"""

import time
import logging
from datetime import datetime
import httpx
from typing import Dict, Optional, Tuple

from src.api.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class IikoAuth:
    """
    Handles authentication with the iiko API.
    
    This class manages token retrieval, caching, and renewal for the iiko API.
    It supports both global and account-specific credentials.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize the authentication manager.
        
        Args:
            base_url: Optional override for the base URL
            username: Optional username for direct authentication
            password: Optional password for direct authentication
        """
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = 0  # Unix timestamp when token expires
        self.last_connected_at = None
        self.connection_error = None
    
    async def get_token(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Get a valid authentication token.
        
        If a cached token is available and not expired, return it.
        Otherwise, retrieve a new token.
        
        Returns:
            Tuple[Optional[str], Optional[str]]: (token, error_message)
        """
        current_time = time.time()
        
        # If token exists and is not expired, return it
        if self.token and current_time < self.token_expiry:
            return self.token, None
        
        # Otherwise, retrieve a new token
        return await self._retrieve_token()
    
    async def _retrieve_token(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieve a new authentication token from the iiko API.
        
        Returns:
            Tuple[Optional[str], Optional[str]]: (token, error_message)
        """
        if not self.username or not self.password:
            return None, "Missing credentials"
        
        auth_url = f"{self.base_url}/resto/api/auth"
        payload = {"login": self.username, "pass": self.password}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    auth_url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                
                response.raise_for_status()
                token = response.text.strip()
                
                if not token:
                    self.connection_error = "Empty token received"
                    return None, self.connection_error
                
                # Store the token with expiry time (default: 1 hour)
                self.token = token
                self.token_expiry = time.time() + settings.DEFAULT_TOKEN_REFRESH_INTERVAL
                self.last_connected_at = datetime.now()
                self.connection_error = None
                
                return token, None
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error during authentication: {e.response.status_code}"
            self.connection_error = error_msg
            logger.error(f"{error_msg}: {e.response.text}")
            return None, error_msg
            
        except httpx.RequestError as e:
            error_msg = f"Network error during authentication: {str(e)}"
            self.connection_error = error_msg
            logger.error(error_msg)
            return None, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error during authentication: {str(e)}"
            self.connection_error = error_msg
            logger.error(error_msg)
            return None, error_msg
    
    async def check_connection(self) -> Dict:
        """
        Check connection to iiko API by attempting to retrieve a token.
        
        Returns:
            Dict: Connection status information
        """
        token, error = await self._retrieve_token()
        
        return {
            "is_connected": token is not None,
            "last_connected_at": self.last_connected_at,
            "connection_error": error,
        }
    
    async def clear_token(self) -> None:
        """Clear the stored token."""
        self.token = None
        self.token_expiry = 0