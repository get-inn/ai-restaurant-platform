#!/usr/bin/env python3
"""
Test script for the multiple media item functionality in the dialog manager.
This script specifically tests sending multiple media items as a group with optional buttons.
"""

import asyncio
import os
import sys
import uuid
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from src.integrations.platforms.base import PlatformAdapter
from src.bot_manager.dialog_manager import DialogManager
from src.bot_manager.conversation_logger import get_logger, LogEventType


# Mock platform adapter for testing
class MockPlatformAdapter(PlatformAdapter):
    def __init__(self):
        self.sent_messages = []
        self.logger = get_logger()
        
    @property
    def platform_name(self) -> str:
        return "mock"
        
    async def initialize(self, credentials: Dict[str, Any]) -> bool:
        return True
        
    async def send_text_message(self, chat_id: str, text: str) -> Dict[str, Any]:
        self.logger.info(LogEventType.ADAPTER, f"Mock send_text_message to {chat_id}")
        self.sent_messages.append({"type": "text", "chat_id": chat_id, "text": text})
        return {"success": True, "message_id": "12345"}
        
    async def send_media_message(
        self, 
        chat_id: str, 
        media_type: str, 
        file_path: str, 
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        self.logger.info(LogEventType.ADAPTER, f"Mock send_media_message to {chat_id}: {media_type}")
        self.sent_messages.append({
            "type": "media",
            "chat_id": chat_id,
            "media_type": media_type,
            "file_path": file_path,
            "caption": caption
        })
        return {"success": True, "message_id": "12346"}
        
    async def send_buttons(
        self,
        chat_id: str,
        text: str,
        buttons: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        self.logger.info(LogEventType.ADAPTER, f"Mock send_buttons to {chat_id}")
        button_texts = [b.get("text", "") for b in buttons]
        self.sent_messages.append({
            "type": "buttons",
            "chat_id": chat_id,
            "text": text,
            "buttons": buttons
        })
        print(f"Sent buttons with text: '{text}' and options: {button_texts}")
        return {"success": True, "message_id": "12347"}
    
    async def send_media_with_buttons(
        self, 
        chat_id: str, 
        media_type: str, 
        file_path: str, 
        caption: Optional[str] = None,
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        self.logger.info(LogEventType.ADAPTER, f"Mock send_media_with_buttons to {chat_id}")
        self.sent_messages.append({
            "type": "media_with_buttons",
            "chat_id": chat_id,
            "media_type": media_type,
            "file_path": file_path,
            "caption": caption,
            "buttons": buttons
        })
        return {"success": True, "message_id": "12348"}
        
    async def send_media_group(
        self,
        chat_id: str,
        media_items: List[Dict[str, Any]],
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        self.logger.info(LogEventType.ADAPTER, f"Mock send_media_group to {chat_id}: {len(media_items)} items")
        media_types = []
        for item in media_items:
            if isinstance(item, dict):
                media_types.append(item.get("type", "unknown"))
            else:
                media_types.append(getattr(item, "type", "unknown"))
                
        self.sent_messages.append({
            "type": "media_group",
            "chat_id": chat_id,
            "media_items": media_items,
            "media_types": media_types,
            "caption": caption
        })
        print(f"Sent media group with {len(media_items)} items of types: {media_types}")
        return {"success": True, "message_ids": ["12349", "12350", "12351"][:len(media_items)]}
        
    async def set_webhook(self, webhook_url: str) -> bool:
        return True
        
    async def delete_webhook(self) -> bool:
        return True
        
    async def get_webhook_info(self) -> Dict[str, Any]:
        return {"url": "https://example.com/webhook"}
        
    async def process_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        return update_data
        
    async def get_file_from_platform(self, file_id: str) -> Optional[bytes]:
        return b"mock_file_content"
        
    async def upload_file_to_platform(self, file_path: str) -> Optional[str]:
        return "mock_file_id"


# Mock State Repository
class MockStateRepository:
    def __init__(self):
        self.states = {}
        
    async def get_dialog_state(self, bot_id, platform, platform_chat_id):
        key = f"{bot_id}:{platform}:{platform_chat_id}"
        return self.states.get(key, {
            "id": str(uuid.uuid4()),
            "bot_id": bot_id,
            "platform": platform,
            "platform_chat_id": platform_chat_id,
            "current_step": "test_step",
            "collected_data": {}
        })
        
    async def update_dialog_state(self, dialog_state):
        key = f"{dialog_state['bot_id']}:{dialog_state['platform']}:{dialog_state['platform_chat_id']}"
        self.states[key] = dialog_state
        return dialog_state


class MockDb:
    """Mock database session"""
    pass


async def test_media_group_with_buttons():
    """Test sending multiple media items with buttons"""
    print("\n=== Testing Multiple Media Items with Buttons ===")
    
    # Setup test environment
    adapter = MockPlatformAdapter()
    dialog_manager = DialogManager(
        db=MockDb(),
        platform_adapters={"mock": adapter},
        state_repository=MockStateRepository()
    )
    
    # Test data
    bot_id = uuid.uuid4()
    platform = "mock"
    chat_id = "123456789"
    
    # Create a message with multiple media items and buttons
    media = [
        {"type": "image", "file_id": "image1", "description": "First test image"},
        {"type": "image", "file_id": "image2", "description": "Second test image"},
        {"type": "document", "file_id": "doc1", "description": "Test document"}
    ]
    
    message = {
        "text": "Here are multiple media items with buttons",
        "media": media
    }
    
    buttons = [
        {"text": "Button 1", "value": "btn1"},
        {"text": "Button 2", "value": "btn2"}
    ]
    
    # Send the message
    print("Sending message with multiple media items and buttons...")
    result = await dialog_manager.send_message(
        bot_id=bot_id,
        platform=platform,
        platform_chat_id=chat_id,
        message=message,
        buttons=buttons
    )
    
    # Analyze results
    print(f"\nMessage send result: {result}")
    print(f"Total messages sent: {len(adapter.sent_messages)}")
    
    # Look for media group
    media_group_found = False
    buttons_found = False
    
    for i, msg in enumerate(adapter.sent_messages):
        print(f"\nMessage {i+1} - Type: {msg['type']}")
        
        if msg['type'] == "media_group":
            media_group_found = True
            print(f"  Media group with {len(msg['media_items'])} items")
            print(f"  Media types: {msg['media_types']}")
            print(f"  Caption: {msg['caption']}")
            
        if msg['type'] == "buttons":
            buttons_found = True
            print(f"  Buttons text: {msg['text']}")
            print(f"  Button count: {len(msg['buttons'])}")
            print(f"  Button labels: {[b['text'] for b in msg['buttons']]}")
    
    # Verify success
    if media_group_found and buttons_found:
        print("\n✅ SUCCESS: Multiple media items sent as a group and buttons sent as follow-up")
        return True
    else:
        missing = []
        if not media_group_found:
            missing.append("media group")
        if not buttons_found:
            missing.append("buttons")
            
        print(f"\n❌ FAILURE: Missing {', '.join(missing)} in sent messages")
        return False


async def test_media_group_without_buttons():
    """Test sending multiple media items without buttons"""
    print("\n=== Testing Multiple Media Items WITHOUT Buttons ===")
    
    # Setup test environment
    adapter = MockPlatformAdapter()
    dialog_manager = DialogManager(
        db=MockDb(),
        platform_adapters={"mock": adapter},
        state_repository=MockStateRepository()
    )
    
    # Test data
    bot_id = uuid.uuid4()
    platform = "mock"
    chat_id = "123456789"
    
    # Create a message with multiple media items but no buttons
    media = [
        {"type": "image", "file_id": "image1", "description": "First test image"},
        {"type": "image", "file_id": "image2", "description": "Second test image"},
        {"type": "document", "file_id": "doc1", "description": "Test document"}
    ]
    
    message = {
        "text": "Here are multiple media items without buttons",
        "media": media
    }
    
    # Send the message
    print("Sending message with multiple media items (no buttons)...")
    result = await dialog_manager.send_message(
        bot_id=bot_id,
        platform=platform,
        platform_chat_id=chat_id,
        message=message
    )
    
    # Analyze results
    print(f"\nMessage send result: {result}")
    print(f"Total messages sent: {len(adapter.sent_messages)}")
    
    # Look for media group
    media_group_found = False
    
    for i, msg in enumerate(adapter.sent_messages):
        print(f"\nMessage {i+1} - Type: {msg['type']}")
        
        if msg['type'] == "media_group":
            media_group_found = True
            print(f"  Media group with {len(msg['media_items'])} items")
            print(f"  Media types: {msg['media_types']}")
            print(f"  Caption: {msg['caption']}")
    
    # Verify success
    if media_group_found:
        print("\n✅ SUCCESS: Multiple media items sent as a group without buttons")
        return True
    else:
        print("\n❌ FAILURE: Media group not found in sent messages")
        return False


async def run_tests():
    """Run all tests"""
    # Get logger
    logger = get_logger()
    logger.info(LogEventType.PROCESSING, "Starting media group tests")
    
    # Run tests
    with_buttons = await test_media_group_with_buttons()
    without_buttons = await test_media_group_without_buttons()
    
    # Report results
    print("\n=== TEST RESULTS ===")
    print(f"Media Group with Buttons: {'✅ PASS' if with_buttons else '❌ FAIL'}")
    print(f"Media Group without Buttons: {'✅ PASS' if without_buttons else '❌ FAIL'}")
    
    if with_buttons and without_buttons:
        print("\n🎉 All tests passed! The multiple media implementation is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Check the implementation of multiple media handling.")
        return False


if __name__ == "__main__":
    asyncio.run(run_tests())
