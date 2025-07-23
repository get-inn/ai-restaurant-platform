"""
iiko API client module.

This module provides a client for making requests to the iiko API and handles XML responses.
"""

import logging
import httpx
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union

from .iiko_auth import IikoAuth
from src.api.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def xml_to_dict(element):
    """Convert XML element to dictionary recursively."""
    result = {}
    
    # Add element attributes
    for key, value in element.attrib.items():
        result[f"@{key}"] = value
    
    # Handle text content if it exists
    if element.text and element.text.strip():
        if not result:  # Only text content, no children or attributes
            return element.text.strip()
        else:
            result["#text"] = element.text.strip()
    
    # Process child elements
    child_counts = {}
    for child in element:
        tag = child.tag
        child_counts[tag] = child_counts.get(tag, 0) + 1
    
    # Add children to result
    for child in element:
        tag = child.tag
        child_data = xml_to_dict(child)
        
        # If there are multiple children with the same tag, create a list
        if child_counts[tag] > 1:
            if tag not in result:
                result[tag] = []
            result[tag].append(child_data)
        else:
            result[tag] = child_data
    
    return result


def parse_response(response, expected_format="auto"):
    """
    Parse API response based on content type.
    
    Args:
        response: httpx Response object
        expected_format: The expected format ('json', 'xml', or 'auto' to detect)
        
    Returns:
        Dict or List: Parsed response data
    """
    content_type = response.headers.get("content-type", "").lower()
    
    # Empty response
    if not response.text.strip():
        return {}
    
    # Force specific format if requested
    if expected_format == "json" or content_type.startswith("application/json"):
        try:
            return response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            logger.debug(f"Response content: {response.text[:500]}")
            raise
    
    if expected_format == "xml" or content_type.startswith("application/xml"):
        try:
            root = ET.fromstring(response.text)
            return xml_to_dict(root)
        except Exception as e:
            logger.error(f"Failed to parse XML: {str(e)}")
            logger.debug(f"Response content: {response.text[:500]}")
            raise
    
    # If auto-detect and not caught by the above
    try:
        return response.json()
    except Exception:
        try:
            root = ET.fromstring(response.text)
            return xml_to_dict(root)
        except Exception as e:
            logger.error(f"Failed to auto-detect format: {str(e)}")
            logger.debug(f"Response content: {response.text[:500]}")
            # Return text content as fallback
            return {"text_content": response.text}


