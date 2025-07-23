# Import routers to make them available for main.py
from src.api.routers import auth, accounts, bots
from src.api.routers.chef import menu_router, recipe_router

__all__ = ["auth", "accounts", "menu_router", "recipe_router", "bots"]