from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
import logging

from src.api.models import BotInstance, BotPlatformCredential
from src.api.core.logging_config import get_logger

logger = get_logger("platform_service")


class PlatformService:
    @staticmethod
    def create_platform_credential(
        db: Session, bot_id: str, platform: str, credentials: Dict[str, Any], is_active: bool = True
    ) -> Optional[BotPlatformCredential]:
        """
        Create new platform credentials for a bot.
        """
        try:
            logger.info(f"Creating platform credential for bot_id={bot_id}, platform={platform}")
            
            # Validate UUID format for bot_id
            try:
                bot_uuid = uuid.UUID(bot_id)
                logger.info(f"Validated bot_id as proper UUID: {bot_uuid}")
            except ValueError as e:
                logger.error(f"Invalid UUID format for bot_id: {bot_id}")
                raise ValueError(f"Invalid UUID format for bot_id: {bot_id}") from e
            
            # Check if bot exists first
            bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
            if not bot:
                logger.error(f"Bot with id={bot_id} not found")
                raise ValueError(f"Bot with id={bot_id} not found")
                
            credential = BotPlatformCredential(
                bot_id=bot_uuid,  # Use the UUID object
                platform=platform,
                credentials=credentials,
                is_active=is_active
            )
            db.add(credential)
            db.commit()
            db.refresh(credential)
            logger.info(f"Created platform credential: {credential.id} for bot {bot_id}")
            return credential
        except SQLAlchemyError as e:
            logger.error(f"Database error creating platform credential: {str(e)}")
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in create_platform_credential: {str(e)}")
            db.rollback()
            raise

    @staticmethod
    def get_platform_credentials(db: Session, bot_id: str) -> List[BotPlatformCredential]:
        """
        Get all platform credentials for a bot.
        """
        try:
            # Validate UUID format for bot_id
            try:
                bot_uuid = uuid.UUID(bot_id)
                logger.info(f"Getting credentials for bot with UUID: {bot_uuid}")
            except ValueError as e:
                logger.error(f"Invalid UUID format for bot_id: {bot_id}")
                raise ValueError(f"Invalid UUID format for bot_id: {bot_id}") from e
                
            credentials = db.query(BotPlatformCredential).filter(
                BotPlatformCredential.bot_id == bot_uuid
            ).all()
            logger.info(f"Found {len(credentials)} platform credentials for bot {bot_id}")
            return credentials
        except SQLAlchemyError as e:
            logger.error(f"Error getting platform credentials: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_platform_credentials: {str(e)}")
            raise

    @staticmethod
    def get_platform_credential(db: Session, bot_id: str, platform: str) -> Optional[BotPlatformCredential]:
        """
        Get platform credential for a specific bot and platform.
        """
        try:
            # Validate UUID format for bot_id
            try:
                bot_uuid = uuid.UUID(bot_id)
                logger.info(f"Getting credential for bot with UUID: {bot_uuid}, platform: {platform}")
            except ValueError as e:
                logger.error(f"Invalid UUID format for bot_id: {bot_id}")
                raise ValueError(f"Invalid UUID format for bot_id: {bot_id}") from e
                
            credential = db.query(BotPlatformCredential).filter(
                BotPlatformCredential.bot_id == bot_uuid,
                BotPlatformCredential.platform == platform
            ).first()
            
            if credential:
                logger.info(f"Found platform credential for bot {bot_id}, platform {platform}")
            else:
                logger.info(f"No platform credential found for bot {bot_id}, platform {platform}")
                
            return credential
        except SQLAlchemyError as e:
            logger.error(f"Error getting platform credential: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_platform_credential: {str(e)}")
            raise

    @staticmethod
    def update_platform_credential(
        db: Session, 
        bot_id: str, 
        platform: str, 
        update_data: Dict[str, Any]
    ) -> Optional[BotPlatformCredential]:
        """
        Update platform credentials.
        """
        try:
            # Validate UUID format for bot_id
            try:
                bot_uuid = uuid.UUID(bot_id)
                logger.info(f"Updating credential for bot with UUID: {bot_uuid}, platform: {platform}")
            except ValueError as e:
                logger.error(f"Invalid UUID format for bot_id: {bot_id}")
                raise ValueError(f"Invalid UUID format for bot_id: {bot_id}") from e
                
            credential = db.query(BotPlatformCredential).filter(
                BotPlatformCredential.bot_id == bot_uuid,
                BotPlatformCredential.platform == platform
            ).first()
            
            if not credential:
                logger.error(f"No credential found for bot {bot_id}, platform {platform}")
                return None
                
            for key, value in update_data.items():
                if hasattr(credential, key) and value is not None:
                    setattr(credential, key, value)
                    
            db.commit()
            db.refresh(credential)
            logger.info(f"Updated platform credential: {credential.id}")
            return credential
        except SQLAlchemyError as e:
            logger.error(f"Error updating platform credential: {str(e)}")
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in update_platform_credential: {str(e)}")
            db.rollback()
            raise

    @staticmethod
    def delete_platform_credential(db: Session, bot_id: str, platform: str) -> bool:
        """
        Delete platform credentials.
        """
        try:
            # Validate UUID format for bot_id
            try:
                bot_uuid = uuid.UUID(bot_id)
                logger.info(f"Deleting credential for bot with UUID: {bot_uuid}, platform: {platform}")
            except ValueError as e:
                logger.error(f"Invalid UUID format for bot_id: {bot_id}")
                raise ValueError(f"Invalid UUID format for bot_id: {bot_id}") from e
                
            credential = db.query(BotPlatformCredential).filter(
                BotPlatformCredential.bot_id == bot_uuid,
                BotPlatformCredential.platform == platform
            ).first()
            
            if not credential:
                logger.error(f"No credential found for bot {bot_id}, platform {platform}")
                return False
                
            db.delete(credential)
            db.commit()
            logger.info(f"Deleted platform credential for bot {bot_id}, platform {platform}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting platform credential: {str(e)}")
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in delete_platform_credential: {str(e)}")
            db.rollback()
            raise