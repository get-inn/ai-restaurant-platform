"""
Labor management models: StaffOnboarding, OnboardingStep, etc.
"""
from src.api.models.base import *


class StaffOnboarding(Base):
    __tablename__ = "staff_onboarding"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    position = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="in_progress")  # 'in_progress', 'completed', 'terminated'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="staff_onboarding")
    steps = relationship("OnboardingStep", back_populates="staff_onboarding", cascade="all, delete-orphan")


class OnboardingStep(Base):
    __tablename__ = "onboarding_step"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_onboarding_id = Column(UUID(as_uuid=True), ForeignKey("staff_onboarding.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")  # 'pending', 'in_progress', 'completed', 'failed'
    completion_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    staff_onboarding = relationship("StaffOnboarding", back_populates="steps")