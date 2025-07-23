"""
Credentials service for managing integration credentials.

This module provides functionality to securely store, retrieve, and manage
credentials for external system integrations.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.api.models import AccountIntegrationCredentials
from src.api.models.base import IntegrationType
from src.api.services.integrations.encryption_service import encryption_service

logger = logging.getLogger(__name__)


class CredentialsService:
    """Service for managing integration credentials."""
    
    def __init__(self, db: Session):
        """
        Initialize the credentials service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def store_credentials(
        self,
        account_id: str,
        integration_type: str,
        credentials: Dict[str, Any],
        base_url: Optional[str] = None
    ) -> AccountIntegrationCredentials:
        """
        Store integration credentials for an account.
        
        Args:
            account_id: Account ID
            integration_type: Type of integration (e.g., "iiko")
            credentials: Credentials dictionary
            base_url: Optional custom base URL for the integration
        
        Returns:
            AccountIntegrationCredentials: Stored credentials entity
        
        Raises:
            ValueError: If encryption fails
        """
        # Encrypt the credentials
        encrypted = encryption_service.encrypt(credentials)
        if not encrypted:
            raise ValueError("Failed to encrypt credentials")
        
        # Check if credentials already exist
        existing = self.db.query(AccountIntegrationCredentials).filter(
            and_(
                AccountIntegrationCredentials.account_id == account_id,
                AccountIntegrationCredentials.integration_type == integration_type
            )
        ).first()
        
        if existing:
            # Update existing credentials
            existing.credentials = encrypted
            existing.base_url = base_url
            existing.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new credentials
        new_credentials = AccountIntegrationCredentials(
            id=uuid.uuid4(),
            account_id=account_id,
            integration_type=integration_type,
            credentials=encrypted,
            base_url=base_url,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.db.add(new_credentials)
        self.db.commit()
        self.db.refresh(new_credentials)
        
        return new_credentials
    
    def get_credentials(
        self,
        account_id: str,
        integration_type: str,
        credential_id: Optional[str] = None,
        decrypt: bool = True
    ) -> Tuple[Optional[AccountIntegrationCredentials], Optional[Dict[str, Any]]]:
        """
        Get integration credentials for an account.
        
        Args:
            account_id: Account ID
            integration_type: Type of integration
            credential_id: Optional specific credential ID
            decrypt: Whether to decrypt the credentials
        
        Returns:
            Tuple[Optional[AccountIntegrationCredentials], Optional[Dict[str, Any]]]:
                Credential entity and decrypted credentials dictionary
        """
        # Build query
        query = self.db.query(AccountIntegrationCredentials).filter(
            and_(
                AccountIntegrationCredentials.account_id == account_id,
                AccountIntegrationCredentials.integration_type == integration_type,
                AccountIntegrationCredentials.is_active == True
            )
        )
        
        # Filter by specific ID if provided
        if credential_id:
            query = query.filter(AccountIntegrationCredentials.id == credential_id)
        
        # Get the first matching credential
        credential = query.first()
        
        if not credential:
            return None, None
        
        # Return credential without decryption if requested
        if not decrypt:
            return credential, None
        
        # Decrypt credentials
        decrypted = encryption_service.decrypt(credential.credentials)
        
        # Verify that decryption was successful
        if decrypted is None:
            logger.error(f"Failed to decrypt credentials for account {account_id}, integration {integration_type}")
            return credential, None
        
        # Ensure we have a dictionary
        if not isinstance(decrypted, dict):
            logger.error(f"Decrypted credentials for account {account_id} are not a dictionary")
            return credential, None
        
        return credential, decrypted
    
    def update_connection_status(
        self,
        credential_id: str,
        is_connected: bool,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update the connection status of integration credentials.
        
        Args:
            credential_id: Credential ID
            is_connected: Whether the connection was successful
            error_message: Optional error message
        
        Returns:
            bool: True if successful, False otherwise
        """
        credential = self.db.query(AccountIntegrationCredentials).get(credential_id)
        
        if not credential:
            logger.error(f"Credential with ID {credential_id} not found")
            return False
        
        # Update the status
        credential.last_connected_at = datetime.now() if is_connected else None
        credential.connection_status = "connected" if is_connected else "error"
        credential.connection_error = error_message
        credential.updated_at = datetime.now()
        
        try:
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating connection status: {str(e)}")
            return False
    
    def list_credentials(self, account_id: str) -> List[AccountIntegrationCredentials]:
        """
        List all integration credentials for an account.
        
        Args:
            account_id: Account ID
        
        Returns:
            List[AccountIntegrationCredentials]: List of credential entities
        """
        return self.db.query(AccountIntegrationCredentials).filter(
            AccountIntegrationCredentials.account_id == account_id
        ).all()
    
    def delete_credentials(self, credential_id: str) -> bool:
        """
        Delete integration credentials.
        
        Args:
            credential_id: Credential ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        credential = self.db.query(AccountIntegrationCredentials).get(credential_id)
        
        if not credential:
            logger.error(f"Credential with ID {credential_id} not found")
            return False
        
        try:
            self.db.delete(credential)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting credentials: {str(e)}")
            return False