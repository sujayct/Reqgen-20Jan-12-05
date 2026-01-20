# ReqGen Audio Transcription Fix - Render Deployment Guide

## Problem
Audio transcription failing on Render with 503 error:
```
Error: Failed to connect to primary transcription service. The service might be down.
```

## Root Cause
On Render, the application uses a **three-tier transcription fallback system**:

1. **Vakyansh API** (Primary) - Indian languages support
2. **Python Whisper Backend** (Fallback 1) - Self-hosted on Render
3. **OpenAI Whisper API** (Fallback 2) - Cloud-based, requires API key

All three are currently unavailable, causing the 503 error.

## Solution for Render

### Option 1: Quick Fix - Use OpenAI Whisper API (Recommended)

This is the fastest solution that requires no infrastructure changes.

#### Step 1: Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-`)
4. Keep it safe - you'll need it in the next step

#### Step 2: Add to Render Environment Variables

**Via Render Dashboard:**
1. Go to your Render service dashboard
2. Click **Environment** (or **Settings** > **Environment**)
3. Click **Add Environment Variable**
4. Name: `OPENAI_API_KEY`
5. Value: Paste your API key from Step 1
6. Save and redeploy

**Via Render CLI:**
```bash
# If using Render CLI
render env set OPENAI_API_KEY=sk-your-api-key-here
```

#### Step 3: Redeploy
- Push a new commit, or
- Click **Redeploy** in Render dashboard
- Audio transcription will now use OpenAI Whisper automatically

**Cost**: ~$0.006 per minute of audio (very cheap)

---

### Option 2: Deploy Python Backend on Render

This enables the local Whisper fallback and is more cost-effective for heavy usage.

#### Step 1: Create a New Render Service for Python Backend

1. Go to https://dashboard.render.com
2. Click **New +** > **Web Service**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `reqgen-python-backend`
   - **Root Directory**: `python-backend` (or leave empty if in root)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:10000 app:app` (or `python app.py` for simple deployments)
   - **Environment**: Python 3.11
   - **Plan**: Free or Starter (depending on usage)

#### Step 2: Add Environment Variables to Python Service

In Render dashboard for the Python service:
```
HUGGINGFACE_TOKEN=your_huggingface_token
```

#### Step 3: Get Python Backend URL

Once deployed, you'll get a URL like:
```
https://reqgen-python-backend.onrender.com
```

#### Step 4: Update Main ReqGen Service

1. Go back to your main ReqGen service on Render
2. Go to **Environment** settings
3. Add/Update environment variable:
   - **Name**: `PYTHON_BACKEND_URL`
   - **Value**: `https://reqgen-python-backend.onrender.com` (your Python service URL)
4. Redeploy the main service

#### Step 5: Test

Upload an audio file - it should now work with the Python backend fallback.

---

### Option 3: Combine Both Solutions (Best for Production)

Use OpenAI as primary fallback + Python backend as secondary fallback for cost optimization.

#### Configuration:
```env
OPENAI_API_KEY=sk-your-api-key-here
PYTHON_BACKEND_URL=https://reqgen-python-backend.onrender.com
```

#### How it works:
1. Try Vakyansh API (free, but unreliable)
2. If fails → Try Python Whisper backend (costs you compute time on Render)
3. If fails → Try OpenAI Whisper API (pay per minute, ~$0.006/min)

---

## Environment Variables Summary

Add these to your Render service in **Environment** settings:

### For OpenAI Fallback (Option 1):
```env
OPENAI_API_KEY=sk-your-api-key-here
```

### For Python Backend Fallback (Option 2):
```env
PYTHON_BACKEND_URL=https://your-python-service.onrender.com
HUGGINGFACE_TOKEN=hf_your_token_here
```

### For Both (Option 3):
```env
OPENAI_API_KEY=sk-your-api-key-here
PYTHON_BACKEND_URL=https://your-python-service.onrender.com
HUGGINGFACE_TOKEN=hf_your_token_here
```

---

## Transcription Service Fallback Chain

The application now tries services in this order:

