# Technical Specification: Database Media Storage Migration

## 1. Overview

Currently, the GET INN Restaurant Platform stores media files in the local filesystem, with paths to those files recorded in the database. This technical specification outlines the changes needed to completely replace this approach by storing media file contents directly in the database. All filesystem storage code will be removed, improving portability, backup capabilities, and deployment consistency.

## 2. Current Implementation to be Replaced

### 2.1 Legacy Database Schema

The legacy `BotMediaFile` model that will be completely replaced stores only metadata about media files and references the filesystem for content:

```python
class BotMediaFile(Base):
    __tablename__ = "bot_media_file"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    file_type = Column(String, nullable=False)  # 'image', 'video', etc.
    file_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)  # To be removed completely
    platform_file_ids = Column(JSONB, nullable=True)  # Map of platform -> file_id
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 2.2 Legacy Media Service Methods

The following legacy implementation methods will be completely replaced:
- `MediaService.create_media_file()` - Currently saves files to the filesystem (to be replaced)
- `MediaService.get_file_content()` - Currently opens and reads files from filesystem (to be replaced)
- `MediaService.delete_media_file()` - Currently removes files from the filesystem (to be replaced)

### 2.3 API Endpoints

The key endpoints affected:
- `GET /media/{media_id}` - Returns media metadata
- `GET /media/{media_id}/content` - Returns the binary file content from the filesystem
- `POST /bots/{bot_id}/media` - Uploads media files to the filesystem

## 3. Proposed Changes

### 3.1 Database Schema Changes

Modify the `BotMediaFile` model to store the binary file content directly:

```python
class BotMediaFile(Base):
    __tablename__ = "bot_media_file"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instance.id"), nullable=False)
    file_type = Column(String, nullable=False)  # 'image', 'video', etc.
    file_name = Column(String, nullable=False)
    # New columns for storing file content
    file_content = Column(LargeBinary, nullable=False)
    content_type = Column(String, nullable=False)  # MIME type
    file_size = Column(Integer, nullable=False)
    # No longer using filesystem storage
    # storage_path field will be removed
    platform_file_ids = Column(JSONB, nullable=True)  # Map of platform -> file_id
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 3.2 Implementation Strategy

1. Create a new database migration script:
   - Add new columns (`file_content`, `content_type`, `file_size`)
   - Remove the `storage_path` column

2. Clean Cutover Deployment:
   - Deploy schema changes
   - Deploy code changes
   - Verify API endpoints are working properly
   - Start using database storage for all new media uploads

### 3.3 Service Layer Changes

Modify `MediaService` methods:

```python
class MediaService:
    @staticmethod
    async def create_media_file(db: AsyncSession, file: UploadFile, bot_id: UUID) -> Optional[BotMediaFileDB]:
        """Create a new media file entry and store the file content in the database"""
        # Check if bot exists
        query = select(BotInstance).where(BotInstance.id == bot_id)
        result = await db.execute(query)
        bot_instance = result.scalars().first()
        
        if not bot_instance:
            return None
        
        # Determine file type from content-type
        file_type = file.content_type.split('/')[0] if file.content_type else "unknown"
        filename = file.filename
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Create database entry
        db_media_file = BotMediaFile(
            bot_id=bot_id,
            file_type=file_type,
            file_name=filename,
            file_content=file_content,
            content_type=file.content_type,
            file_size=file_size,
            platform_file_ids={}
        )
        
        db.add(db_media_file)
        await db.commit()
        await db.refresh(db_media_file)
        
        return BotMediaFileDB.model_validate(db_media_file)

    @staticmethod
    async def get_file_content(media_id: UUID, db: AsyncSession) -> Optional[Tuple[bytes, str]]:
        """Get file content and content type from the database"""
        query = select(BotMediaFile).where(BotMediaFile.id == media_id)
        result = await db.execute(query)
        media_file = result.scalars().first()
        
        if not media_file or not media_file.file_content:
            return None
        
        return (media_file.file_content, media_file.content_type)
```

