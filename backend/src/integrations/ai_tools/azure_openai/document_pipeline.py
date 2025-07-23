"""
Document Recognition Pipeline.

This module implements the 3-stage document recognition process using Azure OpenAI.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

from src.integrations.ai_tools.azure_openai.azure_openai_client import AzureOpenAIClient
from src.integrations.ai_tools.azure_openai.document_preprocessing import preprocess_document

logger = logging.getLogger(__name__)


class DocumentRecognitionPipeline:
    """
    3-stage document recognition pipeline using Azure OpenAI.
    
    This class orchestrates the document recognition process through three stages:
    1. Classification - Determine document type
    2. Field Extraction - Extract structured data
    3. Validation - Validate and enrich data
    """
    
    def __init__(
        self,
        azure_client: Optional[AzureOpenAIClient] = None,
        deployment_name: Optional[str] = None,
    ):
        """
        Initialize document recognition pipeline.
        
        Args:
            azure_client: Optional pre-configured AzureOpenAIClient
            deployment_name: Optional deployment name to use
        """
        self.client = azure_client or AzureOpenAIClient()
        self.deployment = deployment_name
        
    async def process_document(
        self,
        document_path: str,
        reference_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a document through the complete 3-stage pipeline.
        
        Args:
            document_path: Path to the document file
            reference_data: Optional reference data for validation
            
        Returns:
            Dict with processing results containing:
            - stage_results: Results from each stage
            - final_result: Final processed data
            - success: Whether processing was successful
            - errors: Any errors encountered
        """
        result = {
            "document_path": document_path,
            "processing_timestamp": datetime.utcnow().isoformat(),
            "stage_results": {},
            "final_result": None,
            "success": False,
            "errors": []
        }
        
        try:
            # Step 0: Preprocess document
            document_content, preprocess_error = await preprocess_document(document_path)
            
            if preprocess_error:
                result["errors"].append(f"Preprocessing error: {preprocess_error}")
                return result
                
            # Stage 1: Classification
            classification, error = await self._classify_document(document_content)
            result["stage_results"]["classification"] = classification
            
            if error:
                result["errors"].append(f"Classification error: {error}")
                return result
                
            document_type = classification.get("document_type")
            if not document_type:
                result["errors"].append("Classification did not return a document type")
                return result
                
            # Stage 2: Field Extraction
            extracted_data, error = await self._extract_document_fields(
                document_content, 
                document_type
            )
            result["stage_results"]["extraction"] = extracted_data
            
            if error:
                result["errors"].append(f"Extraction error: {error}")
                return result
                
            # Stage 3: Validation
            validated_data, error = await self._validate_document_data(
                extracted_data,
                document_type,
                reference_data
            )
            result["stage_results"]["validation"] = validated_data
            
            if error:
                result["errors"].append(f"Validation error: {error}")
                # Continue with extracted data even if validation fails
            
            # Set final result based on validation or extraction
            if validated_data and "validated_data" in validated_data:
                result["final_result"] = validated_data["validated_data"]
            else:
                result["final_result"] = extracted_data
                
            # Mark as successful if we have a final result
            if result["final_result"]:
                result["success"] = True
                
            return result
            
        except Exception as e:
            logger.error(f"Error in document pipeline: {str(e)}")
            result["errors"].append(f"Pipeline error: {str(e)}")
            return result
    
    async def _classify_document(
        self, 
        document_content: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Stage 1: Document Classification.
        
        Args:
            document_content: Document content to classify
            
        Returns:
            Tuple containing (classification_data, error_message)
        """
        logger.info("Starting document classification")
        return await self.client.classify_document(
            document_content=document_content,
            deployment=self.deployment
        )
    
    async def _extract_document_fields(
        self,
        document_content: str,
        document_type: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Stage 2: Field Extraction.
        
        Args:
            document_content: Document content to extract fields from
            document_type: Document type determined from classification
            
        Returns:
            Tuple containing (extracted_data, error_message)
        """
        logger.info(f"Starting field extraction for document type: {document_type}")
        return await self.client.extract_document_fields(
            document_content=document_content,
            document_type=document_type,
            deployment=self.deployment
        )
    
    async def _validate_document_data(
        self,
        extracted_data: Dict[str, Any],
        document_type: str,
        reference_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Stage 3: Data Validation.
        
        Args:
            extracted_data: Data extracted from document
            document_type: Document type
            reference_data: Optional reference data for validation
            
        Returns:
            Tuple containing (validated_data, error_message)
        """
        logger.info(f"Starting data validation for document type: {document_type}")
        return await self.client.validate_document_data(
            extracted_data=extracted_data,
            document_type=document_type,
            reference_data=reference_data,
            deployment=self.deployment
        )