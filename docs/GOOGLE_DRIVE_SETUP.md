# Google Drive Storage Setup

This guide explains how to configure Google Drive storage for audio recordings to save backend server space.

## Overview

Audio recordings are stored in Google Drive instead of the backend server to:
- Save server storage space
- Reduce server costs
- Store 1-hour audio chunks efficiently
- Automatically manage storage scaling

## Prerequisites

1. A Google Cloud Platform (GCP) account
2. A Google Drive account

## Setup Steps

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID

### 2. Enable Google Drive API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click "Enable"

### 3. Create a Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in the service account details:
   - Name: `audio-storage-service`
   - Description: `Service account for storing audio recordings`
4. Click "Create and Continue"
5. Skip optional permissions (click "Continue")
6. Click "Done"

### 4. Create Service Account Key

1. Find your service account in the credentials list
2. Click on it to open details
3. Go to the "Keys" tab
4. Click "Add Key" → "Create new key"
5. Select "JSON" format
6. Click "Create"
7. The JSON key file will be downloaded to your computer
8. **Keep this file secure!** It provides full access to your Google Drive

### 5. Share Google Drive Folder

#### Option A: Use an Existing Shared Folder (Recommended)

If you already have a Google Drive folder that you want to use:

1. Open the folder in Google Drive
2. Copy the folder link (e.g., `https://drive.google.com/drive/folders/1gQu8i7TtVI--EiVIW6N7wCL-GzubKflA`)
3. Extract the folder ID from the URL (the part after `folders/`):
   - Example: `1gQu8i7TtVI--EiVIW6N7wCL-GzubKflA`
4. Right-click the folder → "Share"
5. Add the service account email (found in the JSON key file, looks like `audio-storage-service@project-id.iam.gserviceaccount.com`)
6. Give it "Editor" permissions
7. Click "Share"
8. Save the folder ID for the next step

#### Option B: Let the App Create a New Folder

If you want the application to create a new folder:

1. The app will automatically create a folder named "Secret Audio Recordings" (or your specified name)
2. The folder will be created in the service account's drive
3. You can find it by searching for the folder name in your shared drives

**Note:** Option A (using a specific folder ID) is recommended when you want full control over where files are stored.

### 6. Configure Environment Variables

#### Option 1: Using JSON File (Local Development)

1. Place the JSON key file in a secure location on your server (e.g., `/etc/secrets/google-drive-key.json`)
2. Set the environment variable:
   ```bash
   export GOOGLE_DRIVE_CREDENTIALS_PATH=/etc/secrets/google-drive-key.json
   ```

#### Option 2: Using JSON String (Railway/Cloud Deployment)

1. Open the JSON key file in a text editor
2. Copy the entire JSON content
3. Set it as an environment variable (paste the entire JSON as a single line):
   ```bash
   export GOOGLE_DRIVE_CREDENTIALS_JSON='{"type":"service_account","project_id":"...",...}'
   ```

#### Additional Configuration

You can configure the folder in two ways:

**Option A: Use specific folder ID (recommended)**
```bash
export GOOGLE_DRIVE_FOLDER_ID="1gQu8i7TtVI--EiVIW6N7wCL-GzubKflA"
```

**Option B: Use folder name (app will search/create)**
```bash
export GOOGLE_DRIVE_FOLDER_NAME="Secret Audio Recordings"
```

**Note:** If both are set, `GOOGLE_DRIVE_FOLDER_ID` takes precedence.

### 7. Update .env File

Add these lines to your `.env` file:

```env
# Google Drive Storage
GOOGLE_DRIVE_CREDENTIALS_PATH=/path/to/service-account-key.json
# OR
GOOGLE_DRIVE_CREDENTIALS_JSON={"type":"service_account",...}

# Folder configuration (choose one)
# Option A: Specific folder ID (recommended)
GOOGLE_DRIVE_FOLDER_ID=1gQu8i7TtVI--EiVIW6N7wCL-GzubKflA
# Option B: Folder name
GOOGLE_DRIVE_FOLDER_NAME=Secret Audio Recordings
```

### 8. Install Dependencies

The required packages are already in `requirements.txt`:
```bash
pip install -r backend/requirements.txt
```

### 9. Restart the Application

```bash
python manage.py runserver
```

## How It Works

1. When a user consents and audio recording starts, 1-hour audio chunks are created
2. Each chunk is automatically uploaded to Google Drive
3. The file metadata (file ID, size, duration) is stored in the database
4. If Google Drive is unavailable, files fall back to local storage automatically
5. Audio files can be accessed through Django admin or API endpoints

## Storage Details

- **Chunk Duration:** 1 hour per chunk
- **File Format:** WebM with Opus codec
- **Bitrate:** 16 kbps (very low, optimized for voice)
- **Sample Rate:** 16 kHz
- **Average File Size:** ~7 MB per hour
- **Storage Location:** Google Drive folder "Secret Audio Recordings"

## Fallback Behavior

If Google Drive credentials are not configured or the service is unavailable:
- Files are automatically saved to local storage (`media/secret_audio/`)
- No errors are thrown
- The application continues to function normally

## Monitoring

Check the Django admin panel to monitor:
- Number of audio recordings
- Storage used
- Upload timestamps
- File sizes

## Security Notes

- **Never commit** the service account JSON key to version control
- Store credentials as environment variables or in secure secret management
- The service account has access only to files it creates (unless you share a folder)
- Use HTTPS for all API communications
- Regularly rotate service account keys

## Troubleshooting

### Authentication Error

**Error:** `Failed to initialize Google Drive storage`

**Solution:**
1. Verify the JSON key file is valid
2. Check that the service account email is correct
3. Ensure the Google Drive API is enabled in GCP

### Permission Denied

**Error:** `403 Forbidden when uploading files`

**Solution:**
1. Check that the service account has proper permissions
2. Verify the Google Drive API is enabled
3. Ensure the folder is shared with the service account email

### Files Not Appearing

**Issue:** Files upload but don't appear in Drive

**Solution:**
1. Files are stored in the service account's drive, not your personal drive
2. Share a folder with the service account to see files in your drive
3. Check the Django admin to see if files are marked as uploaded

### Fallback to Local Storage

**Issue:** Files are saved locally instead of Google Drive

**Solution:**
1. Check environment variables are set correctly
2. Verify credentials are valid
3. Check server logs for error messages
4. Ensure internet connectivity from the server

## Cost Considerations

Google Drive storage pricing (as of 2024):
- First 15 GB: **Free**
- Beyond 15 GB: Varies by Google Workspace plan

For reference:
- 1 hour of audio ≈ 7 MB
- 15 GB = ~2,100 hours of audio (87 days of continuous recording)

## Alternative: Google Cloud Storage

For higher volume, consider migrating to Google Cloud Storage (GCS):
- More cost-effective for large volumes
- Better integration with GCP services
- Similar setup process

Contact the development team for GCS migration guide.
