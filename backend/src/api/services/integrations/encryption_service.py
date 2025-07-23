"""
Encryption service for securely storing and retrieving integration credentials.

This module provides functionality to encrypt and decrypt sensitive information
like integration credentials before storing them in the database.
"""

import base64
import json
import logging
from typing import Dict, Any, Optional, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.api.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    
    Uses AES-256-GCM encryption for secure storage of integration credentials.
    """
    
    def __init__(self, key: Optional[str] = None, nonce: Optional[str] = None):
        """
        Initialize the encryption service.
        
        Args:
            key: Optional encryption key (base64 encoded)
            nonce: Optional nonce value (base64 encoded)
        """
        # Use provided values or get from settings
        self.key = key or settings.CREDENTIAL_ENCRYPTION_KEY
        self.nonce = nonce or settings.CREDENTIAL_ENCRYPTION_NONCE
        
        if not self.key:
            logger.warning("No encryption key provided or found in settings")
            self._aesgcm = None
            self._nonce_bytes = None
            return
        
        try:
            # Convert key and nonce from base64 to bytes
            key_bytes = base64.b64decode(self.key)
            self._nonce_bytes = base64.b64decode(self.nonce) if self.nonce else b'0' * 12  # Default nonce if none provided
            
            # Initialize AES-GCM cipher
            self._aesgcm = AESGCM(key_bytes)
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {str(e)}")
            self._aesgcm = None
            self._nonce_bytes = None
    
    def encrypt(self, data: Union[str, Dict[str, Any]]) -> Optional[str]:
        """
        Encrypt data using AES-GCM.
        
        Args:
            data: String or dictionary to encrypt
        
        Returns:
            Optional[str]: Base64-encoded encrypted data, or None if encryption fails
        """
        if not self._aesgcm:
            logger.error("Encryption service not properly initialized")
            return None
        
        try:
            # Convert dict to JSON string if needed
            if isinstance(data, dict):
                data = json.dumps(data)
            
            # Encrypt the data
            encrypted = self._aesgcm.encrypt(
                self._nonce_bytes,
                data.encode('utf-8'),
                None  # No additional data
            )
            
            # Return as base64 string
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            return None
    
    def decrypt(self, encrypted_data: str) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Decrypt AES-GCM encrypted data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
        
        Returns:
            Optional[Union[str, Dict[str, Any]]]: Decrypted data, or None if decryption fails
        """
        if not self._aesgcm:
            logger.error("Encryption service not properly initialized")
            return None
        
        try:
            # Convert from base64 to bytes
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Decrypt the data
            decrypted = self._aesgcm.decrypt(
                self._nonce_bytes,
                encrypted_bytes,
                None  # No additional data
            )
            
            # Convert bytes to string
            decrypted_str = decrypted.decode('utf-8')
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                # Return as string if not valid JSON
                return decrypted_str
                
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            return None
    
    @staticmethod
    def generate_key() -> Dict[str, str]:
        """
        Generate a new encryption key and nonce.
        
        Returns:
            Dict[str, str]: Dictionary with base64-encoded key and nonce
        """
        # Generate a random key
        key = AESGCM.generate_key(bit_length=256)
        
        # Generate a random nonce
        nonce = AESGCM.generate_key(bit_length=96)[:12]  # 12 bytes for nonce
        
        return {
            "key": base64.b64encode(key).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8')
        }


# Create a singleton instance
encryption_service = EncryptionService()