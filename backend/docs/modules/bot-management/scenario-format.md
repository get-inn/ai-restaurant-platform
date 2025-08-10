# Bot Scenario Format

This document describes the scenario format used for defining bot conversations in the GET INN Restaurant Platform.

## Overview

Bot scenarios are structured JSON documents that define the conversation flow between a bot and a user. They include steps, messages, expected inputs, and conditional logic to create interactive dialog experiences.

## Basic Structure

A bot scenario has the following basic structure:

```json
{
  "version": "1.0",
  "name": "Example Scenario",
  "description": "An example bot scenario",
  "start_step": "welcome",
  "steps": {
    "welcome": {
      "id": "welcome",
      "type": "message",
      "message": {
        "text": "Hello! What's your name?",
        "media": []
      },
      "expected_input": {
        "type": "text",
        "variable": "first_name"
      },
      "next_step": "ask_lastname"
    },
    "ask_lastname": {
      "id": "ask_lastname",
      "type": "message",
      "message": {
        "text": "What's your last name?",
        "media": []
      },
      "expected_input": {
        "type": "text",
        "variable": "last_name"
      },
      "next_step": "finish"
    }
    // More steps...
  },
  "metadata": {
    "created_at": "2023-07-01",
    "updated_at": "2023-07-15",
    "version_history": [
      {
        "version": "1.0",
        "description": "Initial version",
        "date": "2023-07-01"
      }
    ],
    "platforms": ["telegram", "whatsapp"]
  },
  "variables_mapping": {
    "position": {
      "cook": "Повар",
      "manager": "Менеджер"
    }
  }
}
```

## Components

### Metadata

The `metadata` object contains descriptive information about the scenario:

```json
"metadata": {
  "created_at": "2023-07-10",
  "updated_at": "2023-07-15",
  "version_history": [
    {
      "version": "1.0",
      "description": "Initial version",
      "date": "2023-07-01"
    }
  ],
  "platforms": ["telegram", "whatsapp"]
}
```

### Steps

The `steps` object is the core of the scenario, with each key representing a unique step ID. Each step has:

- **id**: Unique identifier for the step (should match the key in the steps object)
- **type**: Type of step (e.g., "message", "conditional_message")
- **message**: The content to send to the user
- **expected_input**: What type of input is expected from the user
- **next_step**: The ID of the next step to execute or a conditional structure

Example step:

```json
"ask_position": {
  "id": "ask_position",
  "type": "message",
  "message": {
    "text": "What's your position in the company?",
    "media": [
      {
        "type": "image",
        "description": "Our team positions",
        "file_id": "positions_image"
      }
    ]
  },
  "buttons": [
    {"text": "Food Guide", "value": "food-guide"},
    {"text": "Cook", "value": "cook"},
    {"text": "Manager", "value": "manager"},
    {"text": "Office Worker 🤓", "value": "office"}
  ],
  "expected_input": {
    "type": "button",
    "variable": "position",
    "validation": {
      "required": true
    }
  },
  "next_step": "ask_project"
}
```

### Message Structure

The `message` object defines what is sent to the user:

```json
"message": {
  "text": "Please upload your passport photo.",
  "media": [
    {
      "type": "image",
      "description": "Example of a passport photo",
      "file_id": "passport_example"
    }
  ]
}
```

### Input Types

The `expected_input` object defines what the bot expects from the user:

#### Text Input

```json
"expected_input": {
  "type": "text",
  "variable": "full_name",
  "validation": {
    "required": true,
    "min_length": 2,
    "max_length": 100,
    "pattern": "^[A-Za-z\\s]{2,50}$",
    "error_message": "Please enter a valid name (2-50 letters only)"
  }
}
```

#### Button Input

```json
"expected_input": {
  "type": "button",
  "variable": "gender"
}
```

#### File Upload

