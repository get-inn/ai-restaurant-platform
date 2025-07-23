"""
Chef management models: Recipe, Menu, MenuItem, etc.
"""
from src.api.models.base import *


class Recipe(Base):
    __tablename__ = "recipe"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    yield_quantity = Column(Numeric(10, 2), nullable=False)
    yield_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="recipes")
    yield_unit = relationship("Unit", back_populates="recipes")
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="recipe")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredient"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipe.id"), nullable=False)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_item.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    inventory_item = relationship("InventoryItem", back_populates="recipe_ingredients")
    unit = relationship("Unit", back_populates="recipe_ingredients")


class Menu(Base):
    __tablename__ = "menu"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(Time, nullable=True)  # NULL means all day
    end_time = Column(Time, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="menus")
    menu_items = relationship("MenuContainsMenuItem", back_populates="menu", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_item"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    base_price = Column(Numeric(10, 2), nullable=False)
    category = Column(String, nullable=True)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipe.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="menu_items")
    recipe = relationship("Recipe", back_populates="menu_items")
    menus = relationship("MenuContainsMenuItem", back_populates="menu_item", cascade="all, delete-orphan")
    sales = relationship("SalesData", back_populates="menu_item", cascade="all, delete-orphan")


class MenuContainsMenuItem(Base):
    __tablename__ = "menu_contains_menu_item"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menu_id = Column(UUID(as_uuid=True), ForeignKey("menu.id"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_item.id"), nullable=False)
    display_order = Column(Integer, nullable=True)
    price_override = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    menu = relationship("Menu", back_populates="menu_items")
    menu_item = relationship("MenuItem", back_populates="menus")