"""
API endpoints for iiko integration.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from uuid import UUID

from src.api.dependencies.db import get_db
from src.api.dependencies.auth import get_current_user
from src.api.models import UserProfile, AccountIntegrationCredentials
from src.api.services.integrations.iiko_service import IikoIntegrationService
from src.api.schemas.integrations import iiko_schemas

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/accounts/{account_id}/integrations/iiko", tags=["iiko integration"])


@router.post("/connect", response_model=iiko_schemas.IntegrationConnectionStatus)
async def connect_iiko(
    credentials: iiko_schemas.IikoCredentials,
    account_id: UUID = Path(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test and save iiko connection credentials for a specific account."""
    # Check if user has access to this account
    if str(current_user.account_id) != str(account_id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to manage this account's integrations")
    
    # Initialize service
    iiko_service = IikoIntegrationService(db)
    
    # Test and store credentials
    connection_status = await iiko_service.connect_and_test(
        account_id=str(account_id),
        username=credentials.username,
        password=credentials.password,
        base_url=credentials.base_url
    )
    
    return connection_status


@router.get("/status", response_model=iiko_schemas.IntegrationConnectionStatus)
async def get_iiko_status(
    account_id: UUID = Path(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current iiko connection status for a specific account."""
    # Check if user has access to this account
    if str(current_user.account_id) != str(account_id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this account's integrations")
    
    # Initialize service
    iiko_service = IikoIntegrationService(db)
    
    # Get connection status
    connection_status = await iiko_service.get_connection_status(str(account_id))
    
    return connection_status


@router.post("/sync/restaurants", response_model=iiko_schemas.SyncJobResponse)
async def sync_restaurants(
    account_id: UUID = Path(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync restaurants from iiko for a specific account."""
    # Check if user has access to this account
    if str(current_user.account_id) != str(account_id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to sync this account's data")
    
    # Initialize service
    iiko_service = IikoIntegrationService(db)
    
    # Perform sync
    results = await iiko_service.sync_restaurants(str(account_id))
    
    return results


@router.post("/sync/stores", response_model=iiko_schemas.SyncJobResponse)
async def sync_stores(
    account_id: UUID = Path(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync stores from iiko for a specific account."""
    # Check if user has access to this account
    if str(current_user.account_id) != str(account_id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to sync this account's data")
    
    # Initialize service
    iiko_service = IikoIntegrationService(db)
    
    # Perform sync
    results = await iiko_service.sync_stores(str(account_id))
    
    return results


@router.post("/sync/suppliers", response_model=iiko_schemas.SyncJobResponse)
async def sync_suppliers(
    account_id: UUID = Path(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync suppliers from iiko for a specific account."""
    # Check if user has access to this account
    if str(current_user.account_id) != str(account_id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to sync this account's data")
    
    # Initialize service
    iiko_service = IikoIntegrationService(db)
    
    # Perform sync
    results = await iiko_service.sync_suppliers(str(account_id))
    
    return results


@router.post("/sync/invoices", response_model=iiko_schemas.SyncJobResponse)
async def sync_invoices(
    sync_request: iiko_schemas.InvoiceSyncRequest,
    account_id: UUID = Path(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync invoices from iiko for a specific account and restaurant."""
    # Check if user has access to this account
    if str(current_user.account_id) != str(account_id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to sync this account's data")
    
    # Initialize service
    iiko_service = IikoIntegrationService(db)
    
    # Perform sync
    results = await iiko_service.sync_invoices(
        account_id=str(account_id),
        restaurant_id=str(sync_request.restaurant_id),
        days_back=sync_request.days_back
    )
    
    return results