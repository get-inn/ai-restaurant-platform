"""
iiko integration package.

This package provides integration with the iiko back-office system, allowing for synchronization
of restaurants, stores, suppliers, and invoices.
"""

from .iiko_auth import IikoAuth
from .iiko_client import IikoClient
from .iiko_adapters import (
    adapt_iiko_restaurant_to_internal,
    adapt_iiko_store_to_internal,
    adapt_iiko_supplier_to_internal,
    adapt_iiko_invoice_to_internal,
)
from .iiko_sync import IikoSyncManager
from .iiko_types import (
    IikoRestaurant,
    IikoStore,
    IikoSupplier,
    IikoInvoice,
)