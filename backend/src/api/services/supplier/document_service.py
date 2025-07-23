"""
Supplier document service.

This module provides services for handling supplier documents,
including document processing with Azure OpenAI.
"""

import os
import uuid
import logging
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.api.core.config import get_settings
from src.api.schemas.supplier.document_schemas import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentType,
    DocumentStatus,
)
from src.api.models import Document
from src.integrations.ai_tools.azure_openai.document_pipeline import DocumentRecognitionPipeline
from src.integrations.ai_tools.azure_openai.azure_openai_client import AzureOpenAIClient

settings = get_settings()
logger = logging.getLogger(__name__)


async def upload_document(
    db: Session,
    document_data: DocumentCreate,
    file: UploadFile,
    user_id: uuid.UUID
) -> Document:
    """
    Upload and process a supplier document.
    
    Args:
        db: Database session
        document_data: Document metadata
        file: Uploaded file
        user_id: ID of the user uploading the document
        
    Returns:
        Document: Created document object
    """
    try:
        # Create storage directory if it doesn't exist
        storage_dir = Path(f"storage/documents/{document_data.account_id}")
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        storage_path = storage_dir / unique_filename
        
        # Save file to storage
        with open(storage_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create document record
        doc = Document(
            id=uuid.uuid4(),
            account_id=document_data.account_id,
            document_type=document_data.document_type,
            file_name=document_data.file_name,
            file_type=file.content_type,
            storage_path=str(storage_path),
            upload_date=datetime.utcnow(),
            uploaded_by=user_id,
            status=DocumentStatus.UPLOADED,
            restaurant_id=document_data.restaurant_id,
            store_id=document_data.store_id,
            supplier_id=document_data.supplier_id,
        )
        
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Queue document for processing if Azure OpenAI is enabled
        if settings.AZURE_OPENAI_ENABLED:
            # This would typically be a background task
            # For now, we'll process it synchronously
            await process_document(db, doc.id)
        
        return doc
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading document: {str(e)}")
        raise


async def process_document(
    db: Session,
    document_id: uuid.UUID
) -> bool:
    """
    Process a document using Azure OpenAI for analysis.
    
    Args:
        db: Database session
        document_id: Document ID
        
    Returns:
        bool: Success or failure
    """
    try:
        # Get document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document not found: {document_id}")
            return False
        
        # Update status to processing
        doc.status = DocumentStatus.PROCESSING
        db.commit()
        
        # Create Azure OpenAI pipeline
        azure_client = AzureOpenAIClient()
        if not azure_client.is_configured():
            doc.status = DocumentStatus.ERROR
            doc.error_message = "Azure OpenAI is not configured"
            db.commit()
            return False
            
        pipeline = DocumentRecognitionPipeline(azure_client=azure_client)
        
        # Get reference data based on document type
        reference_data = await get_reference_data(db, doc)
        
        # Process document through pipeline
        result = await pipeline.process_document(
            document_path=doc.storage_path,
            reference_data=reference_data
        )
        
        if result["success"]:
            # Update document with processed data
            doc.status = DocumentStatus.PROCESSED
            doc.doc_metadata = {
                "processing_result": result["final_result"],
                "classification": result["stage_results"].get("classification"),
                "validation_results": result["stage_results"].get("validation", {}).get("validation_results")
            }
        else:
            # Update document with error
            doc.status = DocumentStatus.ERROR
            doc.error_message = "\n".join(result["errors"])
            doc.doc_metadata = {
                "processing_result": result.get("final_result"),
                "errors": result["errors"]
            }
        
        db.commit()
        return result["success"]
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        
        # Update document with error
        try:
            doc.status = DocumentStatus.ERROR
            doc.error_message = str(e)
            db.commit()
        except Exception:
            db.rollback()
            
        return False


async def get_reference_data(db: Session, document: Document) -> Dict[str, Any]:
    """
    Get reference data for document processing based on document type.
    
    Args:
        db: Database session
        document: Document to process
        
    Returns:
        Dict: Reference data for validation
    """
    reference_data = {
        "account_id": str(document.account_id)
    }
    
    if document.restaurant_id:
        reference_data["restaurant_id"] = str(document.restaurant_id)
        
        # Here you would add restaurant details from the database
        # restaurant = db.query(Restaurant).filter(Restaurant.id == document.restaurant_id).first()
        # if restaurant:
        #     reference_data["restaurant"] = {
        #         "name": restaurant.name,
        #         "address": restaurant.address,
        #     }
    
    if document.supplier_id:
        reference_data["supplier_id"] = str(document.supplier_id)
        
        # Here you would add supplier details from the database
        # supplier = db.query(Supplier).filter(Supplier.id == document.supplier_id).first()
        # if supplier:
        #     reference_data["supplier"] = {
        #         "name": supplier.name,
        #         "tax_id": supplier.tax_id,
        #     }
    
    return reference_data


async def get_document(
    db: Session,
    document_id: uuid.UUID,
    user_data: Dict[str, Any]
) -> Optional[Document]:
    """
    Get a document by ID.
    
    Args:
        db: Database session
        document_id: Document ID
        user_data: Current user data
        
    Returns:
        Document: Document object if found
    """
    # In a real implementation, you would check user permissions
    return db.query(Document).filter(Document.id == document_id).first()


async def get_documents(
    db: Session,
    account_id: uuid.UUID,
    document_type: Optional[DocumentType] = None,
    restaurant_id: Optional[uuid.UUID] = None,
    store_id: Optional[uuid.UUID] = None,
    supplier_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
    user_data: Dict[str, Any] = None
) -> List[Document]:
    """
    Get documents with filters.
    
    Args:
        db: Database session
        account_id: Account ID
        document_type: Optional document type filter
        restaurant_id: Optional restaurant ID filter
        store_id: Optional store ID filter
        supplier_id: Optional supplier ID filter
        skip: Items to skip for pagination
        limit: Maximum number of items to return
        user_data: Current user data
        
    Returns:
        List[Document]: List of documents
    """
    query = db.query(Document).filter(Document.account_id == account_id)
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
        
    if restaurant_id:
        query = query.filter(Document.restaurant_id == restaurant_id)
        
    if store_id:
        query = query.filter(Document.store_id == store_id)
        
    if supplier_id:
        query = query.filter(Document.supplier_id == supplier_id)
    
    return query.order_by(Document.upload_date.desc()).offset(skip).limit(limit).all()


async def update_document(
    db: Session,
    document_id: uuid.UUID,
    document_data: DocumentUpdate,
    user_data: Dict[str, Any]
) -> Optional[Document]:
    """
    Update document details.
    
    Args:
        db: Database session
        document_id: Document ID
        document_data: Updated document data
        user_data: Current user data
        
    Returns:
        Document: Updated document if found
    """
    doc = await get_document(db, document_id, user_data)
    if not doc:
        return None
        
    # Update fields if provided
    if document_data.document_type:
        doc.document_type = document_data.document_type
        
    if document_data.restaurant_id is not None:
        doc.restaurant_id = document_data.restaurant_id
        
    if document_data.store_id is not None:
        doc.store_id = document_data.store_id
        
    if document_data.supplier_id is not None:
        doc.supplier_id = document_data.supplier_id
    
    db.commit()
    db.refresh(doc)
    
    return doc


async def delete_document(
    db: Session,
    document_id: uuid.UUID,
    user_data: Dict[str, Any]
) -> bool:
    """
    Delete a document.
    
    Args:
        db: Database session
        document_id: Document ID to delete
        user_data: Current user data
        
    Returns:
        bool: Success or failure
    """
    doc = await get_document(db, document_id, user_data)
    if not doc:
        return False
        
    # Delete file from storage
    try:
        if os.path.exists(doc.storage_path):
            os.remove(doc.storage_path)
    except Exception as e:
        logger.error(f"Error deleting file {doc.storage_path}: {str(e)}")
    
    # Delete database record
    db.delete(doc)
    db.commit()
    
    return True