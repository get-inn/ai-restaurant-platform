"""
Reconciliation service for supplier documents.

This module provides services for reconciling supplier documents 
with restaurant records using Azure OpenAI for analysis.
"""

import uuid
import logging
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from src.api.core.config import get_settings
from src.api.schemas.supplier.reconciliation_schemas import (
    ReconciliationCreate,
    ReconciliationResponse,
    ReconciliationItemResponse,
    ReconciliationStatusUpdate,
    ReconciliationStats,
    ItemStatus,
)
from src.api.models import Document, Reconciliation, ReconciliationItem
from src.api.core.websockets import get_connection_manager
from src.integrations.ai_tools.azure_openai.document_pipeline import DocumentRecognitionPipeline
from src.integrations.ai_tools.azure_openai.azure_openai_client import AzureOpenAIClient

settings = get_settings()
logger = logging.getLogger(__name__)


async def create_reconciliation(
    db: Session,
    reconciliation_data: ReconciliationCreate,
    user_id: uuid.UUID
) -> Reconciliation:
    """
    Create a new reconciliation process.
    
    Args:
        db: Database session
        reconciliation_data: Reconciliation creation data
        user_id: ID of the user creating the reconciliation
        
    Returns:
        Reconciliation: Created reconciliation object
    """
    try:
        # Create reconciliation record
        reconciliation = Reconciliation(
            id=uuid.uuid4(),
            document_id=reconciliation_data.document_id,
            account_id=reconciliation_data.account_id,
            restaurant_id=reconciliation_data.restaurant_id,
            store_id=reconciliation_data.store_id,
            status="pending",
            progress=0,
            created_by=user_id,
        )
        
        db.add(reconciliation)
        db.commit()
        db.refresh(reconciliation)
        
        return reconciliation
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating reconciliation: {str(e)}")
        raise


async def run_reconciliation_process(
    db: Session,
    reconciliation_id: uuid.UUID
) -> bool:
    """
    Run the reconciliation process using Azure OpenAI.
    
    Args:
        db: Database session
        reconciliation_id: Reconciliation ID
        
    Returns:
        bool: Success or failure
    """
    try:
        # Get reconciliation
        reconciliation = db.query(Reconciliation).filter(Reconciliation.id == reconciliation_id).first()
        if not reconciliation:
            logger.error(f"Reconciliation not found: {reconciliation_id}")
            return False
        
        # Update status to processing
        reconciliation.status = "processing"
        reconciliation.started_at = datetime.utcnow()
        reconciliation.progress = 10
        db.commit()
        
        # Send status update via WebSocket
        await send_reconciliation_update(reconciliation_id, {
            "status": "processing",
            "progress": 10,
            "message": "Started processing reconciliation document."
        })
        
        # Get the document to be reconciled
        document = db.query(Document).filter(Document.id == reconciliation.document_id).first()
        if not document:
            logger.error(f"Document not found: {reconciliation.document_id}")
            reconciliation.status = "error"
            reconciliation.error_message = f"Document not found: {reconciliation.document_id}"
            db.commit()
            
            await send_reconciliation_update(reconciliation_id, {
                "status": "error",
                "progress": 0,
                "message": f"Document not found: {reconciliation.document_id}"
            })
            
            return False
        
        # Create Azure OpenAI pipeline
        azure_client = AzureOpenAIClient()
        if not azure_client.is_configured():
            reconciliation.status = "error"
            reconciliation.error_message = "Azure OpenAI is not configured"
            db.commit()
            
            await send_reconciliation_update(reconciliation_id, {
                "status": "error",
                "progress": 0,
                "message": "Azure OpenAI is not configured"
            })
            
            return False
            
        pipeline = DocumentRecognitionPipeline(azure_client=azure_client)
        
        # Update progress
        reconciliation.progress = 20
        db.commit()
        
        await send_reconciliation_update(reconciliation_id, {
            "status": "processing",
            "progress": 20,
            "message": "Analyzing reconciliation document with Azure OpenAI."
        })
        
        # Get reference data
        reference_data = await get_reconciliation_reference_data(db, reconciliation)
        
        # Process document through pipeline
        result = await pipeline.process_document(
            document_path=document.storage_path,
            reference_data=reference_data
        )
        
        if not result["success"]:
            reconciliation.status = "error"
            reconciliation.error_message = "\n".join(result["errors"])
            db.commit()
            
            await send_reconciliation_update(reconciliation_id, {
                "status": "error",
                "progress": 30,
                "message": "Failed to analyze reconciliation document."
            })
            
            return False
        
        # Update progress
        reconciliation.progress = 50
        db.commit()
        
        await send_reconciliation_update(reconciliation_id, {
            "status": "processing",
            "progress": 50,
            "message": "Document analyzed successfully. Processing reconciliation items."
        })
        
        # Extract reconciliation data from the result
        reconciliation_data = result["final_result"]
        if not reconciliation_data:
            reconciliation.status = "error"
            reconciliation.error_message = "Failed to extract reconciliation data"
            db.commit()
            
            await send_reconciliation_update(reconciliation_id, {
                "status": "error",
                "progress": 50,
                "message": "Failed to extract reconciliation data."
            })
            
            return False
        
        # Store reconciliation metadata
        reconciliation.metadata = {
            "processing_result": result["final_result"],
            "classification": result["stage_results"].get("classification"),
            "validation_results": result["stage_results"].get("validation", {}).get("validation_results")
        }
        
        # Process invoices from reconciliation data
        await process_reconciliation_items(db, reconciliation, reconciliation_data)
        
        # Update progress
        reconciliation.progress = 90
        db.commit()
        
        await send_reconciliation_update(reconciliation_id, {
            "status": "processing",
            "progress": 90,
            "message": "Reconciliation items processed. Finalizing reconciliation."
        })
        
        # Calculate reconciliation statistics
        stats = await calculate_reconciliation_stats(db, reconciliation_id)
        reconciliation.statistics = stats
        
        # Mark reconciliation as complete
        reconciliation.status = "completed"
        reconciliation.completed_at = datetime.utcnow()
        reconciliation.progress = 100
        db.commit()
        
        await send_reconciliation_update(reconciliation_id, {
            "status": "completed",
            "progress": 100,
            "message": "Reconciliation completed successfully."
        })
        
        return True
        
    except Exception as e:
        logger.error(f"Error in reconciliation process {reconciliation_id}: {str(e)}")
        
        # Update reconciliation with error
        try:
            reconciliation.status = "error"
            reconciliation.error_message = str(e)
            db.commit()
            
            await send_reconciliation_update(reconciliation_id, {
                "status": "error",
                "progress": reconciliation.progress,
                "message": f"Error in reconciliation process: {str(e)}"
            })
        except Exception:
            db.rollback()
            
        return False


