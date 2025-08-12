# MediaManager Component

**Version**: 1.0  
**Date**: January 2025  
**Status**: Production Ready ✅

## Overview

The MediaManager is a dedicated component extracted from DialogManager to handle all media processing, validation, and sending operations. This separation of concerns significantly improves maintainability and provides specialized media handling capabilities.

## Architecture Benefits

### Extraction Impact
- **DialogManager reduced**: From 1,403 to 882 lines (37% reduction)
- **Code elimination**: Removed 521 lines of duplicate media handling
- **Focused responsibility**: Dedicated media processing component
- **Improved testability**: Isolated media operations

### Key Features
- ✅ **Single media handling**: Images, videos, documents, audio
- ✅ **Media groups**: Multiple media items in one message
- ✅ **Media with buttons**: Interactive media messages
- ✅ **Multiple formats**: Dictionary and Pydantic object compatibility
- ✅ **Platform abstraction**: Works with any PlatformAdapter
- ✅ **Comprehensive logging**: Detailed media processing logs

## Class Structure

```python
class MediaManager:
    def __init__(self, logger: ConversationLogger):
        self.logger = logger
    
    # Main entry points
    async def process_message_sending(...)  # Core message processing
    
    # Content extraction and validation
    def extract_message_content(...)        # Extract text/media from messages
    def validate_media_items(...)           # Validate media items
    
    # Logging utilities
    def log_media_content(...)              # Log media details
    def log_media_scenario(...)             # Log message composition
    
    # Specialized sending methods
    async def send_text_only_message(...)   # Text without media
    async def send_media_without_buttons(...)
    async def send_media_with_buttons(...)
    async def send_single_media_item(...)
    async def send_media_group(...)
    async def send_follow_up_buttons(...)
```

## Core Methods

### process_message_sending()
Main entry point for all message processing. Determines the appropriate sending strategy based on message content.

**Parameters:**
- `adapter`: PlatformAdapter instance
- `platform_chat_id`: Chat ID for the platform
- `message`: Message content (str, DialogMessage, or dict)
- `buttons`: Optional buttons list

**Logic Flow:**
1. Extract text and media content
2. Log message composition scenario
3. Determine sending strategy:
   - Text-only: Use `send_text_only_message()`
   - Single media: Use `send_single_media_item()`
   - Multiple media: Use `send_media_group()`

### extract_message_content()
Extracts text and media from various message formats:

```python
# Supported formats:
message = "Simple text"                    # String
message = DialogMessage(text="...", media=[...])  # Pydantic object
message = {"text": "...", "media": [...]}  # Dictionary
```

**Returns:** `Tuple[Optional[str], List[Dict[str, Any]]]`

### validate_media_items()
Validates media items for required attributes:
- `type`: Must be in ['photo', 'video', 'audio', 'document', 'animation', 'image']
- `file_id`: Required for all media items

**Compatibility:** Handles both dictionary and Pydantic object formats.

## Sending Strategies

### Text-Only Messages
```python
await media_manager.send_text_only_message(
    adapter, chat_id, text_content, buttons
)
```
- Uses `adapter.send_text_message()` or `adapter.send_buttons()`
- Handles button presence automatically

### Single Media Items
```python
await media_manager.send_single_media_item(
    adapter, chat_id, media_item, buttons
)
```
- Uses `adapter.send_media_message()` or `adapter.send_media_with_buttons()`
- Adds text as caption if present and no existing caption

### Media Groups
```python
await media_manager.send_media_group(
    adapter, chat_id, media_items, buttons
)
```
- Attempts `adapter.send_media_group()` if available
- Falls back to individual media sending
- Sends buttons as follow-up message for groups

## Platform Adapter Integration

The MediaManager integrates with PlatformAdapter interface methods:

```python
# Required PlatformAdapter methods:
async def send_text_message(chat_id: str, text: str)
async def send_media_message(chat_id: str, media_type: str, file_path: str, caption: str = None)
async def send_media_with_buttons(chat_id: str, media_type: str, file_path: str, caption: str = None, buttons: List = None)
async def send_buttons(chat_id: str, text: str, buttons: List)
async def send_media_group(chat_id: str, media_items: List, caption: str = None)  # Optional
```

## Error Handling

MediaManager provides comprehensive error handling:

```python
try:
    result = await media_manager.process_message_sending(...)
except Exception as e:
    self.logger.error("MEDIA_PROCESSING", f"Error: {str(e)}", exc_info=True)
    raise
```

**Error Types:**
- `ValueError`: Invalid media items or missing content
- `AttributeError`: Platform adapter method not found
- `Exception`: General processing errors

## Logging Integration

MediaManager provides detailed logging through ConversationLogger:

### Event Types
- `MEDIA_SCENARIO`: Message composition analysis
- `MEDIA_CONTENT_LOG`: Detailed media content information
- `TEXT_SEND`: Text message sending events
- `MEDIA_SEND`: Media message sending events
- `MEDIA_GROUP`: Media group operations
- `BUTTON_FOLLOWUP`: Follow-up button sending
- `MEDIA_PROCESSING`: General processing events

