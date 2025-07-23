from pydantic import BaseModel, UUID4, validator
from typing import Optional, List
from datetime import datetime


class AccountBase(BaseModel):
    name: str


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None


class AccountResponse(AccountBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RestaurantBase(BaseModel):
    name: str
    account_id: UUID4


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    account_id: Optional[UUID4] = None


class RestaurantResponse(RestaurantBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StoreBase(BaseModel):
    name: str
    restaurant_id: UUID4


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    restaurant_id: Optional[UUID4] = None


class StoreResponse(StoreBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierBase(BaseModel):
    name: str
    account_id: UUID4
    contact_info: Optional[dict] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    account_id: Optional[UUID4] = None
    contact_info: Optional[dict] = None


class SupplierResponse(SupplierBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True