"""
Integration tests for the supplier API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
from uuid import uuid4

from src.api.tests.base import BaseAPITest
from src.api.tests.utils import APITestUtils


@pytest.mark.supplier
class TestSupplierAPI(BaseAPITest):
    """
    Tests for supplier management endpoints in the API.
    """

    def test_create_reconciliation(self, authorized_client: TestClient) -> None:
        """
        Test creating a supplier reconciliation.
        """
        # Create test data
        reconciliation_data = {
            "supplier_id": str(uuid4()),
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "notes": "Monthly reconciliation"
        }
        
        response = authorized_client.post(
            self.get_api_v1_url("/supplier/reconciliations"), 
            json=reconciliation_data
        )
        
        # Assert successful reconciliation creation
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["supplier_id"] == reconciliation_data["supplier_id"]
        assert data["start_date"] == reconciliation_data["start_date"]
        assert data["end_date"] == reconciliation_data["end_date"]
        assert data["notes"] == reconciliation_data["notes"]

    def test_get_reconciliations(self, authorized_client: TestClient) -> None:
        """
        Test retrieving supplier reconciliations.
        """
        # Create a supplier ID for filtering
        supplier_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/supplier/reconciliations?supplier_id={supplier_id}")
        )
        
        # Assert successful reconciliations retrieval
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_reconciliation_by_id(self, authorized_client: TestClient) -> None:
        """
        Test retrieving a reconciliation by ID.
        """
        # Create test data and mock ID
        reconciliation_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/supplier/reconciliations/{reconciliation_id}")
        )
        
        # In the current implementation, this might return a mock object or 404
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["id"] == reconciliation_id
        else:
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_create_document(self, authorized_client: TestClient) -> None:
        """
        Test creating a supplier document.
        """
        # Create test data
        document_data = {
            "supplier_id": str(uuid4()),
            "document_type": "invoice",
            "document_number": "INV-12345",
            "issue_date": "2023-01-15",
            "total_amount": 1250.50,
            "currency": "USD",
            "status": "pending"
        }
        
        response = authorized_client.post(
            self.get_api_v1_url("/supplier/documents"), 
            json=document_data
        )
        
        # Assert successful document creation
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["supplier_id"] == document_data["supplier_id"]
        assert data["document_type"] == document_data["document_type"]
        assert data["document_number"] == document_data["document_number"]
        assert data["total_amount"] == document_data["total_amount"]

    def test_get_documents(self, authorized_client: TestClient) -> None:
        """
        Test retrieving supplier documents.
        """
        # Create a supplier ID for filtering
        supplier_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/supplier/documents?supplier_id={supplier_id}")
        )
        
        # Assert successful documents retrieval
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_invoice(self, authorized_client: TestClient) -> None:
        """
        Test creating a supplier invoice.
        """
        # Create test data
        invoice_data = {
            "supplier_id": str(uuid4()),
            "invoice_number": "INV-54321",
            "issue_date": "2023-02-15",
            "due_date": "2023-03-15",
            "total_amount": 2500.75,
            "currency": "USD",
            "status": "unpaid",
            "items": [
                {
                    "description": "Product 1",
                    "quantity": 5,
                    "unit_price": 100.15,
                    "total_price": 500.75
                },
                {
                    "description": "Product 2",
                    "quantity": 10,
                    "unit_price": 200.0,
                    "total_price": 2000.0
                }
            ]
        }
        
        response = authorized_client.post(
            self.get_api_v1_url("/supplier/invoices"), 
            json=invoice_data
        )
        
        # Assert successful invoice creation
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["supplier_id"] == invoice_data["supplier_id"]
        assert data["invoice_number"] == invoice_data["invoice_number"]
        assert data["total_amount"] == invoice_data["total_amount"]
        assert "items" in data
        assert len(data["items"]) == 2

    def test_get_invoices(self, authorized_client: TestClient) -> None:
        """
        Test retrieving supplier invoices.
        """
        # Create a supplier ID for filtering
        supplier_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/supplier/invoices?supplier_id={supplier_id}")
        )
        
        # Assert successful invoices retrieval
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_inventory(self, authorized_client: TestClient) -> None:
        """
        Test creating a supplier inventory item.
        """
        # Create test data
        inventory_data = {
            "supplier_id": str(uuid4()),
            "item_name": "Test Product",
            "item_code": "TP-123",
            "unit": "kg",
            "unit_price": 15.50,
            "currency": "USD",
            "minimum_order_quantity": 10,
            "is_active": True
        }
        
        response = authorized_client.post(
            self.get_api_v1_url("/supplier/inventory"), 
            json=inventory_data
        )
        
        # Assert successful inventory item creation
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["supplier_id"] == inventory_data["supplier_id"]
        assert data["item_name"] == inventory_data["item_name"]
        assert data["item_code"] == inventory_data["item_code"]
        assert data["unit_price"] == inventory_data["unit_price"]

    def test_get_inventory(self, authorized_client: TestClient) -> None:
        """
        Test retrieving supplier inventory.
        """
        # Create a supplier ID for filtering
        supplier_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/supplier/inventory?supplier_id={supplier_id}")
        )
        
        # Assert successful inventory retrieval
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_supplier(self, authorized_client: TestClient, test_supplier: Dict[str, Any]) -> None:
        """
        Test updating supplier details.
        """
        # Create a supplier ID
        supplier_id = str(uuid4())
        
        # Update data
        update_data = {
            "name": "Updated Supplier Name",
            "contact_info": {
                "phone": "+9876543210",
                "email": "updated@example.com"
            }
        }
        
        response = authorized_client.put(
            self.get_api_v1_url(f"/supplier/suppliers/{supplier_id}"),
            json=update_data
        )
        
        # Assert successful supplier update
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == supplier_id
        assert data["name"] == update_data["name"]
        assert data["contact_info"]["email"] == update_data["contact_info"]["email"]