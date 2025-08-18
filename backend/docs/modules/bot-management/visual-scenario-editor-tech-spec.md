# GET INN Visual Chatbot Scenario Editor - Technical Specification

## 1. Project Overview

### 1.1 Product Vision
GET INN Visual Chatbot Scenario Editor is a modern, user-friendly SaaS platform that enables restaurant operators to create, manage, and deploy sophisticated chatbot scenarios without technical expertise. The editor bridges the gap between complex intent-based bot architectures and intuitive visual design.

### 1.2 Core Value Proposition
- **Visual-First Design**: Drag-and-drop interface for creating complex conversation flows
- **Technical Flexibility**: Full JSON access for advanced users while maintaining visual synchronization
- **Multi-Bot Management**: Centralized platform for managing multiple bot types (Onboarding, Sales, Support)
- **Intent-Based Architecture**: Native support for modern bot frameworks (Dialogflow, Rasa, Microsoft Bot Framework)
- **Version Control**: Complete scenario versioning with rollback capabilities

### 1.3 Target Users
- **Primary**: Restaurant managers and operations teams
- **Secondary**: Technical integrators and bot developers
- **Tertiary**: Franchise operators managing multiple locations

## 2. Functional Requirements

### 2.1 Scenario Management

#### 2.1.1 Multi-Bot Support
- **Bot Types**: Support for predefined bot categories:
  - Onboarding Bot (employee training)
  - Sales Bot (customer acquisition)
  - Support Bot (customer service)
  - Custom Bot (user-defined)
- **Bot Templates**: Pre-built scenario templates for each bot type
- **Bot Cloning**: Ability to duplicate and modify existing bots
- **Cross-Bot Dependencies**: Support for scenarios that reference other bots

#### 2.1.2 Scenario Organization
- **Workspace Management**: Multi-tenant architecture supporting multiple restaurant chains
- **Project Folders**: Hierarchical organization of bots by location, brand, or purpose
- **Tagging System**: Custom tags for scenario categorization and filtering
- **Search & Filter**: Full-text search across scenarios with advanced filtering options

### 2.2 Version Control System

#### 2.2.1 Version Management
- **Automatic Versioning**: Auto-save with timestamped versions every 30 seconds
- **Manual Snapshots**: User-initiated version checkpoints with custom descriptions
- **Version Comparison**: Side-by-side diff view showing changes between versions
- **Rollback Capability**: One-click rollback to any previous version

#### 2.2.2 Collaboration Features
- **Change History**: Detailed audit log of all modifications with user attribution
- **Comments System**: Inline comments on scenario steps for team collaboration
- **Review Workflow**: Approval process for scenario changes before deployment
- **Conflict Resolution**: Merge conflict handling for simultaneous edits

### 2.3 Import/Export Functionality

#### 2.3.1 JSON Import
- **File Upload**: Drag-and-drop JSON file upload with validation
- **Schema Validation**: Real-time validation against GET INN bot schema
- **Error Reporting**: Detailed error messages with line numbers for invalid JSON
- **Preview Mode**: Preview imported scenario before committing changes
- **Merge Options**: Ability to merge imported scenarios with existing ones

#### 2.3.2 JSON Export
- **Full Export**: Complete scenario export including all intents and dependencies
- **Selective Export**: Export specific intents or scenario branches
- **Format Options**: Support for different JSON formatting (minified, pretty-printed)
- **Validation Check**: Pre-export validation to ensure schema compliance
- **Download Management**: Secure download links with expiration

### 2.4 Visual-JSON Synchronization

#### 2.4.1 Real-Time Synchronization
- **Bidirectional Sync**: Changes in visual editor instantly reflect in JSON and vice versa
- **Live JSON View**: Split-screen view showing visual editor and JSON simultaneously
- **Syntax Highlighting**: Advanced JSON editor with syntax highlighting and error detection
- **Auto-Formatting**: Automatic JSON formatting and indentation

#### 2.4.2 Advanced JSON Editing
- **Direct JSON Editing**: Full JSON editor with autocomplete and validation
- **Schema Assistance**: Intelligent autocomplete based on GET INN bot schema
- **Error Prevention**: Real-time validation preventing invalid JSON structures
- **Change Propagation**: JSON changes immediately update visual flow representation

### 2.5 Intent-Based Architecture Support

#### 2.5.1 Intent Management
- **Intent Library**: Centralized library of reusable intents across scenarios
- **Intent Dependencies**: Visual representation of intent relationships and dependencies
- **Intent Templates**: Pre-built intent templates for common use cases
- **Cross-Intent Navigation**: Visual flow lines showing intent transitions