async def get_reconciliation_reference_data(db: Session, reconciliation: Reconciliation) -> Dict[str, Any]:
    """
    Get reference data for reconciliation processing.
    
    Args:
        db: Database session
        reconciliation: Reconciliation object
        
    Returns:
        Dict: Reference data
    """
    reference_data = {
        "account_id": str(reconciliation.account_id)
    }
    
    if reconciliation.restaurant_id:
        reference_data["restaurant_id"] = str(reconciliation.restaurant_id)
        
        # Here you would add restaurant details from the database
        # restaurant = db.query(Restaurant).filter(Restaurant.id == reconciliation.restaurant_id).first()
        # if restaurant:
        #     reference_data["restaurant"] = {
        #         "name": restaurant.name,
        #         "address": restaurant.address,
        #     }
        
        # Add restaurant invoices from the database for matching
        # This would be a separate service call in a real implementation
        # invoices = get_restaurant_invoices(db, reconciliation.restaurant_id)
        # reference_data["restaurant_invoices"] = invoices
    
    return reference_data


async def process_reconciliation_items(
    db: Session,
    reconciliation: Reconciliation,
    reconciliation_data: Dict[str, Any]
) -> None:
    """
    Process and store reconciliation items from extracted data.
    
    Args:
        db: Database session
        reconciliation: Reconciliation object
        reconciliation_data: Extracted reconciliation data
    """
    # Check if invoices are present in the data
    if "invoices" not in reconciliation_data or not reconciliation_data["invoices"]:
        return
        
    # Process each invoice in the reconciliation
    for idx, invoice_data in enumerate(reconciliation_data["invoices"]):
        # Create reconciliation item
        item = ReconciliationItem(
            id=uuid.uuid4(),
            reconciliation_id=reconciliation.id,
            item_index=idx,
            item_type="invoice",
            external_id=invoice_data.get("invoice_number", f"unknown-{idx}"),
            external_date=invoice_data.get("date"),
            external_amount=invoice_data.get("amount", 0.0),
            status=invoice_data.get("status", "unmatched"),
            matching_reference=invoice_data.get("matching_reference"),
            metadata=invoice_data,
        )
        
        db.add(item)
        
    # Commit all items at once for better performance
    db.commit()


