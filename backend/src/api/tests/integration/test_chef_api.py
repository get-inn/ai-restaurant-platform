"""
Integration tests for the chef API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any, List
from uuid import uuid4

from src.api.tests.base import BaseAPITest


@pytest.mark.chef
class TestChefAPI(BaseAPITest):
    """
    Tests for chef-related endpoints in the API.
    """

    def test_create_menu(self, authorized_client: TestClient) -> None:
        """
        Test creating a new menu.
        """
        # Create test menu data
        menu_data = {
            "name": "Summer Special Menu",
            "restaurant_id": str(uuid4()),
            "description": "Summer seasonal specials",
            "is_active": True,
            "start_date": "2023-06-01",
            "end_date": "2023-08-31",
            "category": "seasonal"
        }
        
        response = authorized_client.post(
            self.get_api_v1_url("/chef/menus"), 
            json=menu_data
        )
        
        # Assert successful menu creation
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == menu_data["name"]
        assert data["restaurant_id"] == menu_data["restaurant_id"]
        assert data["description"] == menu_data["description"]
        assert data["is_active"] == menu_data["is_active"]
        assert "created_at" in data

    def test_get_menu_by_id(self, authorized_client: TestClient) -> None:
        """
        Test retrieving a menu by ID.
        """
        # Create a mock menu ID
        menu_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/chef/menus/{menu_id}")
        )
        
        # In the current implementation, this might return a mock object or 404
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["id"] == menu_id
            assert "name" in data
            assert "restaurant_id" in data
        else:
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_get_menus(self, authorized_client: TestClient) -> None:
        """
        Test retrieving all menus.
        """
        # Create a restaurant ID for filtering
        restaurant_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/chef/menus?restaurant_id={restaurant_id}")
        )
        
        # Assert successful menus retrieval
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_menu(self, authorized_client: TestClient) -> None:
        """
        Test updating a menu.
        """
        # Create a mock menu ID
        menu_id = str(uuid4())
        
        # Update data
        update_data = {
            "name": "Updated Summer Menu",
            "description": "Updated summer seasonal specials",
            "is_active": False
        }
        
        response = authorized_client.put(
            self.get_api_v1_url(f"/chef/menus/{menu_id}"),
            json=update_data
        )
        
        # Assert successful menu update
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == menu_id
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["is_active"] == update_data["is_active"]
        assert "updated_at" in data

    def test_delete_menu(self, authorized_client: TestClient) -> None:
        """
        Test deleting a menu.
        """
        # Create a mock menu ID
        menu_id = str(uuid4())
        
        response = authorized_client.delete(
            self.get_api_v1_url(f"/chef/menus/{menu_id}")
        )
        
        # Assert successful menu deletion
        assert response.status_code == 204
        assert response.content == b''  # No content in response

    def test_create_recipe(self, authorized_client: TestClient) -> None:
        """
        Test creating a new recipe.
        """
        # Create test recipe data
        recipe_data = {
            "name": "Pasta Carbonara",
            "restaurant_id": str(uuid4()),
            "description": "Traditional Italian pasta dish with eggs and pancetta",
            "cuisine_type": "Italian",
            "preparation_time": 30,  # minutes
            "cooking_time": 15,  # minutes
            "servings": 4,
            "ingredients": [
                {
                    "name": "Spaghetti",
                    "amount": 400,
                    "unit": "g"
                },
                {
                    "name": "Pancetta",
                    "amount": 200,
                    "unit": "g"
                },
                {
                    "name": "Eggs",
                    "amount": 4,
                    "unit": "units"
                },
                {
                    "name": "Parmesan",
                    "amount": 100,
                    "unit": "g"
                }
            ],
            "instructions": [
                "Cook pasta according to package instructions",
                "Fry pancetta until crispy",
                "Beat eggs with grated parmesan",
                "Mix everything while pasta is hot",
                "Serve immediately with extra parmesan"
            ],
            "nutrition_info": {
                "calories": 650,
                "protein": 30,
                "carbs": 70,
                "fat": 25
            },
            "tags": ["pasta", "italian", "quick", "egg-based"]
        }
        
        response = authorized_client.post(
            self.get_api_v1_url("/chef/recipes"), 
            json=recipe_data
        )
        
        # Assert successful recipe creation
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == recipe_data["name"]
        assert data["restaurant_id"] == recipe_data["restaurant_id"]
        assert data["description"] == recipe_data["description"]
        assert "ingredients" in data
        assert len(data["ingredients"]) == len(recipe_data["ingredients"])
        assert "instructions" in data
        assert len(data["instructions"]) == len(recipe_data["instructions"])
        assert "created_at" in data

    def test_get_recipe_by_id(self, authorized_client: TestClient) -> None:
        """
        Test retrieving a recipe by ID.
        """
        # Create a mock recipe ID
        recipe_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/chef/recipes/{recipe_id}")
        )
        
        # In the current implementation, this might return a mock object or 404
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["id"] == recipe_id
            assert "name" in data
            assert "restaurant_id" in data
            assert "ingredients" in data
            assert "instructions" in data
        else:
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_get_recipes(self, authorized_client: TestClient) -> None:
        """
        Test retrieving recipes with filters.
        """
        # Create a restaurant ID for filtering
        restaurant_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/chef/recipes?restaurant_id={restaurant_id}&cuisine_type=Italian")
        )
        
        # Assert successful recipes retrieval
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_recipe(self, authorized_client: TestClient) -> None:
        """
        Test updating a recipe.
        """
        # Create a mock recipe ID
        recipe_id = str(uuid4())
        
        # Update data
        update_data = {
            "name": "Updated Pasta Carbonara",
            "description": "Updated traditional Italian pasta dish",
            "cooking_time": 20,
            "servings": 2,
            "instructions": [
                "Cook pasta according to package instructions",
                "Fry pancetta until crispy",
                "Beat eggs with grated parmesan",
                "Mix everything while pasta is hot",
                "Add freshly ground black pepper",
                "Serve immediately with extra parmesan"
            ]
        }
        
        response = authorized_client.put(
            self.get_api_v1_url(f"/chef/recipes/{recipe_id}"),
            json=update_data
        )
        
        # Assert successful recipe update
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == recipe_id
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["cooking_time"] == update_data["cooking_time"]
        assert data["servings"] == update_data["servings"]
        assert "instructions" in data
        assert len(data["instructions"]) == len(update_data["instructions"])
        assert "updated_at" in data

    def test_add_recipe_to_menu(self, authorized_client: TestClient) -> None:
        """
        Test adding a recipe to a menu.
        """
        # Create mock IDs
        menu_id = str(uuid4())
        recipe_id = str(uuid4())
        
        # Menu item data
        menu_item_data = {
            "recipe_id": recipe_id,
            "price": 12.99,
            "section": "Main Courses",
            "position": 3,
            "is_featured": True,
            "notes": "Chef's recommendation"
        }
        
        response = authorized_client.post(
            self.get_api_v1_url(f"/chef/menus/{menu_id}/items"),
            json=menu_item_data
        )
        
        # Assert successful menu item creation
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["menu_id"] == menu_id
        assert data["recipe_id"] == recipe_id
        assert data["price"] == menu_item_data["price"]
        assert data["section"] == menu_item_data["section"]
        assert data["position"] == menu_item_data["position"]
        assert data["is_featured"] == menu_item_data["is_featured"]

    def test_get_menu_items(self, authorized_client: TestClient) -> None:
        """
        Test retrieving items from a menu.
        """
        # Create a mock menu ID
        menu_id = str(uuid4())
        
        response = authorized_client.get(
            self.get_api_v1_url(f"/chef/menus/{menu_id}/items")
        )
        
        # Assert successful menu items retrieval
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # If there are items, check their structure
        if len(data) > 0:
            item = data[0]
            assert "id" in item
            assert "menu_id" in item
            assert "recipe_id" in item
            assert "price" in item
            assert "section" in item