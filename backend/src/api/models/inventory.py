"""
Inventory management models: InventoryItem, InventoryStock, Unit, etc.
"""
from src.api.models.base import *


class UnitCategory(Base):
    __tablename__ = "unit_category"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)  # 'weight', 'volume', 'count'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    units = relationship("Unit", back_populates="category")


class Unit(Base):
    __tablename__ = "unit"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=True)  # NULL means global unit
    name = Column(String, nullable=False)  # 'kilogram', 'liter', 'piece'
    symbol = Column(String, nullable=False)  # 'kg', 'L', 'pc'
    unit_category_id = Column(UUID(as_uuid=True), ForeignKey("unit_category.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="units")
    category = relationship("UnitCategory", back_populates="units")
    from_conversions = relationship(
        "UnitConversion",
        foreign_keys="[UnitConversion.from_unit_id]",
        back_populates="from_unit",
        cascade="all, delete-orphan",
    )
    to_conversions = relationship(
        "UnitConversion",
        foreign_keys="[UnitConversion.to_unit_id]",
        back_populates="to_unit",
        cascade="all, delete-orphan",
    )
    inventory_items = relationship("InventoryItem", back_populates="default_unit")
    inventory_stock = relationship("InventoryStock", back_populates="unit")
    invoice_items = relationship("InvoiceItem", back_populates="unit")
    price_history = relationship("InventoryItemPriceHistory", back_populates="unit")
    recipes = relationship("Recipe", back_populates="yield_unit")
    recipe_ingredients = relationship("RecipeIngredient", back_populates="unit")


class UnitConversion(Base):
    __tablename__ = "unit_conversion"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=True)
    from_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    to_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    conversion_factor = Column(Numeric(15, 6), nullable=False)  # e.g., 1000 for kg to g
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    from_unit = relationship("Unit", foreign_keys=[from_unit_id], back_populates="from_conversions")
    to_unit = relationship("Unit", foreign_keys=[to_unit_id], back_populates="to_conversions")


class InventoryItem(Base):
    __tablename__ = "inventory_item"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    default_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    category = Column(String, nullable=True)
    item_type = Column(String, nullable=False)  # 'raw_ingredient', 'semi_finished', 'finished_product'
    current_cost_per_unit = Column(Numeric(10, 2), nullable=True)
    reorder_level = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="inventory_items")
    default_unit = relationship("Unit", back_populates="inventory_items")
    stock = relationship("InventoryStock", back_populates="inventory_item", cascade="all, delete-orphan")
    price_history = relationship("InventoryItemPriceHistory", back_populates="inventory_item", cascade="all, delete-orphan")
    invoice_items = relationship("InvoiceItem", back_populates="inventory_item")
    recipe_ingredients = relationship("RecipeIngredient", back_populates="inventory_item")
    specific_conversions = relationship("ItemSpecificUnitConversion", back_populates="inventory_item", cascade="all, delete-orphan")


class ItemSpecificUnitConversion(Base):
    __tablename__ = "inventory_item_units"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_item.id"), nullable=False)
    from_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    to_unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    conversion_factor = Column(Numeric(15, 6), nullable=False)  # e.g., 0.91 for 1 pack = 0.91 kg
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    inventory_item = relationship("InventoryItem", back_populates="specific_conversions")
    from_unit = relationship("Unit", foreign_keys=[from_unit_id])
    to_unit = relationship("Unit", foreign_keys=[to_unit_id])


class InventoryStock(Base):
    __tablename__ = "inventory_stock"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"), nullable=False)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_item.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    store = relationship("Store", back_populates="inventory_stock")
    inventory_item = relationship("InventoryItem", back_populates="stock")
    unit = relationship("Unit", back_populates="inventory_stock")


class InventoryItemPriceHistory(Base):
    __tablename__ = "inventory_item_price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_item.id"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"), nullable=False)
    price_date = Column(Date, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("unit.id"), nullable=False)
    source = Column(String, nullable=False)  # 'invoice', 'manual_update', 'system_calculated'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    inventory_item = relationship("InventoryItem", back_populates="price_history")
    store = relationship("Store", back_populates="price_history")
    unit = relationship("Unit", back_populates="price_history")