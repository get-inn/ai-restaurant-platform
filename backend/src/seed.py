"""
Standalone script to seed the database with test data.
Can be run directly using: python -m backend.src.seed
"""

from src.api.dependencies.db import SessionLocal
from src.api.core.seed.seed_data import seed_database
from src.api.core.logging_config import get_logger

logger = get_logger("restaurant_api")

def main():
    """Run the database seeding script"""
    logger.info("Starting database seed script...")
    
    # Create DB session
    db = SessionLocal()
    
    try:
        seed_database(db)
        logger.info("Seeding completed successfully")
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        raise
    finally:
        db.close()
    
    logger.info("Seed script finished")

if __name__ == "__main__":
    main()