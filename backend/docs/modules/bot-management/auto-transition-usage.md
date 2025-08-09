# Using Auto-Transitions in Bot Scenarios

This guide explains how to use the auto-transition functionality in bot scenarios to create more fluid and natural conversation flows.

## What Are Auto-Transitions?

Auto-transitions allow steps in a bot conversation to automatically proceed to the next step without requiring user input. This creates a smoother, more natural conversation flow by allowing a series of messages to be displayed in sequence with configurable delays between them.

Auto-transitions are useful for:
- Onboarding flows where you want to present information step by step
- Tutorial sequences that guide users through a process
- Multi-part messages that should be shown with natural pauses between them
- "Typing" indicators to make the bot feel more human-like

## How to Use Auto-Transitions

To enable auto-transitions in your bot scenarios, add the `auto_next: true` property to any step that should automatically transition to the next step.

You can also customize the delay between transitions by adding the `auto_next_delay` property (in seconds). If not specified, it defaults to 1.5 seconds.

### Example:

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

In this example, the bot will:
1. Show the "Welcome to our bot!" message
2. Wait 2 seconds
3. Automatically show the "I'm here to help you with your questions." message without requiring user input
4. Wait 1.5 seconds (default)
5. Automatically show the final message with buttons
6. Wait for user input (button click)

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
},
"company_info_3": {
  "id": "company_info_3",
  "type": "message",
  "message": {
    "text": "Our mission is to deliver exceptional customer experiences."
  },
  "next_step": "ask_for_input"
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
},
"feature_intro": {
  "id": "feature_intro",
  "type": "message",
  "message": {
    "text": "Let me show you our main features."
  },
  "next_step": "feature_1",
  "auto_next": true
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
},
"thank_name": {
  "id": "thank_name",
  "type": "message",
  "message": {
    "text": "Thanks, {{name}}! Now I need a few more details."
  },
  "next_step": "email_prompt",
  "auto_next": true,
  "auto_next_delay": 1.5
},
"email_prompt": {
  "id": "email_prompt",
  "type": "message",
  "message": {
    "text": "What's your email address?"
  },
  "expected_input": {
    "type": "email",
    "variable": "email"
  },
  "next_step": "thank_email"
}
```

### 4. Conversational Storytelling

For creating a conversational narrative that unfolds gradually:

```json
"story_start": {
  "id": "story_start",
  "type": "message",
  "message": {
    "text": "Let me tell you about our latest project."
  },
  "next_step": "story_part_1",
  "auto_next": true,
  "auto_next_delay": 1.5
},
"story_part_1": {
  "id": "story_part_1",
  "type": "message",
  "message": {
    "text": "We identified a key market opportunity in Q1."
  },
  "next_step": "story_part_2",
  "auto_next": true,
  "auto_next_delay": 2.0
},
"story_part_2": {
  "id": "story_part_2",
  "type": "message",
  "message": {
    "text": "Our team spent 3 months developing the perfect solution."
  },
  "next_step": "story_part_3",
  "auto_next": true,
  "auto_next_delay": 2.0
}
```

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

## Debugging Auto-Transitions

The system includes a specialized utility for analyzing and debugging auto-transitions:

```bash
python -m scripts.bots.utils.view_auto_transitions
```

This tool shows information about auto-transition chains, including:
- Start and end times
- Duration and step count
- Step sequence details
- Any errors that occurred

Additional options:
- `--bot-id BOT_ID`: Filter by specific bot
- `--platform PLATFORM`: Filter by platform (e.g., telegram, whatsapp)
- `--chat-id CHAT_ID`: Filter by chat ID
- `--with-errors`: Show only chains with errors
- `--timing`: Show detailed timing information
- `--help`: Show all available options

## Example Scenario

For a complete example of a scenario using auto-transitions, see:
`/docs/modules/bot-management/example-scenario/auto_transition_example.json`

This example demonstrates various auto-transition use cases:
- Sequential information presentation
- Auto-transitions with media
- Mixing auto-transitions with user input
- Auto-transitions after user input