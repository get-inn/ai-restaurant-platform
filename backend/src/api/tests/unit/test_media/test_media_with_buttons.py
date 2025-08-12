#!/usr/bin/env python
"""
Test script for testing media processing with buttons in dialog manager.

This script tests the dialog manager's ability to handle messages with both
media attachments and buttons, which is a critical functionality for the bot system.
It now includes tests for multiple media items functionality.
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
        
    @property
    def platform_name(self) -> str:
        return "telegram"
        
    async def initialize(self, credentials):
        return True
        
    async def send_text_message(self, chat_id, text):
        """Mock sending a text message."""
        self.logger.info(LogEventType.ADAPTER, f"Mock send_text_message to {chat_id}")
        self.sent_messages.append({"type": "text", "chat_id": chat_id, "text": text})
        return {"success": True, "message_id": str(uuid4())}
    
    async def send_message(self, chat_id, text, buttons=None):
        """Mock sending a message with optional buttons (for MediaManager compatibility)."""
        self.logger.info(LogEventType.ADAPTER, f"Mock send_message to {chat_id}")
        if buttons:
            return await self.send_buttons(chat_id, text, buttons)
        else:
            return await self.send_text_message(chat_id, text)
    
    async def send_media(self, chat_id, media_type, file_id, caption=None, buttons=None):
        """Mock sending media (for MediaManager compatibility)."""
        self.logger.info(LogEventType.ADAPTER, f"Mock send_media to {chat_id}: {media_type}")
        message_data = {
            "type": "media",
            "chat_id": chat_id,
            "media_type": media_type,
            "file_id": file_id,
            "caption": caption
        }
        if buttons:
            message_data["buttons"] = buttons
            message_data["type"] = "media_with_buttons"
        
        self.sent_messages.append(message_data)
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
    
    async def send_media_with_buttons(self, chat_id, media_type, file_path, caption=None, buttons=None):
        """Mock sending a media message with buttons."""
        self.logger.info(LogEventType.ADAPTER, f"Mock send_media_with_buttons to {chat_id}: {media_type} with {len(buttons) if buttons else 0} buttons")
        self.sent_messages.append({
            "type": "media_with_buttons",
            "chat_id": chat_id,
            "media_type": media_type,
            "file_path": file_path,
            "caption": caption,
            "buttons": buttons
        })
        return {"success": True, "message_id": str(uuid4())}
        
    async def send_media_group(self, chat_id, media_items, caption=None):
        """Mock sending multiple media items as a group."""
        self.logger.info(LogEventType.ADAPTER, f"Mock send_media_group to {chat_id}: {len(media_items)} items")
        media_types = [item.get("type", "unknown") if isinstance(item, dict) else getattr(item, "type", "unknown") for item in media_items]
        self.sent_messages.append({
            "type": "media_group",
            "chat_id": chat_id,
            "media_items": media_items,
            "media_types": media_types,
            "caption": caption
        })
        return {"success": True, "message_ids": [str(uuid4()) for _ in range(len(media_items))]}
        
    async def get_webhook_info(self):
        return {"url": "https://example.com/webhook"}
    
    async def set_webhook(self, webhook_url):
        return True
        
    async def delete_webhook(self):
        return True
        
    async def process_update(self, update_data):
        return update_data
        
    async def get_file_from_platform(self, file_id):
        return b"mock_file_content"
        
    async def upload_file_to_platform(self, file_path):
        return "mock_file_id"


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


async def test_single_media_with_buttons():
    """Test the dialog manager's handling of media with buttons."""
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
    logger.info(LogEventType.PROCESSING, "Starting media with buttons test")
    
    # Create a temporary image file for testing
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_file.write(b"FAKE PNG DATA")
        image_path = tmp_file.name
    
    try:
        # Test case: Send a message with both media and buttons
        logger.info(LogEventType.PROCESSING, "Test case: Send a message with both media and buttons")
        
        # Create buttons
        buttons = [
            {"text": "Button 1", "value": "btn1"},
            {"text": "Button 2", "value": "btn2"}
        ]
        
        # Create media items
        media_items = [
            MediaItem(
                type="image",
                file_id="test_image",
                description="Test image with buttons"
            )
        ]
        
        # Create dialog message with media
        dialog_message = DialogMessage(
            text="Here is an image with buttons",
            media=media_items
        )
        
        # Mock API response for media content retrieval
        async def mock_retrieve_media(*args, **kwargs):
            return {"success": True, "file_path": image_path}
        
        # Note: With the refactored DialogManager using MediaManager, 
        # we don't need to mock internal methods anymore.
        # The MediaManager will handle all media processing automatically.
        
        # Send the message with media and buttons
        await dialog_manager.send_message(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            message=dialog_message,
            buttons=buttons
        )
        
        # Print results
        print("\nMedia with buttons test completed!")
        print(f"Messages sent: {len(adapter.sent_messages)}")
        for i, msg in enumerate(adapter.sent_messages):
            print(f"\nMessage {i+1}:")
            print(f"Type: {msg['type']}")
            print(f"Chat ID: {msg['chat_id']}")
            if msg['type'] == 'media':
                print(f"Media type: {msg['media_type']}")
                print(f"Caption: {msg['caption']}")
            elif msg['type'] == 'media_with_buttons':
                print(f"Media type: {msg['media_type']}")
                print(f"Caption: {msg['caption']}")
                print(f"Buttons: {json.dumps(msg.get('buttons', []), indent=2)}")
            else:
                print(f"Text: {msg['text']}")
            if msg['type'] == 'buttons' or (msg['type'] == 'media' and 'buttons' in msg):
                print(f"Buttons: {json.dumps(msg.get('buttons', []), indent=2)}")
        
        # Simulate a button click response with media
        logger.info(LogEventType.PROCESSING, "Simulating button click response with media")
        
        # Create a mock response with media and buttons
        mock_response = {
            "message": {
                "text": "This is a response to the button click with media",
                "media": [
                    {
                        "type": "image",
                        "file_id": "response_test_image",
                        "description": "Response image"
                    }
                ]
            },
            "buttons": [
                {"text": "Reply Button", "value": "reply_btn"}
            ],
            "next_step": "next_step"
        }
        
        # We need to mock the DialogService.process_user_input method to avoid database calls
        # Since we're just testing the media handling in the dialog manager, we'll directly
        # call the send_message method with a dialog message that includes media and buttons
        
        print("\nTesting button response with media:")
        
        # Create media items for the response
        response_media_items = [
            MediaItem(
                type="image",
                file_id="response_image",
                description="Response image"
            )
        ]
        
        # Create dialog message with media for the response
        response_dialog_message = DialogMessage(
            text="This is a response to the button click with media",
            media=response_media_items
        )
        
        # Create buttons for the response
        response_buttons = [
            {"text": "Reply Button", "value": "reply_btn"}
        ]
        
        # Send the response message with media and buttons
        await dialog_manager.send_message(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            message=response_dialog_message,
            buttons=response_buttons
        )
        
        # Print the results for this test
        latest_message = adapter.sent_messages[-1] if adapter.sent_messages else None
        if latest_message:
            print(f"\nResponse Message:")
            print(f"Type: {latest_message['type']}")
            print(f"Chat ID: {latest_message['chat_id']}")
            if latest_message['type'] == 'media':
                print(f"Media type: {latest_message['media_type']}")
                print(f"Caption: {latest_message['caption']}")
            elif latest_message['type'] == 'media_with_buttons':
                print(f"Media type: {latest_message['media_type']}")
                print(f"Caption: {latest_message['caption']}")
                print(f"Buttons: {json.dumps(latest_message.get('buttons', []), indent=2)}")
            else:
                print(f"Text: {latest_message.get('text', 'None')}")
                
    finally:
        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path)


