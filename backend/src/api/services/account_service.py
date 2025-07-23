from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from datetime import datetime

from src.api.models import Account
from src.api.schemas.account_schemas import AccountCreate, AccountUpdate, AccountResponse


class AccountService:
    @staticmethod
    async def create_account(db: AsyncSession, account_data: AccountCreate) -> Account:
        """Create a new account."""
        db_account = Account(
            name=account_data.name,
        )
        db.add(db_account)
        await db.commit()
        await db.refresh(db_account)
        return db_account

    @staticmethod
    async def get_account(db: AsyncSession, account_id: UUID) -> Optional[Account]:
        """Get an account by ID."""
        query = select(Account).where(Account.id == account_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_accounts(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Account]:
        """Get a list of accounts with pagination."""
        query = select(Account).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_account(
        db: AsyncSession, account_id: UUID, account_data: AccountUpdate
    ) -> Optional[Account]:
        """Update an account."""
        # Check if account exists
        query = select(Account).where(Account.id == account_id)
        result = await db.execute(query)
        db_account = result.scalars().first()
        
        if not db_account:
            return None

        # Update fields that are provided
        update_data = account_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_account, key, value)
        
        await db.commit()
        await db.refresh(db_account)
        return db_account

    @staticmethod
    async def delete_account(db: AsyncSession, account_id: UUID) -> bool:
        """Delete an account."""
        query = select(Account).where(Account.id == account_id)
        result = await db.execute(query)
        db_account = result.scalars().first()
        
        if not db_account:
            return False
        
        await db.delete(db_account)
        await db.commit()
        return True