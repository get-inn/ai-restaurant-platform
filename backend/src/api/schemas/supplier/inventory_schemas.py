from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict
from datetime import datetime, date
from enum import Enum
from decimal import Decimal


class ItemType(str, Enum):
    RAW_INGREDIENT = "raw_ingredient"
    SEMI_FINISHED = "semi_finished" 
    FINISHED_PRODUCT = "finished_product"


class InventoryItemBase(BaseModel):
    name: str
    account_id: UUID4
    default_unit_id: UUID4
    description: Optional[str] = None
    category: Optional[str] = None
    item_type: ItemType
    current_cost_per_unit: Optional[Decimal] = None
    reorder_level: Optional[Decimal] = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_unit_id: Optional[UUID4] = None
    category: Optional[str] = None
    item_type: Optional[ItemType] = None
    current_cost_per_unit: Optional[Decimal] = None
    reorder_level: Optional[Decimal] = None


class InventoryItemResponse(InventoryItemBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StockBase(BaseModel):
    store_id: UUID4
    inventory_item_id: UUID4
    quantity: Decimal
    unit_id: UUID4


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    unit_id: Optional[UUID4] = None


class StockResponse(StockBase):
    id: UUID4
    last_updated: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StockAdjustment(BaseModel):
    store_id: UUID4
    inventory_item_id: UUID4
    quantity_change: Decimal  # Can be positive or negative
    unit_id: UUID4
    reason: Optional[str] = None


class PriceHistoryEntry(BaseModel):
    inventory_item_id: UUID4
    store_id: UUID4
    price_date: date
    unit_price: Decimal
    unit_id: UUID4
    source: str  # 'invoice', 'manual_update', 'system_calculated'


class PriceHistoryResponse(PriceHistoryEntry):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UnitCategoryBase(BaseModel):
    name: str


class UnitCategoryResponse(UnitCategoryBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UnitBase(BaseModel):
    name: str
    symbol: str
    unit_category_id: UUID4
    account_id: Optional[UUID4] = None  # NULL means global unit


class UnitCreate(UnitBase):
    pass


class UnitUpdate(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    unit_category_id: Optional[UUID4] = None


class UnitResponse(UnitBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UnitConversionBase(BaseModel):
    from_unit_id: UUID4
    to_unit_id: UUID4
    conversion_factor: Decimal
    account_id: Optional[UUID4] = None  # NULL means global conversion


class UnitConversionCreate(UnitConversionBase):
    pass


class UnitConversionUpdate(BaseModel):
    conversion_factor: Decimal


class UnitConversionResponse(UnitConversionBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemSpecificConversionBase(BaseModel):
    inventory_item_id: UUID4
    from_unit_id: UUID4
    to_unit_id: UUID4
    conversion_factor: Decimal


class ItemSpecificConversionCreate(ItemSpecificConversionBase):
    pass


class ItemSpecificConversionUpdate(BaseModel):
    conversion_factor: Decimal


class ItemSpecificConversionResponse(ItemSpecificConversionBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True