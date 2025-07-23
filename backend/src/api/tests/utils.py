"""
Utilities for API tests.
"""
import json
from typing import Dict, Any, Optional, List, Union
from fastapi.testclient import TestClient
from uuid import UUID, uuid4

class APITestUtils:
    """
    Utility methods for API testing.
    """
    
    @staticmethod
    def create_test_account(client: TestClient, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a test account through the API.
        """
        # Use test endpoint since regular endpoint requires admin role
        response = client.post("/v1/api/test/accounts", json=account_data)
        if response.status_code != 201:
            print(f"Failed to create account: {response.text}")
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def get_accounts(client: TestClient, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all accounts through the API.
        """
        response = client.get(f"/v1/api/accounts?skip={skip}&limit={limit}")
        if response.status_code != 200:
            print(f"Failed to get accounts: {response.text}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def get_account(client: TestClient, account_id: Union[UUID, str]) -> Dict[str, Any]:
        """
        Get a specific account through the API.
        """
        response = client.get(f"/v1/api/accounts/{account_id}")
        if response.status_code != 200:
            print(f"Failed to get account: {response.text}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def update_account(client: TestClient, account_id: Union[UUID, str], update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an account through the API.
        """
        response = client.put(f"/v1/api/accounts/{account_id}", json=update_data)
        if response.status_code != 200:
            print(f"Failed to update account: {response.text}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def delete_account(client: TestClient, account_id: Union[UUID, str]) -> None:
        """
        Delete an account through the API.
        """
        response = client.delete(f"/v1/api/accounts/{account_id}")
        if response.status_code != 204:
            print(f"Failed to delete account: {response.text}")
        assert response.status_code == 204, f"Expected 204, got {response.status_code}: {response.text}"
    
    @staticmethod
    def create_test_restaurant(client: TestClient, account_id: Union[UUID, str], restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a test restaurant through the API.
        """
        response = client.post(f"/v1/api/accounts/{account_id}/restaurants", json=restaurant_data)
        if response.status_code != 201:
            print(f"Failed to create restaurant: {response.text}")
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def create_test_store(client: TestClient, restaurant_id: Union[UUID, str], store_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a test store through the API.
        """
        response = client.post(f"/v1/api/restaurants/{restaurant_id}/stores", json=store_data)
        if response.status_code != 201:
            print(f"Failed to create store: {response.text}")
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def create_test_supplier(client: TestClient, account_id: Union[UUID, str], supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a test supplier through the API.
        """
        response = client.post(f"/v1/api/accounts/{account_id}/suppliers", json=supplier_data)
        if response.status_code != 201:
            print(f"Failed to create supplier: {response.text}")
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def create_test_user(client: TestClient, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a test user through the API.
        """
        # This would need to be implemented based on your user creation endpoint
        # For now, we'll just return mock data
        return {
            "id": str(uuid4()),
            "email": user_data["email"],
            "is_active": True,
            "role": user_data.get("role", "user")
        }
    
    @staticmethod
    def login_user(client: TestClient, email: str, password: str) -> Dict[str, Any]:
        """
        Login a user and get auth tokens.
        """
        response = client.post(
            "/v1/api/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code != 200:
            print(f"Failed to login user: {response.text}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def create_test_bot(client: TestClient, bot_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a test bot through the API.
        """
        response = client.post("/v1/api/bots", json=bot_data)
        if response.status_code != 201:
            print(f"Failed to create bot: {response.text}")
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def create_test_bot_scenario(
        client: TestClient, bot_id: Union[UUID, str], scenario_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Creates a test bot scenario through the API.
        """
        response = client.post(f"/v1/api/bots/{bot_id}/scenarios", json=scenario_data)
        if response.status_code != 201:
            print(f"Failed to create bot scenario: {response.text}")
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def assert_response_format(
        data: Dict[str, Any], 
        expected_fields: List[str], 
        optional_fields: Optional[List[str]] = None
    ) -> None:
        """
        Assert that a response contains expected fields.
        """
        optional_fields = optional_fields or []
        
        for field in expected_fields:
            assert field in data, f"Expected field '{field}' missing from response"
            
        # Optional fields are not required but should be checked for the correct type if present
        for field in optional_fields:
            if field in data:
                assert data[field] is not None, f"Optional field '{field}' is None"