# Troubleshooting Guide - Audio Transcription & Document Processing Errors

## Quick Error Reference

| Error | Root Cause | Solution |
|-------|-----------|----------|
| "Audio Processing Failed - All services unavailable (503)" | Vakyansh down, Python backend not running, no OpenAI key | Start Python backend or add OpenAI API key |
| "Refinement Failed - Unexpected token '<'" | Missing Express proxy endpoint (returns 404 HTML) | ✅ FIXED in commit 2c80012 - restart Node |
| "JSON.parse: unexpected character" | Backend returning HTML instead of JSON | Endpoints now properly proxied |
| "TypeError: Cannot read property 'transcription'" | API returned error object instead of expected data | Check server logs for error details |

---

## Error 1: Audio Processing Failed (503)

### What You See
```
Audio Processing Failed
All services are currently unavailable
```

### Root Cause Analysis
The audio transcription tries these services in order:
1. **Vakyansh API** (Indian ASR, free but unreliable)
2. **Python Whisper Backend** (requires running locally on :5000)
3. **OpenAI Whisper** (requires API key in environment)

When ALL fail → 503 error

### Solution Checklist

#### ✅ Step 1: Verify Python Backend is Running
```bash
# Terminal 2 - Check if Flask is actually running
# Should show:
#  * Running on http://localhost:5000
#  * Press CTRL+C to quit

# If not running, start it:
cd python-backend
venv\Scripts\activate
python app.py
```

#### ✅ Step 2: Test Python Backend Directly
```bash
# From another terminal, test the transcription endpoint
# First, create a test audio file or use an existing one
# Then:

curl -X POST http://localhost:5000/api/transcribe \
  -F "audio=@path/to/test.wav"

# Should return: {"transcript": "...", "language": "..."}
# If it fails, check Python logs for the error
```

#### ✅ Step 3: Verify Ports Not in Use
```bash
# Windows - check what's using port 5000
netstat -ano | findstr :5000

# If something is using it, kill it:
taskkill /PID <PID> /F

# Then restart Python backend:
python app.py
```

#### ✅ Step 4: Add OpenAI API Key (Optional Backup)
```bash
# On Windows, set environment variable for Node backend:
# This allows fallback to OpenAI if Python backend is also down

# Option A: Temporarily in terminal (lasts until terminal closes)
set OPENAI_API_KEY=sk-proj-YourKeyHere

# Option B: Set permanently in System Environment Variables
# 1. Right-click "This PC" → Properties
# 2. Advanced system settings → Environment Variables
# 3. New → OPENAI_API_KEY = sk-proj-...
# 4. Restart terminal/app
```

#### ✅ Step 5: Verify Python Dependencies
```bash
# Check if all required packages are installed
python -m pip list | findstr "librosa torch transformers"

# If any missing, install:
pip install librosa torch torchaudio transformers

# For CUDA (GPU) support (optional, faster):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### How to Debug Further

**Check Node Backend Logs:**
```bash
# In browser, open Developer Console (F12)
# Filter for "transcription" messages
# Look for the error details

# Example logs:
// "Vakyansh fetch failed, attempting fallback: network error"
// "Attempting fallback transcription via Python backend..."
// "Fallback 1 (Python backend) failed: connect ECONNREFUSED 127.0.0.1:5000"
```

**Check Python Backend Logs:**
```bash
# In Terminal 2 where Python is running, look for:
# "Transcribing audio: ..."
# "Model loaded"
# Any error tracebacks

# If model is downloading:
# "Downloading model..."
# "Model downloaded: 1.5GB file"
# This is normal and takes 5-10 minutes first time
```

---

## Error 2: Refinement Failed - JSON Parse Error

### What You See
```
Refinement Failed
SyntaxError: Unexpected token '<', "<!DOCTYPE html>" is not valid JSON
```

### Root Cause Analysis
- Client sends POST to `/api/python-backend/summarize`
- Express server had NO endpoint for this (returned 404 HTML page)
- JavaScript tried to `JSON.parse(response)` on HTML
- Parser fails: "Expected JSON, got HTML"

### Solution ✅ FIXED

This issue is now **FIXED** in commit `2c80012`.

**If still seeing this error after latest code:**

```bash
# 1. Pull the latest changes
git pull origin main

# 2. Check that routes.ts has the new endpoints
grep -n "python-backend/summarize" server/routes.ts
# Should show line 354 (or nearby)

# 3. Restart Node backend
npm run dev

# 4. Clear browser cache (Ctrl+Shift+Delete)
# Then refresh (Ctrl+F5)
```

### Verify the Fix

```bash
# Test the endpoint directly:
curl -X POST http://localhost:5027/api/python-backend/summarize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world this is a test"}'

# Should return JSON, NOT HTML:
# {"summary": "Hello world test"}
# NOT:
# <!DOCTYPE html><html>...
```

---

## Error 3: Document Generation Failed

### What You See
```
Document Generation Failed
Cannot read property '...' of undefined
```

### Root Cause Analysis
- Similar to refinement: endpoint `/api/python-backend/generate-document` didn't exist
- Or: Python backend crashed during document generation
- Or: Python T5 model failed to load

### Solution Checklist

#### ✅ Step 1: Verify Endpoint Exists
```bash
# Restart Node backend with latest code
git pull origin main
npm run dev
```

#### ✅ Step 2: Check Python Logs
```bash
# Terminal 2 - Watch for model loading messages:
# "Loading T5-Large model..."
# "Model loaded successfully"
# "Generating document..."

# If you see errors like:
# "Model loading failed: out of memory"
# → Your system has insufficient RAM (need 3GB+)

