"""
Integration tests for the authentication API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any

from src.api.tests.base import BaseAPITest
from src.api.tests.utils import APITestUtils


@pytest.mark.auth
class TestAuthAPI(BaseAPITest):
    """
    Tests for authentication endpoints in the API.
    """

    def test_login_valid_credentials(self, test_client: TestClient, test_user: Dict[str, Any]) -> None:
        """
        Test that a user can login with valid credentials.
        """
        # First create a test user (assuming you have a user creation endpoint)
        # For testing, we'll use the test user fixture directly

        # Try logging in
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        response = test_client.post(self.get_api_v1_url("/auth/login"), json=login_data)
        
        # Assert successful login
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, test_client: TestClient) -> None:
        """
        Test that login fails with invalid credentials.
        """
        login_data = {
            "email": "wrong@example.com",
            "password": "wrongpassword"
        }
        response = test_client.post(self.get_api_v1_url("/auth/login"), json=login_data)
        
        # Assert failed login
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect email or password" in data["detail"]

    def test_refresh_token_valid(self, test_client: TestClient, test_user: Dict[str, Any]) -> None:
        """
        Test that a user can refresh their access token with a valid refresh token.
        """
        # First login to get tokens
        login_response = APITestUtils.login_user(
            test_client, test_user["email"], test_user["password"]
        )
        
        # Try to refresh the token
        refresh_data = {"refresh_token": login_response["refresh_token"]}
        response = test_client.post(self.get_api_v1_url("/auth/refresh"), json=refresh_data)
        
        # Assert successful token refresh
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data

    def test_refresh_token_invalid(self, test_client: TestClient) -> None:
        """
        Test that token refresh fails with invalid refresh token.
        """
        refresh_data = {"refresh_token": "invalid_token"}
        response = test_client.post(self.get_api_v1_url("/auth/refresh"), json=refresh_data)
        
        # Assert failed token refresh
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid refresh token" in data["detail"]

    def test_logout(self, authorized_client: TestClient) -> None:
        """
        Test that a user can logout.
        """
        response = authorized_client.post(self.get_api_v1_url("/auth/logout"))
        
        # Assert successful logout
        assert response.status_code == 200
        data = response.json()
        assert "detail" in data
        assert "Successfully logged out" in data["detail"]

    def test_me_authenticated(self, authorized_client: TestClient) -> None:
        """
        Test that an authenticated user can get their profile.
        """
        response = authorized_client.get(self.get_api_v1_url("/auth/me"))
        
        # Assert successful profile retrieval
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "role" in data

    def test_me_unauthenticated(self, test_client: TestClient) -> None:
        """
        Test that an unauthenticated request to /me fails.
        """
        response = test_client.get(self.get_api_v1_url("/auth/me"))
        
        # Assert unauthorized access
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data