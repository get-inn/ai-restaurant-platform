"""
Integration tests for the dashboard API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime, timedelta

from src.api.tests.base import BaseAPITest


@pytest.mark.dashboard
class TestDashboardAPI(BaseAPITest):
    """
    Tests for dashboard-related endpoints in the API.
    """

    def test_get_sales_summary(self, authorized_client: TestClient) -> None:
        """
        Test retrieving sales summary data.
        """
        # Create mock date parameters
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        restaurant_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/dashboard/sales?restaurant_id={restaurant_id}&start_date={start_date}&end_date={end_date}")
        )
        
        # Assert successful sales data retrieval
        assert response.status_code == 200
        data = response.json()
        assert "total_sales" in data
        assert "average_order_value" in data
        assert "sales_by_day" in data
        assert isinstance(data["sales_by_day"], list)
        assert "sales_by_category" in data
        assert isinstance(data["sales_by_category"], list)

    def test_get_inventory_summary(self, authorized_client: TestClient) -> None:
        """
        Test retrieving inventory summary data.
        """
        restaurant_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/dashboard/inventory?restaurant_id={restaurant_id}")
        )
        
        # Assert successful inventory data retrieval
        assert response.status_code == 200
        data = response.json()
        assert "total_items" in data
        assert "low_stock_items" in data
        assert isinstance(data["low_stock_items"], list)
        assert "inventory_value" in data
        assert "inventory_by_category" in data
        assert isinstance(data["inventory_by_category"], list)

    def test_get_labor_summary(self, authorized_client: TestClient) -> None:
        """
        Test retrieving labor summary data.
        """
        # Create mock date parameters
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        restaurant_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/dashboard/labor?restaurant_id={restaurant_id}&start_date={start_date}&end_date={end_date}")
        )
        
        # Assert successful labor data retrieval
        assert response.status_code == 200
        data = response.json()
        assert "total_hours" in data
        assert "total_labor_cost" in data
        assert "labor_cost_percentage" in data
        assert "hours_by_department" in data
        assert isinstance(data["hours_by_department"], list)
        assert "hours_by_day" in data
        assert isinstance(data["hours_by_day"], list)

    def test_get_customer_insights(self, authorized_client: TestClient) -> None:
        """
        Test retrieving customer insights data.
        """
        restaurant_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/dashboard/customers?restaurant_id={restaurant_id}")
        )
        
        # Assert successful customer data retrieval
        assert response.status_code == 200
        data = response.json()
        assert "total_customers" in data
        assert "new_customers" in data
        assert "repeat_customers" in data
        assert "average_visits_per_customer" in data
        assert "customer_retention_rate" in data
        assert "top_customers" in data
        assert isinstance(data["top_customers"], list)

    def test_get_supplier_performance(self, authorized_client: TestClient) -> None:
        """
        Test retrieving supplier performance data.
        """
        restaurant_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/dashboard/suppliers?restaurant_id={restaurant_id}")
        )
        
        # Assert successful supplier data retrieval
        assert response.status_code == 200
        data = response.json()
        assert "total_suppliers" in data
        assert "total_orders" in data
        assert "total_spend" in data
        assert "on_time_delivery_rate" in data
        assert "supplier_performance" in data
        assert isinstance(data["supplier_performance"], list)

    def test_get_food_waste_metrics(self, authorized_client: TestClient) -> None:
        """
        Test retrieving food waste metrics.
        """
        # Create mock date parameters
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        restaurant_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/dashboard/waste?restaurant_id={restaurant_id}&start_date={start_date}&end_date={end_date}")
        )
        
        # Assert successful waste data retrieval
        assert response.status_code == 200
        data = response.json()
        assert "total_waste_weight" in data
        assert "total_waste_cost" in data
        assert "waste_percentage" in data
        assert "waste_by_category" in data
        assert isinstance(data["waste_by_category"], list)
        assert "waste_by_day" in data
        assert isinstance(data["waste_by_day"], list)

    def test_get_menu_performance(self, authorized_client: TestClient) -> None:
        """
        Test retrieving menu performance metrics.
        """
        restaurant_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/dashboard/menu-performance?restaurant_id={restaurant_id}")
        )
        
        # Assert successful menu performance data retrieval
        assert response.status_code == 200
        data = response.json()
        assert "top_selling_items" in data
        assert isinstance(data["top_selling_items"], list)
        assert "least_selling_items" in data
        assert isinstance(data["least_selling_items"], list)
        assert "highest_profit_items" in data
        assert isinstance(data["highest_profit_items"], list)
        assert "sales_by_menu_section" in data
        assert isinstance(data["sales_by_menu_section"], list)

    def test_get_dashboard_summary(self, authorized_client: TestClient) -> None:
        """
        Test retrieving overall dashboard summary.
        """
        restaurant_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/dashboard/summary?restaurant_id={restaurant_id}")
        )
        
        # Assert successful dashboard summary retrieval
        assert response.status_code == 200
        data = response.json()
        assert "sales" in data
        assert "inventory" in data
        assert "labor" in data
        assert "customers" in data
        assert "menu" in data
        
        # Check that each section has at least some key metrics
        assert "total_sales" in data["sales"]
        assert "total_items" in data["inventory"]
        assert "total_hours" in data["labor"]
        assert "total_customers" in data["customers"]
        assert "top_selling_items" in data["menu"]