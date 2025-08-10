# Bot Media Scripts

This directory contains scripts for managing media files used by bots. These scripts help you upload media files (like images) to the bot media store for use in bot scenarios.

## Overview

Media files (images, videos, etc.) are essential components of rich bot interactions. The scripts in this directory handle:

- Authentication with the API
- Bot selection
- Media file upload
- Platform file ID registration
- Duplicate detection
- Batch uploading

## Available Scripts

### 1. `upload_bot_media.sh`

A universal script for uploading any media file to the bot media store and registering it for use in scenarios.

#### Usage

```bash
./upload_bot_media.sh [options]
```

#### Options

- `-i, --image PATH` - Path to the image file to upload (required)
- `-f, --file-id ID` - File ID to use in the scenario (auto-generated if not provided)
- `-d, --description DESC` - Description of the image (auto-generated if not provided)
- `-p, --platform NAME` - Platform to register the file ID for (default: telegram)
- `-u, --url URL` - API URL (default: http://localhost:8000)
- `-h, --help` - Show help message

#### What it does

1. Gets an authentication token
2. Lists available bots and selects one automatically
3. Checks if media with the specified file ID already exists
4. If not found, uploads the image file to the media service
5. Registers a platform file ID for the image

#### Examples

```bash
# Upload an image with auto-generated file ID and description
./upload_bot_media.sh --image path/to/image.png

# Upload an image with custom file ID and description
./upload_bot_media.sh --image path/to/image.png --file-id menu_header --description "Restaurant menu header"

# Upload to a specific platform
./upload_bot_media.sh --image path/to/image.png --platform whatsapp
```

### 2. `batch_upload_chiho_media.sh`

A specialized script for batch uploading all images from a directory, particularly designed for Chiho onboarding images.

#### Usage

```bash
./batch_upload_chiho_media.sh [options]
```

#### Options

- `-d, --dir PATH` - Directory containing images to upload (default: chiho images directory)
- `-e, --ext EXTENSION` - File extension to upload (default: png)
- `-p, --platform NAME` - Platform to register IDs for (default: telegram)
- `-u, --url URL` - API URL (default: http://localhost:8000)
- `-s, --script PATH` - Path to upload script (default: auto-detected)
- `--delay SECONDS` - Delay between uploads in seconds (default: 1)
- `-h, --help` - Show help message

#### What it does

1. Finds all files with the specified extension in the target directory
2. For each file, generates a file ID based on the filename
3. Uploads each file using the `upload_bot_media.sh` script
4. Reports statistics on successful and failed uploads

#### Examples

```bash
# Upload all PNG images from the default directory
./batch_upload_chiho_media.sh

# Upload JPG images from a custom directory
./batch_upload_chiho_media.sh --dir /path/to/images --ext jpg

# Upload with a 2-second delay between uploads
./batch_upload_chiho_media.sh --delay 2
```

## Requirements

- The bot API server should be running locally on port 8000 (or specified with --url)
- `curl` - For API requests
- `jq` - For JSON processing (install with `brew install jq` on macOS or `apt-get install jq` on Linux)
- Bash shell

## Using Media in Bot Scenarios

After uploading media files, you can reference them in your bot scenarios. Here's how:

### Adding Media to a Bot Scenario

```json
{
  "step_id": {
    "message": {
      "text": "Your message text here",
      "media": [
        {
          "type": "image",
          "description": "Your image description",
          "file_id": "your_file_id"
        }
      ]
    },
    "next_step": "next_step_id"
  }
}
```

### Example: Adding an image to the "company_history" step

To add an image to the "company_history" step in the onboarding scenario:

```bash
# Upload the image and register it with the file ID "company_history_image"
./upload_bot_media.sh \
  --image /path/to/chiho_history.jpg \
  --file-id company_history_image \
  --description "First ChiHo restaurant at Krivokolennyy Lane"
```

Then, update the scenario JSON:

```json
"company_history": {
  "message": {
    "text": "The first ChiHo restaurant was opened in 2018...",
    "media": [
      {
        "type": "image",
        "description": "First ChiHo restaurant at Krivokolennyy Lane",
        "file_id": "company_history_image"
      }
    ]
  },
  "next_step": "next_step_id"
}
```

Finally, upload and activate the updated scenario using the bot management API.

## Troubleshooting

### Common Issues

1. **Authentication Failures**: Ensure the API is running and accessible at the specified URL.

2. **File Not Found**: Double-check the file paths for your images.

3. **Platform File ID Already Exists**: If you get warnings about file IDs already existing, the script will use the existing media file.

4. **Invalid JSON Response**: Make sure the API is returning valid JSON responses. Check your API URL and connectivity.

### Getting Help

For more information or help with these scripts, contact the GetInn development team.

## See Also

- [Bot Management Documentation](/docs/modules/bot-management/)
- [API Reference](/docs/api/reference.md)