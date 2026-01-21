# Complete Local Setup Guide - ReqGen Audio Transcription & Document Processing

## Overview
This guide provides step-by-step instructions to run the complete ReqGen system locally with:
- ✅ Audio transcription (with triple-fallback: Vakyansh → Python → OpenAI)
- ✅ Document refinement (AI-powered summarization via T5-Large)
- ✅ Document generation (structured document creation)

## Prerequisites
- Node.js v18+ and npm installed
- Python 3.8+ installed with pip
- MySQL database running locally (XAMPP or native MySQL)

## Step 1: Database Setup (If Not Already Done)

```bash
# Start your MySQL server
# On Windows: Start XAMPP and enable MySQL, or start MySQL service directly

# Run SQL setup
mysql -u root -p < database/COMPLETE_MYSQL_SETUP.sql
```

## Step 2: Node Backend Setup (Terminal 1)

```bash
# Navigate to project root
cd "c:\Users\sujay.palande\Downloads\Reqgen 20Jan-12-05"

# Install Node dependencies
npm install

# Start the Node backend on port 5027
npm run dev
```

**Expected output:**
```
[vite] listening on http://localhost:5173
vite v5.1.0 starting server at 5173...
Server running on port 5027
```

## Step 3: Python Backend Setup (Terminal 2)

```bash
# Navigate to python backend
cd "c:\Users\sujay.palande\Downloads\Reqgen 20Jan-12-05\python-backend"

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install Python dependencies
pip install flask flask-cors python-dotenv transformers torch torchaudio librosa pydub requests

# Start the Python backend on port 5000
python app.py
```

**Expected output:**
```
 * Running on http://localhost:5000
 * WARNING in production...
```

## Step 4: Frontend Access

Open your browser and navigate to:
```
http://localhost:5173
```

## Testing the System

### Test 1: Audio Recording Transcription
1. Click **"Record Audio"** button
2. Speak something in English or Hindi
3. Stop recording and wait for transcription
4. Expected: Text appears in the note editor

**Fallback chain** (if primary fails):
- Try: Vakyansh API → Python Whisper → OpenAI Whisper

### Test 2: File Upload with Audio
1. Click **"Upload Audio"** button
2. Select an MP3, WAV, M4A, or WEBM file
3. Wait for processing
4. Expected: Transcribed text appears in editor

### Test 3: AI Refinement (Summarization)
1. Enter or paste text in the note editor
2. Click **"Refine with AI"** button
3. Expected: AI generates a concise summary
4. Result appears in the text area

### Test 4: Document Generation
1. Enter text in the note editor
2. Select a document type from dropdown (CV, Cover Letter, etc.)
3. Click **"Generate Document"** button
4. Expected: Formatted document appears below
5. Click **"Download PDF"** to save

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Browser (localhost:5173)         │
│         React Note Editor                │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌───────────────────┐  ┌────────────────────┐
│  Node.js Server   │  │  Python Backend    │
│  (localhost:5027) │  │  (localhost:5000)  │
│                   │  │                    │
│ - Routes          │  │ - Whisper          │
│ - File upload     │  │   (audio→text)     │
│ - Auth            │  │                    │
│ - Document CRUD   │  │ - T5-Large         │
│ - Proxy to Python │  │   (summarize)      │
└─────────┬─────────┘  │                    │
          │            │ - Document Gen     │
          │            │   (structure)      │
          └────────────┤                    │
                       └────────────────────┘
                               ▲
                       ┌───────┴──────────┐
                       │                  │
                  Vakyansh API       OpenAI API
               (Primary/Hindi)    (Fallback)
```

## Environment Variables

### Node Backend (.env in root)
```bash
# Already set in vite.config.ts
VITE_PYTHON_BACKEND_URL=http://localhost:5000
```

### Python Backend (.env in python-backend/)
```bash
# Optional - Flask configuration
FLASK_ENV=development
FLASK_DEBUG=1
```

## Common Issues & Solutions

### Issue 1: "Audio Processing Failed - All services unavailable"
**Causes:**
- Vakyansh API is down (it's free but unreliable)
- Python backend not running on port 5000
- OpenAI API key not set

**Solutions:**
```bash
# Ensure Python backend is running
cd python-backend && python app.py

