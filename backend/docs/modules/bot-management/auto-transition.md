# Auto-Transition Functionality for Bot Scenarios

## Overview

This technical specification outlines the implementation of an "auto-transition" feature for bot scenarios. Auto-transitions allow steps in a conversation flow to automatically proceed to the next step without requiring user input, creating a more fluid and natural conversation experience.

## Background

In the current implementation, every step in a bot scenario requires user input before proceeding to the next step. However, there are cases where we want to display multiple messages in sequence without user interaction between them. The `auto_next` property exists in the scenario schema but is not currently implemented in the codebase.

## Requirements

1. Implement support for automatic transitions between dialog steps
2. Honor the `auto_next: true` property in scenario steps
3. Allow customizable delay between auto-transitions
4. Support chains of auto-transitions (multiple steps that automatically follow each other)
5. Ensure compatibility with existing scenario format and dialog flow
6. Implement detailed logging for auto-transitions to aid in debugging

## Auto-Transition Behavior

Auto-transitions will occur when:
- There's a defined next step in the scenario
- The current step has `auto_next: true` set
- There's no expected user input for the current step
- A configurable delay (default: 1.5 seconds) is used before transitioning to give users time to read the message

## Technical Implementation

### 1. Update Scenario Processor

The `ScenarioProcessor` class will be enhanced to recognize and process the `auto_next` property:

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
        "auto_next": auto_next,  # Add to return value
        "auto_next_delay": step.get("auto_next_delay", 1.5)  # Default delay of 1.5 seconds
    }
```

### 2. Enhance Dialog Service

The `DialogService` class will be modified to handle auto-transitions:

```python
async def process_user_input(self, platform, chat_id, input_type, input_value, **kwargs):
    # Existing input processing logic...
    
    # Get processed step
    processed_step = self.scenario_processor.process_step(
        scenario=scenario,
        step_id=current_step,
        collected_data=dialog_state.collected_data
    )
    
    # Prepare response
    response = self._prepare_response(processed_step, dialog_state.collected_data)
    
    # Check for auto_next
    auto_next = processed_step.get("auto_next", False)
    auto_next_delay = processed_step.get("auto_next_delay", 1.5)
    
    # Update dialog state with next step
    dialog_state.current_step = processed_step["next_step"]
    self.state_repository.update_dialog_state(dialog_state)
    
    return {
        "response": response,
        "auto_next": auto_next,
        "auto_next_delay": auto_next_delay,
        "next_step": processed_step["next_step"]
    }
```

### 3. Update Dialog Manager

The `DialogManager` will need to implement the logic to handle automatic transitions:

```python
async def process_incoming_message(self, platform, message):
    # Existing message processing logic...
    
    # Process the user input
    result = await self.dialog_service.process_user_input(
        platform=platform,
        chat_id=chat_id,
        input_type=input_type,
        input_value=input_value
    )
    
    # Send the initial response
    await self.send_message(platform, chat_id, result["response"])
    
    # Handle auto-transitions
    if result.get("auto_next", False):
        # Log the start of auto-transition
        self.logger.info(
            LogEventType.AUTO_TRANSITION, 
            f"Starting auto-transition to step '{result['next_step']}' with delay {result['auto_next_delay']}s",
            {"next_step": result["next_step"], "delay": result["auto_next_delay"]}
        )
        
        # Wait for the specified delay
        await asyncio.sleep(result["auto_next_delay"])
        
        # Process the auto-next step (without user input)
        await self._process_auto_next_step(platform, chat_id, result["next_step"])

