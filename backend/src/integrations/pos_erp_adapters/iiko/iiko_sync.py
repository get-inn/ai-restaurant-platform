"""
iiko synchronization manager module.

This module orchestrates data synchronization between iiko and the internal system.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session

from .iiko_client import IikoClient
from .iiko_auth import IikoAuth
from .iiko_adapters import (
    adapt_iiko_restaurant_to_internal,
    adapt_iiko_store_to_internal,
    adapt_iiko_supplier_to_internal,
    adapt_iiko_invoice_to_internal,
)
from src.api.models import (
    Restaurant, 
    Store, 
    Supplier, 
    Invoice, 
    InvoiceItem,
    Unit,
    AccountIntegrationCredentials
)
from src.api.models.base import SyncStatus

logger = logging.getLogger(__name__)


class IikoSyncManager:
    """
    Manager for synchronizing data between iiko and the internal system.
    
    This class handles the orchestration of data synchronization, including:
    - Restaurants (departments)
    - Stores
    - Suppliers
    - Invoices
    """
    
    def __init__(
        self, 
        db: Session,
        account_id: str,
        iiko_client: Optional[IikoClient] = None,
        credential_id: Optional[str] = None
    ):
        """
        Initialize the synchronization manager.
        
        Args:
            db: Database session
            account_id: Internal account ID
            iiko_client: Optional pre-configured IikoClient instance
            credential_id: Optional specific credential ID to use
        """
        self.db = db
        self.account_id = account_id
        
        # If client isn't provided, create one using account credentials
        if not iiko_client:
            auth = self._load_auth_from_credentials(credential_id)
            self.client = IikoClient(auth_manager=auth)
        else:
            self.client = iiko_client
    
    def _load_auth_from_credentials(self, credential_id: Optional[str] = None) -> IikoAuth:
        """
        Load iiko authentication manager from account credentials.
        
        Args:
            credential_id: Optional specific credential ID to use
            
        Returns:
            IikoAuth: Authentication manager
            
        Raises:
            Exception: If credentials cannot be loaded
        """
        try:
            # Query for credentials
            query = self.db.query(AccountIntegrationCredentials).filter(
                AccountIntegrationCredentials.account_id == self.account_id,
                AccountIntegrationCredentials.integration_type == "iiko",
                AccountIntegrationCredentials.is_active == True
            )
            
            # If specific credential ID is provided, filter by it
            if credential_id:
                query = query.filter(AccountIntegrationCredentials.id == credential_id)
            
            # Get the first matching credential
            credential = query.first()
            
            if not credential:
                raise Exception(f"No active iiko credentials found for account {self.account_id}")
            
            # Extract credential details (in a real implementation, these would be decrypted)
            username = credential.credentials.get("username")
            password = credential.credentials.get("password")
            base_url = credential.base_url
            
            if not username or not password:
                raise Exception("Invalid credentials: missing username or password")
            
            # Create and return auth manager
            return IikoAuth(base_url, username, password)
            
        except Exception as e:
            logger.error(f"Error loading iiko credentials: {str(e)}")
            raise
    
    async def sync_restaurants(self) -> Dict[str, Any]:
        """
        Synchronize restaurants from iiko.
        
        Returns:
            Dict[str, Any]: Sync results
        """
        try:
            # Get restaurants from iiko
            iiko_restaurants = await self.client.get_restaurants()
            
            # Track results
            results = {
                "total": len(iiko_restaurants),
                "created": 0,
                "updated": 0,
                "errors": 0,
                "error_details": []
            }
            
            # Process each restaurant
            for iiko_data in iiko_restaurants:
                try:
                    # Skip inactive restaurants
                    if not iiko_data.get("isActive", True):
                        continue
                    
                    # Convert to internal format
                    iiko_restaurant, internal_attrs = adapt_iiko_restaurant_to_internal(
                        iiko_data, 
                        self.account_id
                    )
                    
                    # Check if restaurant exists
                    restaurant = self.db.query(Restaurant).filter(
                        Restaurant.external_id == iiko_restaurant.iiko_id,
                        Restaurant.external_system_type == "iiko",
                        Restaurant.account_id == self.account_id
                    ).first()
                    
                    if restaurant:
                        # Update existing restaurant
                        for key, value in internal_attrs.items():
                            setattr(restaurant, key, value)
                        results["updated"] += 1
                    else:
                        # Create new restaurant
                        restaurant = Restaurant(**internal_attrs)
                        self.db.add(restaurant)
                        results["created"] += 1
                    
                    # Commit changes for this restaurant
                    self.db.commit()
                    
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Error syncing restaurant {iiko_data.get('id')}: {str(e)}")
                    results["errors"] += 1
                    results["error_details"].append({
                        "entity_id": iiko_data.get("id"),
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in restaurant synchronization: {str(e)}")
            return {
                "total": 0,
                "created": 0,
                "updated": 0,
                "errors": 1,
                "error_details": [{"error": str(e)}]
            }
    
    async def sync_stores(self) -> Dict[str, Any]:
        """
        Synchronize stores from iiko.
        
        Returns:
            Dict[str, Any]: Sync results
        """
        try:
            # Get stores from iiko
            iiko_stores = await self.client.get_stores()
            
            # Track results
            results = {
                "total": len(iiko_stores),
                "created": 0,
                "updated": 0,
                "errors": 0,
                "error_details": []
            }
            
            # Process each store
            for iiko_data in iiko_stores:
                try:
                    # Skip inactive stores
                    if not iiko_data.get("isActive", True):
                        continue
                    
                    # Find matching restaurant based on department ID
                    department_id = iiko_data.get("departmentId")
                    if not department_id:
                        continue
                    
                    restaurant = self.db.query(Restaurant).filter(
                        Restaurant.external_id == department_id,
                        Restaurant.external_system_type == "iiko",
                        Restaurant.account_id == self.account_id
                    ).first()
                    
                    if not restaurant:
                        results["errors"] += 1
                        results["error_details"].append({
                            "entity_id": iiko_data.get("id"),
                            "error": f"Restaurant with iiko_id {department_id} not found"
                        })
                        continue
                    
                    # Convert to internal format
                    iiko_store, internal_attrs = adapt_iiko_store_to_internal(
                        iiko_data, 
                        str(restaurant.id)
                    )
                    
                    # Check if store exists
                    store = self.db.query(Store).filter(
                        Store.external_id == iiko_store.iiko_id,
                        Store.external_system_type == "iiko",
                        Store.restaurant_id == restaurant.id
                    ).first()
                    
                    if store:
                        # Update existing store
                        for key, value in internal_attrs.items():
                            setattr(store, key, value)
                        results["updated"] += 1
                    else:
                        # Create new store
                        store = Store(**internal_attrs)
                        self.db.add(store)
                        results["created"] += 1
                    
                    # Commit changes for this store
                    self.db.commit()
                    
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Error syncing store {iiko_data.get('id')}: {str(e)}")
                    results["errors"] += 1
                    results["error_details"].append({
                        "entity_id": iiko_data.get("id"),
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in store synchronization: {str(e)}")
            return {
                "total": 0,
                "created": 0,
                "updated": 0,
                "errors": 1,
                "error_details": [{"error": str(e)}]
            }
    
    async def sync_suppliers(self) -> Dict[str, Any]:
        """
        Synchronize suppliers from iiko.
        
        Returns:
            Dict[str, Any]: Sync results
        """
        try:
            # Get suppliers from iiko
            iiko_suppliers = await self.client.get_suppliers()
            
            # Track results
            results = {
                "total": len(iiko_suppliers),
                "created": 0,
                "updated": 0,
                "errors": 0,
                "error_details": []
            }
            
            # Process each supplier
            for iiko_data in iiko_suppliers:
                try:
                    # Skip inactive suppliers
                    if not iiko_data.get("isActive", True):
                        continue
                    
                    # Convert to internal format
                    iiko_supplier, internal_attrs = adapt_iiko_supplier_to_internal(
                        iiko_data, 
                        self.account_id
                    )
                    
                    # Check if supplier exists
                    supplier = self.db.query(Supplier).filter(
                        Supplier.external_id == iiko_supplier.iiko_id,
                        Supplier.external_system_type == "iiko",
                        Supplier.account_id == self.account_id
                    ).first()
                    
                    if supplier:
                        # Update existing supplier
                        for key, value in internal_attrs.items():
                            setattr(supplier, key, value)
                        results["updated"] += 1
                    else:
                        # Create new supplier
                        supplier = Supplier(**internal_attrs)
                        self.db.add(supplier)
                        results["created"] += 1
                    
                    # Commit changes for this supplier
                    self.db.commit()
                    
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Error syncing supplier {iiko_data.get('id')}: {str(e)}")
                    results["errors"] += 1
                    results["error_details"].append({
                        "entity_id": iiko_data.get("id"),
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in supplier synchronization: {str(e)}")
            return {
                "total": 0,
                "created": 0,
                "updated": 0,
                "errors": 1,
                "error_details": [{"error": str(e)}]
            }
    
    async def sync_invoices(
        self,
        restaurant_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Synchronize invoices from iiko for a specific restaurant.
        
        Args:
            restaurant_id: Internal restaurant ID
            from_date: Optional start date (defaults to 30 days ago)
            to_date: Optional end date (defaults to now)
            
        Returns:
            Dict[str, Any]: Sync results
        """
        try:
            # Set default date range if not provided
            if not from_date:
                from_date = datetime.now() - timedelta(days=30)
            if not to_date:
                to_date = datetime.now()
            
            # Format dates for iiko API
            from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S")
            to_date_str = to_date.strftime("%Y-%m-%dT%H:%M:%S")
            
            # Get restaurant
            restaurant = self.db.query(Restaurant).filter_by(id=restaurant_id).first()
            if not restaurant or not restaurant.external_id or restaurant.external_system_type != "iiko":
                raise Exception(f"Restaurant with ID {restaurant_id} not found or has no iiko_id")
            
            # Get invoices from iiko
            iiko_invoices = await self.client.get_invoices(
                organization_id=restaurant.external_id,
                from_date=from_date_str,
                to_date=to_date_str
            )
            
            # Track results
            results = {
                "total": len(iiko_invoices),
                "created": 0,
                "updated": 0,
                "errors": 0,
                "error_details": []
            }
            
            # Process each invoice
            for iiko_data in iiko_invoices:
                try:
                    # Skip invoices without a number
                    if not iiko_data.get("number"):
                        continue
                    
                    # Find supplier based on supplier ID
                    supplier_id = iiko_data.get("supplierId")
                    if not supplier_id:
                        results["errors"] += 1
                        results["error_details"].append({
                            "entity_id": iiko_data.get("id"),
                            "error": "Invoice has no supplier ID"
                        })
                        continue
                    
                    supplier = self.db.query(Supplier).filter(
                        Supplier.external_id == supplier_id,
                        Supplier.external_system_type == "iiko",
                        Supplier.account_id == self.account_id
                    ).first()
                    
                    if not supplier:
                        results["errors"] += 1
                        results["error_details"].append({
                            "entity_id": iiko_data.get("id"),
                            "error": f"Supplier with iiko_id {supplier_id} not found"
                        })
                        continue
                    
                    # Find store based on department ID
                    department_id = iiko_data.get("departmentId")
                    if not department_id:
                        results["errors"] += 1
                        results["error_details"].append({
                            "entity_id": iiko_data.get("id"),
                            "error": "Invoice has no department ID"
                        })
                        continue
                    
                    # Find the store associated with this department/restaurant
                    store = self.db.query(Store).filter(
                        Store.restaurant_id == restaurant.id
                    ).first()
                    
                    if not store:
                        results["errors"] += 1
                        results["error_details"].append({
                            "entity_id": iiko_data.get("id"),
                            "error": f"No store found for restaurant {restaurant.id}"
                        })
                        continue
                    
                    # Convert to internal format
                    iiko_invoice, invoice_attrs, invoice_item_attrs = adapt_iiko_invoice_to_internal(
                        iiko_data,
                        str(supplier.id),
                        str(store.id)
                    )
                    
                    # Check if invoice exists
                    invoice = self.db.query(Invoice).filter(
                        Invoice.invoice_number == iiko_invoice.number,
                        Invoice.supplier_id == supplier.id,
                        Invoice.store_id == store.id
                    ).first()
                    
                    if invoice:
                        # Update existing invoice
                        for key, value in invoice_attrs.items():
                            setattr(invoice, key, value)
                        results["updated"] += 1
                        
                        # TODO: Handle updating invoice items
                        # This would require more complex logic to identify and update existing items
                        
                    else:
                        # Create new invoice
                        invoice = Invoice(**invoice_attrs)
                        self.db.add(invoice)
                        self.db.flush()  # Get ID for new invoice
                        results["created"] += 1
                        
                        # Create invoice items
                        for item_attrs in invoice_item_attrs:
                            # Find or create the appropriate unit
                            # For simplicity, we're assuming a default unit exists - in a real implementation,
                            # you would need to match or create appropriate units based on iiko data
                            default_unit = self.db.query(Unit).first()
                            if not default_unit:
                                raise Exception("No units available in the system")
                            
                            # Add invoice and unit IDs to item attributes
                            item_attrs["invoice_id"] = invoice.id
                            item_attrs["unit_id"] = default_unit.id
                            
                            # Create invoice item
                            invoice_item = InvoiceItem(**item_attrs)
                            self.db.add(invoice_item)
                    
                    # Commit changes for this invoice
                    self.db.commit()
                    
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Error syncing invoice {iiko_data.get('id')}: {str(e)}")
                    results["errors"] += 1
                    results["error_details"].append({
                        "entity_id": iiko_data.get("id"),
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in invoice synchronization: {str(e)}")
            return {
                "total": 0,
                "created": 0,
                "updated": 0,
                "errors": 1,
                "error_details": [{"error": str(e)}]
            }