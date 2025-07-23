from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
from uuid import UUID

from src.api.dependencies.db import get_db
from src.api.dependencies.auth import get_current_user, check_role
from src.api.schemas.auth_schemas import UserRole
from src.api.schemas.account_schemas import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
    StoreCreate,
    StoreUpdate,
    StoreResponse,
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from src.api.core.exceptions import NotFoundError, PermissionDeniedError
from src.api.services.account_service import AccountService
from src.api.services.restaurant_service import RestaurantService
from src.api.services.store_service import StoreService
from src.api.services.supplier_service import SupplierService

router = APIRouter()

# Account endpoints
@router.post("/accounts", response_model=AccountResponse, status_code=201)
async def create_new_account(
    account_data: AccountCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """
    Create new account.
    
    Note: Requires authentication with admin role.
    """
    try:
        # Check if user has admin role
        user_role = current_user.get("role")
        if user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {user_role} not authorized to create accounts"
            )
            
        db_account = await AccountService.create_account(db, account_data)
        return db_account
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}"
        )


@router.get("/accounts", response_model=List[AccountResponse])
async def read_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(check_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve accounts.
    
    Requires admin role.
    """
    accounts = await AccountService.get_accounts(db, skip=skip, limit=limit)
    return accounts


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def read_account(
    account_id: UUID = Path(..., description="The ID of the account to get"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get account by ID.
    
    Admin can access any account.
    Account managers, restaurant managers, etc. can only access their own account.
    """
    account = await AccountService.get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    # Check if user has access to the account (either admin or own account)
    user_role = current_user.get("role")
    user_account_id = current_user.get("account_id")
    
    if user_role != "admin" and str(account_id) != user_account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this account"
        )
    
    return account


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_existing_account(
    account_data: AccountUpdate = Body(...),
    account_id: UUID = Path(..., description="The ID of the account to update"),
    current_user: dict = Depends(check_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update account.
    
    Requires admin role.
    """
    updated_account = await AccountService.update_account(db, account_id, account_data)
    if not updated_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    return updated_account


@router.delete("/accounts/{account_id}", status_code=204)
async def delete_existing_account(
    account_id: UUID = Path(..., description="The ID of the account to delete"),
    current_user: dict = Depends(check_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete account.
    
    Requires admin role.
    """
    result = await AccountService.delete_account(db, account_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )


# Restaurant endpoints
@router.get("/restaurants/{restaurant_id}", response_model=RestaurantResponse)
async def read_restaurant(
    restaurant_id: UUID = Path(..., description="The ID of the restaurant to get"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get restaurant by ID.
    
    Admin can access any restaurant.
    Account managers, restaurant managers, etc. can only access restaurants in their own account.
    """
    restaurant = await RestaurantService.get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID {restaurant_id} not found"
        )
    
    # Check if user has access to the restaurant's account
    user_role = current_user.get("role")
    user_account_id = current_user.get("account_id")
    
    if user_role != "admin" and str(restaurant.account_id) != user_account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this restaurant"
        )
    
    return restaurant

@router.get("/accounts/{account_id}/restaurants", response_model=List[RestaurantResponse])
async def read_restaurants_by_account(
    account_id: UUID = Path(..., description="The ID of the account to get restaurants for"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get restaurants for an account.
    
    Admin can access any account's restaurants.
    Account managers, restaurant managers, etc. can only access restaurants for their own account.
    """
    # First check if account exists
    account = await AccountService.get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    # Check if user has access to the account
    user_role = current_user.get("role")
    user_account_id = current_user.get("account_id")
    
    if user_role != "admin" and str(account_id) != user_account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access restaurants for this account"
        )
    
    # Get restaurants for the account
    restaurants = await RestaurantService.get_restaurants(db, account_id=account_id, skip=skip, limit=limit)
    return restaurants

@router.post("/accounts/{account_id}/restaurants", response_model=RestaurantResponse, status_code=201)
async def create_new_restaurant(
    account_id: UUID,
    restaurant_data: RestaurantCreate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create new restaurant for an account.
    """
    # Check if account exists
    account = await AccountService.get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    # Check if user has access to the account
    user_role = current_user.get("role")
    user_account_id = current_user.get("account_id")
    
    if user_role != "admin" and str(account_id) != user_account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create restaurants for this account"
        )
    
    # Create restaurant with specified account ID
    restaurant_data_with_account = RestaurantCreate(
        name=restaurant_data.name,
        account_id=account_id
    )
    
    restaurant = await RestaurantService.create_restaurant(db, restaurant_data_with_account)
    return restaurant


# Store endpoints
@router.get("/stores/{store_id}", response_model=StoreResponse)
async def read_store(
    store_id: UUID = Path(..., description="The ID of the store to get"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get store by ID.
    
    Admin can access any store.
    Account managers, restaurant managers, etc. can only access stores in their own account.
    """
    store = await StoreService.get_store(db, store_id)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found"
        )
    
    # Get the restaurant to check access permissions
    restaurant = await RestaurantService.get_restaurant(db, store.restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Restaurant not found for this store"
        )
    
    # Check if user has access to the store's restaurant's account
    user_role = current_user.get("role")
    user_account_id = current_user.get("account_id")
    
    if user_role != "admin" and str(restaurant.account_id) != user_account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this store"
        )
    
    return store

@router.get("/restaurants/{restaurant_id}/stores", response_model=List[StoreResponse])
async def read_stores_by_restaurant(
    restaurant_id: UUID = Path(..., description="The ID of the restaurant to get stores for"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get stores for a restaurant.
    
    Admin can access any restaurant's stores.
    Account managers, restaurant managers, etc. can only access stores for restaurants in their own account.
    """
    # First check if restaurant exists
    restaurant = await RestaurantService.get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID {restaurant_id} not found"
        )
    
    # Check if user has access to the restaurant's account
    user_role = current_user.get("role")
    user_account_id = current_user.get("account_id")
    
    if user_role != "admin" and str(restaurant.account_id) != user_account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access stores for this restaurant"
        )
    
    # Get stores for the restaurant
    stores = await StoreService.get_stores(db, restaurant_id=restaurant_id, skip=skip, limit=limit)
    return stores

@router.post("/restaurants/{restaurant_id}/stores", response_model=StoreResponse, status_code=201)
async def create_new_store(
    restaurant_id: UUID,
    store_data: StoreCreate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create new store for a restaurant.
    """
    # Check if restaurant exists
    restaurant = await RestaurantService.get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID {restaurant_id} not found"
        )
    
    # Check if user has access to the restaurant's account
    user_role = current_user.get("role")
    user_account_id = current_user.get("account_id")
    
    if user_role != "admin" and str(restaurant.account_id) != user_account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create stores for this restaurant"
        )
    
    # Create store with specified restaurant ID
    store_data_with_restaurant = StoreCreate(
        name=store_data.name,
        restaurant_id=restaurant_id
    )
    
    store = await StoreService.create_store(db, store_data_with_restaurant)
    return store


# Supplier endpoints
@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def read_supplier(
    supplier_id: UUID = Path(..., description="The ID of the supplier to get"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get supplier by ID.
    
    Admin can access any supplier.
    Account managers, restaurant managers, etc. can only access suppliers in their own account.
    """
    supplier = await SupplierService.get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found"
        )
    
    # Check if user has access to the supplier's account
    user_role = current_user.get("role")
    user_account_id = current_user.get("account_id")
    
    if user_role != "admin" and str(supplier.account_id) != user_account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this supplier"
        )
    
    return supplier

@router.get("/accounts/{account_id}/suppliers", response_model=List[SupplierResponse])
async def read_suppliers_by_account(
    account_id: UUID = Path(..., description="The ID of the account to get suppliers for"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get suppliers for an account.
    
    Admin can access any account's suppliers.
    Account managers, restaurant managers, etc. can only access suppliers for their own account.
    """
    # First check if account exists
    account = await AccountService.get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    # Check if user has access to the account
    user_role = current_user.get("role")
    user_account_id = current_user.get("account_id")
    
    if user_role != "admin" and str(account_id) != user_account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access suppliers for this account"
        )
    
    # Get suppliers for the account
    suppliers = await SupplierService.get_suppliers(db, account_id=account_id, skip=skip, limit=limit)
    return suppliers

@router.post("/accounts/{account_id}/suppliers", response_model=SupplierResponse, status_code=201)
async def create_new_supplier(
    account_id: UUID,
    supplier_data: SupplierCreate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create new supplier for an account.
    """
    # Check if account exists
    account = await AccountService.get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    
    # Check if user has access to the account
    user_role = current_user.get("role")
    user_account_id = current_user.get("account_id")
    
    if user_role != "admin" and str(account_id) != user_account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create suppliers for this account"
        )
    
    # Create supplier with specified account ID
    supplier_data_with_account = SupplierCreate(
        name=supplier_data.name,
        account_id=account_id,
        contact_info=supplier_data.contact_info,
    )
    
    supplier = await SupplierService.create_supplier(db, supplier_data_with_account)
    return supplier