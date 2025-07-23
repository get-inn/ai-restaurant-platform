# Import chef schemas for easier access

from src.api.schemas.chef.recipe_schemas import (
    RecipeBase,
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeIngredientBase,
    RecipeIngredientCreate,
    RecipeIngredientUpdate,
    RecipeIngredientResponse,
    RecipeDetailResponse,
    RecipeCostBreakdown,
    IngredientCost,
)

from src.api.schemas.chef.menu_schemas import (
    MenuBase,
    MenuCreate,
    MenuUpdate,
    MenuResponse,
    MenuItemBase,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    MenuItemAssignment,
    MenuContainsMenuItemBase,
    MenuContainsMenuItemCreate,
    MenuContainsMenuItemUpdate,
    MenuContainsMenuItemResponse,
    MenuDetailResponse,
    MenuItemWithDetails,
)

from src.api.schemas.chef.analysis_schemas import (
    ABCCategory,
    SalesDataBase,
    SalesDataCreate,
    SalesDataResponse,
    SalesDataBatchCreate,
    MenuItemPerformance,
    ABCAnalysisParameters,
    ABCAnalysisResult,
    MenuInsight,
    NutritionalInfo,
    RecipeAnalysis,
)