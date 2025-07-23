"""
Analytics models: SalesData and related entities.
"""
from src.api.models.base import *


class SalesData(Base):
    __tablename__ = "sales_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_item.id"), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    sale_price = Column(Numeric(10, 2), nullable=False)
    sale_datetime = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="sales_data")
    menu_item = relationship("MenuItem", back_populates="sales")