#### 2.5.2 Flow Visualization
- **Hierarchical View**: Collapsible intent groups for complex scenario organization
- **Flow Validation**: Real-time validation of intent flows and transitions
- **Circular Dependency Detection**: Automatic detection and warning of infinite loops
- **Entry/Exit Points**: Clear visualization of intent entry and exit points

### 2.6 Interactive Elements Support

#### 2.6.1 Button Configuration
- **Button Designer**: Visual button builder with text, styling, and action configuration
- **Button Types**: Support for various button types (quick reply, postback, URL, phone)
- **Dynamic Buttons**: Conditional button display based on user context
- **Button Validation**: Validation of button text length and action validity

#### 2.6.2 Media Management
- **Media Library**: Centralized media asset management with CDN integration
- **Media Types**: Support for images, videos, audio, documents, and GIFs
- **Media Preview**: In-editor preview of media assets
- **Media Optimization**: Automatic media compression and format optimization
- **Alt Text Management**: Accessibility support with alt text for images

#### 2.6.3 Conditional Logic
- **Visual Condition Builder**: Drag-and-drop interface for creating complex conditions
- **Condition Types**: Support for user data, time-based, location-based conditions
- **Nested Conditions**: Support for AND/OR logic with nested condition groups
- **Condition Testing**: Built-in testing interface for validating condition logic

### 2.7 Scenario Testing and Simulation

#### 2.7.1 Interactive Test Runner
- **Live Chat Simulation**: Real-time chat interface for testing complete conversation flows
- **Multi-Platform Testing**: Test scenarios across different platforms (Telegram, Web Chat, WhatsApp)
- **User Persona Simulation**: Test with different user profiles and data contexts
- **Step-by-Step Debugging**: Ability to pause, step through, and inspect each conversation step
- **Variable Inspection**: Real-time viewing of user variables and context data during testing

#### 2.7.2 Flow Validation and Analysis
- **Path Coverage Analysis**: Visual representation of all possible conversation paths
- **Dead End Detection**: Automatic identification of conversation paths with no exit
- **Circular Flow Detection**: Detection and visualization of infinite conversation loops
- **Unreachable Step Detection**: Identification of steps that can never be reached
- **Intent Dependency Validation**: Verification that all intent dependencies are satisfied

#### 2.7.3 Automated Testing Suite
- **Test Case Management**: Create, organize, and manage automated test scenarios
- **Regression Testing**: Automated testing against previous versions to detect breaking changes
- **Performance Testing**: Load testing for high-volume conversation scenarios
- **Cross-Platform Consistency**: Ensure identical behavior across all deployment platforms
- **CI/CD Integration**: Automated testing as part of deployment pipeline

#### 2.7.4 Analytics and Insights
- **Conversation Analytics**: Detailed metrics on conversation flow performance
- **User Journey Mapping**: Visual representation of actual user paths through scenarios
- **Drop-off Analysis**: Identification of steps where users commonly abandon conversations
- **A/B Testing Framework**: Built-in support for testing different conversation variations
- **Performance Metrics**: Response times, completion rates, and user satisfaction tracking

## 3. User Interface Design Requirements

### 3.1 Design Philosophy
- **Notion-Inspired**: Clean, modern interface following Notion's design principles
- **Minimalist Approach**: Clutter-free interface focusing on essential functionality
- **Progressive Disclosure**: Advanced features hidden until needed
- **Consistent Patterns**: Unified design language across all interface elements

### 3.2 Layout Structure

#### 3.2.1 Main Application Layout
- **Left Sidebar**: Bot library, project navigation, and quick actions
- **Center Canvas**: Main visual editor workspace with infinite scroll
- **Right Panel**: Properties panel for selected elements and JSON view
- **Top Navigation**: Global actions, user profile, and workspace switcher

#### 3.2.2 Visual Editor Canvas
- **Grid System**: Subtle grid for element alignment and positioning
- **Zoom Controls**: Zoom in/out functionality for complex scenarios
- **Minimap**: Overview minimap for large scenario navigation
- **Rulers and Guides**: Optional rulers and alignment guides

### 3.3 Visual Elements

#### 3.3.1 Node Design
- **Step Nodes**: Rounded rectangles representing individual conversation steps
- **Intent Nodes**: Distinct styling for intent containers with collapsible content
- **Connector Lines**: Smooth curved lines showing conversation flow
- **Status Indicators**: Visual indicators for node validation status

#### 3.3.2 Color System
- **Primary Palette**: Brand-consistent colors for actions and navigation
- **Semantic Colors**: Green (success), Red (error), Yellow (warning), Blue (info)
- **Node Categories**: Color coding for different node types (message, input, condition)
- **Dark Mode Support**: Complete dark mode theme with proper contrast ratios

