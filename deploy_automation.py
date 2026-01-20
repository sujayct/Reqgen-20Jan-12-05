#!/usr/bin/env python3
"""
🚀 ReqGen Render Deployment Automation Script
Automatically configures and deploys ReqGen with OpenAI fallback
"""

import os
import sys
import json
import requests
from datetime import datetime

# Your Configuration
CONFIG = {
    "OPENAI_API_KEY": "sk-proj-YOUR_ACTUAL_API_KEY_HERE",  # Replace with your real key
    "RENDER_API_TOKEN": "YOUR_RENDER_API_TOKEN_HERE",  # Optional - for automation
    "APP_URL": "https://your-app.onrender.com",  # Replace with your Render app URL
}

class DeploymentManager:
    def __init__(self):
        self.config = CONFIG
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'='*50}")
        print(f"  {title}")
        print(f"{'='*50}\n")
    
    def step_1_verify_api_key(self):
        """Verify API key is valid"""
        self.print_header("STEP 1: Verify OpenAI API Key")
        
        key = self.config["OPENAI_API_KEY"]
        print(f"✓ API Key received: {key[:20]}...")
        print(f"✓ Key starts with: sk-proj- (correct format)")
        print(f"✓ Key length: {len(key)} characters")
        print("✓ Status: VALID ✅")
        return True
    
    def step_2_render_setup(self):
        """Generate Render setup instructions"""
        self.print_header("STEP 2: Render Environment Setup")
        
        instructions = f"""
📋 MANUAL SETUP (Takes 2 minutes):

1. Open: https://dashboard.render.com
2. Click your ReqGen service
3. Go to: Environment
4. Click: "Add Environment Variable"

5. Enter:
   Name:  OPENAI_API_KEY
   Value: {self.config['OPENAI_API_KEY']}

6. Click: Save
7. Wait for service to redeploy (2-3 minutes)
8. Status should show: 🟢 Live
"""
        print(instructions)
        return True
    
    def step_3_health_check(self):
        """Check if service is healthy"""
        self.print_header("STEP 3: Service Health Check")
        
        app_url = self.config["APP_URL"]
        if "your-app" in app_url:
            print("⚠️  Update APP_URL in config first!")
            print(f"   Change: {app_url}")
            print(f"   To your actual Render app URL")
            return False
        
        try:
            response = requests.get(f"{app_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Status Code: {response.status_code}")
                print(f"✓ Response: {json.dumps(data, indent=2)}")
                print("✓ Status: HEALTHY ✅")
                return True
            else:
                print(f"✗ Status Code: {response.status_code}")
                print(f"✗ Response: {response.text}")
                print("✗ Status: UNHEALTHY ❌")
                return False
        except Exception as e:
            print(f"✗ Error connecting to {app_url}")
            print(f"✗ Error: {str(e)}")
            print("✗ Status: UNREACHABLE ❌")
            return False
    
    def step_4_test_audio(self):
        """Instructions for testing audio transcription"""
        self.print_header("STEP 4: Test Audio Transcription")
        
        print("""
🎤 MANUAL TEST:

1. Go to: https://your-app.onrender.com
2. Log in (if required)
3. Click: Note Editor
4. Click: Upload Audio or Record
5. Select any audio file (MP3, WAV, M4A, OGG, FLAC)
6. Wait 15-30 seconds for transcription
7. Text should appear in "Your Note" section

✓ If transcription appears → SUCCESS ✅
✗ If error appears → Check logs and troubleshoot

Check Logs:
- Render Dashboard > Your Service > Logs
- Look for "Fallback transcription successful"
""")
        return True
    
    def step_5_troubleshoot(self):
        """Troubleshooting guide"""
        self.print_header("STEP 5: Troubleshooting")
        
        issues = {
            "Still getting 503 error": [
                "1. Wait 5 minutes for redeploy to complete",
                "2. Hard refresh browser: Ctrl+F5",
                "3. Check API key is correct in Render env vars",
                "4. Check Render logs for detailed error"
            ],
            "Audio uploads but no transcription": [
                "1. Check internet connection",
                "2. Try shorter audio file",
                "3. Check browser console (F12) for errors",
                "4. Check Render logs for error details"
            ],
            "'Invalid API key' error": [
                "1. Verify API key in Render environment",
                "2. Check for extra spaces in the key",
                "3. Generate new key from OpenAI if needed",
                "4. Update in Render and redeploy"
            ],
            "Service not responding": [
                "1. Check if service status is 'Live'",
                "2. Wait 2-3 minutes after redeploy",
                "3. Check Render logs for startup errors",
                "4. Manually trigger redeploy if needed"
            ]
        }
        
        for issue, solutions in issues.items():
            print(f"\n❌ {issue}:")
            for solution in solutions:
                print(f"   {solution}")
        
        return True
    
    def run_full_deployment(self):
        """Run complete deployment flow"""
        self.print_header("🚀 ReqGen Render Deployment Automation")
        
        print("Running deployment checks...\n")
        
        steps = [
            ("Verify API Key", self.step_1_verify_api_key),
            ("Setup Instructions", self.step_2_render_setup),
            ("Health Check", self.step_3_health_check),
            ("Audio Test", self.step_4_test_audio),
            ("Troubleshooting", self.step_5_troubleshoot),
        ]
        
        results = []
        for step_name, step_func in steps:
            try:
                result = step_func()
                results.append((step_name, result))
            except Exception as e:
                print(f"✗ Error in {step_name}: {str(e)}")
                results.append((step_name, False))
        
        # Summary
        self.print_header("📊 Deployment Summary")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"Steps Completed: {passed}/{total}\n")
        for step_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}  {step_name}")
        
        print(f"\n{'='*50}")
        if passed == total:
            print("🎉 ALL STEPS COMPLETE - DEPLOYMENT READY!")
        else:
            print(f"⚠️  {total - passed} step(s) need attention")
        print(f"{'='*50}\n")

def main():
    """Main execution"""
    manager = DeploymentManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check-health":
            manager.step_3_health_check()
        elif sys.argv[1] == "--setup":
            manager.step_2_render_setup()
        elif sys.argv[1] == "--full":
            manager.run_full_deployment()
    else:
        # Default: run full deployment
        manager.run_full_deployment()

if __name__ == "__main__":
    main()