```
┌─────────────────────────────────────┐
│   Primary: Vakyansh API (Free)      │
│   Status: Unreliable                │
└────────────┬────────────────────────┘
             │ (if fails)
             ▼
┌─────────────────────────────────────┐
│   Fallback 1: Python Whisper        │
│   Status: Works if backend running  │
└────────────┬────────────────────────┘
             │ (if fails)
             ▼
┌─────────────────────────────────────┐
│   Fallback 2: OpenAI Whisper        │
│   Status: Reliable (requires API key)
└─────────────────────────────────────┘
```

---

## Testing After Setup

### Test 1: Health Check
```bash
curl https://your-reqgen.onrender.com/api/health
# Should return: {"status":"healthy",...}
```

### Test 2: Audio Upload
1. Go to your ReqGen app: `https://your-reqgen.onrender.com`
2. Navigate to **Note Editor**
3. Try uploading an audio file
4. Check browser console (F12) for success message

### Test 3: Check Render Logs
In Render dashboard:
1. Click your service
2. Go to **Logs**
3. Look for messages like:
   - `Fallback transcription successful via Python/Whisper` - Python backend worked
   - `Secondary fallback transcription successful via OpenAI Whisper` - OpenAI worked
   - Error messages indicating which service failed

---

## Cost Comparison

| Option | Setup Time | Monthly Cost | Reliability | Cold Starts |
|--------|-----------|--------------|-------------|------------|
| **Option 1: OpenAI Only** | 5 min | $0.50-$5 | ⭐⭐⭐⭐ | None |
| **Option 2: Python Backend** | 30 min | Free* | ⭐⭐⭐ | ⭐⭐⭐ |
| **Option 3: Both** | 30 min | Free-$5 | ⭐⭐⭐⭐⭐ | None |

*Free tier has limitations on compute hours

---

## Troubleshooting

### Still getting 503 error?

**Check 1: Verify Environment Variables**
```bash
# In Render dashboard, verify:
- NODE_ENV is set to production
- OPENAI_API_KEY or PYTHON_BACKEND_URL is set
- No typos in variable names
```

**Check 2: Check Render Logs**
1. Go to Render dashboard
2. Click your service → **Logs**
3. Look for error messages about which service failed
4. Check if Python backend service is running

**Check 3: Test OpenAI API Key**
```bash
# If using OpenAI fallback:
curl -X POST https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer sk-your-key" \
  -F "file=@audio.wav" \
  -F "model=whisper-1"
```

**Check 4: Verify Python Backend URL**
```bash
# If using Python backend fallback:
curl https://your-python-service.onrender.com/api/health
# Should return successful response
```

### Python Backend Cold Start Issues?

If Python backend is sleeping (free tier), it can take 30-50 seconds to wake up:
- Solution 1: Upgrade to **Starter** plan (continuous running)
- Solution 2: Use OpenAI fallback as primary (Option 1)
- Solution 3: Use paid tier with auto-scaling

### OpenAI Rate Limits?

If you hit OpenAI rate limits:
1. Check your OpenAI account usage: https://platform.openai.com/account/billing/limits
2. Set spending limits to prevent surprises
3. Consider upgrading OpenAI account if heavy usage
4. Use Python backend as primary (Option 2)

---

## Implementation Details

### Code Changes in server/routes.ts:

The backend now attempts transcription in this order:

```typescript
// 1. Try Vakyansh API (60 second timeout)
// 2. If error/timeout → Try Python Whisper (30 second timeout)
// 3. If error/timeout → Try OpenAI Whisper (if OPENAI_API_KEY set)
// 4. If all fail → Return 503 error
```

### Fallback Triggers:

- **On Network Error**: Immediately tries next service
- **On Timeout**: After service timeout, tries next service
- **On HTTP 503/502/504**: Server error, tries fallback
- **On HTTP 400/401/403**: Client error, returns error to user

---

## Next Steps

1. **Choose an option** (1, 2, or 3 above)
2. **Set up environment variables** in Render dashboard
3. **Redeploy** your service
4. **Test** audio transcription
5. **Monitor** Render logs for issues

## Resources

- [Render Environment Variables](https://render.com/docs/environment-variables)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [OpenAI Whisper Pricing](https://openai.com/pricing)
- [Python Backend Setup](./PYTHON_SETUP.md)
- [Original Fix Documentation](./AUDIO_TRANSCRIPTION_FIX.md)

---

**Last Updated**: January 20, 2026  
**Status**: ✅ Fixed for Render deployments with triple fallback system