async def calculate_reconciliation_stats(
    db: Session,
    reconciliation_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Calculate statistics for a reconciliation.
    
    Args:
        db: Database session
        reconciliation_id: Reconciliation ID
        
    Returns:
        Dict: Statistics data
    """
    # Get all items for this reconciliation
    items = db.query(ReconciliationItem).filter(
        ReconciliationItem.reconciliation_id == reconciliation_id
    ).all()
    
    # Initialize counters
    total_invoices = len(items)
    matched_invoices = 0
    unmatched_invoices = 0
    partially_matched_invoices = 0
    total_amount = 0.0
    matched_amount = 0.0
    unmatched_amount = 0.0
    
    # Calculate statistics
    for item in items:
        total_amount += item.external_amount or 0.0
        
        if item.status == "matched":
            matched_invoices += 1
            matched_amount += item.external_amount or 0.0
        elif item.status == "partially_matched":
            partially_matched_invoices += 1
            # For partially matched, count half as matched for simplicity
            matched_amount += (item.external_amount or 0.0) / 2
            unmatched_amount += (item.external_amount or 0.0) / 2
        else:  # unmatched
            unmatched_invoices += 1
            unmatched_amount += item.external_amount or 0.0
    
    # Create statistics object
    return {
        "total_invoices": total_invoices,
        "matched_invoices": matched_invoices,
        "unmatched_invoices": unmatched_invoices,
        "partially_matched_invoices": partially_matched_invoices,
        "total_amount": total_amount,
        "matched_amount": matched_amount,
        "unmatched_amount": unmatched_amount,
        "match_rate": (matched_invoices / total_invoices) if total_invoices > 0 else 0,
        "match_amount_rate": (matched_amount / total_amount) if total_amount > 0 else 0,
    }


async def send_reconciliation_update(
    reconciliation_id: uuid.UUID,
    update_data: Dict[str, Any]
) -> None:
    """
    Send a WebSocket update for a reconciliation.
    
    Args:
        reconciliation_id: Reconciliation ID
        update_data: Update data to send
    """
    connection_manager = get_connection_manager()
    
    # Prepare message
    message = {
        "event": "reconciliation_update",
        "reconciliation_id": str(reconciliation_id),
        **update_data
    }
    
    # Send to all clients listening to this reconciliation
    await connection_manager.broadcast(
        f"reconciliation_{reconciliation_id}",
        message
    )


async def get_reconciliation(
    db: Session,
    reconciliation_id: uuid.UUID,
    user_data: Dict[str, Any]
) -> Optional[Reconciliation]:
    """
    Get a reconciliation by ID.
    
    Args:
        db: Database session
        reconciliation_id: Reconciliation ID
        user_data: Current user data
        
    Returns:
        Reconciliation: Reconciliation object if found
    """
    # In a real implementation, you would check user permissions
    return db.query(Reconciliation).filter(Reconciliation.id == reconciliation_id).first()


async def get_reconciliations(
    db: Session,
    user_data: Dict[str, Any],
    skip: int = 0,
    limit: int = 100
) -> List[Reconciliation]:
    """
    Get reconciliations for the user's account.
    
    Args:
        db: Database session
        user_data: Current user data
        skip: Items to skip for pagination
        limit: Maximum number of items to return
        
    Returns:
        List[Reconciliation]: List of reconciliations
    """
    # In a real implementation, you would filter by the user's account
    return db.query(Reconciliation).order_by(
        Reconciliation.created_at.desc()
    ).offset(skip).limit(limit).all()


async def get_reconciliation_items(
    db: Session,
    reconciliation_id: uuid.UUID,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    user_data: Dict[str, Any] = None
) -> List[ReconciliationItem]:
    """
    Get reconciliation items with filters.
    
    Args:
        db: Database session
        reconciliation_id: Reconciliation ID
        status: Optional status filter
        skip: Items to skip for pagination
        limit: Maximum number of items to return
        user_data: Current user data
        
    Returns:
        List[ReconciliationItem]: List of reconciliation items
    """
    query = db.query(ReconciliationItem).filter(
        ReconciliationItem.reconciliation_id == reconciliation_id
    )
    
    if status:
        query = query.filter(ReconciliationItem.status == status)
    
    return query.order_by(
        ReconciliationItem.item_index
    ).offset(skip).limit(limit).all()


async def get_matched_items(
    db: Session,
    reconciliation_id: uuid.UUID,
    user_data: Dict[str, Any],
    skip: int = 0,
    limit: int = 100
) -> List[ReconciliationItem]:
    """Get matched items from reconciliation."""
    return await get_reconciliation_items(
        db, reconciliation_id, status="matched", skip=skip, limit=limit, user_data=user_data
    )


async def get_missing_in_restaurant(
    db: Session,
    reconciliation_id: uuid.UUID,
    user_data: Dict[str, Any],
    skip: int = 0,
    limit: int = 100
) -> List[ReconciliationItem]:
    """Get items missing in restaurant from reconciliation."""
    return await get_reconciliation_items(
        db, reconciliation_id, status="missing_in_restaurant", skip=skip, limit=limit, user_data=user_data
    )


async def get_missing_in_supplier(
    db: Session,
    reconciliation_id: uuid.UUID,
    user_data: Dict[str, Any],
    skip: int = 0,
    limit: int = 100
) -> List[ReconciliationItem]:
    """Get items missing in supplier document from reconciliation."""
    return await get_reconciliation_items(
        db, reconciliation_id, status="missing_in_supplier", skip=skip, limit=limit, user_data=user_data
    )


async def get_mismatches(
    db: Session,
    reconciliation_id: uuid.UUID,
    user_data: Dict[str, Any],
    skip: int = 0,
    limit: int = 100
) -> List[ReconciliationItem]:
    """Get mismatched items from reconciliation."""
    return await get_reconciliation_items(
        db, reconciliation_id, status="mismatched", skip=skip, limit=limit, user_data=user_data
    )