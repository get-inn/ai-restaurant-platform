"""
Base service class providing common database operations.
Eliminates duplicate CRUD patterns across services.
"""
from typing import List, Optional, Type, TypeVar, Generic, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func
from sqlalchemy.orm import joinedload
from pydantic import BaseModel

from src.api.core.exceptions import NotFoundError, BotOperationError

# Type variables for generic operations
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """
    Base service class providing common CRUD operations.
    
    Type parameters:
        ModelType: SQLAlchemy model class
        CreateSchemaType: Pydantic schema for creating entities
        UpdateSchemaType: Pydantic schema for updating entities
        ResponseSchemaType: Pydantic schema for responses
    """
    
    def __init__(self, model: Type[ModelType], response_schema: Type[ResponseSchemaType]):
        self.model = model
        self.response_schema = response_schema
    
    async def get_by_id(
        self, 
        db: AsyncSession, 
        entity_id: UUID,
        load_relationships: List[str] = None
    ) -> Optional[ResponseSchemaType]:
        """
        Get entity by ID with optional relationship loading.
        
        Args:
            db: Database session
            entity_id: Entity ID to retrieve
            load_relationships: List of relationship names to eagerly load
            
        Returns:
            Entity if found, None otherwise
        """
        query = select(self.model).where(self.model.id == entity_id)
        
        # Add eager loading for relationships if specified
        if load_relationships:
            for relationship in load_relationships:
                if hasattr(self.model, relationship):
                    query = query.options(joinedload(getattr(self.model, relationship)))
        
        result = await db.execute(query)
        entity = result.unique().scalars().first() if load_relationships else result.scalars().first()
        
        if entity:
            return self.response_schema.model_validate(entity)
        return None
    
    async def get_by_id_or_404(
        self, 
        db: AsyncSession, 
        entity_id: UUID,
        load_relationships: List[str] = None,
        error_message: str = None
    ) -> ResponseSchemaType:
        """
        Get entity by ID or raise 404 error.
        
        Args:
            db: Database session
            entity_id: Entity ID to retrieve
            load_relationships: List of relationship names to eagerly load
            error_message: Custom error message
            
        Returns:
            Entity if found
            
        Raises:
            NotFoundError: If entity not found
        """
        entity = await self.get_by_id(db, entity_id, load_relationships)
        if not entity:
            message = error_message or f"{self.model.__name__} not found"
            raise NotFoundError(detail=message)
        return entity
    
    async def get_multiple(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        load_relationships: List[str] = None
    ) -> List[ResponseSchemaType]:
        """
        Get multiple entities with filtering and pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field->value filters
            order_by: Field name to order by
            load_relationships: List of relationship names to eagerly load
            
        Returns:
            List of entities
        """
        query = select(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        # Add eager loading for relationships if specified
        if load_relationships:
            for relationship in load_relationships:
                if hasattr(self.model, relationship):
                    query = query.options(joinedload(getattr(self.model, relationship)))
        
        # Add ordering
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))
        
        # Add pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        entities = result.unique().scalars().all() if load_relationships else result.scalars().all()
        
        return [self.response_schema.model_validate(entity) for entity in entities]
    
    async def create(
        self,
        db: AsyncSession,
        create_data: CreateSchemaType,
        **additional_fields
    ) -> ResponseSchemaType:
        """
        Create a new entity.
        
        Args:
            db: Database session
            create_data: Data for creating the entity
            **additional_fields: Additional fields to set on the entity
            
        Returns:
            Created entity
        """
        try:
            # Convert Pydantic model to dict and merge with additional fields
            data = create_data.model_dump()
            data.update(additional_fields)
            
            # Create entity instance
            db_entity = self.model(**data)
            
            db.add(db_entity)
            await db.commit()
            await db.refresh(db_entity)
            
            return self.response_schema.model_validate(db_entity)
        
        except Exception as e:
            await db.rollback()
            raise BotOperationError(detail=f"Failed to create {self.model.__name__}: {str(e)}")
    
    async def update(
        self,
        db: AsyncSession,
        entity_id: UUID,
        update_data: UpdateSchemaType,
        **additional_fields
    ) -> Optional[ResponseSchemaType]:
        """
        Update an existing entity.
        
        Args:
            db: Database session
            entity_id: ID of entity to update
            update_data: Data for updating the entity
            **additional_fields: Additional fields to set
            
        Returns:
            Updated entity if found, None otherwise
        """
        try:
            # Get update data excluding None values
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict.update(additional_fields)
            
            if not update_dict:
                # No fields to update, just return current entity
                return await self.get_by_id(db, entity_id)
            
            # Add updated_at timestamp if the model has it
            if hasattr(self.model, 'updated_at'):
                update_dict['updated_at'] = datetime.now()
            
            result = await db.execute(
                update(self.model)
                .where(self.model.id == entity_id)
                .values(**update_dict)
                .returning(self.model)
            )
            
            updated_entity = result.scalars().first()
            if updated_entity:
                await db.commit()
                return self.response_schema.model_validate(updated_entity)
            
            return None
        
        except Exception as e:
            await db.rollback()
            raise BotOperationError(detail=f"Failed to update {self.model.__name__}: {str(e)}")
    
    async def delete(
        self,
        db: AsyncSession,
        entity_id: UUID
    ) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            db: Database session
            entity_id: ID of entity to delete
            
        Returns:
            True if entity was deleted, False if not found
        """
        try:
            result = await db.execute(
                delete(self.model).where(self.model.id == entity_id)
            )
            
            if result.rowcount > 0:
                await db.commit()
                return True
            
            return False
        
        except Exception as e:
            await db.rollback()
            raise BotOperationError(detail=f"Failed to delete {self.model.__name__}: {str(e)}")
    
    async def count(
        self,
        db: AsyncSession,
        filters: Dict[str, Any] = None
    ) -> int:
        """
        Count entities with optional filtering.
        
        Args:
            db: Database session
            filters: Dictionary of field->value filters
            
        Returns:
            Count of entities
        """
        query = select(func.count(self.model.id))
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def exists(
        self,
        db: AsyncSession,
        entity_id: UUID
    ) -> bool:
        """
        Check if entity exists by ID.
        
        Args:
            db: Database session
            entity_id: Entity ID to check
            
        Returns:
            True if entity exists, False otherwise
        """
        result = await db.execute(
            select(self.model.id).where(self.model.id == entity_id)
        )
        return result.scalars().first() is not None