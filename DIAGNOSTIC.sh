#!/bin/bash
# 🔍 DIAGNOSTIC SCRIPT - Check Deployment Status

echo "==========================================="
echo "  ReqGen Render Deployment Diagnostics"
echo "==========================================="
echo ""

# Check 1: Service Status
echo "1️⃣  CHECKING SERVICE STATUS..."
echo "   Go to: https://dashboard.render.com"
echo "   Check if service shows: 🟢 Live"
echo ""

# Check 2: Environment Variables
echo "2️⃣  CHECKING ENVIRONMENT VARIABLES..."
echo "   Dashboard > Environment"
echo "   Should see:"
echo "   - OPENAI_API_KEY (starts with sk-proj-)"
echo ""

# Check 3: Logs
echo "3️⃣  CHECKING LOGS FOR ERRORS..."
echo "   Dashboard > Service > Logs"
echo "   Look for:"
echo "   - 'Fallback transcription successful' ✅"
echo "   - 'Error' or 'Failed' ❌"
echo ""

# Check 4: Test Endpoint
echo "4️⃣  TESTING HEALTH ENDPOINT..."
echo "   Run in terminal or browser:"
echo "   curl https://your-app.onrender.com/api/health"
echo ""

# Check 5: Audio Upload Test
echo "5️⃣  TESTING AUDIO TRANSCRIPTION..."
echo "   1. Go to your app"
echo "   2. Note Editor page"
echo "   3. Upload audio file"
echo "   4. Wait 15-30 seconds"
echo "   5. Text should appear"
echo ""

echo "==========================================="
echo "  REPORT ERRORS YOU SEE BELOW:"
echo "==========================================="
echo ""
echo "Error 1: _____________________________"
echo "Error 2: _____________________________"
echo "Error 3: _____________________________"
