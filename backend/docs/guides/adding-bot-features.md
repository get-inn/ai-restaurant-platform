# Adding Bot Features

This guide explains how to add new features to bots in the GET INN Restaurant Platform.

## Overview

The bot management system provides a flexible architecture for implementing new bot features. This guide covers the process of adding new functionality to bots, including scenario extensions, new input types, custom commands, and integration with external services.

## Prerequisites

Before adding bot features, you should be familiar with:

- [Bot Management Overview](../modules/bot-management/overview.md)
- [Bot Scenario Format](../modules/bot-management/scenario-format.md)
- [Input Validation Overview](../modules/bot-management/input-validation-overview.md)
- [Webhook Management](../modules/bot-management/webhook-management.md)

## Types of Bot Features

You can add several types of features to bots:

1. **Scenario Extensions**: New conversation flows or branches
2. **Input Types**: New ways for users to provide data
3. **Commands**: Special commands that trigger specific actions
4. **Platform-specific Features**: Functionality for particular messaging platforms
5. **Integration Features**: Connections to external services or APIs

## Extending Bot Scenarios

### Adding New Scenario Steps

To add new steps to a scenario:

1. Identify where in the flow you want to add the new steps
2. Design the conversation flow, including messages and expected inputs
3. Add the new steps to the scenario JSON:

```json
"steps": [
  // Existing steps...
  {
    "id": "ask_preferences",
    "message": {
      "text": "What are your food preferences?"
    },
    "expected_input": {
      "type": "text",
      "variable": "food_preferences"
    },
    "next_step": "confirm_preferences"
  },
  {
    "id": "confirm_preferences",
    "message": {
      "text": "You've specified these preferences: ${food_preferences}. Is this correct?"
    },
    "buttons": [
      {"text": "Yes", "value": "yes"},
      {"text": "No", "value": "no"}
    ],
    "expected_input": {
      "type": "button",
      "variable": "preferences_confirmed"
    },
    "next_step": {
      "condition": "preferences_confirmed == 'yes'",
      "if_true": "next_existing_step",
      "if_false": "ask_preferences"
    }
  }
  // More steps...
]
```

4. Update any transitions from existing steps to include your new flow
5. Test the updated scenario to ensure proper flow

## Adding Custom Commands

You can add special commands that users can type at any point in a conversation:

### 1. Define Command Handlers

Create a new file or update an existing one in `src/bot_manager/commands/`:

```python
# src/bot_manager/commands/help_command.py
from typing import Dict, Any, Optional
from src.bot_manager.command_handler import CommandHandler
from src.bot_manager.types import BotMessage, DialogContext

class HelpCommandHandler(CommandHandler):
    """Handler for /help command."""
    
    def can_handle(self, command: str) -> bool:
        """Check if this handler can process the command."""
        return command.lower() in ['/help', 'help']
    
    async def handle(self, dialog_context: DialogContext) -> Optional[BotMessage]:
        """Process the /help command."""
        available_commands = [
            "/help - Show this help message",
            "/restart - Restart the conversation",
            "/status - Check your current status",
            # List other available commands
        ]
        
        return BotMessage(
            text="Available commands:\n" + "\n".join(available_commands),
            media=[],
            buttons=[]
        )
```

### 2. Register the Command Handler

Update the command registry in `src/bot_manager/command_registry.py`:

```python
# src/bot_manager/command_registry.py
from src.bot_manager.commands.help_command import HelpCommandHandler
from src.bot_manager.commands.restart_command import RestartCommandHandler
from src.bot_manager.commands.status_command import StatusCommandHandler

class CommandRegistry:
    """Registry of available command handlers."""
    
    def __init__(self):
        self.handlers = [
            HelpCommandHandler(),
            RestartCommandHandler(),
            StatusCommandHandler(),
            # Add your new command handler here
        ]
    
    def get_handler_for_command(self, command: str):
        """Get the appropriate handler for a command."""
        for handler in self.handlers:
            if handler.can_handle(command):
                return handler
        return None
```

### 3. Test the New Command

Test the command in all supported platforms to ensure it works correctly.

## Implementing New Input Types

To add a new input type to the bot system:

### 1. Update Input Type Definitions

Add your new input type to `src/bot_manager/types.py`:

```python
# src/bot_manager/types.py
from enum import Enum, auto

class InputType(Enum):
    TEXT = auto()
    BUTTON = auto()
    FILE = auto()
    LOCATION = auto()
    # Add your new input type
    CALENDAR = auto()
```

### 2. Create Input Processor

Implement the processor for the new input type in `src/bot_manager/input_processors/`:

```python
# src/bot_manager/input_processors/calendar_processor.py
from datetime import datetime
from typing import Dict, Any, Optional
from src.bot_manager.input_processor import InputProcessor
from src.bot_manager.types import InputType, UserInput, ProcessedInput

class CalendarInputProcessor(InputProcessor):
    """Processor for calendar inputs."""
    
    def can_process(self, input_type: InputType) -> bool:
        """Check if this processor can handle the input type."""
        return input_type == InputType.CALENDAR
    
    async def process(self, user_input: UserInput, expected_input: Dict[str, Any]) -> Optional[ProcessedInput]:
        """Process calendar input from the user."""
        if not user_input.text:
            return None
        
        try:
            # Parse date from text (format: YYYY-MM-DD)
            date_value = datetime.strptime(user_input.text, "%Y-%m-%d").date()
            
            # Validate against any constraints
            validation = expected_input.get("validation", {})
            if validation:
                min_date = validation.get("min_date")
                max_date = validation.get("max_date")
                
                if min_date:
                    min_date_obj = datetime.strptime(min_date, "%Y-%m-%d").date()
                    if date_value < min_date_obj:
                        return ProcessedInput(
                            is_valid=False,
                            error_message=f"Date must be after {min_date}",
                            processed_value=None
                        )
                
                if max_date:
                    max_date_obj = datetime.strptime(max_date, "%Y-%m-%d").date()
                    if date_value > max_date_obj:
                        return ProcessedInput(
                            is_valid=False,
                            error_message=f"Date must be before {max_date}",
                            processed_value=None
                        )
            
            return ProcessedInput(
                is_valid=True,
                error_message=None,
                processed_value=date_value.isoformat()
            )
        except ValueError:
            return ProcessedInput(
                is_valid=False,
                error_message="Please enter a valid date in YYYY-MM-DD format",
                processed_value=None
            )
```

### 3. Register Input Processor

Add your processor to the registry in `src/bot_manager/input_processor_registry.py`:

```python
# src/bot_manager/input_processor_registry.py
from src.bot_manager.input_processors.text_processor import TextInputProcessor
from src.bot_manager.input_processors.button_processor import ButtonInputProcessor
from src.bot_manager.input_processors.file_processor import FileInputProcessor
from src.bot_manager.input_processors.calendar_processor import CalendarInputProcessor

class InputProcessorRegistry:
    """Registry of input processors."""
    
    def __init__(self):
        self.processors = [
            TextInputProcessor(),
            ButtonInputProcessor(),
            FileInputProcessor(),
            # Add your new processor
            CalendarInputProcessor(),
        ]
    
    def get_processor_for_type(self, input_type):
        """Get the appropriate processor for an input type."""
        for processor in self.processors:
            if processor.can_process(input_type):
                return processor
        return None
```

### 4. Update Platform Adapters

Update platform-specific adapters to handle the new input type:

```python
# src/integrations/platforms/telegram_adapter.py
async def render_expected_input(self, expected_input: Dict[str, Any]) -> Dict[str, Any]:
    """Render the expected input for Telegram."""
    input_type = expected_input.get("type")
    
    if input_type == "text":
        # Regular text input
        return {}
    elif input_type == "button":
        # Button input handling
        # ...
    elif input_type == "calendar":
        # Calendar input for Telegram
        # Use Telegram's calendar keyboard or custom implementation
        keyboard = [
            # Generate calendar keyboard layout
        ]
        return {
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
    # Handle other input types...
```

## Adding Platform-Specific Features

To add features specific to a particular messaging platform:

### 1. Update Platform Adapter

Modify the appropriate platform adapter in `src/integrations/platforms/`:

```python
# src/integrations/platforms/telegram_adapter.py
class TelegramAdapter(PlatformAdapter):
    # Existing methods...
    
    async def send_location(self, chat_id: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """Send a location message via Telegram."""
        url = f"{self.api_base_url}/sendLocation"
        payload = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude
        }
        response = await self.http_client.post(url, json=payload)
        return response.json()
    
    async def send_poll(self, chat_id: str, question: str, options: List[str]) -> Dict[str, Any]:
        """Send a poll via Telegram."""
        url = f"{self.api_base_url}/sendPoll"
        payload = {
            "chat_id": chat_id,
            "question": question,
            "options": options,
            "is_anonymous": False
        }
        response = await self.http_client.post(url, json=payload)
        return response.json()
```

### 2. Add Platform-Specific Message Handling

Update the webhook handler to process platform-specific messages:

```python
# src/api/routers/webhooks/telegram.py
@router.post("/{bot_id}")
async def telegram_webhook(
    request: Request,
    bot_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Handle Telegram webhook requests."""
    body = await request.json()
    
    # Extract message details
    message = body.get("message", {})
    poll_answer = body.get("poll_answer")
    
    # Handle poll answers
    if poll_answer:
        # Process poll answer
        poll_id = poll_answer.get("poll_id")
        selected_options = poll_answer.get("option_ids", [])
        user_id = poll_answer.get("user", {}).get("id")
        
        # Process the poll answer
        # ...
    
    # Process regular messages
    # ...
```

