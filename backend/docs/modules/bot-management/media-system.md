# Media System in Bot Management

## Overview

The bot management system supports rich media messages including images, videos, audio, and documents. The media system handles both single and multiple media items with comprehensive error handling, logging, and platform-specific optimizations. Media can be used in bot responses and user inputs, providing an engaging conversation experience.

## Architecture

The media system uses a clean, layered architecture with clear separation of concerns:

### Core Components

1. **DialogManager Layer**: Handles high-level conversation orchestration and coordinates with MediaManager
2. **MediaManager Layer**: Dedicated component for all media processing, validation, and delivery (extracted from DialogManager)
3. **Platform Adapter Layer**: Provides platform-specific implementations for media delivery
4. **Input Validation Layer**: Ensures user inputs are valid and handles media-related button validation
5. **Logging Layer**: Provides detailed insights across all operations for monitoring and debugging

### MediaManager Processing Modules

The MediaManager uses a specialized architecture with focused methods:

- `process_message_sending`: Main coordinator that routes media requests based on content
- `_send_media_group`: Handles groups of multiple media items
- `_send_single_media_item`: Processes individual media items
- `_send_media_with_buttons`: Specialized handler for media with interactive buttons
- `_send_follow_up_buttons`: Manages button messages that follow media content
- `_validate_media_content`: Ensures media content meets requirements before processing

This modular approach enables better:
- **Maintainability**: Each function has a single responsibility
- **Testability**: Methods can be tested in isolation
- **Error Handling**: Specialized error handling for each scenario
- **Extensibility**: New media types or platforms can be added with minimal changes

## Media in Bot Scenarios

### Single Media Item

Media can be included in any message step of a bot scenario:

```json
{
  "steps": {
    "product_display": {
      "id": "product_display",
      "type": "message",
      "message": {
        "text": "Here's our featured product:",
        "media": [
          {
            "type": "image",
            "description": "Product image",
            "file_id": "product-xyz-image"
          }
        ]
      },
      "buttons": [
        {"text": "Buy now", "value": "buy_product"},
        {"text": "More info", "value": "product_details"}
      ],
      "expected_input": {
        "type": "button",
        "variable": "product_action"
      },
      "next_step": "handle_product_action"
    }
  }
}
```

### Multiple Media Items

The system supports sending multiple media items as a group:

```json
{
  "steps": {
    "product_gallery": {
      "type": "message",
      "message": {
        "text": "Check out our new products:",
        "media": [
          {
            "type": "image",
            "file_id": "product1_image",
            "description": "First product"
          },
          {
            "type": "image",
            "file_id": "product2_image",
            "description": "Second product"
          },
          {
            "type": "image",
            "file_id": "product3_image",
            "description": "Third product"
          }
        ]
      },
      "buttons": [
        {"text": "Buy Now", "value": "buy"},
        {"text": "More Info", "value": "info"}
      ],
      "next_step": "product_details"
    }
  }
}
```

### Media Item Properties

- `type`: The type of media. Supported values:
  - `image`: Image file (JPEG, PNG, etc.)
  - `video`: Video file
  - `audio`: Audio file
  - `document`: Any document file
  - `voice`: Voice message

- `file_id`: Unique identifier for the media file used to retrieve the media from the system
- `description` (optional): A textual description of the media

## Implementation Details

### Media Processing Flow

The system follows a clear decision tree when processing media content:

1. **Content Analysis**: Analyze message to extract text and media content
2. **Media Validation**: Validate media items to ensure they have required attributes
3. **Routing Decision**:
   - For multiple media items: Use media group sending with potential follow-up buttons
   - For single media item: Use direct media+buttons or standalone media methods
4. **Error Handling**: Apply appropriate fallback strategies based on error types
5. **Performance Monitoring**: Track timing and resource usage throughout processing

### Key Method: _process_media_sending

