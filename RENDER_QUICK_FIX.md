# ⚡ Quick Fix Checklist - Render Audio Transcription

## The Problem
Audio transcription returns 503 error on your Render-hosted ReqGen app.

## The Solution
Add **one** environment variable and redeploy (5 minutes total)

---

## QUICKEST FIX (Recommended) ⭐

### Step 1: Get OpenAI API Key (2 minutes)
```
1. Go to: https://platform.openai.com/api-keys
2. Click: "Create new secret key"
3. Copy the key (looks like: sk-xxxxxxxxxxxxx)
4. Do NOT share this key with anyone
```

### Step 2: Add to Render (2 minutes)
```
1. Go to: https://dashboard.render.com
2. Click your ReqGen service
3. Go to: Settings > Environment (or just "Environment")
4. Click: "Add Environment Variable"
5. Name: OPENAI_API_KEY
6. Value: sk-xxxxxxxxxxxxx (paste from Step 1)
7. Click: Save
8. Wait for automatic redeploy (1-2 minutes)
```

### Step 3: Test (1 minute)
```
1. Go to your app: https://your-app.onrender.com
2. Try uploading an audio file
3. It should work now! ✅
```

---

## If Quick Fix Doesn't Work

### Check Render Logs
1. Go to Dashboard > Your Service
2. Click **Logs**
3. Look for any error messages
4. Share the error with support

### Verify Settings
- [ ] Environment variable name is exactly: `OPENAI_API_KEY`
- [ ] Value starts with `sk-` (your actual API key)
- [ ] Service has redeployed (check "Deploys" tab)
- [ ] No typos in the key

---

## ALTERNATIVE FIX: Use Python Backend

If you prefer not to use OpenAI:

### Step 1: Deploy Python Backend Service
```
1. https://dashboard.render.com
2. New > Web Service
3. Select your GitHub repo
4. Root directory: python-backend
5. Build: pip install -r requirements.txt
6. Start: python app.py
7. Create Service
8. Note the URL (e.g., https://xxx.onrender.com)
```

### Step 2: Add Python Backend URL to Main Service
```
1. Go to main ReqGen service
2. Settings > Environment
3. Add: PYTHON_BACKEND_URL = https://xxx.onrender.com
4. Save and redeploy
```

---

## BEST FIX: Use Both (Backup Plan)

Set both variables so you have two fallbacks:

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
PYTHON_BACKEND_URL=https://your-python-backend.onrender.com
```

---

## FAQ

**Q: Will audio transcription cost me money?**  
A: Yes, ~$0.006 per minute of audio with OpenAI. Very cheap.

**Q: What if I don't have an OpenAI account?**  
A: Create one free at https://platform.openai.com (requires credit card but free trial included)

**Q: Can I use Python backend instead?**  
A: Yes, see "ALTERNATIVE FIX" above

**Q: How long does it take?**  
A: 5 minutes for quickest fix, 30 minutes for full setup

**Q: Will my audio be uploaded to OpenAI servers?**  
A: Yes, temporarily for transcription only. Not stored. Check OpenAI privacy policy.

---

## Support

If it still doesn't work:
1. Check [RENDER_TRANSCRIPTION_FIX.md](./RENDER_TRANSCRIPTION_FIX.md) for detailed guide
2. Check Render logs for errors
3. Verify environment variables are set correctly
4. Check OpenAI account has available credits

---

**Last Updated**: January 20, 2026
