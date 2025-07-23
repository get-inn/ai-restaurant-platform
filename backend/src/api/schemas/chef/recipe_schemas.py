from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class RecipeBase(BaseModel):
    account_id: UUID4
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    yield_quantity: Decimal
    yield_unit_id: UUID4


class RecipeCreate(RecipeBase):
    ingredients: List["RecipeIngredientCreate"] = []


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    yield_quantity: Optional[Decimal] = None
    yield_unit_id: Optional[UUID4] = None


class RecipeResponse(RecipeBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecipeIngredientBase(BaseModel):
    recipe_id: UUID4
    inventory_item_id: UUID4
    quantity: Decimal
    unit_id: UUID4


class RecipeIngredientCreate(BaseModel):
    inventory_item_id: UUID4
    quantity: Decimal
    unit_id: UUID4


class RecipeIngredientUpdate(BaseModel):
    inventory_item_id: Optional[UUID4] = None
    quantity: Optional[Decimal] = None
    unit_id: Optional[UUID4] = None


class RecipeIngredientResponse(RecipeIngredientBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecipeDetailResponse(RecipeResponse):
    ingredients: List[RecipeIngredientResponse]
    estimated_cost: Optional[Decimal] = None


class RecipeCostBreakdown(BaseModel):
    recipe_id: UUID4
    recipe_name: str
    total_cost: Decimal
    cost_per_serving: Decimal
    yield_quantity: Decimal
    yield_unit: str
    ingredients: List["IngredientCost"]


class IngredientCost(BaseModel):
    ingredient_id: UUID4
    ingredient_name: str
    quantity: Decimal
    unit: str
    cost_per_unit: Decimal
    total_cost: Decimal
    percentage_of_total: float


# Update forward references
RecipeCreate.update_forward_refs()