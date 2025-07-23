from src.integrations.platforms.base import PlatformAdapter
from src.integrations.platforms.telegram_adapter import TelegramAdapter

__all__ = [
    'PlatformAdapter',
    'TelegramAdapter',
]

# Platform adapter factory
def get_platform_adapter(platform: str) -> PlatformAdapter:
    """
    Factory function to get the appropriate platform adapter
    """
    if platform.lower() == "telegram":
        return TelegramAdapter()
    else:
        raise ValueError(f"Unsupported platform: {platform}")