```python
async def _process_media_sending(
    self, 
    adapter: PlatformAdapter,
    chat_id: str,
    media: List[Any],
    message_text: str,
    buttons: Optional[List[Dict[str, str]]],
    platform: str
) -> Dict[str, Any]:
    """Process and send media messages, handling multiple media items
    
    Args:
        adapter: The platform adapter to use for sending
        chat_id: The platform chat ID to send to
        media: List of media items to send
        message_text: Text message or caption
        buttons: Optional list of buttons to include
        platform: Platform identifier (telegram, whatsapp, etc.)
        
    Returns:
        Dict with success status and response information
    """
    # Handle case with no media items
    if not media or len(media) == 0:
        return await self._send_text_only_message(adapter, chat_id, message_text, buttons)
    
    # Log the media processing
    self._log_media_processing_start(media, platform, buttons)
    
    # Send multiple media items as a group
    if len(media) > 1:
        return await self._send_media_group(adapter, chat_id, media, message_text, buttons, platform)
    
    # Handle single media item
    return await self._send_single_media_item(adapter, chat_id, media[0], message_text, buttons, platform)
```

### Error Handling and Fallback Strategies

The implementation uses a comprehensive error handling approach:

1. **Validation First**: Pre-check content before attempting to send
2. **Graceful Degradation**: Multi-level fallback strategies:
   - Media group fails → Try single media
   - Single media fails → Try text with buttons
   - All else fails → Send text-only message
3. **Detailed Error Logging**: Capture comprehensive error context
4. **Performance Monitoring**: Track timings for all operations
5. **Retry Mechanisms**: For transient errors in network operations

```python
# Example error handling with fallback and monitoring
async def _send_media_with_buttons(self, adapter, chat_id, media_type, file_id, message_text, buttons):
    try:
        # Track timing for performance monitoring
        start_time = datetime.now()
        result = await adapter.send_media_with_buttons(...)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log success with performance metrics
        self.logger.debug(LogEventType.MEDIA, f"Successfully sent {media_type}", {
            "processing_time_ms": processing_time,
            "message_id": result.get("message_id")
        })
        return result
    except Exception as e:
        # Detailed error logging
        self.logger.error(LogEventType.ERROR, f"Error: {str(e)}", {
            "exception_type": type(e).__name__,
            "media_type": media_type
        }, exc_info=e)
        
        # Fallback to simpler option
        try:
            return await adapter.send_buttons(...)
        except Exception as fallback_error:
            # Handle fallback error too
            self.logger.error(LogEventType.ERROR, "Fallback also failed")
            return {"success": False, "error": str(fallback_error)}
```

## Platform Adapter Interface

All platform adapters implement a consistent interface for media handling:

```python
# Send single media message
async def send_media_message(self, chat_id, media_type, file_path, caption=None):
    """Send a media message to a chat"""
    pass
    
# Send media with buttons attached
async def send_media_with_buttons(self, chat_id, media_type, file_path, caption=None, buttons=None):
    """Send a media message with buttons attached"""
    pass
    
# Send multiple media items as a group
async def send_media_group(self, chat_id, media_items, caption=None):
    """Send multiple media items as a group"""
    pass

# Resolve file ID to actual file path
async def _get_file_path_from_id(self, file_id):
    """Convert platform file ID to actual file path"""
    pass
```

## Telegram Implementation

The Telegram adapter implements specialized methods for media handling with enhanced error handling and performance monitoring.

### Media with Buttons Implementation

