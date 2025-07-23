"""
iiko integration service.

This module provides high-level business logic for interacting with the iiko system.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session

from src.api.models.base import IntegrationType, SyncStatus
from src.api.services.integrations.credentials_service import CredentialsService
from src.integrations.pos_erp_adapters.iiko.iiko_auth import IikoAuth
from src.integrations.pos_erp_adapters.iiko.iiko_client import IikoClient
from src.integrations.pos_erp_adapters.iiko.iiko_sync import IikoSyncManager
from src.integrations.pos_erp_adapters.iiko.iiko_types import IikoConnectionStatus, IikoCredentials

logger = logging.getLogger(__name__)


class IikoIntegrationService:
    """Service for managing iiko integrations."""
    
    def __init__(self, db: Session):
        """
        Initialize the iiko integration service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.credentials_service = CredentialsService(db)
    
    async def connect_and_test(
        self,
        account_id: str,
        username: str,
        password: str,
        base_url: Optional[str] = None
    ) -> IikoConnectionStatus:
        """
        Test and save iiko connection credentials.
        
        Args:
            account_id: Account ID
            username: iiko username
            password: iiko password
            base_url: Optional custom base URL
        
        Returns:
            IikoConnectionStatus: Connection status
        """
        # Create auth manager with provided credentials
        auth = IikoAuth(base_url, username, password)
        
        # Test connection
        status = await auth.check_connection()
        
        # If connection successful, store credentials
        if status["is_connected"]:
            credentials = {
                "username": username,
                "password": password
            }
            
            try:
                credential_entity = self.credentials_service.store_credentials(
                    account_id=account_id,
                    integration_type=IntegrationType.IIKO,
                    credentials=credentials,
                    base_url=base_url
                )
                
                # Return connection status
                return IikoConnectionStatus(
                    account_id=account_id,
                    is_connected=True,
                    last_connected_at=auth.last_connected_at,
                    connection_error=None,
                    integration_type=IntegrationType.IIKO
                )
                
            except Exception as e:
                logger.error(f"Failed to store iiko credentials: {str(e)}")
                return IikoConnectionStatus(
                    account_id=account_id,
                    is_connected=False,
                    last_connected_at=None,
                    connection_error=f"Failed to store credentials: {str(e)}",
                    integration_type=IntegrationType.IIKO
                )
        
        # Connection failed
        return IikoConnectionStatus(
            account_id=account_id,
            is_connected=False,
            last_connected_at=None,
            connection_error=status["connection_error"],
            integration_type=IntegrationType.IIKO
        )
    
    async def get_connection_status(self, account_id: str) -> IikoConnectionStatus:
        """
        Get current iiko connection status for an account.
        
        Args:
            account_id: Account ID
        
        Returns:
            IikoConnectionStatus: Connection status
        """
        # Get credentials
        credential_entity, credentials = self.credentials_service.get_credentials(
            account_id=account_id,
            integration_type=IntegrationType.IIKO
        )
        
        if not credential_entity:
            return IikoConnectionStatus(
                account_id=account_id,
                is_connected=False,
                last_connected_at=None,
                connection_error="No iiko integration configured for this account",
                integration_type=IntegrationType.IIKO
            )
        
        # If credentials couldn't be decrypted
        if not credentials:
            return IikoConnectionStatus(
                account_id=account_id,
                is_connected=False,
                last_connected_at=credential_entity.last_connected_at,
                connection_error="Failed to decrypt credentials",
                integration_type=IntegrationType.IIKO
            )
        
        # Test connection
        auth = IikoAuth(
            base_url=credential_entity.base_url,
            username=credentials.get("username"),
            password=credentials.get("password")
        )
        
        status = await auth.check_connection()
        
        # Update connection status in database
        self.credentials_service.update_connection_status(
            credential_id=str(credential_entity.id),
            is_connected=status["is_connected"],
            error_message=status["connection_error"]
        )
        
        # Return status
        return IikoConnectionStatus(
            account_id=account_id,
            is_connected=status["is_connected"],
            last_connected_at=auth.last_connected_at if status["is_connected"] else None,
            connection_error=status["connection_error"],
            integration_type=IntegrationType.IIKO
        )
    
    async def sync_restaurants(self, account_id: str) -> Dict[str, Any]:
        """
        Synchronize restaurants from iiko for an account.
        
        Args:
            account_id: Account ID
        
        Returns:
            Dict[str, Any]: Sync results
        """
        # Get credentials and create client
        sync_manager = self._create_sync_manager(account_id)
        if not sync_manager:
            return {
                "status": "error",
                "message": "Failed to initialize sync manager",
                "details": "No valid credentials found for this account"
            }
        
        # Perform sync
        try:
            results = await sync_manager.sync_restaurants()
            return {
                "status": "success",
                "message": f"Synchronized {results['created'] + results['updated']} restaurants",
                "details": results
            }
        except Exception as e:
            logger.error(f"Failed to sync restaurants: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to sync restaurants: {str(e)}",
                "details": None
            }
    
    async def sync_stores(self, account_id: str) -> Dict[str, Any]:
        """
        Synchronize stores from iiko for an account.
        
        Args:
            account_id: Account ID
        
        Returns:
            Dict[str, Any]: Sync results
        """
        # Get credentials and create client
        sync_manager = self._create_sync_manager(account_id)
        if not sync_manager:
            return {
                "status": "error",
                "message": "Failed to initialize sync manager",
                "details": "No valid credentials found for this account"
            }
        
        # Perform sync
        try:
            results = await sync_manager.sync_stores()
            return {
                "status": "success",
                "message": f"Synchronized {results['created'] + results['updated']} stores",
                "details": results
            }
        except Exception as e:
            logger.error(f"Failed to sync stores: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to sync stores: {str(e)}",
                "details": None
            }
    
    async def sync_suppliers(self, account_id: str) -> Dict[str, Any]:
        """
        Synchronize suppliers from iiko for an account.
        
        Args:
            account_id: Account ID
        
        Returns:
            Dict[str, Any]: Sync results
        """
        # Get credentials and create client
        sync_manager = self._create_sync_manager(account_id)
        if not sync_manager:
            return {
                "status": "error",
                "message": "Failed to initialize sync manager",
                "details": "No valid credentials found for this account"
            }
        
        # Perform sync
        try:
            results = await sync_manager.sync_suppliers()
            return {
                "status": "success",
                "message": f"Synchronized {results['created'] + results['updated']} suppliers",
                "details": results
            }
        except Exception as e:
            logger.error(f"Failed to sync suppliers: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to sync suppliers: {str(e)}",
                "details": None
            }
    
    async def sync_invoices(
        self,
        account_id: str,
        restaurant_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Synchronize invoices from iiko for an account and restaurant.
        
        Args:
            account_id: Account ID
            restaurant_id: Restaurant ID
            days_back: Number of days to look back
        
        Returns:
            Dict[str, Any]: Sync results
        """
        # Get credentials and create client
        sync_manager = self._create_sync_manager(account_id)
        if not sync_manager:
            return {
                "status": "error",
                "message": "Failed to initialize sync manager",
                "details": "No valid credentials found for this account"
            }
        
        # Calculate date range
        from_date = datetime.now() - timedelta(days=days_back)
        to_date = datetime.now()
        
        # Perform sync
        try:
            results = await sync_manager.sync_invoices(
                restaurant_id=restaurant_id,
                from_date=from_date,
                to_date=to_date
            )
            return {
                "status": "success",
                "message": f"Synchronized {results['created'] + results['updated']} invoices",
                "details": results
            }
        except Exception as e:
            logger.error(f"Failed to sync invoices: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to sync invoices: {str(e)}",
                "details": None
            }
    
    def _create_sync_manager(self, account_id: str) -> Optional[IikoSyncManager]:
        """
        Create an IikoSyncManager for an account.
        
        Args:
            account_id: Account ID
        
        Returns:
            Optional[IikoSyncManager]: Sync manager or None if creation fails
        """
        try:
            # Get credentials
            credential_entity, credentials = self.credentials_service.get_credentials(
                account_id=account_id,
                integration_type=IntegrationType.IIKO
            )
            
            if not credential_entity or not credentials:
                logger.error(f"No valid credentials found for account {account_id}")
                return None
            
            # Create auth manager
            auth = IikoAuth(
                base_url=credential_entity.base_url,
                username=credentials.get("username"),
                password=credentials.get("password")
            )
            
            # Create client
            client = IikoClient(auth_manager=auth)
            
            # Create and return sync manager
            return IikoSyncManager(
                db=self.db,
                account_id=account_id,
                iiko_client=client,
                credential_id=str(credential_entity.id)
            )
            
        except Exception as e:
            logger.error(f"Failed to create sync manager: {str(e)}")
            return None