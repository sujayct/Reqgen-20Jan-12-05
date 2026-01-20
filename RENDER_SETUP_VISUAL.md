# 📋 Render Setup Instructions - Step by Step

## What's the Problem?
Audio transcription on Render returns 503 "Service Unavailable" error

## What's the Solution?
Add **one** or **two** environment variables and redeploy

---

## ⚡ OPTION A: OpenAI Only (Easiest - 5 Minutes)

### Why Choose This?
- ✅ Fastest setup
- ✅ Most reliable
- ✅ Works immediately after redeploy
- ❌ Costs ~$0.006 per minute of audio

### Steps:

#### 1️⃣ Get API Key from OpenAI

**Go to**: https://platform.openai.com/api-keys

![OpenAI API Keys Page](https://raw.githubusercontent.com/openai/openai-python/main/README.svg)

**Steps**:
1. Log in (or create account)
2. Click "+ Create new secret key"
3. Name it "ReqGen Render"
4. Copy the key (e.g., `sk-proj-xxxxxxxxxxxx`)
5. Keep it safe!

#### 2️⃣ Add to Render Environment

**Go to**: https://dashboard.render.com > Your Service > Environment

**Steps**:
1. Scroll down to "Environment"
2. Click "Add Environment Variable"
3. Name: `OPENAI_API_KEY`
4. Value: Paste the key from Step 1
5. Click "Save"
6. Wait for auto-redeploy

#### 3️⃣ Test

**In your app**:
1. Go to Note Editor
2. Upload an audio file
3. Should work! ✅

---

## 🚀 OPTION B: Python Backend (Medium - 30 Minutes)

### Why Choose This?
- ✅ No transcription costs (uses your compute)
- ✅ Faster after deployment
- ❌ Takes longer to set up
- ❌ Cold start delays (30-50 seconds) on free tier

### Steps:

#### 1️⃣ Create Python Service on Render

**Go to**: https://dashboard.render.com

**Steps**:
1. Click "New +" button
2. Select "Web Service"
3. Choose your GitHub repository
4. Configuration:
   - **Name**: `reqgen-python-backend`
   - **Branch**: `main`
   - **Root Directory**: `python-backend`
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Free Plan** or **Starter Plan**
5. Click "Create Web Service"
6. Wait for deployment (2-5 minutes)

#### 2️⃣ Get Python Backend URL

**After deployment**:
1. Go to the new Python service
2. Copy the URL from top (e.g., `https://reqgen-python-backend.onrender.com`)
3. Save this URL

#### 3️⃣ Update Main ReqGen Service

**Go to**: Dashboard > ReqGen Service > Environment

**Steps**:
1. Add Environment Variable:
   - Name: `PYTHON_BACKEND_URL`
   - Value: Paste URL from Step 2
2. Click "Save"
3. Wait for redeploy

#### 4️⃣ Test

Same as Option A - upload audio file, should work!

---

## 🛡️ OPTION C: Both Services (Best - 30 Minutes)

### Why Choose This?
- ✅ Maximum reliability (two fallbacks)
- ✅ Lower costs (uses free Python first)
- ✅ Works even if one service is down
- ❌ Slightly more complex setup

### Steps:

#### 1️⃣ Do Option B (Python Backend) First
Follow all steps from Option B above

#### 2️⃣ Add OpenAI as Backup

In main ReqGen service Environment, add:
- Name: `OPENAI_API_KEY`
- Value: Your OpenAI key from Option A

#### 3️⃣ Redeploy

Service should auto-redeploy. Test to confirm!

---

## 📝 Environment Variables Cheat Sheet

### For Option A Only:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
```

### For Option B Only:
```
PYTHON_BACKEND_URL=https://reqgen-python-backend.onrender.com
```

### For Option C (Best):
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
PYTHON_BACKEND_URL=https://reqgen-python-backend.onrender.com
```

---

## 🔍 How to Add Environment Variables

### Method 1: Via Render Dashboard (Easy)

1. Go to https://dashboard.render.com
2. Click your service name
3. Scroll down to "Environment"
4. Click "Add Environment Variable" (blue button)
5. Enter Name and Value
6. Click "Save"
7. Service auto-redeploys

### Method 2: Via Render CLI (Advanced)

```bash
# Install Render CLI
npm install -g render

# Login to Render
render auth

# Set environment variable
render env set OPENAI_API_KEY=sk-xxxx
```

---

## ✅ Verify It Works

### Check 1: Service is Running
Go to Render Dashboard > Your Service
- Status should show "Live" (green)
- No error messages

### Check 2: Environment Variable Set
1. Go to Environment section
2. Scroll down - should see your variable
3. Value should start with `sk-` (if OpenAI)

### Check 3: Manual Test
1. Go to your ReqGen app
2. Note Editor page
3. Upload any audio file
4. Should transcribe successfully ✅

### Check 4: Check Logs
1. Render Dashboard > Your Service > Logs
2. Look for success messages:
   - "Fallback transcription successful via OpenAI"
   - "Secondary fallback transcription successful"

---

## 🐛 Troubleshooting

### Still Getting 503 Error?

#### Problem: "Service Unavailable"
**Solution**:
1. Verify environment variable is set (check spelling!)
2. Check service has redeployed (go to Deploys tab)
3. Wait 2-3 minutes for changes to take effect
4. Hard refresh browser (Ctrl+F5)

#### Problem: "Invalid API Key"
**Solution**:
1. Copy-paste key again (might have extra spaces)
2. Generate new key at openai.com
3. Verify it starts with `sk-`

#### Problem: Python Backend Returns Error
**Solution**:
1. Check if Python service is running (should be "Live")
2. Click Python service > Logs for errors
3. Might need to upgrade from Free tier

#### Problem: Still Doesn't Work?

**Debug Steps**:
1. Check Render logs: Dashboard > Service > Logs
2. Look for error messages
3. Search for "Fallback" or "Error" in logs
4. Copy the error and search for solution

---

## 💰 Cost Breakdown

### Option A: OpenAI Only
- **Setup Cost**: Free
- **Per Month**: Depends on usage
  - 1 hour audio/day = ~$5-10/month
  - 10 min audio/day = ~$0.50-$1/month
  - Occasional use = free (includes free tier)

### Option B: Python Backend
- **Setup Cost**: Free (time only)
- **Per Month**: 
  - Free tier: Limited compute hours (may stop after limit)
  - Starter tier: $7/month (continuous)
  - Usage: Zero per-minute charges

### Option C: Both
- **Best reliability**
- **Lower cost** (Python tries first)
- **Recommended** for production

---

## 🎯 Recommended Setup

For most users:
1. Use **Option A** (OpenAI only)
2. Fastest to set up
3. Most reliable
4. Low cost for typical usage
5. Upgrade to Option C later if needed

For power users:
1. Use **Option C** (Both)
2. Best reliability
3. Optimize for cost
4. Automatic failover

---

## 📚 More Information

- **Detailed Guide**: [RENDER_TRANSCRIPTION_FIX.md](./RENDER_TRANSCRIPTION_FIX.md)
- **General Fix**: [AUDIO_TRANSCRIPTION_FIX.md](./AUDIO_TRANSCRIPTION_FIX.md)
- **OpenAI Pricing**: https://openai.com/pricing
- **Render Docs**: https://render.com/docs

---

## ❓ FAQ

**Q: Do I need to code anything?**  
A: No! Just add environment variables and redeploy.

**Q: Will my audio be private?**  
A: Audio sent to transcription service (OpenAI/Python backend), not stored.

**Q: Can I change my mind?**  
A: Yes! Can switch options anytime by changing environment variables.

**Q: What if both services fail?**  
A: User sees helpful error message suggesting to retry.

**Q: How fast is transcription?**  
A: Usually 5-15 seconds for 1-minute audio.

---

**Status**: ✅ Ready for Render  
**Last Updated**: January 20, 2026
