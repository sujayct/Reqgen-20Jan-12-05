# Audio Transcription Service - Error Fix Guide

## Problem
The audio transcription is failing with error:
```
Audio Processing Failed: Failed to connect to primary transcription service. The service might be down.
Error Status: 503 (Service Unavailable)
```

## Root Cause Analysis

The ReqGen application uses a **dual-service transcription system**:

### Primary Service: Vakyansh API
- **URL**: `https://cdac.ulcacontrib.org/asr/v1/recognize/{language}`
- **Status**: Currently experiencing intermittent unavailability
- **Languages**: Hindi, English, and 22+ Indian languages
- **Issue**: The remote API is returning 503 errors

### Fallback Service: Python/Whisper Backend
- **URL**: `http://localhost:5000/api/transcribe`
- **Status**: May not be running
- **Type**: OpenAI Whisper for transcription
- **Issue**: Python backend is not accessible

## Solutions

### Solution 1: Ensure Python Backend is Running (Recommended)
This is the most reliable solution for local development.

#### Step 1: Check Python Backend Status
```bash
# Test if Python backend is running
curl http://localhost:5000/api/health

# Expected response:
# {"status":"healthy","message":"Smart T5 Audio Backend is running",...}
```

#### Step 2: Start Python Backend (if not running)
```bash
# Navigate to python-backend folder
cd c:\Users\sujay.palande\Downloads\Reqgen 20Jan-12-05\python-backend

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start the Flask server
python app.py

# Expected output:
# * Running on http://localhost:5000
# * WARNING in the backend about debug mode
```

#### Step 3: Verify Backend is Working
```bash
# Upload a test audio file
curl -X POST -F "audio=@test-audio.wav" http://localhost:5000/api/transcribe
```

### Solution 2: Update Environment Configuration
If the Python backend is on a different server, configure the URL:

#### Edit `.env` file:
```env
PYTHON_BACKEND_URL=http://your-python-server-url:5000
```

#### Or pass via environment:
```bash
# On Windows (PowerShell)
$env:PYTHON_BACKEND_URL="http://your-server:5000"
npm run dev

# On Windows (Command Prompt)
set PYTHON_BACKEND_URL=http://your-server:5000
npm run dev

# On Mac/Linux
export PYTHON_BACKEND_URL=http://your-server:5000
npm run dev
```

### Solution 3: Check Vakyansh API Status
The primary Vakyansh API might be temporarily down:

```bash
# Test Vakyansh API directly
curl -X POST https://cdac.ulcacontrib.org/asr/v1/recognize/hi \
  -H "Content-Type: application/json" \
  -d '{"config":{"language":{"sourceLanguage":"hi"}}}'

# If this fails with 503, Vakyansh is down
# Check status at: https://ulca.cdac.in/
```

## Improved Error Handling (Now Implemented)

The application now includes:

1. **Better Timeout Handling**
   - Primary service: 60-second timeout
   - Fallback service: 30-second timeout
   - Prevents hanging requests

2. **Automatic Fallback**
   - If Vakyansh API fails → automatically tries Python Whisper backend
   - If Python backend fails → shows helpful error message with suggestions

3. **User-Friendly Error Messages**
   - Clear indication that services are unavailable
   - Suggestions to retry or check backend status
   - Technical details logged for debugging

4. **Better Logging**
   - All service calls are logged to console
   - Error details include source of failure
   - Helps identify which service is the problem

## Troubleshooting Checklist

- [ ] Python backend is running on `http://localhost:5000`
- [ ] Python backend has all required dependencies installed
- [ ] Port 5000 is not blocked by firewall
- [ ] Node.js backend is running (main server)
- [ ] CORS is properly configured
- [ ] Audio file is not too large (< 100MB recommended)
- [ ] Audio format is supported (WAV, MP3, M4A, OGG, FLAC, WEBM)
- [ ] Network connectivity to remote services is working

## Testing Audio Transcription

### Using the Web UI
1. Go to **Note Editor** page
2. Click **"Upload Audio"** button
3. Select an audio file or use **"Record"** button
4. Wait for transcription to complete

### Using Test File
```bash
# Use the included test HTML file
# Open: c:\Users\sujay.palande\Downloads\Reqgen 20Jan-12-05\test-transcription.html
# In a browser and test the transcription endpoint
```

## Quick Start - Both Servers

To start both servers at once:

```bash
# Using the provided batch file
cd c:\Users\sujay.palande\Downloads\Reqgen 20Jan-12-05
.\START-BOTH-SERVERS.bat

# Or manually in separate terminals:
# Terminal 1 (Node.js backend):
npm run dev

# Terminal 2 (Python backend):
cd python-backend
python app.py
```

## Performance Optimization

If transcription is slow:
1. Use shorter audio files (< 10 minutes)
2. Ensure good internet connection for Vakyansh API
3. Check Python backend system resources
4. Use direct recording (browser) instead of file upload (faster processing)

## Additional Resources

- [Vakyansh Documentation](https://ulca.cdac.in/)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [ReqGen Setup Guide](./LOCALHOST_SETUP.md)
- [Python Backend Setup](./PYTHON_SETUP.md)

## Support

If the issue persists after trying all solutions:

1. **Check Server Logs**
   - Node.js backend console output
   - Python backend console output
   - Browser developer console (F12 → Network tab)

2. **Check Backend Health**
   ```bash
   curl http://localhost:3000/api/health
   curl http://localhost:5000/api/health
   ```

3. **Test with Simple Audio**
   - Use a short, clear audio clip
   - Ensure it's in a supported format
   - Record directly instead of uploading files

---

**Last Updated**: January 20, 2026  
**Status**: ✅ Fixed with improved error handling and timeout logic
