from fastapi import APIRouter, Depends, Path, Query, HTTPException, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from uuid import UUID
from datetime import date

from src.api.dependencies.db import get_db
from src.api.dependencies.auth import get_current_user, check_role
from src.api.schemas.auth_schemas import UserRole
from src.api.core.logging_config import get_logger
from src.api.schemas.supplier.invoice_schemas import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceDetailResponse,
    InvoiceItemUpdate,
    InvoiceItemResponse,
    InvoiceStatus,
)

# These services will need to be created
# from src.api.services.supplier.invoice_service import (
#     create_invoice,
#     get_invoice,
#     get_invoices,
#     update_invoice,
#     delete_invoice,
#     update_invoice_item,
#     delete_invoice_item,
#     mark_invoice_as_paid,
#     mark_invoice_as_cancelled,
# )

logger = get_logger("restaurant_api")
router = APIRouter()


@router.post("/invoice", response_model=InvoiceDetailResponse, status_code=201)
async def create_new_invoice(
    invoice_data: InvoiceCreate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new invoice with line items."""
    try:
        # Placeholder for actual implementation
        # invoice = create_invoice(db, invoice_data, current_user["id"])
        
        # Return invoice with line items
        invoice_id = "00000000-0000-0000-0000-000000000001"  # Placeholder
        return {
            "id": invoice_id,
            "supplier_id": invoice_data.supplier_id,
            "store_id": invoice_data.store_id,
            "invoice_number": invoice_data.invoice_number,
            "invoice_date": invoice_data.invoice_date,
            "due_date": invoice_data.due_date,
            "total_amount": invoice_data.total_amount,
            "currency": invoice_data.currency,
            "document_id": invoice_data.document_id,
            "status": invoice_data.status,
            "created_at": "2023-06-28T00:00:00",
            "updated_at": "2023-06-28T00:00:00",
            "line_items": [
                {
                    "id": f"00000000-0000-0000-0000-00000000000{i}",
                    "invoice_id": invoice_id,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_id": item.unit_id,
                    "unit_price": item.unit_price,
                    "line_total": item.line_total,
                    "inventory_item_id": item.inventory_item_id,
                    "created_at": "2023-06-28T00:00:00",
                    "updated_at": "2023-06-28T00:00:00",
                }
                for i, item in enumerate(invoice_data.line_items, start=1)
            ],
        }
    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoice", response_model=List[InvoiceResponse])
async def list_invoices(
    supplier_id: Optional[UUID] = Query(None, description="Filter by supplier ID"),
    store_id: Optional[UUID] = Query(None, description="Filter by store ID"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by invoice status"),
    start_date: Optional[date] = Query(None, description="Filter by invoice date (start)"),
    end_date: Optional[date] = Query(None, description="Filter by invoice date (end)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """List all invoices matching the given filters."""
    # Placeholder for actual implementation
    # invoices = get_invoices(db, supplier_id, store_id, status, start_date, end_date, skip, limit, current_user)
    return []


@router.get("/invoice/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice_details(
    invoice_id: UUID = Path(..., description="The ID of the invoice to get"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get detailed information about a specific invoice including line items."""
    # Placeholder for actual implementation
    # invoice = get_invoice(db, invoice_id, current_user)
    # if not invoice:
    #     raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "id": invoice_id,
        "supplier_id": "00000000-0000-0000-0000-000000000100",
        "store_id": "00000000-0000-0000-0000-000000000200",
        "invoice_number": "INV-12345",
        "invoice_date": "2023-06-15",
        "due_date": "2023-07-15",
        "total_amount": "1250.75",
        "currency": "USD",
        "document_id": None,
        "status": "active",
        "created_at": "2023-06-28T00:00:00",
        "updated_at": "2023-06-28T00:00:00",
        "line_items": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "invoice_id": invoice_id,
                "description": "Organic Tomatoes",
                "quantity": "50.0",
                "unit_id": "00000000-0000-0000-0000-000000000010",
                "unit_price": "2.99",
                "line_total": "149.50",
                "inventory_item_id": "00000000-0000-0000-0000-000000000001",
                "created_at": "2023-06-28T00:00:00",
                "updated_at": "2023-06-28T00:00:00",
            },
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "invoice_id": invoice_id,
                "description": "Fresh Chicken",
                "quantity": "100.0",
                "unit_id": "00000000-0000-0000-0000-000000000011",
                "unit_price": "5.75",
                "line_total": "575.00",
                "inventory_item_id": "00000000-0000-0000-0000-000000000002",
                "created_at": "2023-06-28T00:00:00",
                "updated_at": "2023-06-28T00:00:00",
            }
        ],
    }


