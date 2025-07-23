"""
iiko data adapters module.

This module provides functions to convert between iiko data models and internal models.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging

from .iiko_types import IikoRestaurant, IikoStore, IikoSupplier, IikoInvoice, IikoInvoiceItem
from src.api.models import Restaurant, Store, Supplier, Invoice, InvoiceItem
from src.api.models.base import SyncStatus

logger = logging.getLogger(__name__)


def adapt_iiko_restaurant_to_internal(
    iiko_data: Dict[str, Any],
    account_id: str
) -> Tuple[IikoRestaurant, dict]:
    """
    Convert iiko restaurant data to internal model format.
    
    Args:
        iiko_data: Raw iiko restaurant data
        account_id: Internal account ID
    
    Returns:
        Tuple[IikoRestaurant, dict]: Parsed iiko data model and attributes for internal model
    """
    try:
        # Handle XML-converted structure where name may be stored in "n" field
        name = iiko_data.get("name", "")
        if not name and "n" in iiko_data:
            name = iiko_data.get("n", "Unnamed Restaurant")
        
        # XML structure might have taxpayerIdNumber instead of taxId
        tax_id = iiko_data.get("taxId", "")
        if not tax_id and "taxpayerIdNumber" in iiko_data:
            tax_id = iiko_data.get("taxpayerIdNumber", "")
        
        # Parse into iiko model first
        iiko_restaurant = IikoRestaurant(
            iiko_id=iiko_data.get("id"),
            name=name or "Unnamed Restaurant",
            code=iiko_data.get("code"),
            parent_id=iiko_data.get("parentId"),
            phone=iiko_data.get("phone"),
            address=iiko_data.get("address"),
            tax_id=tax_id,
            is_active=iiko_data.get("isActive", True),
            iiko_metadata=iiko_data
        )
        
        # Create attributes for internal model
        internal_attrs = {
            "account_id": account_id,
            "name": iiko_restaurant.name,
            "external_id": iiko_restaurant.iiko_id,
            "external_sync_status": SyncStatus.SYNCED,
            "external_system_type": "iiko",
            "external_last_synced_at": datetime.now(),
            "external_metadata": iiko_restaurant.iiko_metadata,
        }
        
        return iiko_restaurant, internal_attrs
        
    except Exception as e:
        logger.error(f"Error adapting iiko restaurant data: {str(e)}")
        raise


def adapt_iiko_store_to_internal(
    iiko_data: Dict[str, Any],
    restaurant_id: str
) -> Tuple[IikoStore, dict]:
    """
    Convert iiko store data to internal model format.
    
    Args:
        iiko_data: Raw iiko store data
        restaurant_id: Internal restaurant ID
    
    Returns:
        Tuple[IikoStore, dict]: Parsed iiko data model and attributes for internal model
    """
    try:
        # Handle XML-converted structure where name may be stored in "n" field
        name = iiko_data.get("name", "")
        if not name and "n" in iiko_data:
            name = iiko_data.get("n", "Unnamed Store")
            
        # Parse into iiko model first
        iiko_store = IikoStore(
            iiko_id=iiko_data.get("id"),
            name=name or "Unnamed Store",
            code=iiko_data.get("code"),
            department_id=iiko_data.get("departmentId"),
            is_active=iiko_data.get("isActive", True),
            iiko_metadata=iiko_data
        )
        
        # Create attributes for internal model
        internal_attrs = {
            "restaurant_id": restaurant_id,
            "name": iiko_store.name,
            "external_id": iiko_store.iiko_id,
            "external_sync_status": SyncStatus.SYNCED,
            "external_system_type": "iiko",
            "external_last_synced_at": datetime.now(),
            "external_metadata": iiko_store.iiko_metadata,
        }
        
        return iiko_store, internal_attrs
        
    except Exception as e:
        logger.error(f"Error adapting iiko store data: {str(e)}")
        raise


def adapt_iiko_supplier_to_internal(
    iiko_data: Dict[str, Any],
    account_id: str
) -> Tuple[IikoSupplier, dict]:
    """
    Convert iiko supplier data to internal model format.
    
    Args:
        iiko_data: Raw iiko supplier data
        account_id: Internal account ID
    
    Returns:
        Tuple[IikoSupplier, dict]: Parsed iiko data model and attributes for internal model
    """
    try:
        # Extract contact information
        contact_info = {}
        if iiko_data.get("phone"):
            contact_info["phone"] = iiko_data.get("phone")
        if iiko_data.get("email"):
            contact_info["email"] = iiko_data.get("email")
        if iiko_data.get("contactPerson"):
            contact_info["contact_person"] = iiko_data.get("contactPerson")
        
        # For suppliers in XML, inn is used instead of taxId
        tax_id = iiko_data.get("taxId", "")
        if not tax_id and "inn" in iiko_data:
            tax_id = iiko_data.get("inn", "")
            
        # Parse into iiko model first
        iiko_supplier = IikoSupplier(
            iiko_id=iiko_data.get("id"),
            name=iiko_data.get("name", "Unnamed Supplier"),
            code=iiko_data.get("code"),
            phone=iiko_data.get("phone"),
            email=iiko_data.get("email"),
            tax_id=tax_id,
            is_active=iiko_data.get("isActive", True),
            contact_person=iiko_data.get("contactPerson"),
            iiko_metadata=iiko_data
        )
        
        # Create attributes for internal model
        internal_attrs = {
            "account_id": account_id,
            "name": iiko_supplier.name,
            "contact_info": contact_info,
            "external_id": iiko_supplier.iiko_id,
            "external_sync_status": SyncStatus.SYNCED,
            "external_system_type": "iiko",
            "external_last_synced_at": datetime.now(),
            "external_metadata": iiko_supplier.iiko_metadata,
        }
        
        return iiko_supplier, internal_attrs
        
    except Exception as e:
        logger.error(f"Error adapting iiko supplier data: {str(e)}")
        raise


def adapt_iiko_invoice_to_internal(
    iiko_data: Dict[str, Any],
    supplier_id: str,
    store_id: str
) -> Tuple[IikoInvoice, dict, List[dict]]:
    """
    Convert iiko invoice data to internal model format.
    
    Args:
        iiko_data: Raw iiko invoice data
        supplier_id: Internal supplier ID
        store_id: Internal store ID
    
    Returns:
        Tuple[IikoInvoice, dict, List[dict]]: 
            - Parsed iiko data model
            - Attributes for internal invoice model
            - List of attributes for internal invoice items
    """
    try:
        # Parse invoice items - handle both JSON and XML structures
        items = []
        invoice_items_attrs = []
        
        # Get items from either JSON or XML structure
        item_list = []
        if "items" in iiko_data and isinstance(iiko_data["items"], list):
            # JSON structure
            item_list = iiko_data["items"]
        elif "items" in iiko_data and isinstance(iiko_data["items"], dict):
            # XML structure might have item nested under items
            items_dict = iiko_data["items"]
            if "item" in items_dict:
                if isinstance(items_dict["item"], list):
                    item_list = items_dict["item"]
                else:
                    item_list = [items_dict["item"]]
        
        for item_data in item_list:
            # Handle different field names in XML vs JSON
            product_id = item_data.get("productId") or item_data.get("product_id")
            product_name = item_data.get("name") or item_data.get("product_name", "Unnamed Product")
            quantity = item_data.get("amount") or item_data.get("quantity", 0)
            unit_name = item_data.get("measureUnit") or item_data.get("unit_name", "pcs")
            unit_price = item_data.get("price") or item_data.get("unit_price", 0)
            total_price = item_data.get("sum") or item_data.get("total_price", 0)
            vat = item_data.get("vatPercent") or item_data.get("vat")
            
            item = IikoInvoiceItem(
                product_id=product_id,
                product_name=product_name,
                quantity=float(quantity) if quantity else 0,
                unit_name=unit_name,
                unit_price=float(unit_price) if unit_price else 0,
                total_price=float(total_price) if total_price else 0,
                vat=float(vat) if vat else None
            )
            items.append(item)
            
            # Will need to be updated with proper unit_id after looking up or creating the unit
            invoice_items_attrs.append({
                "description": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "line_total": item.total_price,
                # unit_id will be added later
            })
        
        # Parse invoice date - handle both standard and XML format
        invoice_date = None
        date_str = iiko_data.get("date") or iiko_data.get("dateTime")
        if date_str:
            try:
                # Handle different date formats
                date_str = str(date_str).replace("Z", "+00:00")
                if "T" not in date_str and " " in date_str:
                    # Format might be "YYYY-MM-DD HH:MM:SS"
                    date_str = date_str.replace(" ", "T")
                invoice_date = datetime.fromisoformat(date_str)
            except ValueError:
                logger.warning(f"Could not parse invoice date: {date_str}")
        
        # Parse due date - handle both standard and XML format
        due_date = None
        date_str = iiko_data.get("dueDate") or iiko_data.get("due_date")
        if date_str:
            try:
                # Handle different date formats
                date_str = str(date_str).replace("Z", "+00:00")
                if "T" not in date_str and " " in date_str:
                    # Format might be "YYYY-MM-DD HH:MM:SS"
                    date_str = date_str.replace(" ", "T")
                due_date = datetime.fromisoformat(date_str)
            except ValueError:
                logger.warning(f"Could not parse invoice due date: {date_str}")
        
        # Parse into iiko model - handle different field naming in XML
        iiko_invoice = IikoInvoice(
            iiko_id=iiko_data.get("id"),
            number=iiko_data.get("number", ""),
            supplier_id=iiko_data.get("supplierId") or iiko_data.get("supplier_id"),
            department_id=iiko_data.get("departmentId") or iiko_data.get("department_id"),
            date=invoice_date or datetime.now(),
            due_date=due_date,
            total_amount=float(iiko_data.get("sum", 0)) if iiko_data.get("sum") else 0,
            currency=iiko_data.get("currency", "USD"),
            status=iiko_data.get("status", "active"),
            comment=iiko_data.get("comment"),
            items=items,
            iiko_metadata=iiko_data
        )
        
        # Create attributes for internal model
        internal_attrs = {
            "supplier_id": supplier_id,
            "store_id": store_id,
            "invoice_number": iiko_invoice.number,
            "invoice_date": iiko_invoice.date.date(),
            "due_date": iiko_invoice.due_date.date() if iiko_invoice.due_date else None,
            "total_amount": iiko_invoice.total_amount,
            "currency": iiko_invoice.currency,
            "status": "active",  # Default status
        }
        
        return iiko_invoice, internal_attrs, invoice_items_attrs
        
    except Exception as e:
        logger.error(f"Error adapting iiko invoice data: {str(e)}")
        raise