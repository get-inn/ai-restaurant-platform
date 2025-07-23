from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from decimal import Decimal


class ABCCategory(str, Enum):
    A = "A"  # High profitability, high sales volume
    B = "B"  # Medium profitability, medium sales volume
    C = "C"  # Low profitability, low sales volume
    D = "D"  # Low profitability, high sales volume (problematic items)


class SalesDataBase(BaseModel):
    restaurant_id: UUID4
    menu_item_id: UUID4
    quantity_sold: int
    sale_price: Decimal
    sale_datetime: datetime


class SalesDataCreate(SalesDataBase):
    pass


class SalesDataResponse(SalesDataBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalesDataBatchCreate(BaseModel):
    sales_data: List[SalesDataCreate]


class MenuItemPerformance(BaseModel):
    menu_item_id: UUID4
    menu_item_name: str
    category: Optional[str] = None
    total_quantity_sold: int
    total_revenue: Decimal
    average_price: Decimal
    cost_per_item: Decimal
    profit_margin: float = Field(..., ge=0, le=1)
    profit_per_item: Decimal
    total_profit: Decimal
    abc_category: ABCCategory


class ABCAnalysisParameters(BaseModel):
    restaurant_id: UUID4
    start_date: date
    end_date: date
    category_filter: Optional[str] = None


class ABCAnalysisResult(BaseModel):
    analysis_date: datetime
    period_start: date
    period_end: date
    items: List[MenuItemPerformance]
    category_summary: Dict[ABCCategory, int]  # Count of items in each category
    profit_summary: Dict[ABCCategory, Decimal]  # Total profit by category


class MenuInsight(BaseModel):
    id: UUID4
    restaurant_id: UUID4
    insight_type: str  # 'recommendation', 'warning', 'observation'
    title: str
    description: str
    related_menu_items: List[UUID4]
    priority: int = Field(..., ge=1, le=5)  # 1 is highest priority, 5 is lowest
    actions: List[str]
    data: Optional[Dict[str, Any]] = None
    created_at: datetime


class NutritionalInfo(BaseModel):
    calories: float
    protein: float  # grams
    carbohydrates: float  # grams
    fat: float  # grams
    fiber: float  # grams
    sugar: float  # grams
    sodium: float  # milligrams
    cholesterol: Optional[float] = None  # milligrams
    saturated_fat: Optional[float] = None  # grams
    trans_fat: Optional[float] = None  # grams
    vitamins: Optional[Dict[str, float]] = None  # percentage of daily value
    minerals: Optional[Dict[str, float]] = None  # percentage of daily value


class RecipeAnalysis(BaseModel):
    recipe_id: UUID4
    recipe_name: str
    serving_size: float
    serving_unit: str
    servings_per_recipe: float
    nutritional_info_per_serving: NutritionalInfo
    total_nutritional_info: NutritionalInfo
    allergens: List[str]
    dietary_flags: List[str]  # vegan, vegetarian, gluten-free, etc.
    analysis_date: datetime
    
    class Config:
        from_attributes = True