### 3.4 API Endpoint Changes

1. Update the content endpoint:

```python
@router.get("/media/{media_id}/content")
async def get_media_file_content(
    media_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Response:
    """Get the actual content of a media file."""
    try:
        # Find the media file by UUID or file_id
        media_file = await MediaService.find_media_file_by_id_or_name(db, media_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Check permissions...
        
        # Get file content directly from database
        if not media_file.file_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file content not found"
            )
            
        # Return the file content from database
        return Response(
            content=media_file.file_content,
            media_type=media_file.content_type,
            headers={"Content-Disposition": f"attachment; filename={media_file.file_name}"}
        )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file content not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting media file content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get media file content: {str(e)}"
        )
```

2. Update the upload endpoint to store file content in the database.

## 4. Schema Updates

### 4.1 Database Migration

Create an Alembic migration script:

```python
"""add media file content columns

Revision ID: abcdef123456
Revises: previous_revision_id
Create Date: 2025-XX-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abcdef123456'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None


def upgrade():
    # First add the new columns
    op.add_column('bot_media_file', sa.Column('file_content', sa.LargeBinary(), nullable=False))
    op.add_column('bot_media_file', sa.Column('content_type', sa.String(), nullable=False))
    op.add_column('bot_media_file', sa.Column('file_size', sa.Integer(), nullable=False))
    
    # Then completely remove the legacy storage_path column
    op.drop_column('bot_media_file', 'storage_path')
    
    # Remove any obsolete data or rows that would be invalid in new schema
    op.execute("DELETE FROM bot_media_file WHERE file_content IS NULL")


def downgrade():
    op.add_column('bot_media_file', sa.Column('storage_path', sa.String(), nullable=True))
    op.drop_column('bot_media_file', 'file_size')
    op.drop_column('bot_media_file', 'content_type')
    op.drop_column('bot_media_file', 'file_content')
```

### 4.2 Content Type Determination Helper

Create a helper function to determine content type based on file name and type:

```python
def determine_content_type(file_name: str, file_type: str) -> str:
    """Determine the appropriate content type based on file name and type"""
    extension = os.path.splitext(file_name)[1].lower()
    content_type = "application/octet-stream"  # Default
    
    if file_type == "image":
        if extension in [".jpg", ".jpeg"]:
            content_type = "image/jpeg"
        elif extension == ".png":
            content_type = "image/png"
        elif extension == ".gif":
            content_type = "image/gif"
        else:
            content_type = f"image/{extension[1:]}"
    elif file_type == "video":
        content_type = f"video/{extension[1:]}"
    elif file_type == "audio":
        content_type = f"audio/{extension[1:]}"
    elif file_type == "document":
        # Handle common document types
        if extension == ".pdf":
            content_type = "application/pdf"
        elif extension in [".doc", ".docx"]:
            content_type = "application/msword"
        elif extension in [".xls", ".xlsx"]:
            content_type = "application/vnd.ms-excel"
    
    return content_type
```

## 5. Implementation Plan

### 5.1 Implementation

1. Create and apply the database migration script that removes the legacy storage_path column
2. Completely replace the `BotMediaFile` model to use binary content storage
3. Update all Pydantic schemas to remove any filesystem-related fields
4. Replace all filesystem-related code in the `MediaService` with database storage
5. Update API endpoints to retrieve directly from the database
6. Remove any unused filesystem utility functions and imports

### 5.2 Verification and Cleanup

1. Verify API endpoints are working properly with database storage
2. Monitor database performance with binary data
3. Test file uploads and retrievals using the new system
4. Check that the Dialog Manager correctly handles media
5. Search codebase for any remaining references to storage_path and filesystem operations
6. Remove any unused imports or functions related to filesystem operations
7. Delete any legacy media directories that are no longer used

## 6. Benefits and Considerations

