import logging
import asyncio
from uuid import UUID
from src.worker.celery_app import celery_app
from src.api.core.logging_config import get_logger
from src.api.dependencies.db import get_db_session
from src.api.services.supplier.reconciliation_service import run_reconciliation_process

logger = get_logger("restaurant_api")

@celery_app.task(bind=True)
def run_reconciliation(self, reconciliation_id: str):
    """
    Run reconciliation process for supplier documents using Azure OpenAI.
    
    Args:
        reconciliation_id: Reconciliation ID to process
    """
    logger.info(f"Starting reconciliation {reconciliation_id}")
    
    try:
        # Set up database session
        db = next(get_db_session())
        
        # Run the reconciliation process
        # Since our service is async and Celery tasks are sync,
        # we need to run the async function in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(
            run_reconciliation_process(db, UUID(reconciliation_id))
        )
        loop.close()
        
        # The WebSocket updates are handled inside the service
        
        if success:
            logger.info(f"Reconciliation {reconciliation_id} completed successfully")
            return {"status": "success", "reconciliation_id": reconciliation_id}
        else:
            logger.error(f"Reconciliation {reconciliation_id} failed")
            return {"status": "failure", "reconciliation_id": reconciliation_id}
        
    except Exception as e:
        logger.error(f"Error in reconciliation {reconciliation_id}: {str(e)}")
        
        # Re-raise the exception to mark the task as failed
        raise