### 3.4 Testing Interface Design

#### 3.4.1 Test Runner Interface
- **Split-Screen Layout**: Visual editor on left, chat simulator on right
- **Chat Simulator**: Native chat interface mimicking target platform (Telegram, Web Chat)
- **Debug Panel**: Collapsible panel showing variables, execution state, and call stack
- **Test Controls**: Play, pause, step-through, restart buttons with keyboard shortcuts
- **Speed Controls**: Adjustable playback speed for automated test execution

#### 3.4.2 Flow Analysis Visualization
- **Path Highlighting**: Visual highlighting of conversation paths on canvas
- **Coverage Heatmap**: Color-coded nodes showing test coverage frequency
- **Issue Indicators**: Visual markers for dead ends, loops, and unreachable steps
- **Performance Overlay**: Response time indicators on each step node
- **Zoom and Filter**: Ability to zoom into specific flows and filter by test results

#### 3.4.3 Test Management Interface
- **Test Suite Panel**: Hierarchical view of test cases and results
- **Results Dashboard**: Summary view of test execution results with charts
- **Comparison View**: Side-by-side comparison of different test runs
- **A/B Test Monitor**: Real-time monitoring of A/B test performance
- **Performance Metrics**: Charts showing response times, success rates, and throughput

### 3.5 Responsive Design
- **Desktop First**: Optimized for desktop editing with large canvas area
- **Tablet Support**: Responsive layout for tablet-based editing
- **Mobile Viewing**: Read-only mobile view for scenario review
- **Cross-Browser**: Support for Chrome, Firefox, Safari, and Edge

## 4. Technical Architecture

### 4.1 Frontend Architecture

#### 4.1.1 Technology Stack
- **Framework**: React 18+ with TypeScript for type safety
- **State Management**: Redux Toolkit for complex state management
- **Canvas Rendering**: React Flow or similar for visual node-based editing
- **JSON Editing**: Monaco Editor (VS Code editor) for JSON manipulation
- **UI Components**: Custom component library built on Radix UI primitives

#### 4.1.2 Performance Considerations
- **Virtual Scrolling**: Efficient rendering of large scenario canvases
- **Lazy Loading**: Progressive loading of scenario components
- **Memoization**: React.memo and useMemo for preventing unnecessary re-renders
- **Web Workers**: Background processing for complex validation and parsing

### 4.2 Backend Architecture

#### 4.2.1 API Design
- **REST API**: RESTful endpoints for scenario CRUD operations
- **WebSocket**: Real-time collaboration and live updates
- **GraphQL**: Flexible data fetching for complex scenario relationships
- **File Upload**: Secure file upload with virus scanning and validation

#### 4.2.2 Data Storage
- **Primary Database**: PostgreSQL for scenario data and user management
- **File Storage**: AWS S3 or similar for media assets
- **Caching Layer**: Redis for session management and performance
- **Search Engine**: Elasticsearch for full-text scenario search

### 4.3 Security & Compliance

#### 4.3.1 Authentication & Authorization
- **SSO Integration**: Support for Google, Microsoft, and SAML SSO
- **Role-Based Access**: Granular permissions for viewing, editing, and publishing
- **API Security**: JWT tokens with refresh mechanism
- **Session Management**: Secure session handling with automatic timeout

#### 4.3.2 Data Protection
- **Encryption**: AES-256 encryption for sensitive data at rest
- **Transport Security**: TLS 1.3 for all data in transit
- **Backup Strategy**: Automated daily backups with point-in-time recovery
- **GDPR Compliance**: Data portability and deletion capabilities

## 5. Integration Requirements

### 5.1 Bot Platform Integration

#### 5.1.1 Deployment Targets
- **GET INN Platform**: Native integration with existing bot management system
- **Telegram**: Direct deployment to Telegram Bot API
- **WhatsApp Business**: Integration with WhatsApp Business API
- **Web Chat**: Embeddable web chat widget generation

#### 5.1.2 Webhook Management
- **Webhook Configuration**: Visual webhook setup and testing
- **Webhook Testing**: Built-in webhook testing tools
- **Event Monitoring**: Real-time webhook event monitoring and logging
- **Error Handling**: Automatic retry logic and error notification

### 5.2 External Integrations

#### 5.2.1 Restaurant Systems
- **POS Integration**: Connection to major POS systems for order data
- **CRM Integration**: Customer data synchronization
- **Analytics Platforms**: Google Analytics, Mixpanel integration
- **Notification Systems**: Email and SMS notification services