```json
"expected_input": {
  "type": "file",
  "variable": "passport_photo",
  "validation": {
    "required": true,
    "allowed_types": ["image/jpeg", "image/png"],
    "max_size_kb": 5000
  }
}
```

#### Phone Number

```json
"expected_input": {
  "type": "phone",
  "variable": "contact_number"
}
```

#### Email

```json
"expected_input": {
  "type": "email",
  "variable": "email_address"
}
```

#### Date

```json
"expected_input": {
  "type": "date",
  "variable": "birth_date",
  "validation": {
    "required": true,
    "min_date": "1950-01-01",
    "max_date": "2005-12-31"
  }
}
```

#### Location

```json
"expected_input": {
  "type": "location",
  "variable": "current_location"
}
```

### Buttons

Buttons provide predefined options for the user to select:

```json
"buttons": [
  {"text": "Yes ✅", "value": "yes"},
  {"text": "No ❌", "value": "no"},
  {"text": "Not sure 🤔", "value": "maybe"}
]
```

### Step Types

The `type` field in a step indicates how the step should be processed:

#### Message Step

Standard message step with text and optional media:

```json
"welcome": {
  "id": "welcome",
  "type": "message",
  "message": {
    "text": "Hello! Welcome to our service."
  },
  "next_step": "next_step_id"
}
```

#### Conditional Message Step

Sends different messages based on conditions:

```json
"greeting": {
  "id": "greeting",
  "type": "conditional_message",
  "conditions": [
    {
      "if": "time_of_day == 'morning'",
      "message": {
        "text": "Good morning!"
      }
    },
    {
      "if": "time_of_day == 'evening'",
      "message": {
        "text": "Good evening!"
      }
    },
    {
      "message": {
        "text": "Hello!"
      }
    }
  ],
  "next_step": "next_step_id"
}
```

### Next Step Logic

There are several ways to define the next step:

#### Direct Next Step

```json
"next_step": "ask_experience"
```

#### Auto Next

Automatically proceed to the next step without waiting for user input:

```json
"next_step": "next_step_id",
"auto_next": true
```

#### Conditional Next Step

```json
"next_step": {
  "type": "conditional",
  "conditions": [
    {
      "if": "position == 'cook'",
      "then": "cook_experience"
    },
    {
      "if": "position == 'manager'",
      "then": "manager_experience"
    },
    {
      "then": "general_experience"  // Default case
    }
  ]
}
```

### Variables and Templating

Variables can be referenced in messages using double curly braces:

```json
"message": {
  "text": "Thank you, {{first_name}}! How many years of experience do you have?"
}
```

### Variables Mapping

The `variables_mapping` object defines how values stored in variables map to display text:

```json
"variables_mapping": {
  "position": {
    "food-guide": "Фуд-гид",
    "cook": "Повар",
    "manager": "Менеджер",
    "office": "Я из офиса 🤓"
  }
}
```

## Media Support

Multiple types of media can be included in messages:

```json
"media": [
  {
    "type": "image",
    "description": "Welcome to our team!",
    "file_id": "welcome_image"
  },
  {
    "type": "video",
    "description": "Introduction to our company",
    "file_id": "intro_video"
  },
  {
    "type": "document",
    "description": "Employee Handbook",
    "file_id": "employee_handbook"
  }
]
```

## Advanced Features

### Menu System

You can create a menu system with different options:

```json
"menu": {
  "id": "menu",
  "type": "message",
  "message": {
    "text": "📂 What would you like to view?"
  },
  "buttons": [
    {"text": "Ideology", "value": "ideology"},
    {"text": "Responsibilities", "value": "duties"},
    {"text": "Contacts", "value": "contacts"}
  ],
  "expected_input": {
    "type": "button",
    "variable": "menu_choice"
  },
  "next_step": {
    "type": "conditional",
    "conditions": [
      {
        "if": "menu_choice == 'ideology'",
        "then": "menu_ideology"
      },
      {
        "if": "menu_choice == 'duties'",
        "then": "menu_duties"
      },
      {
        "if": "menu_choice == 'contacts'",
        "then": "menu_contacts"
      }
    ]
  }
}
```