```python
async def send_media_with_buttons(
    self, 
    chat_id: str, 
    media_type: str, 
    file_path: str, 
    caption: Optional[str] = None,
    buttons: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Send a media message with buttons using Telegram's inline keyboard"""
    
    # Prepare inline keyboard if buttons are provided
    reply_markup = None
    if buttons and len(buttons) > 0:
        inline_keyboard = []
        row = []
        
        # Group buttons in rows of 2
        for i, btn in enumerate(buttons):
            callback_data = btn.get("value", f"btn_{i}")
            if len(callback_data) > 64:  # Telegram limit
                callback_data = callback_data[:60] + "..."
                
            row.append({
                "text": btn.get("text", "Button"),
                "callback_data": callback_data
            })
            
            # Create a new row after every 2 buttons
            if (i + 1) % 2 == 0 or i == len(buttons) - 1:
                inline_keyboard.append(row)
                row = []
                
        reply_markup = {"inline_keyboard": inline_keyboard}
    
    # Map media types to Telegram methods
    telegram_map = {
        "image": {"method": "sendPhoto", "file_param": "photo"},
        "video": {"method": "sendVideo", "file_param": "video"},
        "audio": {"method": "sendAudio", "file_param": "audio"},
        "document": {"method": "sendDocument", "file_param": "document"}
    }
    
    media_info = telegram_map.get(media_type.lower(), {"method": "sendDocument", "file_param": "document"})
    method = media_info["method"]
    file_param = media_info["file_param"]
    
    # Verify file exists and send
    if not os.path.exists(file_path):
        return {"success": False, "error": "File not found"}
    
    try:
        with open(file_path, "rb") as file:
            files = {file_param: file}
            data = {"chat_id": chat_id}
            
            if caption:
                data["caption"] = caption
                data["parse_mode"] = "HTML"
            
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            
            url = f"{self.api_url}{self.token}/{method}"
            response = await client.post(url, data=data, files=files)
            
            if response.json().get("ok", False):
                result = response.json().get("result", {})
                return {
                    "success": True,
                    "message_id": result.get("message_id"),
                    "response": result
                }
            else:
                error_description = response.json().get("description")
                return {"success": False, "error": error_description}
                
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### File Path Resolution with Retry Logic

```python
async def _get_file_path_from_id(self, file_id: str) -> Optional[str]:
    """Helper method to get a file path from a media ID with retry logic"""
    
    # Validate input
    if not file_id:
        self.logger.error(LogEventType.ERROR, "Cannot retrieve file: Empty file_id")
        return None
    
    # Check if already a file path
    if os.path.exists(file_id) and os.path.isfile(file_id):
        return file_id
    
    # Implement retry logic with exponential backoff
    max_retries = 2
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # Track timing
            start_time = datetime.now()
            
            # Download file with timeout protection
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(media_url)
                
                # Calculate metrics
                download_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    # Determine proper file extension based on content type
                    content_type = response.headers.get("content-type", "")
                    ext = self._get_extension_for_content_type(content_type)
                    content_length = len(response.content)
                    
                    # Log download metrics
                    self.logger.debug(LogEventType.MEDIA, f"Downloaded {content_length} bytes in {download_time:.2f}ms", {
                        "content_type": content_type,
                        "content_length": content_length,
                        "download_time_ms": download_time,
                        "download_speed_kbps": (content_length / 1024) / (download_time / 1000) if download_time > 0 else 0
                    })
                    
                    # Save to temporary file with proper extension
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(response.content)
                        tmp_path = tmp.name
                    
                    return tmp_path
                else:
                    # Handle error with smart retry decisions
                    if response.status_code in [400, 404, 403]:
                        return None  # Don't retry for these errors
                    
                    # Retry for other status codes
                    if retry_count < max_retries:
                        retry_count += 1
                        await asyncio.sleep(retry_count * 1.5)  # Exponential backoff
                        continue
                    else:
                        return None
                        
        except Exception as e:
            # Exception handling with specific retry logic
            if retry_count < max_retries and isinstance(e, (httpx.NetworkError, httpx.ConnectError)):
                retry_count += 1
                await asyncio.sleep(retry_count * 1.5)
                continue
            else:
                return None
    
    return None
