from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.orm import joinedload

from src.api.models import BotInstance, BotPlatformCredential, Account
from src.api.schemas.bots.instance_schemas import (
    BotInstanceCreate,
    BotInstanceUpdate,
    BotInstanceDB,
    BotPlatformCredentialCreate,
    BotPlatformCredentialUpdate,
    BotPlatformCredentialDB
)


class InstanceService:
    @staticmethod
    async def create_bot_instance(
        db: AsyncSession, bot_instance: BotInstanceCreate
    ) -> Optional[BotInstanceDB]:
        """Create a new bot instance"""
        # Check if the account exists
        query = select(Account).where(Account.id == bot_instance.account_id)
        result = await db.execute(query)
        account = result.scalars().first()
        
        if not account:
            return None
        
        # Create bot instance
        db_bot = BotInstance(
            name=bot_instance.name,
            description=bot_instance.description,
            account_id=bot_instance.account_id,
            is_active=bot_instance.is_active
        )
        
        db.add(db_bot)
        await db.flush()  # Get the ID without committing yet
        
        # Add platform credentials if provided
        for credential in bot_instance.platform_credentials:
            db_credential = BotPlatformCredential(
                bot_id=db_bot.id,
                platform=credential.platform,
                credentials=credential.credentials,
                is_active=credential.is_active
            )
            db.add(db_credential)
        
        await db.commit()
        await db.refresh(db_bot)
        
        return await InstanceService.get_bot_instance(db, db_bot.id)

    @staticmethod
    async def get_bot_instance(
        db: AsyncSession, bot_id: UUID
    ) -> Optional[BotInstanceDB]:
        """Get a bot instance by ID with its platform credentials"""
        query = (
            select(BotInstance)
            .options(joinedload(BotInstance.platform_credentials))
            .where(BotInstance.id == bot_id)
        )
        result = await db.execute(query)
        bot = result.unique().scalars().first()
        
        if bot:
            return BotInstanceDB.model_validate(bot)
        return None

    @staticmethod
    async def get_account_bots(
        db: AsyncSession, account_id: UUID
    ) -> List[BotInstanceDB]:
        """Get all bots for a specific account"""
        query = (
            select(BotInstance)
            .options(joinedload(BotInstance.platform_credentials))
            .where(BotInstance.account_id == account_id)
            .order_by(BotInstance.created_at)
        )
        result = await db.execute(query)
        bots = result.unique().scalars().all()
        
        return [BotInstanceDB.model_validate(bot) for bot in bots]

    @staticmethod
    async def update_bot_instance(
        db: AsyncSession,
        bot_id: UUID,
        bot_update: BotInstanceUpdate
    ) -> Optional[BotInstanceDB]:
        """Update an existing bot instance"""
        query = select(BotInstance).where(BotInstance.id == bot_id)
        result = await db.execute(query)
        db_bot = result.scalars().first()
        
        if not db_bot:
            return None
        
        update_data = bot_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_bot, key, value)
            
        await db.commit()
        await db.refresh(db_bot)
        
        return await InstanceService.get_bot_instance(db, bot_id)

    @staticmethod
    async def delete_bot_instance(db: AsyncSession, bot_id: UUID) -> bool:
        """Delete a bot instance and all associated data"""
        # First, check if the bot exists
        query = select(BotInstance).where(BotInstance.id == bot_id)
        result = await db.execute(query)
        bot = result.unique().scalars().first()
        
        if not bot:
            return False
        
        # Delete will cascade to related tables due to relationship settings
        await db.delete(bot)
        await db.commit()
        
        return True

    @staticmethod
    async def activate_bot(
        db: AsyncSession, bot_id: UUID, activate: bool = True
    ) -> Optional[BotInstanceDB]:
        """Activate or deactivate a bot"""
        query = select(BotInstance).where(BotInstance.id == bot_id)
        result = await db.execute(query)
        db_bot = result.scalars().first()
        
        if not db_bot:
            return None
        
        db_bot.is_active = activate
        await db.commit()
        await db.refresh(db_bot)
        
        return await InstanceService.get_bot_instance(db, bot_id)

    @staticmethod
    async def add_platform_credential(
        db: AsyncSession,
        bot_id: UUID,
        credential: BotPlatformCredentialCreate
    ) -> Optional[BotPlatformCredentialDB]:
        """Add platform credentials to a bot"""
        # Check if bot exists
        query = select(BotInstance).where(BotInstance.id == bot_id)
        result = await db.execute(query)
        bot = result.unique().scalars().first()
        
        if not bot:
            return None
        
        # Check if credentials for this platform already exist
        query = select(BotPlatformCredential).where(
            BotPlatformCredential.bot_id == bot_id,
            BotPlatformCredential.platform == credential.platform
        )
        result = await db.execute(query)
        existing_credential = result.scalars().first()
        
        if existing_credential:
            # Update existing credential
            for key, value in credential.model_dump(exclude={"bot_id"}).items():
                setattr(existing_credential, key, value)
            
            await db.commit()
            await db.refresh(existing_credential)
            return BotPlatformCredentialDB.model_validate(existing_credential)
        
        # Create new credential
        db_credential = BotPlatformCredential(
            bot_id=bot_id,
            platform=credential.platform,
            credentials=credential.credentials,
            is_active=credential.is_active
        )
        
        db.add(db_credential)
        await db.commit()
        await db.refresh(db_credential)
        
        return BotPlatformCredentialDB.model_validate(db_credential)

    @staticmethod
    async def update_platform_credential(
        db: AsyncSession,
        bot_id: UUID,
        platform: str,
        credential_update: BotPlatformCredentialUpdate
    ) -> Optional[BotPlatformCredentialDB]:
        """Update platform credentials for a bot"""
        query = select(BotPlatformCredential).where(
            BotPlatformCredential.bot_id == bot_id,
            BotPlatformCredential.platform == platform
        )
        result = await db.execute(query)
        db_credential = result.scalars().first()
        
        if not db_credential:
            return None
        
        update_data = credential_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_credential, key, value)
            
        await db.commit()
        await db.refresh(db_credential)
        
        return BotPlatformCredentialDB.model_validate(db_credential)

    @staticmethod
    async def get_platform_credential(
        db: AsyncSession,
        bot_id: UUID,
        platform: str
    ) -> Optional[BotPlatformCredentialDB]:
        """Get platform credentials for a bot"""
        query = select(BotPlatformCredential).where(
            BotPlatformCredential.bot_id == bot_id,
            BotPlatformCredential.platform == platform
        )
        result = await db.execute(query)
        credential = result.scalars().first()
        
        if credential:
            return BotPlatformCredentialDB.model_validate(credential)
        return None

    @staticmethod
    async def delete_platform_credential(
        db: AsyncSession,
        bot_id: UUID,
        platform: str
    ) -> bool:
        """Delete platform credentials for a bot"""
        result = await db.execute(
            delete(BotPlatformCredential)
            .where(
                BotPlatformCredential.bot_id == bot_id,
                BotPlatformCredential.platform == platform
            )
        )
        await db.commit()
        
        return result.rowcount > 0
        
    @staticmethod
    async def get_bot_platform_credentials(
        db: AsyncSession,
        bot_id: UUID
    ) -> List[BotPlatformCredentialDB]:
        """Get all platform credentials for a bot"""
        query = select(BotPlatformCredential).where(
            BotPlatformCredential.bot_id == bot_id
        ).order_by(BotPlatformCredential.created_at)
        
        result = await db.execute(query)
        credentials = result.scalars().all()
        
        return [BotPlatformCredentialDB.model_validate(cred) for cred in credentials]