"""
Bot management router package.
"""
from fastapi import APIRouter

from src.api.routers.bots.instances import router as instance_router
from src.api.routers.bots.platforms import router as platform_router
from src.api.routers.bots.dialogs import router as dialog_router
from src.api.routers.bots.scenarios import router as scenario_router
from src.api.routers.bots.media import router as media_router

# Keep prefix empty here as main.py already adds the API_V1_STR prefix (/v1/api)
router = APIRouter()

router.include_router(instance_router)
router.include_router(platform_router)
router.include_router(dialog_router)
router.include_router(scenario_router)
router.include_router(media_router)