```

## Enhanced Logging System

The media system provides comprehensive logging across all operations:

### Log Event Types

Media-related log event types from LogEventType enum:
- `MEDIA`: General media operations
- `MEDIA_SCENARIO`: Media in scenario definitions
- `MEDIA_REFERENCE`: Media reference resolution
- `MEDIA_FORMAT`: Media format detection
- `MEDIA_VALIDATION`: Media validation
- `MEDIA_ERROR`: Media errors

### Logging Methods

The conversation logger includes specialized methods for media-related events:

```python
# Log media processing operations
logger.media_processing(operation, media_type, data)

# Log media in scenario steps
logger.media_scenario(step_id, media_count, data)

# Log media reference resolution
logger.media_reference(file_id, resolved, data)

# Log media format detection
logger.media_format(file_path, media_type, data)

# Log media validation results
logger.media_validation(file_path, valid, data)

# Log platform-specific media operations
logger.media_platform_operation(platform, operation, data)

# Log media errors
logger.media_error(error_type, media_type, data, exc_info)
```

### Example Log Output

```
INFO | MEDIA | Media content detected in message: 3 items
  media_count: 3
  media_types: ['image', 'image', 'document']
  media_ids: ['img123', 'img456', 'doc789']
  has_buttons: true
  platform: telegram
  
DEBUG | MEDIA | Downloaded 256789 bytes in 324.56ms
  content_type: image/jpeg
  content_length: 256789
  download_time_ms: 324.56
  download_speed_kbps: 772.4
  
INFO | MEDIA | Successfully sent media group with 3 items
  message_ids: [12345, 12346, 12347]
  chat_id: 98765432
  processing_time_ms: 782.34
```

## Debugging and Troubleshooting

### Viewing Media Logs

Media logs can be viewed using the standard bot logs viewer:

```bash
# View all media logs
python -m scripts.bots.utils.view_bot_logs --source file --file logs/bot_conversations_latest.log --filter MEDIA

# View media errors only
python -m scripts.bots.utils.view_bot_logs --source file --file logs/bot_conversations_latest.log --filter MEDIA_ERROR

# View media for a specific bot
python -m scripts.bots.utils.view_bot_logs --bot-id BOT_ID --filter MEDIA
```

### Common Issues and Solutions

1. **Media Not Displaying**:
   - Ensure the file_id exists in the media system
   - Check that the media format is supported by the platform
   - Verify platform-specific media size limits

2. **Media Showing Without Buttons**:
   - Some platforms have limitations on combining media with buttons
   - The system will fall back to sending media first, then buttons separately if needed

3. **Media Not Processing in Auto-transitions**:
   - Media is fully supported in auto-transition steps
   - Ensure media is properly defined in the scenario step

### Common Media Log Patterns

1. **Media Detection**: Look for "Media content detected in message" logs
2. **Media Resolution**: Check "Retrieving media from API" logs
3. **Media Sending**: Look for platform-specific sending logs
4. **Media Errors**: Search for MEDIA_ERROR logs to find specific issues

## Testing

### Test Scripts

Comprehensive test scripts are available to validate media functionality:

```bash
# Test single media with buttons
python -m src.api.tests.unit.test_media.test_media_with_buttons

# Test multiple media items as groups
python -m src.api.tests.unit.test_media.test_media_group

# Test dialog manager media handling
python -m src.api.tests.unit.test_media.test_dialog_manager_media
```

The tests cover:
1. Single media with buttons
2. Multiple media items as groups
3. Error handling and fallback strategies
4. Performance metrics collection
5. Platform-specific implementations

## Platform Limitations

- **Telegram**: 
  - Maximum 10 media items per group
  - Only the first item can have a caption
  - File size limits vary by media type
- **Other Platforms**: Each platform has its own limitations based on API capabilities

## Future Considerations

1. **Media Optimization**: Automatic resizing and format optimization before sending
2. **Enhanced Preview Capabilities**: Richer preview options for media groups
3. **Cross-Platform Consistency**: Normalize behavior across different messaging platforms
4. **Media Analysis**: Integration with image/video analysis for content moderation
5. **Caching**: Implement media caching to improve performance
6. **Progressive Loading**: Support for progressive media loading in large groups