### Log Examples
```json
{
  "event_type": "MEDIA_SCENARIO",
  "has_text": true,
  "text_length": 29,
  "media_count": 1,
  "has_buttons": true,
  "button_count": 2,
  "text_preview": "Here is an image with buttons",
  "media_types": ["image"]
}
```

## Usage Examples

### Basic Text Message
```python
media_manager = MediaManager(conversation_logger)

await media_manager.process_message_sending(
    adapter=telegram_adapter,
    platform_chat_id="123456789",
    message="Hello, world!",
    buttons=None
)
```

### Media with Buttons
```python
dialog_message = DialogMessage(
    text="Choose an option:",
    media=[
        MediaItem(type="image", file_id="abc123", description="Sample image")
    ]
)

buttons = [
    {"text": "Option 1", "value": "opt1"},
    {"text": "Option 2", "value": "opt2"}
]

await media_manager.process_message_sending(
    adapter=telegram_adapter,
    platform_chat_id="123456789",
    message=dialog_message,
    buttons=buttons
)
```

### Multiple Media Items
```python
media_items = [
    MediaItem(type="image", file_id="img1", description="First image"),
    MediaItem(type="image", file_id="img2", description="Second image"),
    MediaItem(type="document", file_id="doc1", description="Document")
]

dialog_message = DialogMessage(
    text="Here are multiple files:",
    media=media_items
)

await media_manager.process_message_sending(
    adapter=telegram_adapter,
    platform_chat_id="123456789",
    message=dialog_message,
    buttons=[{"text": "Got it", "value": "confirm"}]
)
```

## Testing

MediaManager includes comprehensive test coverage:

### Unit Tests
- `test_single_media_with_buttons.py`: Single media item handling
- `test_multiple_media_with_buttons.py`: Media group handling
- `test_media_group.py`: Media group specific tests
- `test_dialog_manager_media.py`: Integration with DialogManager

### Test Results ✅
```
src/api/tests/unit/test_media/test_dialog_manager_media.py::test_dialog_manager_media PASSED
src/api/tests/unit/test_media/test_media_group.py::test_media_group_with_buttons PASSED
src/api/tests/unit/test_media/test_media_group.py::test_media_group_without_buttons PASSED
src/api/tests/unit/test_media/test_media_with_buttons.py::test_single_media_with_buttons PASSED
src/api/tests/unit/test_media/test_media_with_buttons.py::test_multiple_media_with_buttons PASSED
```

### Mock Adapters
Tests use MockAdapter that implements the PlatformAdapter interface:

```python
class MockAdapter:
    async def send_text_message(self, chat_id: str, text: str): ...
    async def send_media_message(self, chat_id: str, media_type: str, file_path: str, caption: str = None): ...
    async def send_media_with_buttons(self, chat_id: str, media_type: str, file_path: str, caption: str = None, buttons: List = None): ...
    async def send_buttons(self, chat_id: str, text: str, buttons: List): ...
    async def send_media_group(self, chat_id: str, media_items: List, caption: str = None): ...
```

## Integration with DialogManager

MediaManager is integrated into DialogManager through dependency injection:

```python
class DialogManager:
    def __init__(self, ...):
        self._media_manager_class = MediaManager
    
    def _get_media_manager(self, bot_id, platform, platform_chat_id):
        conversation_logger = ConversationLogger(
            bot_id=str(bot_id),
            dialog_id=f"{platform}:{platform_chat_id}",
            platform=platform,
            platform_chat_id=platform_chat_id
        )
        return self._media_manager_class(conversation_logger)
    
    async def send_message(self, ...):
        media_manager = self._get_media_manager(bot_id, platform, platform_chat_id)
        return await media_manager.process_message_sending(...)
```

## Production Compatibility

### Recent Fixes ✅
- **Method alignment**: Corrected calls to match TelegramAdapter interface
- **Parameter compatibility**: Fixed file_id vs file_path handling
- **Error handling**: Improved error messages and debugging
- **Test coverage**: Complete test suite for all functionality

### Platform Support
- ✅ **Telegram**: Full compatibility with TelegramAdapter
- ✅ **Generic platforms**: Works with any PlatformAdapter implementation
- ✅ **Mock testing**: Complete mock adapter for testing

## Performance Considerations

### Optimizations
- **Lazy instantiation**: MediaManager created per conversation context
- **Efficient logging**: Structured logging with minimal overhead
- **Memory management**: No persistent state, garbage collection friendly
- **Error isolation**: Individual media item failures don't affect others

### Scalability
- **Stateless design**: No shared state between instances
- **Platform abstraction**: Easy to add new messaging platforms
- **Async operations**: Non-blocking media processing
- **Resource cleanup**: Proper cleanup of temporary resources

## Future Enhancements

1. **Media caching**: Cache processed media for performance
2. **Media validation**: Enhanced validation for file types and sizes
3. **Media transformation**: Automatic resizing and format conversion
4. **Analytics integration**: Media usage analytics and metrics
5. **Advanced media groups**: Support for mixed media types in groups

## Related Documentation

- [Bot Management Overview](overview.md) - System architecture
- [Media System](media-system.md) - Media storage and processing
- [Conversation Logging](conversation-logging.md) - Logging system details
- [Platform Adapters](../integrations/telegram.md) - Platform integration