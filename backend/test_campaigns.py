import asyncio
import json
import httpx
from datetime import datetime

API_URL = "http://localhost:8000"

async def test_campaign_flow():
    async with httpx.AsyncClient() as client:
        # 1. Login to get token
        print("🔐 Logging in...")
        login_res = await client.post(
            f"{API_URL}/api/auth/login",
            data={"username": "demo@example.com", "password": "password123"}
        )
        
        if login_res.status_code != 200:
            print(f"❌ Login failed: {login_res.text}")
            # Try to register if login failed
            print("📝 Registering demo business...")
            await client.post(
                f"{API_URL}/api/auth/register",
                json={"email": "demo@example.com", "password": "password123", "business_name": "Demo Clinic"}
            )
            login_res = await client.post(
                f"{API_URL}/api/auth/login",
                data={"username": "demo@example.com", "password": "password123"}
            )
            
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Add some patients first
        print("👥 Adding a patient...")
        # Since patients are added via appointment service normally, we can just mock it or assume some exist
        # For this test, we'll use a direct phone number
        
        # 3. Create Campaign
        print("🚀 Creating WhatsApp Campaign...")
        campaign_data = {
            "name": "Health Check Reminder",
            "message_template": "Hello! This is a health check reminder from MedVoice AI.",
            "recipient_phones": ["+1234567890", "+0987654321"]
        }
        
        res = await client.post(
            f"{API_URL}/api/campaigns",
            json=campaign_data,
            headers=headers
        )
        
        if res.status_code != 200:
            print(f"❌ Campaign creation failed: {res.text}")
            return
            
        campaign = res.json()
        campaign_id = campaign["id"]
        print(f"✅ Campaign created: {campaign_id}")
        
        # 4. List Campaigns
        print("📋 Listing campaigns...")
        res = await client.get(f"{API_URL}/api/campaigns", headers=headers)
        print(f"✅ Found {len(res.json())} campaigns")
        
        # 5. Run Campaign
        print("⚡ Triggering campaign execution...")
        res = await client.post(f"{API_URL}/api/campaigns/{campaign_id}/run", headers=headers)
        print(f"✅ {res.json()['message']}")
        
        # 6. Check Status (wait a bit)
        print("⏳ Waiting for background processing...")
        await asyncio.sleep(2)
        
        res = await client.get(f"{API_URL}/api/campaigns/{campaign_id}", headers=headers)
        details = res.json()
        print(f"📊 Campaign Status: {details['campaign']['status']}")
        print(f"✅ Success: {details['campaign']['success_count']}, Failure: {details['campaign']['failure_count']}")
        
        for r in details['recipients']:
            print(f"   - {r['phone_number']}: {r['status']} ({r.get('message_sid', 'N/A')})")

if __name__ == "__main__":
    asyncio.run(test_campaign_flow())
