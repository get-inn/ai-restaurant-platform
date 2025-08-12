from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.api.dependencies.async_db import get_async_db
from src.api.dependencies.auth import get_current_user
from src.api.dependencies.permissions import (
    require_account_access,
    require_bot_access,
    check_admin_role
)
from src.api.core.logging_config import get_logger
from src.api.core.exceptions import BadRequestError, NotFoundError
from src.api.schemas.bots.instance_schemas import (
    BotInstanceCreate,
    BotInstanceUpdate,
    BotInstanceDB
)
from src.api.services.bots.instance_service import InstanceService
from src.api.utils.error_handlers import handle_router_errors
from src.api.utils.user_helpers import get_user_role, get_user_account_id
from src.api.utils.validation import validate_pagination_params

logger = get_logger("bot_router")


router = APIRouter(
    tags=["bots"],
    responses={404: {"description": "Not found"}},
)


@router.post("/accounts/{account_id}/bots", response_model=BotInstanceDB, status_code=status.HTTP_201_CREATED)
@handle_router_errors("create bot instance")
async def create_bot_instance(
    account_id: UUID,
    bot_data: BotInstanceCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict[str, Any] = Depends(require_account_access)
) -> BotInstanceDB:
    """
    Create a new bot instance for an account.
    """
    # Ensure account_id in path matches the one in the request body
    if str(account_id) != str(bot_data.account_id):
        raise BadRequestError(
            detail="Account ID in path must match account ID in request body"
        )
    
    bot_instance = await InstanceService.create_bot_instance(db, bot_data)
    if not bot_instance:
        raise NotFoundError(detail="Account not found")
    
    return bot_instance


@router.get("/accounts/{account_id}/bots", response_model=List[BotInstanceDB])
@handle_router_errors("get account bots")
async def get_account_bots(
    account_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict[str, Any] = Depends(require_account_access)
) -> List[BotInstanceDB]:
    """
    Get all bots for an account.
    """
    bots = await InstanceService.get_account_bots(db, account_id)
    return bots


@router.get("/bots/{bot_id}", response_model=BotInstanceDB)
@handle_router_errors("get bot")
async def get_bot(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict[str, Any] = Depends(require_bot_access)
) -> BotInstanceDB:
    """
    Get a bot by ID.
    """
    bot = await InstanceService.get_bot_instance(db, bot_id)
    if not bot:
        raise NotFoundError(detail="Bot not found")
    
    return bot


@router.put("/bots/{bot_id}", response_model=BotInstanceDB)
@handle_router_errors("update bot instance")
async def update_bot_instance(
    bot_id: UUID,
    bot_update: BotInstanceUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict[str, Any] = Depends(require_bot_access)
) -> BotInstanceDB:
    """
    Update a bot instance.
    """
    updated_bot = await InstanceService.update_bot_instance(db, bot_id, bot_update)
    if not updated_bot:
        raise NotFoundError(detail="Bot not found")
    
    return updated_bot


@router.delete("/bots/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_router_errors("delete bot instance")
async def delete_bot_instance(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict[str, Any] = Depends(require_bot_access)
) -> None:
    """
    Delete a bot instance and all associated data.
    """
    success = await InstanceService.delete_bot_instance(db, bot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bot"
        )


@router.post("/bots/{bot_id}/activate", response_model=BotInstanceDB)
@handle_router_errors("activate bot")
async def activate_bot(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict[str, Any] = Depends(require_bot_access)
) -> BotInstanceDB:
    """
    Activate a bot.
    """
    bot_instance = await InstanceService.activate_bot(db, bot_id, True)
    if not bot_instance:
        raise NotFoundError(detail="Bot not found")
    
    return bot_instance


@router.post("/bots/{bot_id}/deactivate", response_model=BotInstanceDB)
@handle_router_errors("deactivate bot")
async def deactivate_bot(
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict[str, Any] = Depends(require_bot_access)
) -> BotInstanceDB:
    """
    Deactivate a bot.
    """
    bot_instance = await InstanceService.activate_bot(db, bot_id, False)
    if not bot_instance:
        raise NotFoundError(detail="Bot not found")
    
    return bot_instance


@router.get("/bots", response_model=List[BotInstanceDB])
@handle_router_errors("get all bots")
async def get_all_bots(
    account_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[BotInstanceDB]:
    """
    Get all bots, optionally filtered by account ID.
    """
    # Validate pagination parameters
    skip, limit = validate_pagination_params(skip, limit)
    
    user_role = get_user_role(current_user)
    user_account_id = get_user_account_id(current_user)
    
    if account_id:
        # Check permission for specific account
        if user_role != "admin" and user_account_id != str(account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view bots for this account"
            )
        return await InstanceService.get_account_bots(db, account_id)
    
    # If no account_id is provided and user is not admin, return only bots for their account
    if user_role != "admin" and user_account_id:
        return await InstanceService.get_account_bots(db, UUID(user_account_id))
    
    # Admin can see all bots
    if user_role == "admin":
        return await InstanceService.get_all_bots_admin(
            db, skip=skip, limit=limit
        )
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to view all bots"
    )