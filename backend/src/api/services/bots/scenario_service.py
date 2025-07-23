from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from src.api.models import BotScenario, BotInstance
from src.api.schemas.bots.scenario_schemas import (
    BotScenarioCreate,
    BotScenarioUpdate,
    BotScenarioDB,
    BotScenarioActivate
)


class ScenarioService:
    @staticmethod
    async def create_scenario(
        db: AsyncSession, scenario: BotScenarioCreate
    ) -> Optional[BotScenarioDB]:
        """Create a new bot scenario"""
        # Check if the bot exists
        query = select(BotInstance).where(BotInstance.id == scenario.bot_id)
        result = await db.execute(query)
        bot_instance = result.scalars().first()
        
        if not bot_instance:
            return None
        
        # Create scenario
        db_scenario = BotScenario(
            bot_id=scenario.bot_id,
            name=scenario.name,
            description=scenario.description,
            version=scenario.version,
            scenario_data=scenario.scenario_data,
            is_active=scenario.is_active
        )
        
        # If this scenario is active, deactivate other scenarios for this bot
        if scenario.is_active:
            await db.execute(
                update(BotScenario)
                .where(
                    BotScenario.bot_id == scenario.bot_id,
                    BotScenario.is_active == True
                )
                .values(is_active=False)
            )
        
        db.add(db_scenario)
        await db.commit()
        await db.refresh(db_scenario)
        
        return BotScenarioDB.model_validate(db_scenario)

    @staticmethod
    async def get_scenario(
        db: AsyncSession, scenario_id: UUID
    ) -> Optional[BotScenarioDB]:
        """Get a scenario by ID"""
        query = select(BotScenario).where(BotScenario.id == scenario_id)
        result = await db.execute(query)
        scenario = result.scalars().first()
        
        if scenario:
            return BotScenarioDB.model_validate(scenario)
        return None

    @staticmethod
    async def get_bot_scenarios(
        db: AsyncSession, bot_id: UUID, active_only: bool = False
    ) -> List[BotScenarioDB]:
        """Get all scenarios for a bot"""
        query = select(BotScenario).where(BotScenario.bot_id == bot_id)
        
        if active_only:
            query = query.where(BotScenario.is_active == True)
            
        query = query.order_by(BotScenario.created_at.desc())
        
        result = await db.execute(query)
        scenarios = result.scalars().all()
        
        return [BotScenarioDB.model_validate(scenario) for scenario in scenarios]

    @staticmethod
    async def update_scenario(
        db: AsyncSession,
        scenario_id: UUID,
        scenario_update: BotScenarioUpdate
    ) -> Optional[BotScenarioDB]:
        """Update a scenario"""
        query = select(BotScenario).where(BotScenario.id == scenario_id)
        result = await db.execute(query)
        db_scenario = result.scalars().first()
        
        if not db_scenario:
            return None
        
        update_data = scenario_update.model_dump(exclude_unset=True)
        
        # If setting to active, deactivate other scenarios for this bot
        if update_data.get("is_active", False) and not db_scenario.is_active:
            await db.execute(
                update(BotScenario)
                .where(
                    BotScenario.bot_id == db_scenario.bot_id,
                    BotScenario.id != scenario_id,
                    BotScenario.is_active == True
                )
                .values(is_active=False)
            )
        
        for key, value in update_data.items():
            setattr(db_scenario, key, value)
            
        await db.commit()
        await db.refresh(db_scenario)
        
        return BotScenarioDB.model_validate(db_scenario)

    @staticmethod
    async def activate_scenario(
        db: AsyncSession,
        scenario_id: UUID,
        activate: BotScenarioActivate
    ) -> Optional[BotScenarioDB]:
        """Activate or deactivate a scenario"""
        query = select(BotScenario).where(BotScenario.id == scenario_id)
        result = await db.execute(query)
        db_scenario = result.scalars().first()
        
        if not db_scenario:
            return None
        
        # If activating, deactivate other scenarios for this bot
        if activate.is_active and not db_scenario.is_active:
            await db.execute(
                update(BotScenario)
                .where(
                    BotScenario.bot_id == db_scenario.bot_id,
                    BotScenario.id != scenario_id,
                    BotScenario.is_active == True
                )
                .values(is_active=False)
            )
        
        db_scenario.is_active = activate.is_active
        await db.commit()
        await db.refresh(db_scenario)
        
        return BotScenarioDB.model_validate(db_scenario)

    @staticmethod
    async def delete_scenario(
        db: AsyncSession, scenario_id: UUID
    ) -> bool:
        """Delete a scenario"""
        result = await db.execute(
            delete(BotScenario)
            .where(BotScenario.id == scenario_id)
        )
        await db.commit()
        
        return result.rowcount > 0

    @staticmethod
    async def get_active_scenario(
        db: AsyncSession, bot_id: UUID
    ) -> Optional[BotScenarioDB]:
        """Get the active scenario for a bot"""
        query = select(BotScenario).where(
            BotScenario.bot_id == bot_id,
            BotScenario.is_active == True
        )
        result = await db.execute(query)
        scenario = result.scalars().first()
        
        if scenario:
            return BotScenarioDB.model_validate(scenario)
        return None