# Bot Scenario Format

This document describes the scenario format used for defining bot conversations in the GET INN Restaurant Platform.

## Overview

Bot scenarios are structured JSON documents that define the conversation flow between a bot and a user. They include steps, messages, expected inputs, and conditional logic to create interactive dialog experiences.

## Basic Structure

A bot scenario has the following basic structure:

```json
{
  "version": "1.0",
  "metadata": {
    "name": "Example Scenario",
    "description": "An example bot scenario",
    "author": "GET INN Developer"
  },
  "steps": [
    {
      "id": "welcome",
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
    // More steps...
  ],
  "conditions": [
    {
      "if": "citizenship == 'РФ'",
      "then": "show_rf_docs",
      "else": "show_sng_docs"
    }
    // More conditions...
  ]
}
```

## Components

### Metadata

The `metadata` object contains descriptive information about the scenario:

```json
"metadata": {
  "name": "Employee Onboarding",
  "description": "Guides new employees through the onboarding process",
  "author": "HR Department",
  "created_at": "2023-07-10",
  "updated_at": "2023-07-15",
  "version": "1.2"
}
```

### Steps

The `steps` array is the core of the scenario, defining each interaction in the conversation. Each step has:

- **id**: Unique identifier for the step
- **message**: The content to send to the user
- **expected_input**: What type of input is expected from the user
- **next_step**: The ID of the next step to execute

Example step:

```json
{
  "id": "ask_position",
  "message": {
    "text": "What's your position in the company?",
    "media": [
      {
        "type": "image",
        "url": "https://example.com/positions.jpg",
        "caption": "Our team positions"
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
      "url": "https://example.com/sample_passport.jpg",
      "caption": "Example of a passport photo"
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
    "max_length": 100
  }
}
```

#### Button Input

```json
"expected_input": {
  "type": "button",
  "variable": "gender",
  "validation": {
    "required": true
  }
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
  "variable": "contact_number",
  "validation": {
    "required": true
  }
}
```

#### Email