# If you see:
# "CUDA out of memory"
# → Disable GPU by setting in python-backend/.env:
# DEVICE=cpu  # Force CPU instead of GPU
```

#### ✅ Step 3: Test Document Generation Endpoint
```bash
curl -X POST http://localhost:5027/api/python-backend/generate-document \
  -H "Content-Type: application/json" \
  -d '{
    "text": "John Doe worked at XYZ company for 5 years",
    "document_type": "cv"
  }'

# Should return: {"document": "...formatted content..."}
```

#### ✅ Step 4: Clear Python Model Cache
```bash
# If model is corrupted, clear cache:
# Navigate to Python model cache directory and delete it

# Windows:
del %USERPROFILE%\.cache\huggingface\transformers\*
# Or manually delete: C:\Users\YourUsername\.cache\huggingface\transformers\

# Linux/Mac:
rm -rf ~/.cache/huggingface/transformers/

# Then restart Python backend (it will redownload):
python app.py
```

---

## Error 4: "Cannot connect to Python backend"

### What You See
```
Error: connect ECONNREFUSED 127.0.0.1:5000
```

### Solutions

```bash
# Check if Python is running
netstat -ano | findstr :5000

# If no process shown, start Python backend:
cd python-backend
python app.py

# Check for common Python startup errors:
# "ModuleNotFoundError: No module named 'flask'"
# → Run: pip install flask flask-cors

# "Permission denied"
# → Run terminal as Administrator (Windows) or use sudo (Mac/Linux)

# "Address already in use"
# → Kill existing process:
netstat -ano | findstr :5000
# Note the PID, then:
taskkill /PID <PID> /F
# Restart Python
```

---

## Error 5: Model Not Loading / "Out of Memory"

### What You See
In Terminal 2 (Python):
```
OutOfMemoryError: CUDA out of memory
RuntimeError: Model failed to load
```

### Solutions

#### Option 1: Use Smaller Model (Faster, Less Memory)
```bash
# Edit python-backend/document_generator.py
# Change line 37 from:
# model_name = "google/flan-t5-large"
# To:
model_name = "google/flan-t5-base"

# Or even smaller:
model_name = "google/flan-t5-small"

# Restart Python backend
python app.py
```

#### Option 2: Use CPU Instead of GPU
```bash
# Create python-backend/.env
echo DEVICE=cpu > .env

# Restart Python
python app.py
```

#### Option 3: Increase System RAM
- Close other applications
- Consider upgrading RAM (minimum 8GB, recommend 16GB)

---

## Complete Diagnostic Script

Run this to check everything:

```bash
# Create check_system.bat on Windows
@echo off
echo === System Diagnostics ===

echo.
echo 1. Checking Node backend on :5027
curl -s http://localhost:5027/api/health || echo "❌ Node backend not responding"

echo.
echo 2. Checking Python backend on :5000
curl -s http://localhost:5000/api/health || echo "❌ Python backend not responding"

echo.
echo 3. Checking ports
netstat -ano | findstr ":5000\|:5027\|:3306"

echo.
echo 4. Checking MySQL connection
mysql -u root -p -e "SELECT VERSION();" 2>nul || echo "❌ MySQL not available"

echo.
echo 5. Checking Python packages
python -m pip list | findstr "flask transformers torch"

pause
```

---

## Prevention: Proper Shutdown & Restart

### Daily Startup Sequence
```bash
# Terminal 1: MySQL (if not already running)
# Start XAMPP or MySQL service

# Terminal 2: Node Backend
cd "c:\Users\sujay.palande\Downloads\Reqgen 20Jan-12-05"
npm run dev
# Wait for "Server running on port 5027"

# Terminal 3: Python Backend
cd python-backend
python app.py
# Wait for " * Running on http://localhost:5000"

# Terminal 4: Browser
# Open http://localhost:5173 and test
```

### Proper Shutdown Sequence
```bash
# Close browser first
# Terminal 3: Press Ctrl+C (stop Python)
# Terminal 2: Press Ctrl+C (stop Node)
# Terminal 1: Restart MySQL or just close
```

---

## Quick Health Check

```bash
# Run this in PowerShell before troubleshooting:

Write-Host "=== REQGEN HEALTH CHECK ===" -ForegroundColor Green

# Check Node backend
$node = Test-Connection -ComputerName localhost -TcpPort 5027 -ErrorAction SilentlyContinue
Write-Host "Node Backend (5027): $(if($node) {'✅ OK'} else {'❌ DOWN'})"

# Check Python backend  
$python = Test-Connection -ComputerName localhost -TcpPort 5000 -ErrorAction SilentlyContinue
Write-Host "Python Backend (5000): $(if($python) {'✅ OK'} else {'❌ DOWN'})"

# Check MySQL
$mysql = Test-Connection -ComputerName localhost -TcpPort 3306 -ErrorAction SilentlyContinue
Write-Host "MySQL (3306): $(if($mysql) {'✅ OK'} else {'❌ DOWN'})"

# Check git status
Write-Host "`nGit Status:"
git status | Select-String "On branch|Your branch|nothing to commit|modified|Untracked"
```

---

## Emergency Reset

If everything is completely broken:

```bash
# 1. Kill all processes
taskkill /F /IM node.exe 2>nul
taskkill /F /IM python.exe 2>nul

# 2. Clear npm cache
npm cache clean --force

# 3. Reinstall dependencies
rm -r node_modules package-lock.json
npm install

# 4. Restart from scratch
npm run dev
# And in another terminal:
python -m app
```

---

**Last Updated:** January 2025  
**Status:** Endpoints FIXED and deployed  
**Commit:** 2c80012
