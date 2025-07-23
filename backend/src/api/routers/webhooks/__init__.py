"""
Webhook handler routers package.
"""
from fastapi import APIRouter

from src.api.routers.webhooks.telegram import router as telegram_router

# Keep prefix empty here as main.py already adds the API_V1_STR prefix (/v1/api)
router = APIRouter()

router.include_router(telegram_router)