# Test Python backend directly
curl -X POST http://localhost:5000/api/health

# Check if port 5000 is in use
# Windows: netstat -ano | findstr :5000
# Mac/Linux: lsof -i :5000
```

### Issue 2: "Refinement Failed - Unexpected token '<'"
**Cause:** Express endpoint returns 404 HTML instead of JSON

**Solution:** The fix has been committed to handle this. If still occurring:
```bash
# Verify routes.ts has the proxy endpoints
grep -n "python-backend/summarize" server/routes.ts

# Restart Node backend
npm run dev
```

### Issue 3: "Document Generation Failed"
**Cause:** Python backend unavailable or T5 model not loaded

**Solutions:**
```bash
# Check Python backend logs for model loading errors
# First time running? Model will download (~1.5GB for T5-Large)
# This can take 5-10 minutes

# Monitor Python process:
# Windows: Monitor python.exe in Task Manager
# Check memory usage during model download
```

### Issue 4: Port Already in Use
```bash
# Kill process using port 5027 (Node)
# Windows: taskkill /PID <PID> /F
# Mac/Linux: kill -9 <PID>

# Kill process using port 5000 (Python)
# Same commands as above
```

## Database Verification

```bash
# Connect to MySQL
mysql -u root -p

# List tables
USE reqgen;
SHOW TABLES;

# Expected tables:
# - users
# - documents
# - document_refinements
# - audit_logs
```

## Testing Checklist

- [ ] Node backend runs on http://localhost:5027
- [ ] Python backend runs on http://localhost:5000
- [ ] Can record audio and transcription works
- [ ] Can upload audio file
- [ ] Can refine text with AI
- [ ] Can generate document PDF
- [ ] Can download PDF file
- [ ] Can save document to database
- [ ] Can view saved documents

## Performance Notes

### First Run Model Downloads
- **T5-Large model**: ~1.5GB, takes 5-10 minutes to download on first run
- **Whisper model**: May download if needed

### Memory Requirements
- Node: ~300MB
- Python (with models): ~2GB during inference
- Total: ~3GB recommended

### Transcription Speed
- Audio: ~5-30 seconds depending on file length and fallback service
- Summarization: 1-3 seconds for T5-Large
- Document generation: 5-10 seconds

## Deployment to Render

After LOCAL testing is complete:

```bash
# Ensure all changes are committed and pushed
git status
git add .
git commit -m "Ready for Render deployment"
git push origin main

# Visit https://render.com and redeploy both services:
# 1. Main Node service: reqgen-20jan-12-05
# 2. Python service: reqgen-20jan-12-05-1
```

## File Locations Reference

```
Project Root
├── server/
│   ├── routes.ts          ← Node backend endpoints (INCLUDES PROXY)
│   └── index.ts
├── client/
│   └── src/pages/
│       └── note-editor.tsx ← React UI component
├── python-backend/
│   ├── app.py             ← Flask app with transcribe/summarize/generate
│   ├── document_generator.py ← T5 model wrapper
│   └── venv/              ← Virtual environment
├── database/
│   ├── schema.sql
│   └── setup.sql
└── package.json
```

## Quick Commands Reference

```bash
# Terminal 1: Node Backend
cd "c:\Users\sujay.palande\Downloads\Reqgen 20Jan-12-05"
npm run dev

# Terminal 2: Python Backend
cd "c:\Users\sujay.palande\Downloads\Reqgen 20Jan-12-05\python-backend"
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
python app.py

# Terminal 3: Database (if needed)
mysql -u root -p < database/COMPLETE_MYSQL_SETUP.sql
```

## Support Commands

```bash
# Check Node backend health
curl http://localhost:5027/api/health

# Check Python backend health
curl http://localhost:5000/api/health

# Check database connection
mysql -u root -p -e "SELECT VERSION();"

# View Node logs
# Check browser console: F12 → Console tab

# View Python logs
# Check Terminal 2 output in real-time
```

---

**Last Updated:** Jan 2025
**Status:** Complete and ready for use
**Latest Commit:** `2c80012` - Added missing proxy endpoints