## Integrating with External Services

To integrate bots with external services or APIs:

### 1. Create Service Client

Implement a client for the external service:

```python
# src/integrations/external_services/weather_service.py
import aiohttp
from typing import Dict, Any, Optional

class WeatherService:
    """Client for weather API integration."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.weatherapi.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.http_client = aiohttp.ClientSession()
    
    async def get_current_weather(self, location: str) -> Optional[Dict[str, Any]]:
        """Get current weather for a location."""
        url = f"{self.base_url}/current.json"
        params = {
            "key": self.api_key,
            "q": location
        }
        
        try:
            response = await self.http_client.get(url, params=params)
            if response.status == 200:
                return await response.json()
            return None
        except Exception as e:
            # Log error
            return None
    
    async def close(self):
        """Close the HTTP client session."""
        await self.http_client.close()
```

### 2. Create Service Integration

Implement a service integration that can be used by the bot:

```python
# src/bot_manager/services/weather_integration.py
from typing import Dict, Any, Optional
from src.integrations.external_services.weather_service import WeatherService
from src.bot_manager.types import BotMessage, DialogContext

class WeatherIntegration:
    """Weather service integration for bots."""
    
    def __init__(self, api_key: str):
        self.weather_service = WeatherService(api_key)
    
    async def get_weather_message(self, location: str) -> BotMessage:
        """Get weather information as a bot message."""
        weather_data = await self.weather_service.get_current_weather(location)
        
        if not weather_data:
            return BotMessage(
                text="Sorry, I couldn't get the weather information at this time.",
                media=[],
                buttons=[]
            )
        
        current = weather_data.get("current", {})
        location_data = weather_data.get("location", {})
        
        temperature = current.get("temp_c")
        condition = current.get("condition", {}).get("text")
        city = location_data.get("name")
        country = location_data.get("country")
        
        message_text = f"Current weather in {city}, {country}:\n" \
                      f"Temperature: {temperature}°C\n" \
                      f"Condition: {condition}"
        
        return BotMessage(
            text=message_text,
            media=[
                {
                    "type": "image",
                    "url": f"https:{current.get('condition', {}).get('icon')}",
                    "caption": condition
                }
            ],
            buttons=[]
        )
    
    async def close(self):
        """Close the weather service."""
        await self.weather_service.close()
```

### 3. Add Service Factory

Create a factory to provide service instances:

```python
# src/bot_manager/service_factory.py
from typing import Dict, Any
from src.bot_manager.services.weather_integration import WeatherIntegration
from src.api.core.config import settings

class ServiceFactory:
    """Factory for creating service integrations."""
    
    def __init__(self):
        self.instances = {}
    
    def get_weather_integration(self) -> WeatherIntegration:
        """Get or create a weather integration instance."""
        if "weather" not in self.instances:
            self.instances["weather"] = WeatherIntegration(
                api_key=settings.WEATHER_API_KEY
            )
        return self.instances["weather"]
    
    async def close_all(self):
        """Close all service instances."""
        for service_name, instance in self.instances.items():
            if hasattr(instance, "close"):
                await instance.close()
```

### 4. Use the Service in Bot Scenarios

Create a command or scenario step that uses the service:

```python
# src/bot_manager/commands/weather_command.py
from typing import Dict, Any, Optional
from src.bot_manager.command_handler import CommandHandler
from src.bot_manager.types import BotMessage, DialogContext
from src.bot_manager.service_factory import ServiceFactory

class WeatherCommandHandler(CommandHandler):
    """Handler for /weather command."""
    
    def __init__(self, service_factory: ServiceFactory):
        self.service_factory = service_factory
    
    def can_handle(self, command: str) -> bool:
        """Check if this handler can process the command."""
        return command.lower().startswith('/weather')
    
    async def handle(self, dialog_context: DialogContext) -> Optional[BotMessage]:
        """Process the /weather command."""
        # Extract location from command (e.g., "/weather Moscow")
        command_parts = dialog_context.message.text.split(' ', 1)
        
        if len(command_parts) < 2:
            return BotMessage(
                text="Please specify a location: /weather [city name]",
                media=[],
                buttons=[]
            )
        
        location = command_parts[1].strip()
        
        # Get weather integration
        weather_integration = self.service_factory.get_weather_integration()
        
        # Get weather message
        return await weather_integration.get_weather_message(location)
```

## Adding API Endpoints for Bot Management

To add new API endpoints for managing bot features:

### 1. Create New Router

Add a new router file or update an existing one:

```python
# src/api/routers/bots/features.py
from fastapi import APIRouter, Depends, Path, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Any
from uuid import UUID

from src.api.dependencies.db import get_db
from src.api.dependencies.auth import get_current_user, check_role
from src.api.schemas.bots import BotFeatureCreate, BotFeatureResponse
from src.api.services.bots.feature_service import BotFeatureService

router = APIRouter()

@router.post("/{bot_id}/features", response_model=BotFeatureResponse, status_code=201)
async def add_bot_feature(
    bot_id: UUID,
    feature_data: BotFeatureCreate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add a new feature to a bot."""
    service = BotFeatureService(db)
    return service.add_feature(bot_id, feature_data, current_user["account_id"])

@router.get("/{bot_id}/features", response_model=List[BotFeatureResponse])
async def list_bot_features(
    bot_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """List all features for a bot."""
    service = BotFeatureService(db)
    return service.list_features(bot_id, current_user["account_id"])
```

### 2. Register the Router

Update the router registration in the bots package:

```python
# src/api/routers/bots/__init__.py
from fastapi import APIRouter

from src.api.routers.bots.instances import router as instances_router
from src.api.routers.bots.platforms import router as platforms_router
from src.api.routers.bots.scenarios import router as scenarios_router
from src.api.routers.bots.features import router as features_router

router = APIRouter()
router.include_router(instances_router, prefix="", tags=["bot-instances"])
router.include_router(platforms_router, prefix="", tags=["bot-platforms"])
router.include_router(scenarios_router, prefix="", tags=["bot-scenarios"])
router.include_router(features_router, prefix="", tags=["bot-features"])
```

## Testing New Bot Features

Always test your bot features thoroughly:

### 1. Unit Testing

Create unit tests for new components:

```python
# src/api/tests/unit/bot_manager/services/test_weather_integration.py
import pytest
from unittest.mock import AsyncMock, patch

from src.bot_manager.services.weather_integration import WeatherIntegration

@pytest.fixture
def weather_service_mock():
    return AsyncMock()

@pytest.fixture
def weather_integration(weather_service_mock):
    with patch('src.integrations.external_services.weather_service.WeatherService', return_value=weather_service_mock):
        return WeatherIntegration(api_key="test_key")

@pytest.mark.asyncio
async def test_get_weather_message_success(weather_integration, weather_service_mock):
    # Arrange
    weather_service_mock.get_current_weather.return_value = {
        "location": {
            "name": "Moscow",
            "country": "Russia"
        },
        "current": {
            "temp_c": 25,
            "condition": {
                "text": "Sunny",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png"
            }
        }
    }
    
    # Act
    result = await weather_integration.get_weather_message("Moscow")
    
    # Assert
    assert "Moscow, Russia" in result.text
    assert "25°C" in result.text
    assert "Sunny" in result.text
    assert len(result.media) == 1
    assert result.media[0]["url"] == "https://cdn.weatherapi.com/weather/64x64/day/113.png"
```

### 2. Integration Testing

Test the integration with real services (but with a mock bot):

```python
# src/api/tests/integration/bot_manager/test_weather_integration.py
import pytest
from unittest.mock import Mock

from src.bot_manager.services.weather_integration import WeatherIntegration
from src.bot_manager.types import DialogContext

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("WEATHER_API_KEY"), reason="Weather API key not set")
@pytest.mark.asyncio
async def test_weather_integration_real_api():
    # Arrange
    integration = WeatherIntegration(api_key=os.getenv("WEATHER_API_KEY"))
    
    # Act
    message = await integration.get_weather_message("London")
    
    # Assert
    assert message.text is not None
    assert "London" in message.text
    assert "°C" in message.text
    
    # Cleanup
    await integration.close()
```

### 3. End-to-End Testing

Test the feature with actual bots in a test environment:

```python
# src/api/tests/integration/test_bot_features.py
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.core.config import settings

@pytest.mark.integration
def test_weather_command_via_webhook(client, test_bot_id, mock_telegram_message):
    # Arrange
    mock_telegram_message["message"]["text"] = "/weather London"
    
    # Act
    response = client.post(
        f"/v1/api/webhooks/telegram/{test_bot_id}",
        json=mock_telegram_message
    )
    
    # Assert
    assert response.status_code == 200
    # In real end-to-end tests, you would check that a message was sent
    # to the Telegram API with the weather information
```

## Deploying New Bot Features

After testing your new features:

1. **Update Documentation**: Add descriptions and examples of the new features to the documentation
2. **Deploy Changes**: Follow standard deployment procedures
3. **Monitor Usage**: Track usage of the new features to identify any issues
4. **Gather Feedback**: Collect user feedback on the new features

## Conclusion

Adding new bot features requires careful planning and implementation across multiple components of the bot management system. By following this guide, you can extend the platform's bot capabilities while maintaining its architecture and code quality standards.