async def _process_auto_next_step(self, platform, chat_id, step_id):
    # Get dialog state
    dialog_state = self.dialog_service.state_repository.get_dialog_state(
        platform=platform,
        chat_id=chat_id
    )
    
    # Log the auto-transition processing
    self.logger.info(
        LogEventType.AUTO_TRANSITION,
        f"Processing auto-transition step '{step_id}'",
        {"step_id": step_id, "dialog_id": str(dialog_state.id)}
    )
    
    # Get scenario
    scenario = self.dialog_service.scenario_repository.get_scenario(dialog_state.scenario_id)
    
    try:
        # Process the step
        processed_step = self.dialog_service.scenario_processor.process_step(
            scenario=scenario,
            step_id=step_id,
            collected_data=dialog_state.collected_data
        )
        
        # Prepare and send response
        response = self.dialog_service._prepare_response(processed_step, dialog_state.collected_data)
        await self.send_message(platform, chat_id, response)
        
        # Log successful auto-transition
        self.logger.info(
            LogEventType.AUTO_TRANSITION,
            f"Auto-transition completed for step '{step_id}'",
            {
                "step_id": step_id,
                "next_step": processed_step["next_step"],
                "has_auto_next": processed_step.get("auto_next", False)
            }
        )
        
        # Update dialog state with next step
        dialog_state.current_step = processed_step["next_step"]
        self.dialog_service.state_repository.update_dialog_state(dialog_state)
        
        # Check if this step also has auto_next and continue the chain if needed
        if processed_step.get("auto_next", False):
            auto_next_delay = processed_step.get("auto_next_delay", 1.5)
            
            # Log the next auto-transition in chain
            self.logger.info(
                LogEventType.AUTO_TRANSITION,
                f"Continuing auto-transition chain to step '{processed_step['next_step']}'",
                {"next_step": processed_step["next_step"], "delay": auto_next_delay}
            )
            
            await asyncio.sleep(auto_next_delay)
            await self._process_auto_next_step(platform, chat_id, processed_step["next_step"])
    except Exception as e:
        # Log auto-transition error
        self.logger.error(
            LogEventType.AUTO_TRANSITION,
            f"Error during auto-transition for step '{step_id}': {str(e)}",
            {"step_id": step_id, "error": str(e)},
            exc_info=e
        )
        
        # Update state to indicate auto-transition failure
        dialog_state.metadata = dialog_state.metadata or {}
        dialog_state.metadata["auto_transition_error"] = {
            "step_id": step_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        self.dialog_service.state_repository.update_dialog_state(dialog_state)
```

### 4. Update Scenario Schema

The scenario schema will be updated to formally include the auto-transition properties:

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

### 5. Add New Log Event Type

Add a new `AUTO_TRANSITION` event type to the `LogEventType` enum in the conversation logger:

```python
class LogEventType(str, Enum):
    # Existing event types...
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    STATE_CHANGE = "STATE_CHANGE"
    ERROR = "ERROR"
    
    # New event type for auto-transitions
    AUTO_TRANSITION = "AUTO_TRANSITION"
```

## Enhanced Logging for Auto-Transitions

To facilitate debugging and monitoring of auto-transitions, a comprehensive logging strategy will be implemented:

### 1. Log Event Types

A new log event type `AUTO_TRANSITION` will be added to capture all auto-transition related events.

### 2. Key Auto-Transition Logging Points

The system will log the following key events:

#### Auto-Transition Start
```json
{
  "timestamp": "2023-07-13T10:15:30.123Z",
  "level": "INFO",
  "event_type": "AUTO_TRANSITION",
  "message": "Starting auto-transition to step 'documents_list_confirm' with delay 1.5s",
  "context": {
    "bot_id": "11111111-1111-1111-1111-111111111111",
    "platform": "telegram",
    "platform_chat_id": "12345678",
    "dialog_id": "22222222-2222-2222-2222-222222222222"
  },
  "data": {
    "next_step": "documents_list_confirm",
    "delay": 1.5,
    "from_step": "documents_list",
    "transition_id": "auto_trans_12345" // Unique ID to track a chain of transitions
  }
}
```

#### Auto-Transition Processing
```json
{
  "timestamp": "2023-07-13T10:15:31.623Z",
  "level": "INFO",
  "event_type": "AUTO_TRANSITION",
  "message": "Processing auto-transition step 'documents_list_confirm'",
  "context": {
    "bot_id": "11111111-1111-1111-1111-111111111111",
    "platform": "telegram",
    "platform_chat_id": "12345678",
    "dialog_id": "22222222-2222-2222-2222-222222222222"
  },
  "data": {
    "step_id": "documents_list_confirm",
    "transition_id": "auto_trans_12345"
  }
}
```

#### Auto-Transition Completion
```json
{
  "timestamp": "2023-07-13T10:15:31.823Z",
  "level": "INFO",
  "event_type": "AUTO_TRANSITION",
  "message": "Auto-transition completed for step 'documents_list_confirm'",
  "context": {
    "bot_id": "11111111-1111-1111-1111-111111111111",
    "platform": "telegram",
    "platform_chat_id": "12345678",
    "dialog_id": "22222222-2222-2222-2222-222222222222"
  },
  "data": {
    "step_id": "documents_list_confirm",
    "next_step": "documents_button",
    "has_auto_next": false,
    "transition_id": "auto_trans_12345",
    "execution_time_ms": 200
  }
}
```

#### Chain Continuation
```json
{
  "timestamp": "2023-07-13T10:15:31.823Z",
  "level": "INFO",
  "event_type": "AUTO_TRANSITION",
  "message": "Continuing auto-transition chain to step 'next_auto_step'",
  "context": {
    "bot_id": "11111111-1111-1111-1111-111111111111",
    "platform": "telegram",
    "platform_chat_id": "12345678",
    "dialog_id": "22222222-2222-2222-2222-222222222222"
  },
  "data": {
    "next_step": "next_auto_step",
    "delay": 1.5,
    "from_step": "current_step",
    "transition_id": "auto_trans_12345",
    "chain_position": 2
  }
}
```

#### Error Handling
```json
{
  "timestamp": "2023-07-13T10:15:31.900Z",
  "level": "ERROR",
  "event_type": "AUTO_TRANSITION",
  "message": "Error during auto-transition for step 'documents_list_confirm': Step not found",
  "context": {
    "bot_id": "11111111-1111-1111-1111-111111111111",
    "platform": "telegram",
    "platform_chat_id": "12345678",
    "dialog_id": "22222222-2222-2222-2222-222222222222"
  },
  "data": {
    "step_id": "documents_list_confirm",
    "error": "Step not found in scenario",
    "transition_id": "auto_trans_12345",
    "stack_trace": "..."
  }
}
```

### 3. Chain Tracking

For chains of auto-transitions, a unique `transition_id` will be generated and included in all related logs to enable easy tracking of complete transition sequences.

### 4. Performance Metrics

Execution times for auto-transitions will be logged to help identify potential performance issues.

### 5. Log Filtering

The existing log viewing utility will be enhanced to support filtering by the new `AUTO_TRANSITION` event type:

```bash
python -m scripts.bots.utils.view_bot_logs --event-type AUTO_TRANSITION
```

### 6. Visualizing Auto-Transition Chains

A new utility function will be added to the log viewing script to visualize chains of auto-transitions:

```bash
python -m scripts.bots.utils.view_bot_logs --auto-transition-chains --dialog-id DIALOG_ID
```

This will output a sequential view of auto-transitions showing timing, steps, and any errors:

```
Auto-Transition Chain: auto_trans_12345
Start time: 2023-07-13 10:15:30.123Z
Total duration: 2.1s
Steps:
1. documents_list → documents_list_confirm (1.5s delay, 0.2s processing)
2. documents_list_confirm → documents_button (1.5s delay, 0.3s processing)
3. documents_button → company_history (1.5s delay, 0.2s processing)
Status: Completed successfully
```

## Considerations

1. **Race Conditions**: The system must handle cases where a user sends input during an auto-transition delay period.

2. **Error Handling**: If an error occurs during auto-transition processing, the system should gracefully fall back to waiting for user input.

3. **Platform Limitations**: Some messaging platforms may have rate limiting or sequential message ordering guarantees that need to be respected.

4. **Timeout Handling**: Auto-transitions should have a maximum chain length or total duration to prevent infinite loops or excessive message sending.

5. **Monitoring and Alerts**: For production environments, consider adding alerts for auto-transition failures or unusually long chains.

## Testing

1. **Unit Tests**: 
   - Test ScenarioProcessor's handling of auto_next property
   - Test DialogService's processing of auto-transitions
   - Test DialogManager's chained auto-transition logic
   - Test proper logging of auto-transition events

2. **Integration Tests**:
   - Test simple auto-transitions between two steps
   - Test chains of auto-transitions across multiple steps
   - Test mixed scenarios with both automatic and user-input steps
   - Test error handling during auto-transitions
   - Verify log entries for all auto-transition events

3. **End-to-End Tests**:
   - Test the complete flow on actual messaging platforms
   - Verify timing and message delivery order
   - Validate logging across the entire auto-transition chain

## Migration Plan

1. Implement the auto-transition functionality in the core components
2. Update schema validation to include the new properties
3. Implement enhanced logging for auto-transitions
4. Add unit and integration tests for the new functionality
5. Update documentation to reflect the new auto-transition feature
6. Review existing scenarios to identify opportunities to utilize auto-transitions

## Conclusion

The auto-transition functionality will enhance the bot conversation experience by allowing more fluid and natural conversation flows. By implementing this feature with comprehensive logging, the system will be able to support more sophisticated scenarios that better mimic human conversation patterns while maintaining excellent visibility for debugging and monitoring.

## Implementation Status

The auto-transition functionality has been implemented in the following components:

1. **ScenarioProcessor**: Updated to extract and return auto_next properties from scenario steps
2. **ConversationLogger**: Added AUTO_TRANSITION event type and auto_transition method
3. **DialogManager**: 
   - Added _process_auto_next_step method to handle auto-transitions
   - Added auto-transition handling to handle_text_message and handle_button_click
   - Implemented chain tracking and performance metrics
4. **Tests**: Added unit tests for auto-transition functionality

### Example Usage

An example scenario that demonstrates the auto-transition functionality is available at:
`/docs/modules/bot-management/example-scenario/auto_transition_example.json`

This scenario shows how to use auto-transitions in various contexts:
- Auto-transitions in a sequence of steps
- Auto-transitions with media content
- Auto-transitions after user input
- Mixing auto-transitions with regular steps requiring user interaction

To use auto-transitions in your own scenarios, simply add the `auto_next: true` property to any step that should automatically transition to the next step, and optionally specify `auto_next_delay` (in seconds) to control the timing between transitions.

Example:
```json
"welcome": {
  "id": "welcome",
  "type": "message",
  "message": {
    "text": "Welcome to the auto-transition demo!"
  },
  "next_step": "introduction",
  "auto_next": true,
  "auto_next_delay": 2.0  // Wait 2 seconds before showing next step
}
```