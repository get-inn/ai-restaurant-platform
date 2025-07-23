import logging
from uuid import UUID
from src.worker.celery_app import celery_app
from src.api.core.logging_config import get_logger
from sqlalchemy.orm import Session
from src.api.dependencies.db import get_db_session
from src.api.services.supplier.document_service import process_document as process_doc_service

logger = get_logger("restaurant_api")

@celery_app.task(bind=True)
def process_document(self, document_id: str):
    """
    Process uploaded document using Azure OpenAI.
    
    Args:
        document_id: Document ID to process
    """
    logger.info(f"Processing document {document_id}")
    
    try:
        # Set up database session
        db = next(get_db_session())
        
        # Process document using Azure OpenAI
        success = process_doc_service(db, UUID(document_id))
        
        # Update task state
        self.update_state(
            state='SUCCESS' if success else 'FAILURE',
            meta={
                'document_id': document_id,
                'status': 'processed' if success else 'error'
            }
        )
        
        logger.info(f"Document {document_id} processed successfully")
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        
        # Re-raise the exception to mark the task as failed
        raise