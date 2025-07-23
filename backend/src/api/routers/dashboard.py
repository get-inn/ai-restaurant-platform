from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from datetime import datetime, timedelta

from src.api.dependencies.db import get_db
from src.api.dependencies.auth import get_current_user
from src.api.core.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter()

@router.get("/summary", response_model=Dict[str, Any])
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Returns a summary of key metrics across all modules.
    
    Requires authentication.
    """
    # Placeholder data for now - will be replaced with actual implementation
    return {
        "revenue": {
            "total": 125000.00,
            "change_percent": 5.2,
            "period": "last_30_days"
        },
        "orders": {
            "total": 1250,
            "change_percent": 3.7,
            "period": "last_30_days"
        },
        "inventory": {
            "items_low_stock": 12,
            "items_out_of_stock": 3,
            "total_items": 250
        },
        "staff": {
            "total_active": 45,
            "upcoming_shifts": 12,
            "open_positions": 2
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/recent-activity", response_model=Dict[str, Any])
async def get_recent_activity(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Returns a list of recent activities across all modules.
    
    Requires authentication.
    """
    # Placeholder data for now - will be replaced with actual implementation
    now = datetime.now()
    
    return {
        "activities": [
            {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "module": "inventory",
                "action": "item_received",
                "description": "Received 50 kg flour from Supplier A",
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "user_id": "00000000-0000-0000-0000-000000000001",
                "user_name": "John Doe"
            },
            {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "module": "staff",
                "action": "shift_assigned",
                "description": "Evening shift assigned to Sarah Johnson",
                "timestamp": (now - timedelta(hours=5)).isoformat(),
                "user_id": "00000000-0000-0000-0000-000000000002",
                "user_name": "Manager Smith"
            },
            {
                "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "module": "orders",
                "action": "order_completed",
                "description": "Order #12345 completed and delivered",
                "timestamp": (now - timedelta(hours=8)).isoformat(),
                "user_id": "00000000-0000-0000-0000-000000000003",
                "user_name": "Chef Mike"
            },
            {
                "id": "d4e5f6a7-b8c9-0123-defg-234567890123",
                "module": "menu",
                "action": "item_added",
                "description": "New menu item 'Summer Salad' added",
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "user_id": "00000000-0000-0000-0000-000000000004",
                "user_name": "Chef Mike"
            },
            {
                "id": "e5f6a7b8-c9d0-1234-efgh-345678901234",
                "module": "supplier",
                "action": "invoice_paid",
                "description": "Invoice #INV-9876 paid to Supplier B",
                "timestamp": (now - timedelta(days=1, hours=5)).isoformat(),
                "user_id": "00000000-0000-0000-0000-000000000005",
                "user_name": "Finance User"
            }
        ],
        "total_count": 5,
        "timestamp": now.isoformat()
    }