@router.patch("/invoice/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice_details(
    invoice_id: UUID = Path(..., description="The ID of the invoice to update"),
    invoice_data: InvoiceUpdate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update invoice details."""
    # Placeholder for actual implementation
    # invoice = update_invoice(db, invoice_id, invoice_data, current_user)
    # if not invoice:
    #     raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "id": invoice_id,
        "supplier_id": invoice_data.supplier_id or "00000000-0000-0000-0000-000000000100",
        "store_id": invoice_data.store_id or "00000000-0000-0000-0000-000000000200",
        "invoice_number": invoice_data.invoice_number or "INV-12345",
        "invoice_date": invoice_data.invoice_date or "2023-06-15",
        "due_date": invoice_data.due_date or "2023-07-15",
        "total_amount": invoice_data.total_amount or "1250.75",
        "currency": invoice_data.currency or "USD",
        "document_id": invoice_data.document_id,
        "status": invoice_data.status or "active",
        "created_at": "2023-06-28T00:00:00",
        "updated_at": "2023-06-28T00:00:00",
    }


@router.delete("/invoice/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: UUID = Path(..., description="The ID of the invoice to delete"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete an invoice."""
    # Placeholder for actual implementation
    # success = delete_invoice(db, invoice_id, current_user)
    # if not success:
    #     raise HTTPException(status_code=404, detail="Invoice not found")
    return None


@router.patch("/invoice/{invoice_id}/item/{item_id}", response_model=InvoiceItemResponse)
async def update_invoice_item(
    invoice_id: UUID = Path(..., description="The ID of the invoice"),
    item_id: UUID = Path(..., description="The ID of the invoice item"),
    item_data: InvoiceItemUpdate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update invoice line item details."""
    # Placeholder for actual implementation
    # item = update_invoice_item(db, invoice_id, item_id, item_data, current_user)
    # if not item:
    #     raise HTTPException(status_code=404, detail="Invoice item not found")
    return {
        "id": item_id,
        "invoice_id": invoice_id,
        "description": item_data.description or "Fresh Chicken",
        "quantity": item_data.quantity or "100.0",
        "unit_id": item_data.unit_id or "00000000-0000-0000-0000-000000000011",
        "unit_price": item_data.unit_price or "5.75",
        "line_total": item_data.line_total or "575.00",
        "inventory_item_id": item_data.inventory_item_id or "00000000-0000-0000-0000-000000000002",
        "created_at": "2023-06-28T00:00:00",
        "updated_at": "2023-06-28T00:00:00",
    }


@router.delete("/invoice/{invoice_id}/item/{item_id}", status_code=204)
async def delete_invoice_item(
    invoice_id: UUID = Path(..., description="The ID of the invoice"),
    item_id: UUID = Path(..., description="The ID of the invoice item"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete an invoice line item."""
    # Placeholder for actual implementation
    # success = delete_invoice_item(db, invoice_id, item_id, current_user)
    # if not success:
    #     raise HTTPException(status_code=404, detail="Invoice item not found")
    return None


@router.post("/invoice/{invoice_id}/mark-as-paid", response_model=InvoiceResponse)
async def mark_invoice_as_paid(
    invoice_id: UUID = Path(..., description="The ID of the invoice to mark as paid"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Mark an invoice as paid."""
    # Placeholder for actual implementation
    # invoice = mark_invoice_as_paid(db, invoice_id, current_user)
    # if not invoice:
    #     raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "id": invoice_id,
        "supplier_id": "00000000-0000-0000-0000-000000000100",
        "store_id": "00000000-0000-0000-0000-000000000200",
        "invoice_number": "INV-12345",
        "invoice_date": "2023-06-15",
        "due_date": "2023-07-15",
        "total_amount": "1250.75",
        "currency": "USD",
        "document_id": None,
        "status": "paid",  # Updated status
        "created_at": "2023-06-28T00:00:00",
        "updated_at": "2023-06-28T00:00:00",
    }


@router.post("/invoice/{invoice_id}/mark-as-cancelled", response_model=InvoiceResponse)
async def mark_invoice_as_cancelled(
    invoice_id: UUID = Path(..., description="The ID of the invoice to mark as cancelled"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Mark an invoice as cancelled."""
    # Placeholder for actual implementation
    # invoice = mark_invoice_as_cancelled(db, invoice_id, current_user)
    # if not invoice:
    #     raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "id": invoice_id,
        "supplier_id": "00000000-0000-0000-0000-000000000100",
        "store_id": "00000000-0000-0000-0000-000000000200",
        "invoice_number": "INV-12345",
        "invoice_date": "2023-06-15",
        "due_date": "2023-07-15",
        "total_amount": "1250.75",
        "currency": "USD",
        "document_id": None,
        "status": "cancelled",  # Updated status
        "created_at": "2023-06-28T00:00:00",
        "updated_at": "2023-06-28T00:00:00",
    }