async def test_multiple_media_with_buttons():
    """Test the dialog manager's handling of multiple media items with buttons."""
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
    logger.info(LogEventType.PROCESSING, "Starting multiple media with buttons test")
    
    # Test case: Send a message with multiple media items and buttons
    logger.info(LogEventType.PROCESSING, "Test case: Send a message with multiple media items and buttons")
    
    # Create buttons
    buttons = [
        {"text": "Button 1", "value": "btn1"},
        {"text": "Button 2", "value": "btn2"}
    ]
    
    # Create multiple media items
    media_items = [
        MediaItem(
            type="image",
            file_id="test_image_1",
            description="First test image"
        ),
        MediaItem(
            type="image",
            file_id="test_image_2",
            description="Second test image"
        ),
        MediaItem(
            type="document",
            file_id="test_document",
            description="Test document"
        )
    ]
    
    # Create dialog message with multiple media items
    dialog_message = DialogMessage(
        text="Here are multiple media items with buttons",
        media=media_items
    )
    
    # Send the message with multiple media items and buttons
    await dialog_manager.send_message(
        bot_id=bot_id,
        platform=platform,
        platform_chat_id=platform_chat_id,
        message=dialog_message,
        buttons=buttons
    )
    
    # Print results
    print("\nMultiple media with buttons test completed!")
    print(f"Messages sent: {len(adapter.sent_messages)}")
    
    # Analyze the sent messages
    media_group_sent = False
    buttons_sent = False
    
    for i, msg in enumerate(adapter.sent_messages):
        print(f"\nMessage {i+1}:")
        print(f"Type: {msg['type']}")
        print(f"Chat ID: {msg['chat_id']}")
        
        if msg['type'] == 'media_group':
            media_group_sent = True
            print(f"Media types: {msg['media_types']}")
            print(f"Caption: {msg['caption']}")
            print(f"Number of media items: {len(msg['media_items'])}")
        
        if msg['type'] == 'buttons':
            buttons_sent = True
            print(f"Text: {msg['text']}")
            print(f"Buttons: {json.dumps(msg.get('buttons', []), indent=2)}")
    
    if media_group_sent and buttons_sent:
        print("\nSuccess: Media group and buttons were sent separately as expected!")
    else:
        print("\nTest failed: Media group or buttons were not sent correctly")


def main():
    """Main function to run the tests"""
    print("Starting media with buttons tests...")
    
    # Run the single media test
    print("\n===== Testing Single Media with Buttons =====")
    asyncio.run(test_single_media_with_buttons())
    
    try:
        # Run the multiple media test
        print("\n===== Testing Multiple Media with Buttons =====")
        asyncio.run(test_multiple_media_with_buttons())
    except Exception as e:
        print(f"Error running multiple media test: {str(e)}")


if __name__ == "__main__":
    main()