### 6.1 Benefits

1. **Portability**: Media files are stored with the database, making backups and migrations easier
2. **Deployment simplicity**: No need to manage separate media storage directories
3. **Consistency**: Files stay with their metadata, preventing orphaned files
4. **Security**: Database access controls apply to media files

### 6.2 Considerations

1. **Database size**: Media files will increase database size; monitoring should be implemented
2. **Performance**: Binary data in the database may impact query performance
3. **Backup and restore**: Database backups will be larger and potentially slower
4. **File size limits**: Large files may exceed database field size limits
5. **Content delivery**: May not be optimal for high-traffic applications (future CDN integration may be needed)

## 7. Scripts and Tests Updates

### 7.1 Upload Script Verification

Verify the existing script `backend/src/scripts/bots/media/upload_bot_media.sh` works correctly with the new implementation:

1. The script already uses API endpoints and won't need code changes
2. It uses curl's form upload which works with both implementations
3. No filesystem-specific code exists in the script

Important to check:
```bash
# Confirm API responses match expected format with new implementation
# Test all script functionality to verify it works with database storage
# The script should continue to work without modification
```

### 7.2 Test Updates

The following test files will need to be updated:

1. **Integration Test**: Update `test_media_processing.py`
   - Rewrite `create_test_media_file()` to directly create database entries with binary content
   - Remove all filesystem operations completely
   - Update assertions to verify only database content

```python
# Before
def create_test_media_file(self, file_name="test_media.png"):
    # Create temp media directory
    media_dir = "media"
    os.makedirs(media_dir, exist_ok=True)
    
    # Create a simple test image (1x1 pixel black PNG)
    file_path = os.path.join(media_dir, file_name)
    with open(file_path, "wb") as f:
        # Minimal valid PNG file (1x1 pixel, black)
        f.write(bytes.fromhex('89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000D4944415478DAE3626000000006000105D4378F0000000049454E44AE426082'))
    
    return file_path

# After
def create_test_media_file(self, file_name="test_media.png"):
    # Create a simple test image (1x1 pixel black PNG) as binary content
    image_content = bytes.fromhex('89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000D4944415478DAE3626000000006000105D4378F0000000049454E44AE426082')
    
    # Upload directly to the API
    files = {'file': (file_name, image_content, 'image/png')}
    url = f"{self.api_base_url}/v1/api/bots/{bot_id}/media"
    response = requests.post(url, files=files, headers=self.headers)
    
    assert response.status_code == 201, f"Failed to upload media file: {response.text}"
    media_data = response.json()
    media_id = media_data["media_id"]
    
    # Register platform file_id
    file_id = os.path.splitext(file_name)[0]
    platform_data = {
        "platform": "telegram",
        "file_id": file_id
    }
    url = f"{self.api_base_url}/v1/api/media/{media_id}/platform-id"
    response = requests.post(url, json=platform_data, headers=self.headers)
    
    assert response.status_code == 200, f"Failed to register platform file ID: {response.text}"
    
    return file_id
```

2. **Test Cleanup**: Replace cleanup procedures
   - Remove all filesystem cleanup code completely
   - Add database cleanup to properly remove test media entries

3. **Other Tests**: Replace all test code that interacts with media files
   - Remove all filesystem-related test code
   - Create new mock objects that include binary content fields
   - Replace file-based assertions with database field assertions
   - Remove any file path validation in tests

## 8. Future Enhancements

1. **File size limits**: Implement validation to prevent files larger than a defined threshold
2. **Content delivery optimization**: Add CDN support for high-traffic scenarios
3. **File deduplication**: Implement deduplication to reduce storage usage
4. **Streaming support**: Add support for streaming large media files instead of loading them all at once

## 9. Rollback Plan

In case of issues, we can roll back the changes by:

1. Rolling back the database migration with Alembic
2. Re-implementing the filesystem storage logic
3. Redeploying the previous version of the code