```json
"expected_input": {
  "type": "email",
  "variable": "email_address",
  "validation": {
    "required": true
  }
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
  "variable": "current_location",
  "validation": {
    "required": true
  }
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

### Conditions

The `conditions` array defines branching logic in the conversation:

```json
"conditions": [
  {
    "id": "check_citizenship",
    "if": "citizenship == 'РФ'",
    "then": "show_rf_docs",
    "else": "show_sng_docs"
  },
  {
    "id": "check_experience",
    "if": "years_experience > 3",
    "then": "experienced_path",
    "else_if": "years_experience > 0",
    "then_else_if": "some_experience_path",
    "else": "no_experience_path"
  }
]
```

## Advanced Features

### Dynamic Messages

Messages can include variable substitution:

```json
"message": {
  "text": "Thank you, ${first_name}! How many years of experience do you have?"
}
```

### Step Transitions

There are several ways to define the next step:

#### Direct Next Step

```json
"next_step": "ask_experience"
```

#### Conditional Next Step

```json
"next_step": {
  "condition": "position == 'cook'",
  "if_true": "cook_experience",
  "if_false": "general_experience"
}
```

#### Multiple Conditions

```json
"next_step": [
  {
    "condition": "position == 'cook'",
    "step": "cook_experience"
  },
  {
    "condition": "position == 'manager'",
    "step": "manager_experience"
  },
  {
    "step": "general_experience"  // Default case
  }
]
```

### Input Validation

Validations can be applied to ensure the user provides acceptable input:

```json
"validation": {
  "required": true,
  "pattern": "^[A-Za-z\\s]{2,50}$",
  "error_message": "Please enter a valid name (2-50 letters only)"
}
```

### Media Support

Multiple types of media can be included in messages:

```json
"media": [
  {
    "type": "image",
    "url": "https://example.com/welcome.jpg",
    "caption": "Welcome to our team!"
  },
  {
    "type": "video",
    "url": "https://example.com/intro.mp4",
    "thumbnail": "https://example.com/intro_thumb.jpg",
    "caption": "Introduction to our company"
  },
  {
    "type": "document",
    "url": "https://example.com/handbook.pdf",
    "caption": "Employee Handbook"
  }
]
```

### Quick Replies

Quick replies provide temporary button options that disappear after selection:

```json
"quick_replies": [
  {"text": "Today", "value": "today"},
  {"text": "Tomorrow", "value": "tomorrow"},
  {"text": "Next week", "value": "next_week"}
]
```

## Integration with Backend

### API Calls

Scenarios can include API calls to fetch or submit data:

```json
"api_call": {
  "endpoint": "/api/v1/restaurants",
  "method": "GET",
  "store_result": "available_restaurants",
  "next_step": "show_restaurants"
}
```

### Data Processing

Process collected data or API results:

```json
"data_processing": {
  "transform": "available_restaurants.map(r => ({text: r.name, value: r.id}))",
  "store_result": "restaurant_buttons",
  "next_step": "ask_restaurant"
}
```

## Example Scenario

Here's a complete example of a simple onboarding scenario:

```json
{
  "version": "1.0",
  "metadata": {
    "name": "Employee Onboarding",
    "description": "Basic onboarding for new employees",
    "author": "HR Team",
    "created_at": "2023-07-01"
  },
  "steps": [
    {
      "id": "welcome",
      "message": {
        "text": "Welcome to GET INN! I'm your onboarding assistant. What's your name?",
        "media": [
          {
            "type": "image",
            "url": "https://example.com/welcome.jpg",
            "caption": "Welcome aboard!"
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
    {
      "id": "ask_position",
      "message": {
        "text": "Nice to meet you, ${first_name}! What position are you applying for?"
      },
      "buttons": [
        {"text": "Cook", "value": "cook"},
        {"text": "Server", "value": "server"},
        {"text": "Manager", "value": "manager"},
        {"text": "Other", "value": "other"}
      ],
      "expected_input": {
        "type": "button",
        "variable": "position"
      },
      "next_step": {
        "condition": "position == 'other'",
        "if_true": "ask_other_position",
        "if_false": "ask_experience"
      }
    },
    {
      "id": "ask_other_position",
      "message": {
        "text": "Please specify what position you are applying for:"
      },
      "expected_input": {
        "type": "text",
        "variable": "other_position"
      },
      "next_step": "ask_experience"
    },
    {
      "id": "ask_experience",
      "message": {
        "text": "How many years of experience do you have in this role?"
      },
      "expected_input": {
        "type": "number",
        "variable": "years_experience",
        "validation": {
          "required": true,
          "min": 0,
          "max": 50
        }
      },
      "next_step": "ask_documents"
    },
    {
      "id": "ask_documents",
      "message": {
        "text": "Please upload your resume/CV."
      },
      "expected_input": {
        "type": "file",
        "variable": "resume",
        "validation": {
          "required": true,
          "allowed_types": ["application/pdf", "application/msword"]
        }
      },
      "next_step": "finish"
    },
    {
      "id": "finish",
      "message": {
        "text": "Thank you for completing the initial onboarding, ${first_name}! Our HR team will contact you soon with next steps."
      },
      "next_step": null
    }
  ],
  "conditions": [
    {
      "id": "check_experience",
      "if": "years_experience > 3",
      "then": "ask_documents",
      "else_if": "position == 'manager'",
      "then_else_if": "ask_management_experience",
      "else": "ask_documents"
    }
  ]
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

2. **Plan for Error Handling**:
   - Include validation for expected inputs
   - Provide helpful error messages
   - Consider adding "retry" steps for critical inputs

3. **Optimize Media Usage**:
   - Keep images under 1MB
   - Host media on a reliable CDN
   - Include thumbnails for videos

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
   - Document important variables

## Localization

Scenarios support multiple languages:

```json
"message": {
  "text": {
    "en": "What is your name?",
    "ru": "Как вас зовут?",
    "es": "¿Cómo te llamas?"
  }
}
```

## Security Considerations

1. **Sensitive Data**: Do not include sensitive information in the scenario definition
2. **Validation**: Always validate user input to prevent injection attacks
3. **API Integration**: Use secure endpoints with proper authentication
4. **File Uploads**: Validate file types and sizes before processing

## Debugging and Testing

Use the conversation logger to track scenario execution:

```bash
python -m scripts.bots.utils.view_bot_logs --bot-id BOT_ID
```

## Further Resources

- [Bot Management Overview](overview.md) - Overview of the bot management system
- [Webhook Management](webhook-management.md) - Telegram webhook integration
- [Conversation Logging](conversation-logging.md) - Bot conversation logging