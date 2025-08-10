# Auto-Transitions in Bot Scenarios

## Overview

Auto-transitions allow steps in a bot conversation to automatically proceed to the next step without requiring user input. This creates a smoother, more natural conversation flow by allowing a series of messages to be displayed in sequence with configurable delays between them.

Auto-transitions are useful for:
- Onboarding flows where you want to present information step by step
- Tutorial sequences that guide users through a process
- Multi-part messages that should be shown with natural pauses between them
- "Typing" indicators to make the bot feel more human-like

## How to Use Auto-Transitions

To enable auto-transitions in your bot scenarios, add the `auto_next: true` property to any step that should automatically transition to the next step.

You can also customize the delay between transitions by adding the `auto_next_delay` property (in seconds). If not specified, it defaults to 1.5 seconds.

### Basic Example

```json
{
  "steps": {
    "welcome": {
      "id": "welcome",
      "type": "message",
      "message": {
        "text": "Welcome to our bot!"
      },
      "next_step": "intro_1",
      "auto_next": true,
      "auto_next_delay": 2.0  // Wait 2 seconds before showing the next message
    },
    "intro_1": {
      "id": "intro_1",
      "type": "message",
      "message": {
        "text": "I'm here to help you with your questions."
      },
      "next_step": "intro_2",
      "auto_next": true  // Uses default delay of 1.5 seconds
    },
    "intro_2": {
      "id": "intro_2",
      "type": "message",
      "message": {
        "text": "Please select from the options below:"
      },
      "buttons": [
        {"text": "Option 1", "value": "opt_1"},
        {"text": "Option 2", "value": "opt_2"}
      ],
      "expected_input": {
        "type": "button",
        "variable": "selected_option"
      },
      "next_step": "handle_selection"
    }
  }
}
```

## Architecture

The auto-transition system involves multiple components working together:

### Component Overview

1. **ScenarioProcessor**: Extracts auto-transition properties (`auto_next`, `auto_next_delay`) from scenario steps
2. **DialogService**: Processes user input and returns responses with auto-transition information
3. **DialogManager**: Handles the execution of auto-transitions, including state management and message sending
4. **ConversationLogger**: Provides detailed logging of auto-transition events

### Separation of Concerns

The architecture maintains a clear separation of concerns:

- **DialogService** is the single source of truth for message sending
- **Auto-transition logic** is responsible only for state updates
- **State-Only Mode** allows transitions without duplicate message sending

### Message Control Flow

The system controls message sending based on the `state_only` parameter:

```python
async def _process_auto_next_step(
    self,
    bot_id: UUID,
    platform: str,
    platform_chat_id: str,
    step_id: str,
    transition_id: str = None,
    _step_sequence: List[str] = None,
    source_step: str = None,
    state_only: bool = False  # Controls message sending
) -> None:
    # Implementation details...
    
    if state_only:
        # Only update state, don't send messages
        self.logger.debug(LogEventType.AUTO_TRANSITION,
                         f"Message sending disabled for step {step_id} (state_only mode)")
    else:
        # Send the message
        sent = await self.send_message(
            bot_id=bot_id,
            platform=platform,
            platform_chat_id=platform_chat_id,
            message=message_text,
            buttons=buttons
        )
```

### Architecture Diagram

```
┌─────────────────┐         ┌───────────────────────┐
│                 │         │                       │
│  DialogService  │◄────────┤    DialogManager      │
│                 │         │                       │
└────────┬────────┘         └───────────┬───────────┘
         │                              │
         │ Processes input              │ Manages auto-transitions
         │ Sends messages               │ Updates state
         │                              │
┌────────▼────────┐         ┌───────────▼───────────┐
│                 │         │                       │
│ ScenarioProc.   │         │  _process_auto_next   │
│                 │         │  state_only=True      │
└─────────────────┘         └───────────────────────┘
```

## Use Cases

### 1. Sequential Information Presentation

When you need to present multiple pieces of information in sequence:

```json
"company_info_1": {
  "id": "company_info_1",
  "type": "message",
  "message": {
    "text": "Our company was founded in 2010."
  },
  "next_step": "company_info_2",
  "auto_next": true,
  "auto_next_delay": 2.0
},
"company_info_2": {
  "id": "company_info_2",
  "type": "message",
  "message": {
    "text": "We have offices in 12 countries worldwide."
  },
  "next_step": "company_info_3",
  "auto_next": true,
  "auto_next_delay": 2.0
}
```