#### 5.2.2 Development Tools
- **Version Control**: Git-like versioning for scenarios
- **CI/CD Pipeline**: Automated testing and deployment workflows
- **API Documentation**: Auto-generated API documentation
- **SDK Support**: SDKs for custom integrations

## 6. Performance & Scalability

### 6.1 Performance Targets
- **Page Load**: < 2 seconds for initial application load
- **Scenario Load**: < 1 second for scenario with 100+ nodes
- **Real-time Sync**: < 100ms latency for collaborative editing
- **Export/Import**: < 5 seconds for typical scenario files

### 6.2 Scalability Requirements
- **Concurrent Users**: Support for 1000+ concurrent editors
- **Scenario Size**: Handle scenarios with 1000+ nodes efficiently
- **File Upload**: Support files up to 50MB
- **Storage**: Scalable storage for unlimited scenarios and media

## 7. Testing & Quality Assurance

### 7.1 Testing Strategy
- **Unit Testing**: 90%+ code coverage for critical components
- **Integration Testing**: End-to-end testing of complete workflows
- **Performance Testing**: Load testing for scalability validation
- **Security Testing**: Regular security audits and penetration testing

### 7.2 Quality Metrics
- **Uptime**: 99.9% availability SLA
- **Bug Rate**: < 1 critical bug per release
- **User Satisfaction**: > 4.5/5 user rating
- **Performance**: < 2s average page load time

## 8. Deployment & Operations

### 8.1 Infrastructure
- **Cloud Platform**: AWS or Azure for scalability and reliability
- **Containerization**: Docker containers with Kubernetes orchestration
- **CDN**: Global CDN for media assets and static content
- **Monitoring**: Comprehensive monitoring with alerting

### 8.2 Release Strategy
- **Staged Rollout**: Gradual feature rollout with feature flags
- **A/B Testing**: Built-in A/B testing for UI/UX improvements
- **Rollback Capability**: Instant rollback for problematic releases
- **Documentation**: Comprehensive user documentation and tutorials

## 9. Success Metrics

### 9.1 User Adoption
- **Active Users**: Monthly active users creating/editing scenarios
- **Scenario Creation**: Number of scenarios created per month
- **Feature Utilization**: Usage metrics for advanced features
- **User Retention**: 30-day, 90-day user retention rates

### 9.2 Business Impact
- **Development Time**: Reduction in bot development time vs manual coding
- **Error Reduction**: Decrease in deployment errors due to visual validation
- **Team Productivity**: Increase in non-technical team members creating bots
- **Customer Satisfaction**: Improvement in deployed bot performance metrics

## 10. Future Roadmap

### 10.1 Phase 1 Features (MVP)
- Basic visual editor with JSON sync
- Single bot scenario management
- Import/export functionality
- Intent-based architecture support

### 10.2 Phase 2 Enhancements
- Multi-bot management
- Version control system
- Collaboration features
- Advanced conditional logic

### 10.3 Phase 3 Advanced Features
- AI-assisted scenario generation
- Advanced analytics and insights
- Custom integrations marketplace
- Multi-language support

## 11. JSON Schema and Examples

### 11.1 Core Data Structures

#### 11.1.1 Scenario Metadata
```json
{
  "scenario_id": "onboarding_bot_v2",
  "scenario_name": "Employee Onboarding Bot",
  "scenario_type": "onboarding",
  "version": "2.1.0",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T14:45:00Z",
  "created_by": "user_123",
  "status": "published",
  "workspace_id": "restaurant_chain_abc",
  "tags": ["onboarding", "employees", "training"],
  "description": "Comprehensive onboarding flow for new restaurant employees",
  "deployment_targets": ["telegram", "web_chat"],
  "dependencies": ["main_menu_intent", "support_intent"]
}
```

#### 11.1.2 Intent-Based Architecture
```json
{
  "intent_id": "user_registration",
  "intent_name": "User Registration Flow",
  "intent_type": "core",
  "version": "1.0",
  "dependencies": ["main_menu"],
  "entry_points": ["start_registration", "from_menu"],
  "exit_points": ["registration_complete", "return_to_menu"],
  "context_requirements": {
    "user_profile": "optional",
    "session_data": "required"
  },
  "start_step": "welcome_message",
  "steps": {
    "welcome_message": {
      "id": "welcome_message",
      "type": "message",
      "position": {"x": 100, "y": 200},
      "message": {
        "text": "Welcome to ChiHo! Let's get you registered.",
        "media": [
          {
            "type": "image",
            "description": "Welcome banner",
            "file_id": "welcome_banner_001",
            "alt_text": "ChiHo restaurant welcome banner"
          }
        ]
      },
      "buttons": [
        {"text": "Start Registration", "value": "start_reg", "type": "postback"},
        {"text": "Skip for now", "value": "skip", "type": "postback"}
      ],
      "expected_input": {
        "type": "button",
        "variable": "user_choice",
        "validation": {
          "required": true,
          "allowed_values": ["start_reg", "skip"]
        }
      },
      "next_step": {
        "type": "conditional",
        "conditions": [
          {
            "if": "user_choice == 'start_reg'",
            "then": "name_input"
          },
          {
            "if": "user_choice == 'skip'",
            "then": "intent://navigation/main_menu/menu"
          }
        ]
      }
    }
  }
}
```

