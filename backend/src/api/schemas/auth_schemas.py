from pydantic import BaseModel, UUID4
from typing import Optional
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    ADMIN = "admin"
    ACCOUNT_MANAGER = "account_manager" 
    RESTAURANT_MANAGER = "restaurant_manager"
    CHEF = "chef"
    STAFF = "staff"


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str
    role: UserRole
    account_id: Optional[UUID4] = None
    restaurant_id: Optional[UUID4] = None


class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    account_id: Optional[UUID4] = None
    restaurant_id: Optional[UUID4] = None


class UserResponse(UserBase):
    id: UUID4
    role: UserRole
    account_id: Optional[UUID4] = None
    restaurant_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int  # expiration timestamp


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str