import asyncio
import os
import sys
from dotenv import load_dotenv
from app.utils.safe_print import safe_print as print

# Add the project root to sys.path
sys.path.append(os.getcwd())

load_dotenv()

async def main():
    from app.services.twilio_service import TwilioService
    
    number = "8801260321"
    # Ensure it has E.164 format
    if not number.startswith('+'):
        number = "+91" + number
        
    twilio = TwilioService()
    
    # Use the dynamic backend URL from environment
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    # Using the verified business ID from the database
    business_id = "c39a32dd-3045-4a1e-8265-a21315b9427d"
    callback_url = f"{base_url}/api/twilio/outbound-answer?business_id={business_id}"
    
    print(f"🚀 Triggering outbound AI flow for: {number}")
    print(f"🔗 Callback URL: {callback_url}")
    
    # Call the service directly
    call_sid = await twilio.initiate_outbound_call(
        to_phone=number,
        callback_url=callback_url
    )
    
    if call_sid:
        print(f"✅ Flow triggered! Call SID: {call_sid}")
    else:
        print("❌ Flow trigger failed.")

if __name__ == "__main__":
    asyncio.run(main())