class IikoClient:
    """
    Client for interacting with the iiko API.
    
    This class handles API requests to the iiko system with proper error handling,
    authentication, and XML/JSON response parsing.
    """
    
    def __init__(
        self,
        auth_manager: Optional[IikoAuth] = None,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize the iiko API client.
        
        Args:
            auth_manager: Optional pre-configured IikoAuth instance
            base_url: Optional base URL for API requests
            username: Optional username for authentication
            password: Optional password for authentication
        """
        if auth_manager:
            self.auth = auth_manager
        else:
            self.auth = IikoAuth(base_url, username, password)
        
        self.base_url = base_url or "https://chiho-co.iiko.it"
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        auth_type: str = "query",
        expected_format: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the iiko API.
        
        Args:
            method: HTTP method (get, post, etc.)
            endpoint: API endpoint (relative to base URL)
            auth_type: How to provide auth token ('query' or 'header')
            expected_format: Expected response format ('json', 'xml', or 'auto')
            **kwargs: Additional arguments to pass to httpx
        
        Returns:
            Dict[str, Any]: API response data
        
        Raises:
            Exception: If the request fails or returns an error
        """
        token, error = await self.auth.get_token()
        if not token:
            raise Exception(f"Failed to get authentication token: {error}")
        
        url = f"{self.base_url}/{endpoint}"
        
        # Add authentication based on auth_type
        if auth_type == "query":
            # Some endpoints expect 'key' query parameter
            if "params" not in kwargs:
                kwargs["params"] = {}
            kwargs["params"]["key"] = token
        elif auth_type == "header":
            # Other endpoints expect Authorization header
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Authorization"] = f"Bearer {token}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await getattr(client, method.lower())(url, **kwargs)
                response.raise_for_status()
                
                # Parse the response based on content type
                return parse_response(response, expected_format)
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for URL {url}: {e.response.text}")
            
            # If authentication error, try to refresh token and retry once
            if e.response.status_code == 401:
                await self.auth.clear_token()
                token, error = await self.auth.get_token()
                
                if token:
                    # Update the token and retry
                    if auth_type == "query":
                        kwargs["params"]["key"] = token
                    elif auth_type == "header":
                        kwargs["headers"]["Authorization"] = f"Bearer {token}"
                    
                    async with httpx.AsyncClient() as client:
                        response = await getattr(client, method.lower())(url, **kwargs)
                        response.raise_for_status()
                        
                        # Parse the response based on content type
                        return parse_response(response, expected_format)
            
            # If we got here, the retry failed or wasn't attempted
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
            
        except httpx.RequestError as e:
            logger.error(f"Request error for URL {url}: {str(e)}")
            raise Exception(f"Network error during API request: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error for URL {url}: {str(e)}")
            raise Exception(f"Unexpected error during API request: {str(e)}")
    
    # API endpoint methods
    
    async def get_restaurants(self, revision_from: int = -1) -> List[Dict[str, Any]]:
        """
        Get list of restaurants (departments) from iiko.
        
        Args:
            revision_from: Data revision number (-1 for all)
        
        Returns:
            List[Dict[str, Any]]: List of restaurant data
        """
        params = {"revisionFrom": revision_from}
        response = await self._make_request(
            "GET", 
            "resto/api/corporation/departments", 
            params=params,
            expected_format="xml"
        )
        
        # Extract restaurant items from XML structure
        restaurants = []
        if "corporateItemDtoes" in response:
            corporate_items = response["corporateItemDtoes"].get("corporateItemDto", [])
            # Ensure we have a list even if only one item was returned
            if not isinstance(corporate_items, list):
                corporate_items = [corporate_items]
                
            # Process each restaurant
            for item in corporate_items:
                restaurant = {}
                
                # Map XML fields to dictionary
                for field in ["id", "parentId", "code"]:
                    if field in item:
                        restaurant[field] = item[field]
                
                # Handle name field (in XML it's "n")
                if "n" in item:
                    restaurant["name"] = item["n"]
                
                # Handle taxpayer ID
                if "taxpayerIdNumber" in item:
                    restaurant["taxId"] = item["taxpayerIdNumber"]
                
                # Add to list if it's a valid restaurant
                if "id" in restaurant:
                    restaurants.append(restaurant)
        
        return restaurants
    
    async def get_stores(self, revision_from: int = -1) -> List[Dict[str, Any]]:
        """
        Get list of stores from iiko.
        
        Args:
            revision_from: Data revision number (-1 for all)
        
        Returns:
            List[Dict[str, Any]]: List of store data
        """
        params = {"revisionFrom": revision_from}
        response = await self._make_request(
            "GET", 
            "resto/api/corporation/stores", 
            params=params,
            expected_format="xml"
        )
        
        # Extract store items from XML structure
        stores = []
        if "corporateItemDtoes" in response:
            corporate_items = response["corporateItemDtoes"].get("corporateItemDto", [])
            # Ensure we have a list even if only one item was returned
            if not isinstance(corporate_items, list):
                corporate_items = [corporate_items]
                
            # Process each store
            for item in corporate_items:
                store = {}
                
                # Map XML fields to dictionary
                for field in ["id", "code"]:
                    if field in item:
                        store[field] = item[field]
                
                # Handle name field (in XML it's "n")
                if "n" in item:
                    store["name"] = item["n"]
                
                # Handle department ID
                if "departmentId" in item:
                    store["departmentId"] = item["departmentId"]
                
                # Add to list if it's a valid store
                if "id" in store:
                    stores.append(store)
        
        return stores
    
    async def get_suppliers(self) -> List[Dict[str, Any]]:
        """
        Get list of suppliers from iiko.
        
        Returns:
            List[Dict[str, Any]]: List of supplier data
        """
        response = await self._make_request(
            "GET", 
            "resto/api/suppliers",
            expected_format="xml"
        )
        
        # Extract supplier items from XML structure
        suppliers = []
        if "suppliers" in response:
            supplier_items = response["suppliers"].get("supplier", [])
            # Ensure we have a list even if only one item was returned
            if not isinstance(supplier_items, list):
                supplier_items = [supplier_items]
                
            # Process each supplier
            for item in supplier_items:
                supplier = {}
                
                # Map XML fields to dictionary
                for field in ["id", "name", "code", "phone", "email", "inn"]:
                    if field in item:
                        # Map inn to taxId for consistency
                        if field == "inn":
                            supplier["taxId"] = item[field]
                        else:
                            supplier[field] = item[field]
                
                # Add to list if it's a valid supplier
                if "id" in supplier:
                    suppliers.append(supplier)
        
        return suppliers
    
    async def search_suppliers(self, name: str) -> List[Dict[str, Any]]:
        """
        Search for suppliers by name.
        
        Args:
            name: Supplier name to search for
        
        Returns:
            List[Dict[str, Any]]: List of matching supplier data
        """
        params = {"name": name}
        response = await self._make_request(
            "GET", 
            "resto/api/suppliers/search", 
            params=params,
            expected_format="xml"
        )
        
        # Extract supplier items from XML structure using the same parser as get_suppliers
        suppliers = []
        if "suppliers" in response:
            supplier_items = response["suppliers"].get("supplier", [])
            # Ensure we have a list even if only one item was returned
            if not isinstance(supplier_items, list):
                supplier_items = [supplier_items]
                
            # Process each supplier
            for item in supplier_items:
                supplier = {}
                
                # Map XML fields to dictionary
                for field in ["id", "name", "code", "phone", "email", "inn"]:
                    if field in item:
                        # Map inn to taxId for consistency
                        if field == "inn":
                            supplier["taxId"] = item[field]
                        else:
                            supplier[field] = item[field]
                
                # Add to list if it's a valid supplier
                if "id" in supplier:
                    suppliers.append(supplier)
        
        return suppliers
    
    async def get_invoices(
        self,
        organization_id: str,
        from_date: str,
        to_date: str,
        document_type: str = "arrival"
    ) -> List[Dict[str, Any]]:
        """
        Get invoices from iiko.
        
        Args:
            organization_id: Restaurant/entity ID
            from_date: Start date (format: YYYY-MM-DDThh:mm:ss)
            to_date: End date (format: YYYY-MM-DDThh:mm:ss)
            document_type: Document type (arrival for purchase invoices)
        
        Returns:
            List[Dict[str, Any]]: List of invoice data
        """
        params = {
            "type": document_type,
            "organizationId": organization_id,
            "from": from_date,
            "to": to_date
        }
        # This endpoint probably returns JSON, but we'll use auto-detect
        response = await self._make_request(
            "GET", 
            "api/invoices", 
            auth_type="header", 
            params=params,
            expected_format="auto"
        )
        
        # The response might be a list directly or nested under a root key
        invoices = []
        
        if isinstance(response, list):
            invoices = response
        elif isinstance(response, dict) and "items" in response:
            invoices = response["items"]
        else:
            logger.warning(f"Unexpected invoice response structure: {response.keys() if isinstance(response, dict) else type(response)}")
        
        return invoices