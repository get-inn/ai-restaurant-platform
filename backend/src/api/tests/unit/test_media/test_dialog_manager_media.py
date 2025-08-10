#!/usr/bin/env python
"""
Test script for dialog manager media handling.

This script creates a minimal environment to test dialog manager media processing.
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from uuid import uuid4, UUID
import tempfile

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from src.bot_manager.dialog_manager import DialogManager
from src.bot_manager.conversation_logger import get_logger, LogEventType
from src.api.schemas.bots.dialog_schemas import DialogMessage, MediaItem


class MockAdapter:
    """Mock platform adapter for testing."""
    
    def __init__(self):
        self.logger = get_logger()
        self.sent_messages = []
        
    def set_context(self, **kwargs):
        """Set context for logging."""
        self.logger.set_context(**kwargs)
        
    async def send_text_message(self, chat_id, text):
        """Mock sending a text message."""
        self.logger.info(LogEventType.ADAPTER, f"Mock send_text_message to {chat_id}")
        self.sent_messages.append({"type": "text", "chat_id": chat_id, "text": text})
        return {"success": True, "message_id": str(uuid4())}
    
    async def send_buttons(self, chat_id, text, buttons):
        """Mock sending buttons."""
        self.logger.info(LogEventType.ADAPTER, f"Mock send_buttons to {chat_id}")
        self.sent_messages.append({"type": "buttons", "chat_id": chat_id, "text": text, "buttons": buttons})
        return {"success": True, "message_id": str(uuid4())}
    
    async def send_media_message(self, chat_id, media_type, file_path, caption=None):
        """Mock sending a media message."""
        self.logger.info(LogEventType.ADAPTER, f"Mock send_media_message to {chat_id}: {media_type}")
        self.sent_messages.append({
            "type": "media",
            "chat_id": chat_id,
            "media_type": media_type,
            "file_path": file_path,
            "caption": caption
        })
        return {"success": True, "message_id": str(uuid4())}


class MockStateRepository:
    """Mock state repository for testing."""
    
    def __init__(self):
        self.states = {}
        
    async def get_dialog_state(self, bot_id, platform, platform_chat_id):
        """Get a dialog state."""
        key = f"{bot_id}:{platform}:{platform_chat_id}"
        return self.states.get(key, {
            "id": str(uuid4()),
            "bot_id": str(bot_id),
            "platform": platform,
            "platform_chat_id": platform_chat_id,
            "current_step": "welcome",
            "collected_data": {}
        })
        
    async def update_dialog_state(self, dialog_state):
        """Update a dialog state."""
        key = f"{dialog_state['bot_id']}:{dialog_state['platform']}:{dialog_state['platform_chat_id']}"
        self.states[key] = dialog_state
        return dialog_state


class MockDb:
    """Mock database session for testing."""
    pass


async def test_dialog_manager_media():
    """Test the dialog manager's media handling."""
    # Set up test context
    bot_id = UUID('11111111-1111-1111-1111-111111111111')
    platform = "telegram"
    platform_chat_id = "123456789"
    
    # Create a mock adapter and state repository
    adapter = MockAdapter()
    state_repo = MockStateRepository()
    
    # Create the dialog manager
    dialog_manager = DialogManager(
        db=MockDb(),
        platform_adapters={"telegram": adapter},
        state_repository=state_repo
    )
    
    # Set up logger context
    logger = get_logger(bot_id=str(bot_id), platform=platform, platform_chat_id=platform_chat_id)
    logger.info(LogEventType.PROCESSING, "Starting dialog manager media test")
    
    # Create a temporary image file for testing
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_file.write(b"FAKE PNG DATA")
        image_path = tmp_file.name
    
    try:
        # Test case 1: Send a simple message
        logger.info(LogEventType.PROCESSING, "Test case 1: Send a simple message")
        await dialog_manager.send_message(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            message="Hello, this is a test message"
        )
        
        # Test case 2: Send a message with buttons
        logger.info(LogEventType.PROCESSING, "Test case 2: Send a message with buttons")
        buttons = [
            {"text": "Button 1", "value": "btn1"},
            {"text": "Button 2", "value": "btn2"}
        ]
        await dialog_manager.send_message(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            message="Please choose an option",
            buttons=buttons
        )
        
        # Test case 3: Send a message with media
        logger.info(LogEventType.PROCESSING, "Test case 3: Send a message with media")
        # Create media items
        media_items = [
            MediaItem(
                type="image",
                file_id="test_image",
                description="Test image"
            )
        ]
        # Create dialog message with media
        dialog_message = DialogMessage(
            text="Here is an image",
            media=media_items
        )
        
        # Mock the send_media_message response
        adapter.send_media_message = lambda chat_id, media_type, file_path, caption=None: {
            "success": True, 
            "message_id": str(uuid4())
        }
        
        # Send the message with media
        await dialog_manager.send_message(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            message=dialog_message
        )
        
        # Print results
        print("\nMedia test completed successfully!")
        print(f"Messages sent: {len(adapter.sent_messages)}")
        for i, msg in enumerate(adapter.sent_messages):
            print(f"\nMessage {i+1}:")
            print(f"Type: {msg['type']}")
            print(f"Chat ID: {msg['chat_id']}")
            if msg['type'] == 'media':
                print(f"Media type: {msg['media_type']}")
                print(f"Caption: {msg['caption']}")
            else:
                print(f"Text: {msg['text']}")
            if msg['type'] == 'buttons':
                print(f"Buttons: {json.dumps(msg['buttons'], indent=2)}")
                
    finally:
        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path)


def main():
    """Main function to run the test"""
    print("Starting dialog manager media test...")
    asyncio.run(test_dialog_manager_media())


if __name__ == "__main__":
    main()