### 2. Onboarding Flow with Media

For creating an engaging onboarding experience with media:

```json
"welcome": {
  "id": "welcome",
  "type": "message",
  "message": {
    "text": "Welcome to our platform!",
    "media": [
      {
        "type": "image",
        "file_id": "welcome_image"
      }
    ]
  },
  "next_step": "feature_intro",
  "auto_next": true,
  "auto_next_delay": 3.0  // Longer delay to allow time to view the image
}
```

### 3. Progressive Form Filling

To break down a long form into smaller, less intimidating pieces:

```json
"ask_name": {
  "id": "ask_name",
  "type": "message",
  "message": {
    "text": "Let's get started with your registration."
  },
  "next_step": "name_prompt",
  "auto_next": true,
  "auto_next_delay": 1.0
},
"name_prompt": {
  "id": "name_prompt",
  "type": "message",
  "message": {
    "text": "What's your name?"
  },
  "expected_input": {
    "type": "text",
    "variable": "name"
  },
  "next_step": "thank_name"
}
```

## Technical Implementation

### Scenario Schema

The scenario schema includes auto-transition properties:

```json
{
  "id": "step_id",
  "type": "message",
  "message": {
    "text": "Message content"
  },
  "next_step": "next_step_id",
  "auto_next": true,           // Indicates automatic transition to next step
  "auto_next_delay": 1.5       // Delay in seconds before auto-transition (optional, default: 1.5)
}
```

### ScenarioProcessor Implementation

The `ScenarioProcessor` class extracts and returns auto-transition properties:

```python
def process_step(self, scenario, step_id, collected_data=None, custom_conditions=None):
    # Existing step processing logic...
    
    # Add handling for auto_next property
    auto_next = step.get("auto_next", False)
    
    return {
        "message": processed_message,
        "buttons": buttons,
        "expected_input": expected_input,
        "next_step": next_step_id,
        "auto_next": auto_next,
        "auto_next_delay": step.get("auto_next_delay", 1.5)
    }
```

### DialogManager Auto-Transition Processing

```python
async def _process_auto_next_step(
    self,
    bot_id: UUID,
    platform: str,
    platform_chat_id: str,
    step_id: str,
    transition_id: str = None,
    _step_sequence: List[str] = None,
    source_step: str = None,
    state_only: bool = False
) -> None:
    # Get dialog state
    dialog_state = await self.dialog_service.state_repository.get_dialog_state(
        bot_id=bot_id,
        platform=platform,
        platform_chat_id=platform_chat_id
    )
    
    # Log the auto-transition processing
    self.logger.info(
        LogEventType.AUTO_TRANSITION,
        f"Processing auto-transition step '{step_id}'",
        {"step_id": step_id, "dialog_id": str(dialog_state.id)}
    )
    
    try:
        # Process the step
        processed_step = await self.dialog_service.scenario_processor.process_step(
            scenario=scenario,
            step_id=step_id,
            collected_data=dialog_state.collected_data
        )
        
        # Send response if not in state_only mode
        if not state_only:
            response = self.dialog_service._prepare_response(processed_step, dialog_state.collected_data)
            await self.send_message(bot_id, platform, platform_chat_id, response)
        
        # Update dialog state
        dialog_state.current_step = processed_step["next_step"]
        await self.dialog_service.state_repository.update_dialog_state(dialog_state)
        
        # Continue auto-transition chain if needed
        if processed_step.get("auto_next", False):
            auto_next_delay = processed_step.get("auto_next_delay", 1.5)
            await asyncio.sleep(auto_next_delay)
            await self._process_auto_next_step(
                bot_id, platform, platform_chat_id, 
                processed_step["next_step"], 
                transition_id, _step_sequence, step_id, state_only
            )
            
    except Exception as e:
        # Log auto-transition error
        self.logger.error(
            LogEventType.AUTO_TRANSITION,
            f"Error during auto-transition for step '{step_id}': {str(e)}",
            {"step_id": step_id, "error": str(e)},
            exc_info=e
        )
```

## Logging and Debugging

### Comprehensive Logging

The system provides detailed logging for auto-transitions:

```
2025-08-09 17:34:44.655 | INFO | AUTO_TRANSITION | Starting auto-transition to step 'documents_list' with delay 1.5s
2025-08-09 17:34:46.155 | INFO | AUTO_TRANSITION | Message sending disabled for step documents_list (state_only mode)
2025-08-09 17:34:46.157 | INFO | AUTO_TRANSITION | Auto-transition completed for step 'documents_list'
```

### Log Event Types

Key auto-transition logging points include:

- **Auto-Transition Start**: When an auto-transition is initiated
- **Auto-Transition Processing**: When a step is being processed
- **Auto-Transition Completion**: When a step completes successfully
- **Chain Continuation**: When continuing a chain of auto-transitions
- **Error Handling**: When errors occur during auto-transitions

### Debugging Tools

Use the specialized utility for analyzing auto-transitions:

```bash
python -m scripts.bots.utils.view_auto_transitions
```

Additional options:
- `--bot-id BOT_ID`: Filter by specific bot
- `--platform PLATFORM`: Filter by platform (e.g., telegram, whatsapp)
- `--chat-id CHAT_ID`: Filter by chat ID
- `--with-errors`: Show only chains with errors
- `--timing`: Show detailed timing information

## Best Practices

### 1. Balance Speed and Readability

- Use longer delays (2-3 seconds) for messages that contain important information
- Use shorter delays (1-1.5 seconds) for brief transitional messages
- Consider the length and complexity of each message when setting delays

### 2. Mix Auto-Transitions with User Input

- Don't create too many consecutive auto-transitions (4-5 maximum)
- Break up long sequences with user interaction to maintain engagement
- Use auto-transitions to lead into user input prompts

### 3. Handle Media Content

- Increase delay times when showing media content to give users time to view it
- Consider the complexity of media when setting delays (complex images need more time)

### 4. Consider Platform Limitations

- Be aware that some messaging platforms may have rate limits
- Test auto-transition sequences on all target platforms
- Ensure media loads properly before auto-transitioning to the next step

## Error Handling and Considerations

### Race Conditions

The system handles cases where a user sends input during an auto-transition delay period by processing the input normally and interrupting the auto-transition sequence.

### Error Recovery

If an error occurs during auto-transition processing, the system gracefully falls back to waiting for user input and logs the error for debugging.

### Platform Limitations

Some messaging platforms may have rate limiting or sequential message ordering guarantees that are respected by the auto-transition system.

### Timeout Handling

Auto-transitions have safeguards to prevent infinite loops or excessive message sending through maximum chain length and total duration limits.

## Testing

### Unit Tests

- Test ScenarioProcessor's handling of auto_next property
- Test DialogService's processing of auto-transitions
- Test DialogManager's chained auto-transition logic
- Test proper logging of auto-transition events

### Integration Tests

- Test simple auto-transitions between two steps
- Test chains of auto-transitions across multiple steps
- Test mixed scenarios with both automatic and user-input steps
- Test error handling during auto-transitions
- Verify log entries for all auto-transition events

### End-to-End Tests

- Test the complete flow on actual messaging platforms
- Verify timing and message delivery order
- Validate logging across the entire auto-transition chain

## Implementation Status

The auto-transition functionality has been fully implemented in the following components:

1. **ScenarioProcessor**: Updated to extract and return auto_next properties from scenario steps
2. **ConversationLogger**: Added AUTO_TRANSITION event type and auto_transition method
3. **DialogManager**: 
   - Added _process_auto_next_step method with state_only parameter
   - Added auto-transition handling to handle_text_message and handle_button_click
   - Implemented chain tracking and performance metrics
4. **Tests**: Added comprehensive unit and integration tests

### Example Scenario

A complete example scenario demonstrating auto-transition functionality is available at:
`/docs/modules/bot-management/examples/auto_transition_example.json`

This scenario shows how to use auto-transitions in various contexts:
- Auto-transitions in a sequence of steps
- Auto-transitions with media content
- Auto-transitions after user input
- Mixing auto-transitions with regular steps requiring user interaction

## Future Improvements

Potential future improvements to the auto-transition system:

1. Make state-only mode configurable at the scenario level
2. Add support for conditional auto-transitions based on collected data
3. Implement auto-transition analytics for conversation flow optimization
4. Add support for parallel auto-transitions in different contexts
5. Enhanced debugging tools with visual flow representation