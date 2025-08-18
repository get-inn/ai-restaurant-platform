# ChiHo Onboarding Bot - Intent-Based Architecture

This directory contains the intent-based version of the ChiHo onboarding bot scenario, converted from the monolithic `onboarding_scenario.json` file.

## Structure

The original 1,143-line, 59-step monolithic scenario has been split into **14 focused intents** organized in 4 categories:

### Core Intents (Essential Flow)
- **`welcome_intent.json`** - Initial greeting and introduction (1 step)
- **`user_registration_intent.json`** - User data collection (5 steps)
- **`data_confirmation_intent.json`** - Data validation and confirmation (1 step) 
- **`first_day_preparation_intent.json`** - First day instructions and documents (3 steps)
- **`onboarding_completion_intent.json`** - Final congratulations and menu transition (1 step)

### Information Intents (Educational Content)
- **`company_ideology_intent.json`** - Company values, positioning, brand metaphor (4 steps)
- **`work_conditions_intent.json`** - Salary, benefits, multisensorics (3 steps)
- **`responsibilities_intent.json`** - Job duties and expectations (1 step)
- **`motivation_program_intent.json`** - KPI and bonus information (1 step)
- **`office_structure_intent.json`** - Key people and office locations (1 step)

### Support Intents (Help and Assistance)
- **`contacts_intent.json`** - Contact information and chat links (1 step)
- **`help_support_intent.json`** - Interactive support system (2 steps)

### Navigation Intents (Flow Control)
- **`main_menu_intent.json`** - Central navigation hub (1 step)
- **`menu_display_intents.json`** - Quick information displays (5 steps)

## Key Improvements

### 1. Modular Architecture
- **Before**: 1 file with 59 steps
- **After**: 14 files with 1-5 steps each
- Each intent focuses on a specific user goal

### 2. Intent Transitions
- Uses `intent://` protocol for cross-intent navigation
- Example: `"next_step": "intent://core/user_registration/ask_lastname"`
- Maintains conversation flow while enabling modularity

### 3. Enhanced Input Validation
- Added validation patterns for names, dates, and messages
- Better error messages for user guidance
- Integrated with the input validation system

### 4. Flexible Navigation
- Menu options lead to dedicated display steps
- Direct return to menu from any information section
- No more getting trapped in onboarding loops

### 5. Context Management
- Intent-specific context requirements
- Entry/exit point definitions
- Dependency tracking between intents

## Deployment

This intent package can be deployed using the bulk upload tools:

### Command Line Deployment
```bash
# Deploy all intents
python -m src.scripts.bots.intents.deploy_intents \
    --bot-id "your-bot-id" \
    --intents-dir "./docs/modules/bot-management/example-scenario-intents/" \
    --activation-group "all"

# Deploy only essential intents first
python -m src.scripts.bots.intents.deploy_intents \
    --bot-id "your-bot-id" \
    --intents-dir "./docs/modules/bot-management/example-scenario-intents/" \
    --activation-group "essential"
```

### API Deployment
```bash
# Create ZIP package
zip -r intents_package.zip . -x "*.md"

# Deploy via API
curl -X POST "http://localhost:8000/v1/api/bots/BOT_ID/intents/deploy" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "package_file=@intents_package.zip" \
  -F "activation_group=all"
```

## Package Configuration

The `package.json` file defines:
- **Deployment order** - Intents are deployed in dependency order
- **Activation groups** - Subsets of intents for different deployment scenarios
- **Variables mapping** - Shared variable definitions
- **Global context** - Brand information and common data

## Benefits

### For Developers
- **Easier maintenance** - Small, focused files instead of 1,143-line monolith
- **Parallel development** - Multiple developers can work on different intents
- **Reusability** - Information intents can be used across different bots
- **Testing** - Unit test individual intents in isolation

### For Users
- **Better navigation** - Quick access to information without getting lost
- **Consistent experience** - All menu options work the same way
- **Faster responses** - Only needed intents are loaded
- **No dead ends** - Always a clear path back to the menu

### For Business
- **Scalability** - Easy to add new intents or modify existing ones
- **A/B testing** - Test different versions of individual intents
- **Analytics** - Track usage and effectiveness of specific information sections
- **Content management** - Non-technical team members can update individual intents

## Migration from Monolithic

The intent-based system is designed to coexist with the original monolithic scenario:

1. **Dual system support** - Both can run simultaneously
2. **Gradual migration** - Migrate one intent at a time
3. **Fallback mechanism** - Automatic fallback to monolithic if intent routing fails
4. **State compatibility** - Existing user states can be migrated

## File Statistics

| Category | Files | Steps | Lines | Avg Lines/File |
|----------|-------|-------|-------|----------------|
| Core | 5 | 11 | 425 | 85 |
| Information | 5 | 10 | 380 | 76 |
| Support | 2 | 3 | 95 | 48 |
| Navigation | 2 | 6 | 210 | 105 |
| **Total** | **14** | **30** | **1,110** | **79** |

**Comparison with Monolithic:**
- **Files**: 1 → 14 (+1,300% modularity)
- **Steps**: 59 → 30 (simplified flow, removed redundancy)
- **Average lines per file**: 1,143 → 79 (-93% complexity)
- **Maintainability**: 1 giant file → 14 focused files

This represents a dramatic improvement in maintainability while preserving all original functionality and enhancing the user experience.