### 11.2 Interactive Elements

#### 11.2.1 Button Configurations
```json
{
  "buttons": [
    {
      "text": "🍜 Food Guide",
      "value": "food-guide",
      "type": "postback",
      "style": {
        "color": "primary",
        "size": "medium"
      },
      "conditions": {
        "show_if": "user.role != 'manager'"
      }
    },
    {
      "text": "📞 Call Restaurant",
      "value": "tel:+1234567890",
      "type": "phone",
      "style": {
        "color": "secondary",
        "size": "small"
      }
    },
    {
      "text": "🌐 Visit Website",
      "value": "https://restaurant.com",
      "type": "url",
      "style": {
        "color": "accent",
        "size": "large"
      },
      "webview_height": "tall"
    }
  ]
}
```

#### 11.2.2 Media Configurations
```json
{
  "media": [
    {
      "type": "image",
      "description": "Menu showcase",
      "file_id": "menu_showcase_v2",
      "alt_text": "Restaurant menu items display",
      "properties": {
        "width": 800,
        "height": 600,
        "format": "webp"
      }
    },
    {
      "type": "video",
      "description": "Training video",
      "file_id": "training_basics_001",
      "alt_text": "Basic training procedures video",
      "properties": {
        "duration": 120,
        "autoplay": false,
        "controls": true
      }
    },
    {
      "type": "audio",
      "description": "Welcome message",
      "file_id": "welcome_audio_en",
      "properties": {
        "duration": 30,
        "format": "mp3"
      }
    }
  ]
}
```

### 11.3 Conditional Logic Examples

#### 11.3.1 Simple Conditions
```json
{
  "next_step": {
    "type": "conditional",
    "conditions": [
      {
        "if": "user.citizenship == 'russian'",
        "then": "russian_documents_step"
      },
      {
        "if": "user.citizenship == 'foreign'",
        "then": "foreign_documents_step"
      },
      {
        "default": "general_documents_step"
      }
    ]
  }
}
```

#### 11.3.2 Complex Nested Conditions
```json
{
  "next_step": {
    "type": "conditional",
    "conditions": [
      {
        "if": "user.position == 'food-guide' AND user.experience == 'beginner'",
        "then": "beginner_foodguide_training"
      },
      {
        "if": "user.position == 'food-guide' AND user.experience == 'experienced'",
        "then": "advanced_foodguide_training"
      },
      {
        "if": "user.position == 'cook' AND (user.project == 'pyatnitskaya' OR user.project == 'pushkinskaya')",
        "then": "premium_location_cook_training"
      },
      {
        "if": "time.hour >= 9 AND time.hour <= 17",
        "then": "daytime_support_available"
      },
      {
        "default": "standard_flow"
      }
    ]
  }
}
```

#### 11.3.3 Dynamic Button Display
```json
{
  "buttons": [
    {
      "text": "View KPI Details",
      "value": "kpi_details",
      "type": "postback",
      "conditions": {
        "show_if": "user.role IN ['food-guide', 'cook'] AND user.onboarding_progress > 50"
      }
    },
    {
      "text": "Manager Dashboard",
      "value": "manager_dashboard",
      "type": "postback",
      "conditions": {
        "show_if": "user.role == 'manager'"
      }
    },
    {
      "text": "Emergency Contact",
      "value": "emergency",
      "type": "postback",
      "conditions": {
        "show_if": "time.hour < 8 OR time.hour > 22"
      }
    }
  ]
}
```

### 11.4 Input Validation

#### 11.4.1 Text Input Validation
```json
{
  "expected_input": {
    "type": "text",
    "variable": "user_name",
    "validation": {
      "required": true,
      "min_length": 2,
      "max_length": 50,
      "pattern": "^[А-Яа-яЁё\\s]+$",
      "error_message": "Please enter your name in Russian (2-50 characters)"
    },
    "preprocessing": {
      "trim": true,
      "capitalize_words": true
    }
  }
}
```

