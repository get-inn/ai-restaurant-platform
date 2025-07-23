# Bot Management System Overview

This document provides a high-level overview of the bot management system in the GET INN Restaurant Platform.

## Introduction

The bot management system enables creation and management of conversational interfaces across multiple messaging platforms. It provides a unified system for defining, deploying, and monitoring chat bots that can interact with users via Telegram and other platforms.

## Key Components

1. **Bot Core Management System** - FastAPI application that manages all bots
2. **Dialog Manager** - Module responsible for storing and executing scenarios
3. **Messenger Adapters** - Integrations with different platforms (Telegram, WhatsApp, etc.)
4. **Dialog State Storage** - Ensuring dialog persistence
5. **Media Storage** - For working with images and videos
6. **LLM Integration Component** - For future expansion of capabilities

## Architecture Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                   Existing GET INN Backend                     │
└──────────────────────┬────────────────────────────────────────┘
                       │
                       │ Direct DB access + API integration
                       ▼
┌───────────────────────────────────────────────────────────────┐
│                     Bot Management System                     │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  Bot Manager │    │Dialog Manager│    │Media Manager │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Platform     │    │ State        │    │ LLM          │     │
│  │ Adapters     │    │ Repository   │    │ Integration  │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└───────────┬──────────────────┬──────────────────┬─────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Telegram API  │    │ WhatsApp API  │    │  Viber API    │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Features

- **Multi-Platform Support**: Create bots that work across multiple messaging platforms
- **Scenario-Based Dialogs**: Define conversational flows with branching and conditions
- **State Management**: Persist conversation state between messages
- **Media Handling**: Support for images, documents, and other media types
- **Webhook Management**: Automatic management of webhooks for real-time updates
- **Conversation Logging**: Detailed logging for debugging and analysis

## Key Concepts

### Bot Instance

A bot instance represents a single bot with its configuration, credentials, and scenarios. A bot can:
- Have multiple platform-specific integrations
- Be associated with specific scenarios
- Be enabled or disabled

### Bot Platform Credentials

Credentials for connecting to specific messaging platforms:
- Platform-specific tokens and settings
- Webhook configuration
- Security settings

### Bot Scenarios

Defined conversation flows that determine how the bot responds to user inputs:
- Steps with messages and expected inputs
- Conditional branching
- Variable collection and manipulation
- Integration with backend services

### Dialog State

Persistence of conversation state including:
- Current step in the scenario
- Collected data
- User information
- Platform-specific metadata

## Integration Points

The bot management system integrates with:

1. **Main Backend**: For access to business logic and data
2. **External APIs**: For message sending and receiving
3. **Storage Systems**: For media files and persistent state

## Further Reading

For more detailed information, see:
- [Scenario Format](scenario-format.md) - Bot scenario specification
- [Webhook Management](webhook-management.md) - Telegram webhook integration
- [Conversation Logging](conversation-logging.md) - Bot conversation logging