## Platform Support

Different messaging platforms have varying capabilities. The bot management system automatically adapts the scenario to each platform's features:

| Feature | Telegram | WhatsApp | Viber |
|---------|----------|----------|-------|
| Text | ✓ | ✓ | ✓ |
| Images | ✓ | ✓ | ✓ |
| Videos | ✓ | ✓ | ✓ |
| Documents | ✓ | ✓ | ✓ |
| Buttons | ✓ | ✓ | ✓ |
| Quick Replies | ✓ | ✓ | ✓ |
| Location | ✓ | ✓ | ✓ |
| File Upload | ✓ | ✓ | Limited |
| Date Picker | ✓ | ✗ | ✗ |

## Best Practices

1. **Use Clear Step IDs**:
   - Make step IDs descriptive and readable
   - Use consistent naming conventions
   - Ensure step IDs match the keys in the steps object

2. **Plan for Error Handling**:
   - Include validation for expected inputs
   - Provide helpful error messages
   - Consider adding "retry" steps for critical inputs

3. **Optimize Media Usage**:
   - Keep images under 1MB
   - Use a consistent naming convention for file_ids
   - Make sure file_ids referenced in scenarios exist in the media store

4. **Test Across Platforms**:
   - Ensure scenarios work on all supported platforms
   - Test with actual users from each platform

5. **Keep Conversations Flowing**:
   - Avoid dead ends
   - Include "back" options for complex flows
   - Provide help commands or instructions

6. **Variables Naming**:
   - Use clear, descriptive variable names
   - Follow snake_case naming convention
   - Document important variables in variables_mapping

## Complete Example

Here's a simplified example of a bot scenario:

```json
{
  "version": "1.0",
  "name": "Employee Onboarding",
  "description": "Basic onboarding for new employees",
  "start_step": "welcome",
  "steps": {
    "welcome": {
      "id": "welcome",
      "type": "message",
      "message": {
        "text": "Welcome! What's your name?",
        "media": [
          {
            "type": "image",
            "description": "Welcome aboard!",
            "file_id": "welcome_image"
          }
        ]
      },
      "expected_input": {
        "type": "text",
        "variable": "first_name",
        "validation": {
          "required": true,
          "min_length": 2
        }
      },
      "next_step": "ask_position"
    },
    "ask_position": {
      "id": "ask_position",
      "type": "message",
      "message": {
        "text": "Nice to meet you, {{first_name}}! What position are you applying for?"
      },
      "buttons": [
        {"text": "Cook", "value": "cook"},
        {"text": "Manager", "value": "manager"}
      ],
      "expected_input": {
        "type": "button",
        "variable": "position"
      },
      "next_step": {
        "type": "conditional",
        "conditions": [
          {
            "if": "position == 'cook'",
            "then": "cook_questions"
          },
          {
            "if": "position == 'manager'",
            "then": "manager_questions"
          }
        ]
      }
    }
  },
  "metadata": {
    "created_at": "2023-07-01",
    "updated_at": "2023-07-15",
    "platforms": ["telegram", "whatsapp"]
  },
  "variables_mapping": {
    "position": {
      "cook": "Cook",
      "manager": "Manager"
    }
  }
}
```

## Debugging and Testing

Use the conversation logger to track scenario execution:

```bash
python -m scripts.bots.utils.view_bot_logs --bot-id BOT_ID
```

## Further Resources

- [Bot Management Overview](overview.md) - Overview of the bot management system
- [Webhook Management](webhook-management.md) - Telegram webhook integration
- [Conversation Logging](conversation-logging.md) - Bot conversation logging
- [Example Scenario](example-scenario/onboarding_scenario.json) - Complete onboarding scenario example