#### 11.4.2 Numeric Input Validation
```json
{
  "expected_input": {
    "type": "number",
    "variable": "user_age",
    "validation": {
      "required": true,
      "min_value": 16,
      "max_value": 80,
      "integer_only": true,
      "error_message": "Age must be between 16 and 80 years"
    }
  }
}
```

### 11.5 Version Control Structure

#### 11.5.1 Version Metadata
```json
{
  "version_id": "v2.1.0_20240120_144500",
  "scenario_id": "onboarding_bot_v2",
  "version_number": "2.1.0",
  "created_at": "2024-01-20T14:45:00Z",
  "created_by": "user_123",
  "description": "Added conditional document requirements based on citizenship",
  "changes": [
    {
      "type": "intent_modified",
      "intent_id": "user_registration",
      "change_description": "Added citizenship-based document flow"
    },
    {
      "type": "step_added",
      "intent_id": "user_registration",
      "step_id": "citizenship_check",
      "change_description": "New step for citizenship verification"
    }
  ],
  "status": "published",
  "deployment_status": {
    "telegram": "deployed",
    "web_chat": "pending",
    "whatsapp": "not_configured"
  }
}
```

#### 11.5.2 Change History
```json
{
  "change_log": [
    {
      "timestamp": "2024-01-20T14:45:00Z",
      "user_id": "user_123",
      "action": "step_modified",
      "target": "user_registration.welcome_message",
      "changes": {
        "message.text": {
          "old": "Welcome to our restaurant!",
          "new": "Welcome to ChiHo! Let's get you registered."
        },
        "buttons": {
          "added": [
            {"text": "Skip for now", "value": "skip", "type": "postback"}
          ]
        }
      }
    }
  ]
}
```

### 11.6 Package Structure for Deployment

#### 11.6.1 Complete Package Export
```json
{
  "package_metadata": {
    "package_id": "chiho_onboarding_complete",
    "name": "ChiHo Employee Onboarding",
    "version": "2.1.0",
    "created_at": "2024-01-20T14:45:00Z",
    "description": "Complete onboarding package for ChiHo restaurant employees"
  },
  "intents": [
    {
      "intent_id": "user_registration",
      "file_path": "core/user_registration_intent.json",
      "activation_group": "core"
    },
    {
      "intent_id": "company_ideology", 
      "file_path": "information/company_ideology_intent.json",
      "activation_group": "information"
    },
    {
      "intent_id": "main_menu",
      "file_path": "navigation/main_menu_intent.json", 
      "activation_group": "navigation"
    }
  ],
  "deployment_order": [
    "core/user_registration_intent",
    "navigation/main_menu_intent",
    "information/company_ideology_intent"
  ],
  "variables_mapping": {
    "user_name": "User's full name",
    "user_position": "Employee position",
    "user_project": "Assigned restaurant location"
  },
  "media_assets": [
    {
      "file_id": "welcome_banner_001",
      "file_name": "welcome_banner.webp",
      "file_size": 45320,
      "mime_type": "image/webp"
    }
  ]
}
```

### 11.7 Visual Editor Canvas Data

#### 11.7.1 Canvas Layout Information
```json
{
  "canvas_data": {
    "zoom_level": 1.0,
    "viewport": {
      "x": 0,
      "y": 0,
      "width": 1920,
      "height": 1080
    },
    "grid_settings": {
      "enabled": true,
      "size": 20,
      "snap_to_grid": true
    },
    "nodes": [
      {
        "node_id": "welcome_message",
        "intent_id": "user_registration",
        "position": {"x": 100, "y": 200},
        "size": {"width": 300, "height": 120},
        "type": "message_node",
        "style": {
          "background_color": "#f0f9ff",
          "border_color": "#0ea5e9",
          "text_color": "#0c4a6e"
        },
        "collapsed": false
      }
    ],
    "connections": [
      {
        "source_node": "welcome_message",
        "target_node": "name_input",
        "condition": "user_choice == 'start_reg'",
        "style": {
          "line_type": "curved",
          "color": "#10b981",
          "width": 2
        }
      }
    ]
  }
}
```

### 11.8 API Response Examples

