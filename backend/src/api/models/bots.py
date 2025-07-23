"""
Bot management models: BotInstance, BotPlatformCredential, BotScenario, etc.
"""
from src.api.models.base import *


class BotInstance(Base):
    __tablename__ = "bot_instance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="bots")
    platform_credentials = relationship("BotPlatformCredential", back_populates="bot", cascade="all, delete-orphan")
    scenarios = relationship("BotScenario", back_populates="bot", cascade="all, delete-orphan")
    dialog_states = relationship("BotDialogState", back_populates="bot", cascade="all, delete-orphan")
    media_files = relationship("BotMediaFile", back_populates="bot", cascade="all, delete-orphan")


class BotPlatformCredential(Base):
    __tablename__ = "bot_platform_credential"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    platform = Column(String, nullable=False)  # 'telegram', 'whatsapp', 'viber', etc.
    credentials = Column(JSONB, nullable=False)  # tokens and platform-specific settings
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Webhook-related fields
    webhook_url = Column(String, nullable=True)
    webhook_last_checked = Column(DateTime, nullable=True)
    webhook_auto_refresh = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    bot = relationship("BotInstance", back_populates="platform_credentials")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('bot_id', 'platform', name='uix_bot_platform'),
    )


class BotScenario(Base):
    __tablename__ = "bot_scenario"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    scenario_data = Column(JSONB, nullable=False)  # full scenario structure
    version = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    bot = relationship("BotInstance", back_populates="scenarios")


class BotDialogState(Base):
    __tablename__ = "bot_dialog_state"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    platform = Column(String, nullable=False)  # 'telegram', 'whatsapp', 'viber', etc.
    platform_chat_id = Column(String, nullable=False)  # Chat ID in the specific platform
    current_step = Column(String, nullable=False)  # current scenario step
    collected_data = Column(JSONB, nullable=False, default={})  # collected data
    last_interaction_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    bot = relationship("BotInstance", back_populates="dialog_states")
    history = relationship("BotDialogHistory", back_populates="dialog_state", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('bot_id', 'platform', 'platform_chat_id', name='uix_bot_platform_chat'),
    )


class BotDialogHistory(Base):
    __tablename__ = "bot_dialog_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dialog_state_id = Column(UUID(as_uuid=True), ForeignKey("bot_dialog_state.id"), nullable=False)
    message_type = Column(String, nullable=False)  # 'user', 'bot'
    message_data = Column(JSONB, nullable=False)  # message content and metadata
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    dialog_state = relationship("BotDialogState", back_populates="history")


class BotMediaFile(Base):
    __tablename__ = "bot_media_file"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    file_type = Column(String, nullable=False)  # 'image', 'video', etc.
    file_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    platform_file_ids = Column(JSONB, nullable=True)  # Map of platform -> file_id
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    bot = relationship("BotInstance", back_populates="media_files")