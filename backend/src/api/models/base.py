"""
Base module for all models, providing common imports and utilities.
"""
import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Date, Time, Integer, Numeric, Text, JSON, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.api.dependencies.db import Base
from src.api.core.config import get_settings

settings = get_settings()

# Common enums
class IntegrationType(str, enum.Enum):
    """Integration types enum"""
    IIKO = "iiko"
    R_KEEPER = "r_keeper"
    # Add more integration types as needed


class SyncStatus(str, enum.Enum):
    """Sync status enum"""
    PENDING = "pending"
    SYNCED = "synced"
    ERROR = "error"