# Bot Media Scripts

This directory contains scripts for managing media files used by bots.

## Available Scripts

### upload_bot_media.sh

A universal script for uploading any media file to the bot media store.

**Usage:**
```bash
./src/scripts/bots/media/upload_bot_media.sh [options]
```

**Options:**
- `-i, --image PATH` - Path to the image file to upload (required)
- `-f, --file-id ID` - File ID to use in the scenario (auto-generated if not provided)
- `-d, --description DESC` - Description of the image (auto-generated if not provided)
- `-u, --url URL` - API URL (default: http://localhost:8000)
- `-h, --help` - Show help message

**Requirements:**
- The bot API server should be running locally on port 8000 (or specified with --url)
- The script requires `jq` for JSON processing

**What it does:**
1. Gets an authentication token
2. Lists available bots and selects one automatically
3. Checks if media with the specified file ID already exists
4. If not found, uploads the image file to the media service
5. Registers a platform file ID for the image

**Examples:**
```bash
# Upload an image with auto-generated file ID and description
./src/scripts/bots/media/upload_bot_media.sh -i path/to/image.png

# Upload an image with custom file ID and description
./src/scripts/bots/media/upload_bot_media.sh -i path/to/image.png -f menu_header -d "Restaurant menu header"
```

### Example: Adding an image to the "company_history" step

To add an image to the "company_history" step in the onboarding scenario, you can use the upload_bot_media.sh script:

```bash
# Upload the image and register it with the file ID "company_history_image"
./src/scripts/bots/media/upload_bot_media.sh \
  -i /path/to/chiho_history.jpg \
  -f company_history_image \
  -d "First ChiHo restaurant at Krivokolennyy Lane"
```

Then, update the scenario JSON to include the image in the "company_history" step:

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

For detailed technical information, see the [technical specification](../../../docs/features/add-company-history-image.md).