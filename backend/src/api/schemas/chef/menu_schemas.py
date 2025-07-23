from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime, time
from decimal import Decimal


class MenuBase(BaseModel):
    restaurant_id: UUID4
    name: str
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: bool = True


class MenuCreate(MenuBase):
    menu_items: Optional[List["MenuItemAssignment"]] = None


class MenuUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: Optional[bool] = None


class MenuResponse(MenuBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuItemBase(BaseModel):
    account_id: UUID4
    name: str
    description: Optional[str] = None
    base_price: Decimal
    category: Optional[str] = None
    recipe_id: Optional[UUID4] = None


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[Decimal] = None
    category: Optional[str] = None
    recipe_id: Optional[UUID4] = None


class MenuItemResponse(MenuItemBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuItemAssignment(BaseModel):
    menu_item_id: UUID4
    display_order: Optional[int] = None
    price_override: Optional[Decimal] = None


class MenuContainsMenuItemBase(BaseModel):
    menu_id: UUID4
    menu_item_id: UUID4
    display_order: Optional[int] = None
    price_override: Optional[Decimal] = None


class MenuContainsMenuItemCreate(MenuContainsMenuItemBase):
    pass


class MenuContainsMenuItemUpdate(BaseModel):
    display_order: Optional[int] = None
    price_override: Optional[Decimal] = None


class MenuContainsMenuItemResponse(MenuContainsMenuItemBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# First define MenuItemWithDetails before it's referenced
class MenuItemWithDetails(MenuItemResponse):
    display_order: Optional[int] = None
    price_override: Optional[Decimal] = None
    effective_price: Decimal


# Now define MenuDetailResponse after MenuItemWithDetails
class MenuDetailResponse(MenuResponse):
    items: List[MenuItemWithDetails]


# Update forward references
MenuCreate.update_forward_refs()