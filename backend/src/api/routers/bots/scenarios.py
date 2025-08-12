from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import json

from src.api.dependencies.async_db import get_async_db
from src.api.dependencies.auth import get_current_user
from src.api.dependencies.permissions import require_bot_access
from src.api.core.logging_config import get_logger
from src.api.core.exceptions import BadRequestError, NotFoundError
from src.api.schemas.bots.scenario_schemas import (
    BotScenarioCreate,
    BotScenarioUpdate,
    BotScenarioActivate,
    BotScenarioUpload,
    BotScenarioDB
)
from src.api.services.bots.scenario_service import ScenarioService
from src.api.services.bots.instance_service import InstanceService
from src.api.utils.error_handlers import handle_router_errors
from src.api.utils.validation import validate_json_data, validate_scenario_data
from src.api.utils.user_helpers import get_user_role, get_user_account_id

logger = get_logger("scenario_router")


router = APIRouter(
    tags=["bots"],
    responses={404: {"description": "Not found"}},
)


@router.post("/bots/{bot_id}/scenarios", response_model=BotScenarioDB, status_code=status.HTTP_201_CREATED)
@handle_router_errors("create scenario")
async def create_scenario(
    bot_id: UUID,
    scenario: BotScenarioCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict[str, Any] = Depends(require_bot_access)
) -> BotScenarioDB:
    """
    Create a new scenario for a bot.
    """
    # Ensure bot_id in path matches the one in the request body
    if str(scenario.bot_id) != str(bot_id):
        raise BadRequestError(
            detail="Bot ID in path must match bot_id in request body"
        )
    
    # Validate scenario data structure
    validate_scenario_data(scenario.scenario_data)
    
    created_scenario = await ScenarioService.create_scenario(db, scenario)
    if not created_scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to create scenario"
        )
    return created_scenario


@router.post("/bots/{bot_id}/scenarios/upload", response_model=BotScenarioDB, status_code=status.HTTP_201_CREATED)
async def upload_scenario(
    bot_id: UUID,
    upload: BotScenarioUpload,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Upload a scenario from JSON content.
    """
    try:
        # Check if bot exists and user has permission
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to upload scenarios for this bot"
            )
        
        # Parse uploaded JSON content
        try:
            scenario_data = json.loads(upload.file_content)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON content"
            )
        
        # Create scenario with uploaded content
        scenario_create = BotScenarioCreate(
            bot_id=bot_id,
            name=f"Uploaded Scenario {scenario_data.get('name', '')}",
            description=f"Uploaded from JSON file",
            version="1.0",
            scenario_data=scenario_data,
            is_active=True
        )
        
        created_scenario = await ScenarioService.create_scenario(db, scenario_create)
        if not created_scenario:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create scenario from uploaded content"
            )
        return created_scenario
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading scenario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload scenario: {str(e)}"
        )


@router.get("/bots/{bot_id}/scenarios", response_model=List[BotScenarioDB])
async def get_bot_scenarios(
    bot_id: UUID,
    active_only: bool = False,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get all scenarios for a bot.
    """
    try:
        # Check if bot exists
        bot = await InstanceService.get_bot_instance(db, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view scenarios for this bot"
            )
        
        scenarios = await ScenarioService.get_bot_scenarios(db, bot_id, active_only)
        return scenarios
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot scenarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot scenarios: {str(e)}"
        )


@router.get("/scenarios/{scenario_id}", response_model=BotScenarioDB)
async def get_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get a specific scenario by ID.
    """
    try:
        scenario = await ScenarioService.get_scenario(db, scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, scenario.bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this scenario"
            )
        
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scenario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scenario: {str(e)}"
        )


@router.put("/scenarios/{scenario_id}", response_model=BotScenarioDB)
async def update_scenario(
    scenario_id: UUID,
    scenario_update: BotScenarioUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Update a specific scenario.
    """
    try:
        # Get the existing scenario to check permissions
        existing_scenario = await ScenarioService.get_scenario(db, scenario_id)
        if not existing_scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, existing_scenario.bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this scenario"
            )
        
        # Update the scenario
        updated_scenario = await ScenarioService.update_scenario(db, scenario_id, scenario_update)
        if not updated_scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found or update failed"
            )
        return updated_scenario
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scenario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scenario: {str(e)}"
        )


@router.post("/scenarios/{scenario_id}/activate", response_model=BotScenarioDB)
async def activate_scenario(
    scenario_id: UUID,
    activation: BotScenarioActivate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Activate or deactivate a scenario.
    """
    try:
        # Get the existing scenario to check permissions
        existing_scenario = await ScenarioService.get_scenario(db, scenario_id)
        if not existing_scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, existing_scenario.bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to activate/deactivate this scenario"
            )
        
        # Update the scenario activation state
        updated_scenario = await ScenarioService.activate_scenario(db, scenario_id, activation)
        if not updated_scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found or activation failed"
            )
        return updated_scenario
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating/deactivating scenario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate/deactivate scenario: {str(e)}"
        )


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    Delete a scenario.
    """
    try:
        # Get the existing scenario to check permissions
        existing_scenario = await ScenarioService.get_scenario(db, scenario_id)
        if not existing_scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found"
            )
        
        # Get the bot to check permissions
        bot = await InstanceService.get_bot_instance(db, existing_scenario.bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if current user has permission
        user_role = get_user_role(current_user)
        user_account_id = get_user_account_id(current_user)
        if user_role != "admin" and user_account_id != str(bot.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this scenario"
            )
        
        # Delete the scenario
        result = await ScenarioService.delete_scenario(db, scenario_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found or deletion failed"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scenario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scenario: {str(e)}"
        )