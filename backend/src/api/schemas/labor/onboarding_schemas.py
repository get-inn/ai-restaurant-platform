from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class StaffStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class StaffOnboardingBase(BaseModel):
    restaurant_id: UUID4
    name: str
    email: Optional[str] = None
    position: str
    start_date: date
    status: StaffStatus = StaffStatus.IN_PROGRESS


class StaffOnboardingCreate(StaffOnboardingBase):
    steps: Optional[List["OnboardingStepCreate"]] = None


class StaffOnboardingUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    start_date: Optional[date] = None
    status: Optional[StaffStatus] = None


class StaffOnboardingResponse(StaffOnboardingBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OnboardingStepBase(BaseModel):
    staff_onboarding_id: UUID4
    name: str
    description: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    completion_date: Optional[date] = None
    notes: Optional[str] = None


class OnboardingStepCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    completion_date: Optional[date] = None
    notes: Optional[str] = None


class OnboardingStepUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[StepStatus] = None
    completion_date: Optional[date] = None
    notes: Optional[str] = None


class OnboardingStepResponse(OnboardingStepBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StaffOnboardingDetailResponse(StaffOnboardingResponse):
    steps: List[OnboardingStepResponse]
    completion_percentage: float


class OnboardingSummary(BaseModel):
    restaurant_id: UUID4
    restaurant_name: str
    total_staff: int
    in_progress: int
    completed: int
    terminated: int
    recent_completions: List[StaffOnboardingResponse]
    recent_additions: List[StaffOnboardingResponse]


# Update forward references
StaffOnboardingCreate.update_forward_refs()