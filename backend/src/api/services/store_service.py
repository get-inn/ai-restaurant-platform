from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from datetime import datetime

from src.api.models import Store
from src.api.schemas.account_schemas import StoreCreate, StoreUpdate, StoreResponse


class StoreService:
    @staticmethod
    async def create_store(db: AsyncSession, store_data: StoreCreate) -> Store:
        """Create a new store."""
        db_store = Store(
            name=store_data.name,
            restaurant_id=store_data.restaurant_id,
        )
        db.add(db_store)
        await db.commit()
        await db.refresh(db_store)
        return db_store

    @staticmethod
    async def get_store(db: AsyncSession, store_id: UUID) -> Optional[Store]:
        """Get a store by ID."""
        query = select(Store).where(Store.id == store_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_stores(db: AsyncSession, 
                         restaurant_id: Optional[UUID] = None,
                         skip: int = 0, 
                         limit: int = 100) -> List[Store]:
        """Get a list of stores with pagination."""
        query = select(Store)
        if restaurant_id:
            query = query.where(Store.restaurant_id == restaurant_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_store(
        db: AsyncSession, store_id: UUID, store_data: StoreUpdate
    ) -> Optional[Store]:
        """Update a store."""
        # Check if store exists
        query = select(Store).where(Store.id == store_id)
        result = await db.execute(query)
        db_store = result.scalars().first()
        
        if not db_store:
            return None

        # Update fields that are provided
        update_data = store_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_store, key, value)
        
        await db.commit()
        await db.refresh(db_store)
        return db_store

    @staticmethod
    async def delete_store(db: AsyncSession, store_id: UUID) -> bool:
        """Delete a store."""
        query = select(Store).where(Store.id == store_id)
        result = await db.execute(query)
        db_store = result.scalars().first()
        
        if not db_store:
            return False
        
        await db.delete(db_store)
        await db.commit()
        return True