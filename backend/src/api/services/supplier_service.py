from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from datetime import datetime

from src.api.models import Supplier
from src.api.schemas.account_schemas import SupplierCreate, SupplierUpdate, SupplierResponse


class SupplierService:
    @staticmethod
    async def create_supplier(db: AsyncSession, supplier_data: SupplierCreate) -> Supplier:
        """Create a new supplier."""
        db_supplier = Supplier(
            name=supplier_data.name,
            account_id=supplier_data.account_id,
            contact_info=supplier_data.contact_info,
        )
        db.add(db_supplier)
        await db.commit()
        await db.refresh(db_supplier)
        return db_supplier

    @staticmethod
    async def get_supplier(db: AsyncSession, supplier_id: UUID) -> Optional[Supplier]:
        """Get a supplier by ID."""
        query = select(Supplier).where(Supplier.id == supplier_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_suppliers(db: AsyncSession, 
                           account_id: Optional[UUID] = None,
                           skip: int = 0, 
                           limit: int = 100) -> List[Supplier]:
        """Get a list of suppliers with pagination."""
        query = select(Supplier)
        if account_id:
            query = query.where(Supplier.account_id == account_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_supplier(
        db: AsyncSession, supplier_id: UUID, supplier_data: SupplierUpdate
    ) -> Optional[Supplier]:
        """Update a supplier."""
        # Check if supplier exists
        query = select(Supplier).where(Supplier.id == supplier_id)
        result = await db.execute(query)
        db_supplier = result.scalars().first()
        
        if not db_supplier:
            return None

        # Update fields that are provided
        update_data = supplier_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_supplier, key, value)
        
        await db.commit()
        await db.refresh(db_supplier)
        return db_supplier

    @staticmethod
    async def delete_supplier(db: AsyncSession, supplier_id: UUID) -> bool:
        """Delete a supplier."""
        query = select(Supplier).where(Supplier.id == supplier_id)
        result = await db.execute(query)
        db_supplier = result.scalars().first()
        
        if not db_supplier:
            return False
        
        await db.delete(db_supplier)
        await db.commit()
        return True