#### 11.8.1 Scenario List Response
```json
{
  "scenarios": [
    {
      "scenario_id": "onboarding_bot_v2",
      "name": "Employee Onboarding Bot",
      "type": "onboarding",
      "status": "published",
      "version": "2.1.0",
      "updated_at": "2024-01-20T14:45:00Z",
      "intents_count": 15,
      "steps_count": 87,
      "deployment_status": {
        "telegram": "active",
        "web_chat": "active"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

#### 11.8.2 Import Validation Response
```json
{
  "validation_result": {
    "valid": false,
    "errors": [
      {
        "line": 15,
        "column": 8,
        "message": "Missing required field 'intent_id'",
        "severity": "error",
        "suggestion": "Add 'intent_id' field to intent definition"
      },
      {
        "line": 23,
        "column": 12,
        "message": "Invalid button type 'custom'",
        "severity": "warning",
        "suggestion": "Use one of: 'postback', 'url', 'phone'"
      }
    ],
    "warnings": [
      {
        "message": "Intent 'old_intent_name' will be renamed during import",
        "suggestion": "Review intent naming conventions"
      }
    ]
  }
}
```

### 11.9 Testing and Simulation

#### 11.9.1 Test Session Configuration
```json
{
  "test_session": {
    "session_id": "test_session_001",
    "scenario_id": "onboarding_bot_v2",
    "platform": "telegram",
    "user_persona": {
      "user_id": "test_user_123",
      "profile": {
        "name": "Александр Петров",
        "position": "food-guide",
        "project": "pyatnitskaya",
        "citizenship": "russian",
        "experience": "beginner"
      },
      "context": {
        "current_time": "2024-01-20T15:30:00Z",
        "location": "moscow",
        "device": "mobile"
      }
    },
    "test_mode": "interactive",
    "debug_enabled": true,
    "breakpoints": ["user_registration.name_input", "company_ideology.brand_person"]
  }
}
```

#### 11.9.2 Test Execution Results
```json
{
  "test_execution": {
    "session_id": "test_session_001",
    "status": "completed",
    "started_at": "2024-01-20T15:30:00Z",
    "completed_at": "2024-01-20T15:45:00Z",
    "duration_seconds": 900,
    "steps_executed": 25,
    "conversation_log": [
      {
        "step_id": "welcome_message",
        "intent_id": "user_registration",
        "timestamp": "2024-01-20T15:30:05Z",
        "message_sent": {
          "text": "Welcome to ChiHo! Let's get you registered.",
          "media": ["welcome_banner_001"]
        },
        "user_input": {
          "type": "button",
          "value": "start_reg",
          "text": "Start Registration"
        },
        "variables_before": {},
        "variables_after": {
          "user_choice": "start_reg"
        },
        "next_step": "name_input",
        "execution_time_ms": 45
      }
    ],
    "final_variables": {
      "user_name": "Александр Петров",
      "user_position": "food-guide",
      "user_project": "pyatnitskaya",
      "onboarding_progress": 100
    },
    "path_taken": [
      "user_registration.welcome_message",
      "user_registration.name_input",
      "user_registration.position_selection",
      "company_ideology.ideology_intro"
    ]
  }
}
```

#### 11.9.3 Flow Analysis Report
```json
{
  "flow_analysis": {
    "scenario_id": "onboarding_bot_v2",
    "analysis_timestamp": "2024-01-20T16:00:00Z",
    "coverage_analysis": {
      "total_steps": 87,
      "reachable_steps": 85,
      "unreachable_steps": [
        {
          "step_id": "error_fallback_legacy",
          "intent_id": "user_registration",
          "reason": "No path leads to this step"
        }
      ],
      "coverage_percentage": 97.7
    },
    "path_analysis": {
      "total_paths": 156,
      "valid_paths": 152,
      "dead_end_paths": [
        {
          "path": ["support_system.contact_info"],
          "reason": "No exit button or next step defined"
        }
      ],
      "circular_paths": [
        {
          "path": ["main_menu.menu", "company_ideology.ideology_intro", "main_menu.menu"],
          "loop_detected": true,
          "max_iterations": 10
        }
      ]
    },
    "validation_issues": [
      {
        "severity": "warning",
        "type": "missing_media",
        "step_id": "motivation_program.kpi_details",
        "message": "Media file 'chiho-kpi1' not found in media library"
      },
      {
        "severity": "error",
        "type": "invalid_transition",
        "step_id": "user_registration.final_confirmation",
        "message": "Next step 'invalid_intent://unknown/step' is not valid"
      }
    ]
  }
}
```

#### 11.9.4 Test Case Definition
```json
{
  "test_case": {
    "test_id": "onboarding_complete_path",
    "name": "Complete Onboarding Flow - Food Guide",
    "description": "Test full onboarding flow for new food guide employee",
    "scenario_id": "onboarding_bot_v2",
    "test_type": "end_to_end",
    "user_inputs": [
      {
        "step_id": "welcome_message",
        "input": {"type": "button", "value": "start_reg"}
      },
      {
        "step_id": "name_input",
        "input": {"type": "text", "value": "Александр Петров"}
      },
      {
        "step_id": "position_selection",
        "input": {"type": "button", "value": "food-guide"}
      },
      {
        "step_id": "project_selection",
        "input": {"type": "button", "value": "pyatnitskaya"}
      }
    ],
    "expected_outcomes": {
      "final_variables": {
        "user_name": "Александр Петров",
        "user_position": "food-guide",
        "user_project": "pyatnitskaya",
        "onboarding_status": "completed"
      },
      "final_step": "onboarding_completion.onboarding_finished",
      "minimum_steps": 20,
      "maximum_duration_seconds": 1800
    },
    "assertions": [
      {
        "type": "variable_equals",
        "variable": "user_position",
        "expected": "food-guide"
      },
      {
        "type": "step_reached",
        "step_id": "motivation_program.premium_calculation"
      },
      {
        "type": "media_displayed",
        "media_id": "chiho-values"
      }
    ]
  }
}
```

#### 11.9.5 Performance Test Results
```json
{
  "performance_test": {
    "test_id": "load_test_001",
    "scenario_id": "onboarding_bot_v2",
    "test_configuration": {
      "concurrent_users": 100,
      "duration_minutes": 15,
      "ramp_up_seconds": 60
    },
    "results": {
      "total_sessions": 1500,
      "successful_sessions": 1487,
      "failed_sessions": 13,
      "success_rate": 99.1,
      "average_response_time_ms": 245,
      "p95_response_time_ms": 450,
      "p99_response_time_ms": 680,
      "throughput_per_second": 16.7
    },
    "bottlenecks": [
      {
        "step_id": "company_ideology.brand_person",
        "average_response_time_ms": 850,
        "issue": "Large media file causing slow loading"
      }
    ],
    "recommendations": [
      {
        "type": "media_optimization",
        "message": "Optimize media files in company_ideology intent",
        "priority": "medium"
      }
    ]
  }
}
```

#### 11.9.6 A/B Test Configuration
```json
{
  "ab_test": {
    "test_id": "welcome_message_variants",
    "name": "Welcome Message Optimization",
    "scenario_id": "onboarding_bot_v2",
    "status": "active",
    "start_date": "2024-01-20T00:00:00Z",
    "end_date": "2024-02-20T00:00:00Z",
    "traffic_split": {
      "variant_a": 50,
      "variant_b": 50
    },
    "variants": {
      "variant_a": {
        "name": "Original Welcome",
        "changes": {
          "user_registration.welcome_message.message.text": "Welcome to ChiHo! Let's get you registered."
        }
      },
      "variant_b": {
        "name": "Friendly Welcome",
        "changes": {
          "user_registration.welcome_message.message.text": "Привет! 👋 Добро пожаловать в команду ЧиХо! Давай знакомиться?"
        }
      }
    },
    "success_metrics": [
      {
        "metric": "completion_rate",
        "target": "maximize"
      },
      {
        "metric": "time_to_complete",
        "target": "minimize"
      },
      {
        "metric": "user_satisfaction",
        "target": "maximize"
      }
    ],
    "current_results": {
      "variant_a": {
        "sessions": 750,
        "completion_rate": 85.2,
        "average_completion_time": 1240,
        "satisfaction_score": 4.3
      },
      "variant_b": {
        "sessions": 742,
        "completion_rate": 89.1,
        "average_completion_time": 1180,
        "satisfaction_score": 4.6
      }
    }
  }
}
```

#### 11.9.7 Debugging Session Data
```json
{
  "debug_session": {
    "session_id": "debug_001",
    "scenario_id": "onboarding_bot_v2",
    "breakpoints": [
      {
        "step_id": "user_registration.name_input",
        "conditions": ["user_input.length > 50"],
        "actions": ["pause", "inspect_variables"]
      }
    ],
    "variable_watches": [
      "user_name",
      "user_position",
      "validation_errors"
    ],
    "step_execution": {
      "current_step": "user_registration.name_input",
      "execution_state": "paused",
      "variables": {
        "user_choice": "start_reg",
        "validation_errors": [],
        "step_start_time": "2024-01-20T15:30:15Z"
      },
      "call_stack": [
        "user_registration.welcome_message",
        "user_registration.name_input"
      ],
      "next_possible_steps": [
        "user_registration.position_selection",
        "user_registration.validation_error"
      ]
    }
  }
}
```

This technical specification serves as the foundation for developing a world-class visual chatbot scenario editor that empowers restaurant operators to create sophisticated conversational experiences without technical barriers.