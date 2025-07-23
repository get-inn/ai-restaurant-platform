import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError

from src.api.models import Base, UserProfile, UnitCategory, Unit
from src.api.core.logging_config import get_logger
import uuid

logger = get_logger("restaurant_api")

def init_db(db: Session) -> None:
    """
    Initialize the database with required seed data.
    
    This function creates basic data required for the application to work:
    - Default unit categories
    - Common units and their conversions
    - Admin user (if not exists)
    
    Args:
        db: Database session
    """
    try:
        logger.info("Creating initial data...")
        
        # Create default unit categories
        weight_category_id = create_unit_category(db, "Weight")
        volume_category_id = create_unit_category(db, "Volume")
        count_category_id = create_unit_category(db, "Count")
        
        # Create common units
        create_unit(db, "Kilogram", "kg", weight_category_id)
        create_unit(db, "Gram", "g", weight_category_id)
        create_unit(db, "Pound", "lb", weight_category_id)
        create_unit(db, "Ounce", "oz", weight_category_id)
        
        create_unit(db, "Liter", "L", volume_category_id)
        create_unit(db, "Milliliter", "ml", volume_category_id)
        create_unit(db, "Gallon", "gal", volume_category_id)
        create_unit(db, "Fluid Ounce", "fl oz", volume_category_id)
        create_unit(db, "Cup", "cup", volume_category_id)
        create_unit(db, "Tablespoon", "tbsp", volume_category_id)
        create_unit(db, "Teaspoon", "tsp", volume_category_id)
        
        create_unit(db, "Piece", "pc", count_category_id)
        create_unit(db, "Each", "ea", count_category_id)
        create_unit(db, "Dozen", "dz", count_category_id)
        
        # Create admin user if not exists
        admin_id = "00000000-0000-0000-0000-000000000000"  # Fixed UUID for easy reference
        create_admin_user(db, admin_id)
        
        logger.info("Initial data created successfully")
        
    except Exception as e:
        logger.error(f"Error creating initial data: {str(e)}")
        db.rollback()
        raise


def create_unit_category(db: Session, name: str) -> str:
    """
    Create a unit category if it doesn't already exist.
    
    Args:
        db: Database session
        name: Category name
        
    Returns:
        str: Category ID
    """
    existing = db.query(UnitCategory).filter(UnitCategory.name == name).first()
    if existing:
        return str(existing.id)
        
    category = UnitCategory(
        name=name
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return str(category.id)


def create_unit(db: Session, name: str, symbol: str, category_id: str) -> str:
    """
    Create a unit if it doesn't already exist.
    
    Args:
        db: Database session
        name: Unit name
        symbol: Unit symbol
        category_id: Unit category ID
        
    Returns:
        str: Unit ID
    """
    existing = db.query(Unit).filter(Unit.name == name, Unit.symbol == symbol).first()
    if existing:
        return str(existing.id)
        
    unit = Unit(
        name=name,
        symbol=symbol,
        unit_category_id=category_id
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    
    return str(unit.id)


def create_admin_user(db: Session, user_id: str) -> None:
    """
    Create admin user if it doesn't already exist.
    
    Args:
        db: Database session
        user_id: User ID
    """
    existing = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if existing:
        return
        
    # Create admin user
    admin = UserProfile(
        id=user_id,
        role="admin"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)