"""
Core entity models: Account, Restaurant, Store, UserProfile, etc.
"""
from src.api.models.base import *

class Account(Base):
    __tablename__ = "account"
    __table_args__ = {'schema': 'getinn_ops'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurants = relationship("Restaurant", back_populates="account", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="account", cascade="all, delete-orphan")
    users = relationship("UserProfile", back_populates="account")
    inventory_items = relationship("InventoryItem", back_populates="account", cascade="all, delete-orphan")
    recipes = relationship("Recipe", back_populates="account", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="account", cascade="all, delete-orphan")
    units = relationship("Unit", back_populates="account")
    integration_credentials = relationship("AccountIntegrationCredentials", back_populates="account", cascade="all, delete-orphan")
    
    # Bot management relationships
    bots = relationship("BotInstance", back_populates="account", cascade="all, delete-orphan")


class AccountIntegrationCredentials(Base):
    """Account-specific integration credentials"""
    __tablename__ = "account_integration_credentials"
    __table_args__ = (
        UniqueConstraint('account_id', 'integration_type', name='uix_account_integration_type'),
        {'schema': 'getinn_ops'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("getinn_ops.account.id"), nullable=False)
    integration_type = Column(Enum(IntegrationType), nullable=False)  # 'iiko', 'r_keeper', etc.
    credentials = Column(JSONB, nullable=False)  # Encrypted credentials
    base_url = Column(String, nullable=True)  # Optional custom URL
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_connected_at = Column(DateTime, nullable=True)
    connection_status = Column(String, nullable=True)
    connection_error = Column(String, nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="integration_credentials")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('account_id', 'integration_type', name='uix_account_integration_type'),
    )


class Restaurant(Base):
    __tablename__ = "restaurant"
    __table_args__ = {'schema': 'getinn_ops'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("getinn_ops.account.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # External system integration fields
    external_id = Column(String, nullable=True, index=True)
    external_sync_status = Column(Enum(SyncStatus), nullable=True)
    external_system_type = Column(Enum(IntegrationType), nullable=True)
    external_last_synced_at = Column(DateTime, nullable=True)
    external_sync_error = Column(String, nullable=True)
    external_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="restaurants")
    stores = relationship("Store", back_populates="restaurant", cascade="all, delete-orphan")
    users = relationship("UserProfile", back_populates="restaurant")
    menus = relationship("Menu", back_populates="restaurant", cascade="all, delete-orphan")
    staff_onboarding = relationship("StaffOnboarding", back_populates="restaurant", cascade="all, delete-orphan")
    sales_data = relationship("SalesData", back_populates="restaurant", cascade="all, delete-orphan")


class Store(Base):
    __tablename__ = "store"
    __table_args__ = {'schema': 'getinn_ops'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("getinn_ops.restaurant.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # External system integration fields
    external_id = Column(String, nullable=True, index=True)
    external_sync_status = Column(Enum(SyncStatus), nullable=True)
    external_system_type = Column(Enum(IntegrationType), nullable=True)
    external_last_synced_at = Column(DateTime, nullable=True)
    external_sync_error = Column(String, nullable=True)
    external_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="stores")
    inventory_stock = relationship("InventoryStock", back_populates="store", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="store", cascade="all, delete-orphan")
    price_history = relationship("InventoryItemPriceHistory", back_populates="store", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profile"
    __table_args__ = {'schema': 'getinn_ops'}
    
    id = Column(UUID(as_uuid=True), primary_key=True)  # Maps to Supabase auth.users.id
    account_id = Column(UUID(as_uuid=True), ForeignKey("getinn_ops.account.id"), nullable=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("getinn_ops.restaurant.id"), nullable=True)
    role = Column(String, nullable=False)  # 'admin', 'account_manager', 'restaurant_manager', 'chef'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="users")
    restaurant = relationship("Restaurant", back_populates="users")