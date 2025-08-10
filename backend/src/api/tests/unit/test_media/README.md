# Bot Media Handling Tests

This directory contains test scripts for validating media handling functionality in the bot management system.

## Available Tests

### test_media_group.py

Tests the functionality for sending multiple media items as a group with or without buttons.

Usage:
```bash
python -m src.api.tests.unit.test_media.test_media_group
```

This test validates:
1. Sending multiple media items with follow-up buttons
2. Sending multiple media items without buttons

### test_media_with_buttons.py

Tests the functionality for sending a single media item with attached buttons.

Usage:
```bash
python -m src.api.tests.unit.test_media.test_media_with_buttons
```

This test validates:
1. Sending an image with attached buttons
2. Error handling when media files are not available

### test_dialog_manager_media.py

Tests the dialog manager's media handling methods directly.

Usage:
```bash
python -m src.api.tests.unit.test_media.test_dialog_manager_media
```

This test validates:
1. Media extraction from different message formats
2. Media validation process
3. Fallback strategies when media operations fail

## Running All Tests

To run all media tests:

```bash
for test in test_media_group.py test_media_with_buttons.py test_dialog_manager_media.py; do
  echo "Running $test..."
  python -m src.api.tests.unit.test_media.$test
  echo "----------------------------------------"
done
```