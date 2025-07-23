"""
Integration tests for the external integrations API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
from uuid import uuid4

from src.api.tests.base import BaseAPITest


@pytest.mark.integrations
class TestIntegrationsAPI(BaseAPITest):
    """
    Tests for external integration endpoints in the API.
    """

    def test_connect_iiko(self, authorized_client: TestClient) -> None:
        """
        Test connecting to iiko integration.
        """
        # Create test connection data
        connection_data = {
            "restaurant_id": str(uuid4()),
            "api_key": "test-api-key",
            "server_url": "https://api.iiko.example.com",
            "organization_id": "org-123456",
            "is_test_mode": True,
            "connection_name": "Test iiko Connection"
        }
        
        response = authorized_client.post(
            self.get_api_v1_url("/integrations/iiko/connect"), 
            json=connection_data
        )
        
        # Assert successful connection
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["restaurant_id"] == connection_data["restaurant_id"]
        assert data["status"] == "connected"
        assert "connection_id" in data
        assert "created_at" in data

    def test_disconnect_iiko(self, authorized_client: TestClient) -> None:
        """
        Test disconnecting from iiko integration.
        """
        # Create a mock connection ID
        connection_id = str(uuid4())
        
        response = authorized_client.post(
            self.get_api_v1_url(f"/integrations/iiko/disconnect/{connection_id}")
        )
        
        # Assert successful disconnection
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disconnected"
        assert data["connection_id"] == connection_id

    def test_get_iiko_connection_status(self, authorized_client: TestClient) -> None:
        """
        Test retrieving iiko connection status.
        """
        # Create a mock connection ID
        connection_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/integrations/iiko/status/{connection_id}")
        )
        
        # Assert successful status retrieval
        assert response.status_code == 200
        data = response.json()
        assert "connection_id" in data
        assert "status" in data
        assert "last_sync_time" in data
        assert "error_message" in data or data["status"] == "connected"

    def test_sync_iiko_menu(self, authorized_client: TestClient) -> None:
        """
        Test synchronizing menu data from iiko.
        """
        # Create a mock connection ID
        connection_id = str(uuid4())
        
        response = authorized_client.post(
            self.get_api_v1_url(f"/integrations/iiko/sync/menu/{connection_id}")
        )
        
        # Assert successful sync
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "sync_id" in data
        assert "items_synced" in data
        assert "errors" in data

    def test_sync_iiko_inventory(self, authorized_client: TestClient) -> None:
        """
        Test synchronizing inventory data from iiko.
        """
        # Create a mock connection ID
        connection_id = str(uuid4())
        
        response = authorized_client.post(
            self.get_api_v1_url(f"/integrations/iiko/sync/inventory/{connection_id}")
        )
        
        # Assert successful sync
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "sync_id" in data
        assert "items_synced" in data
        assert "errors" in data

    def test_get_iiko_organizations(self, authorized_client: TestClient) -> None:
        """
        Test retrieving available iiko organizations.
        """
        # Create test API credentials
        credentials = {
            "api_key": "test-api-key",
            "server_url": "https://api.iiko.example.com"
        }
        
        response = authorized_client.post(
            self.get_api_v1_url("/integrations/iiko/organizations"), 
            json=credentials
        )
        
        # Assert successful organizations retrieval
        assert response.status_code == 200
        data = response.json()
        assert "organizations" in data
        assert isinstance(data["organizations"], list)
        
        # If there are organizations, check their structure
        if len(data["organizations"]) > 0:
            organization = data["organizations"][0]
            assert "id" in organization
            assert "name" in organization

    def test_get_iiko_terminals(self, authorized_client: TestClient) -> None:
        """
        Test retrieving available iiko terminals.
        """
        # Create a mock connection ID
        connection_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/integrations/iiko/terminals/{connection_id}")
        )
        
        # Assert successful terminals retrieval
        assert response.status_code == 200
        data = response.json()
        assert "terminals" in data
        assert isinstance(data["terminals"], list)
        
        # If there are terminals, check their structure
        if len(data["terminals"]) > 0:
            terminal = data["terminals"][0]
            assert "id" in terminal
            assert "name" in terminal
            assert "status" in terminal

    def test_get_iiko_sales_report(self, authorized_client: TestClient) -> None:
        """
        Test retrieving sales report from iiko.
        """
        # Create a mock connection ID
        connection_id = str(uuid4())
        
        # Report parameters
        report_params = {
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "report_type": "summary"
        }
        
        response = authorized_client.post(
            self.get_api_v1_url(f"/integrations/iiko/reports/sales/{connection_id}"), 
            json=report_params
        )
        
        # Assert successful report retrieval
        assert response.status_code == 200
        data = response.json()
        assert "report_data" in data
        assert "report_date" in data
        assert "currency" in data

    def test_get_iiko_mapping_status(self, authorized_client: TestClient) -> None:
        """
        Test retrieving iiko data mapping status.
        """
        # Create a mock connection ID
        connection_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/integrations/iiko/mapping/status/{connection_id}")
        )
        
        # Assert successful mapping status retrieval
        assert response.status_code == 200
        data = response.json()
        assert "menu_items_mapped" in data
        assert "inventory_items_mapped" in data
        assert "categories_mapped" in data
        assert "unmapped_items" in data
        assert isinstance(data["unmapped_items"], list)