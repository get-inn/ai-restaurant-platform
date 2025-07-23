"""
Azure OpenAI Client module.

This module provides a client for making requests to Azure OpenAI API
with proper configuration and error handling.
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any, Union, Tuple
import asyncio

try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("OpenAI library not found. Azure OpenAI functionality will be disabled.")
    AzureOpenAI = None

from src.api.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """
    Client for interacting with Azure OpenAI API using the latest SDK.
    
    This class handles API requests to Azure OpenAI with proper error handling,
    authentication, and response parsing using the OpenAI v1.0+ Python package.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        deployment: Optional[str] = None,
    ):
        """
        Initialize the Azure OpenAI client.
        
        Args:
            api_key: Optional API key (defaults to settings.AZURE_OPENAI_API_KEY)
            endpoint: Optional endpoint URL (defaults to settings.AZURE_OPENAI_ENDPOINT)
            api_version: Optional API version (defaults to settings.AZURE_OPENAI_API_VERSION)
            deployment: Optional deployment name (defaults to settings.AZURE_OPENAI_GPT41_DEPLOYMENT)
        """
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self.api_version = api_version or settings.AZURE_OPENAI_API_VERSION
        self.deployment = deployment or settings.AZURE_OPENAI_GPT41_DEPLOYMENT
        self.client = None
        
        # Check if OpenAI is available
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not installed. Azure OpenAI functionality will be disabled.")
            return
            
        # Validate required settings
        if not self.api_key or not self.endpoint:
            logger.warning("Azure OpenAI API key or endpoint not provided")
        else:
            # Create the Azure OpenAI client
            try:
                self.client = AzureOpenAI(
                    api_key=self.api_key,
                    azure_endpoint=self.endpoint,
                    api_version=self.api_version or "2024-05-01-preview"
                )
                logger.info(f"Azure OpenAI client initialized with API version {self.api_version}")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
                self.client = None
    
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return self.client is not None
    
    async def send_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        deployment: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Send a chat completion request to Azure OpenAI.
        
        Args:
            messages: List of messages in the conversation
            deployment: Optional deployment name (defaults to self.deployment)
            temperature: Optional temperature value (defaults to settings.AZURE_OPENAI_TEMPERATURE)
            max_tokens: Optional max tokens (defaults to settings.AZURE_OPENAI_MAX_TOKENS)
            response_format: Optional response format
            
        Returns:
            Tuple containing (response_data, error_message)
        """
        if not self.is_configured():
            return None, "Azure OpenAI client is not configured"
        
        # Use provided values or defaults
        deployment_name = deployment or self.deployment
        temp = temperature if temperature is not None else settings.AZURE_OPENAI_TEMPERATURE
        tokens = max_tokens or settings.AZURE_OPENAI_MAX_TOKENS
        
        try:
            # Create completion options
            completion_options = {
                "model": deployment_name,
                "messages": messages,
                "temperature": temp,
                "max_tokens": tokens,
            }
            
            # Add response format if provided - only for validation stage
            if response_format:
                # Add 'json' to the system message to satisfy Azure OpenAI requirements
                for message in messages:
                    if message["role"] == "system":
                        message["content"] += "\n\nPlease format your response as valid JSON."
                completion_options["response_format"] = response_format
            
            # Send request to Azure OpenAI (run in thread to avoid blocking)
            response = await self._run_async(
                lambda: self.client.chat.completions.create(**completion_options)
            )
            
            # Extract and return response content
            result = {
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            return result, None
            
        except Exception as e:
            logger.error(f"Error sending chat completion: {str(e)}")
            return None, f"Unexpected error: {str(e)}"
    
    async def _run_async(self, func):
        """Run a synchronous function asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func)
    
    async def classify_document(
        self, 
        document_content: str,
        deployment: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Classify document type using Azure OpenAI.
        
        Args:
            document_content: Document content to classify
            deployment: Optional deployment name
            
        Returns:
            Tuple containing (classification_data, error_message)
        """
        # Truncate document content if too long
        max_content_length = 15000  # Adjust based on token limits
        if len(document_content) > max_content_length:
            document_content = document_content[:max_content_length] + "..."
        
        # Create system prompt for classification
        system_prompt = """
        You are an expert document classifier for restaurant operations.
        Analyze this document and determine its type (reconciliation, invoice, etc.).
        Return a JSON object with the following structure:
        {
          "document_type": "reconciliation|invoice|etc",
          "confidence": 0.0 to 1.0 confidence score,
          "detected_languages": ["en", "fr", etc.],
          "document_date": "YYYY-MM-DD" or null if not found,
          "requires_special_processing": true/false based on document complexity
        }
        """
        
        # Create messages for completion
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": document_content}
        ]
        
        # Request JSON response format
        response_format = {"type": "json_object"}
        
        # Send classification request
        result, error = await self.send_chat_completion(
            messages=messages,
            deployment=deployment,
            temperature=0.1,  # Low temperature for consistent classification
            response_format=response_format
        )
        
        if error:
            return None, error
        
        try:
            # Parse JSON response
            classification = json.loads(result["content"])
            return classification, None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse classification response: {str(e)}")
            return None, f"Failed to parse classification response: {str(e)}"
    
    async def extract_document_fields(
        self,
        document_content: str,
        document_type: str,
        deployment: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Extract structured data fields from a document.
        
        Args:
            document_content: Document content to extract fields from
            document_type: Document type determined from classification
            deployment: Optional deployment name
            
        Returns:
            Tuple containing (extracted_data, error_message)
        """
        # Truncate document content if too long
        max_content_length = 15000  # Adjust based on token limits
        if len(document_content) > max_content_length:
            document_content = document_content[:max_content_length] + "..."
        
        # Create extraction prompt based on document type
        extraction_prompts = {
            "invoice": """
                Extract the following information from this invoice:
                - Invoice number
                - Issue date
                - Due date
                - Supplier information (name, address, tax ID)
                - Line items (description, quantity, unit, unit price, total)
                - Totals (subtotal, tax, total)
                
                Format the output as a structured JSON object with the following schema:
                {
                  "invoice_number": "string",
                  "issue_date": "YYYY-MM-DD",
                  "due_date": "YYYY-MM-DD",
                  "supplier": {
                    "name": "string",
                    "address": "string",
                    "tax_id": "string"
                  },
                  "line_items": [
                    {
                      "description": "string",
                      "quantity": number,
                      "unit": "string",
                      "unit_price": number,
                      "total_price": number
                    }
                  ],
                  "totals": {
                    "subtotal": number,
                    "tax": number,
                    "total": number
                  }
                }
            """,
            "reconciliation": """
                Extract the following information from this reconciliation document:
                - Reconciliation period (start and end dates)
                - Supplier information
                - Restaurant information
                - Invoices list with their status (matched, unmatched)
                - Summary of matched and unmatched items
                
                Format the output as a structured JSON object with the following schema:
                {
                  "period": {
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD"
                  },
                  "supplier": {
                    "name": "string",
                    "id": "string"
                  },
                  "restaurant": {
                    "name": "string",
                    "id": "string"
                  },
                  "invoices": [
                    {
                      "invoice_number": "string",
                      "date": "YYYY-MM-DD",
                      "amount": number,
                      "status": "matched|unmatched|partially_matched",
                      "matching_reference": "string"
                    }
                  ],
                  "summary": {
                    "total_invoices": number,
                    "matched_invoices": number,
                    "unmatched_invoices": number,
                    "total_amount": number,
                    "matched_amount": number,
                    "unmatched_amount": number
                  }
                }
            """
        }
        
        # Use default prompt if document type not recognized
        default_prompt = """
            Extract key information from this document and return a structured JSON representation.
            Include dates, monetary amounts, entity names, and any other important information.
            Format the output as a structured JSON object that best represents the document contents.
        """
        
        extraction_prompt = extraction_prompts.get(document_type.lower(), default_prompt)
        
        # Create messages for completion
        messages = [
            {"role": "system", "content": f"You are an expert data extraction system for restaurant documents. {extraction_prompt}"},
            {"role": "user", "content": document_content}
        ]
        
        # Request JSON response format
        response_format = {"type": "json_object"}
        
        # Send extraction request
        result, error = await self.send_chat_completion(
            messages=messages,
            deployment=deployment,
            temperature=0.0,  # Zero temperature for deterministic extraction
            response_format=response_format
        )
        
        if error:
            return None, error
        
        try:
            # Parse JSON response
            extracted_data = json.loads(result["content"])
            return extracted_data, None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {str(e)}")
            return None, f"Failed to parse extraction response: {str(e)}"
            
    async def validate_document_data(
        self,
        extracted_data: Dict[str, Any],
        document_type: str,
        reference_data: Optional[Dict[str, Any]] = None,
        deployment: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate and enrich extracted document data.
        
        Args:
            extracted_data: Data extracted from document
            document_type: Document type
            reference_data: Optional reference data for validation
            deployment: Optional deployment name
            
        Returns:
            Tuple containing (validated_data, error_message)
        """
        # Convert extracted data to string
        extracted_json = json.dumps(extracted_data, indent=2)
        
        # Create validation prompt based on document type
        validation_prompts = {
            "invoice": """
                Validate the following extracted invoice data:
                1. Check if all required fields are present
                2. Validate date formats (YYYY-MM-DD)
                3. Verify numerical values are reasonable
                4. Check if calculations are correct (line items sum to totals)
                5. Flag any suspicious or unusual values
                
                Required fields for invoice:
                - invoice_number
                - issue_date
                - supplier information
                - totals
                
                Return a validation result with the following structure:
                {
                  "validated_data": {
                    // The original data, corrected if needed
                  },
                  "validation_results": {
                    "passed": true/false,
                    "errors": ["error1", "error2"],
                    "warnings": ["warning1", "warning2"],
                    "confidence_scores": {
                      "field_name": confidence score from 0.0 to 1.0
                    }
                  }
                }
            """,
            "reconciliation": """
                Validate the following extracted reconciliation data:
                1. Check if all required fields are present
                2. Validate date formats (YYYY-MM-DD)
                3. Verify numerical values are reasonable
                4. Check if calculations in the summary are correct
                5. Flag any suspicious or unusual values
                
                Required fields for reconciliation:
                - period information
                - supplier information
                - restaurant information
                - invoices list
                - summary
                
                Return a validation result with the following structure:
                {
                  "validated_data": {
                    // The original data, corrected if needed
                  },
                  "validation_results": {
                    "passed": true/false,
                    "errors": ["error1", "error2"],
                    "warnings": ["warning1", "warning2"],
                    "confidence_scores": {
                      "field_name": confidence score from 0.0 to 1.0
                    }
                  }
                }
            """
        }
        
        # Use default prompt if document type not recognized
        default_prompt = """
            Validate the extracted data and flag any issues or inconsistencies.
            Check for missing required fields, invalid formats, and suspicious values.
            
            Return a validation result with the following structure:
            {
              "validated_data": {
                // The original data, corrected if needed
              },
              "validation_results": {
                "passed": true/false,
                "errors": ["error1", "error2"],
                "warnings": ["warning1", "warning2"],
                "confidence_scores": {
                  "field_name": confidence score from 0.0 to 1.0
                }
              }
            }
        """
        
        validation_prompt = validation_prompts.get(document_type.lower(), default_prompt)
        
        # Add reference data if provided
        reference_context = ""
        if reference_data:
            reference_json = json.dumps(reference_data, indent=2)
            reference_context = f"""
            Use the following reference data to validate and enrich the extracted information:
            {reference_json}
            """
        
        # Create messages for completion
        messages = [
            {"role": "system", "content": f"You are an expert validation system for restaurant documents. {validation_prompt} {reference_context}"},
            {"role": "user", "content": f"Please validate this extracted {document_type} data:\n{extracted_json}"}
        ]
        
        # Request JSON response format
        response_format = {"type": "json_object"}
        
        # Send validation request
        result, error = await self.send_chat_completion(
            messages=messages,
            deployment=deployment,
            temperature=0.0,  # Zero temperature for deterministic validation
            response_format=response_format
        )
        
        if error:
            return None, error
        
        try:
            # Parse JSON response
            validation_result = json.loads(result["content"])
            return validation_result, None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse validation response: {str(e)}")
            return None, f"Failed to parse validation response: {str(e)}"