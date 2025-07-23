from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from datetime import datetime

from src.api.models import Restaurant
from src.api.schemas.account_schemas import RestaurantCreate, RestaurantUpdate, RestaurantResponse


class RestaurantService:
    @staticmethod
    async def create_restaurant(db: AsyncSession, restaurant_data: RestaurantCreate) -> Restaurant:
        """Create a new restaurant."""
        db_restaurant = Restaurant(
            name=restaurant_data.name,
            account_id=restaurant_data.account_id,
        )
        db.add(db_restaurant)
        await db.commit()
        await db.refresh(db_restaurant)
        return db_restaurant

    @staticmethod
    async def get_restaurant(db: AsyncSession, restaurant_id: UUID) -> Optional[Restaurant]:
        """Get a restaurant by ID."""
        query = select(Restaurant).where(Restaurant.id == restaurant_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_restaurants(db: AsyncSession, 
                              account_id: Optional[UUID] = None, 
                              skip: int = 0, 
                              limit: int = 100) -> List[Restaurant]:
        """Get a list of restaurants with pagination."""
        query = select(Restaurant)
        if account_id:
            query = query.where(Restaurant.account_id == account_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_restaurant(
        db: AsyncSession, restaurant_id: UUID, restaurant_data: RestaurantUpdate
    ) -> Optional[Restaurant]:
        """Update a restaurant."""
        # Check if restaurant exists
        query = select(Restaurant).where(Restaurant.id == restaurant_id)
        result = await db.execute(query)
        db_restaurant = result.scalars().first()
        
        if not db_restaurant:
            return None

        # Update fields that are provided
        update_data = restaurant_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_restaurant, key, value)
        
        await db.commit()
        await db.refresh(db_restaurant)
        return db_restaurant

    @staticmethod
    async def delete_restaurant(db: AsyncSession, restaurant_id: UUID) -> bool:
        """Delete a restaurant."""
        query = select(Restaurant).where(Restaurant.id == restaurant_id)
        result = await db.execute(query)
        db_restaurant = result.scalars().first()
        
        if not db_restaurant:
            return False
        
        await db.delete(db_restaurant)
        await db.commit()
        return True