"""
Test SMS sending directly
Useful for debugging SMS issues without SQS
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.twilio_service import send_sms
from app.config import settings

def test_sms():
    """Test sending SMS directly"""
    print("Testing SMS sending...")
    print(f"Twilio Account SID: {settings.TWILIO_ACCOUNT_SID[:10]}..." if settings.TWILIO_ACCOUNT_SID else "Not configured")
    print(f"Twilio Auth Token: {'Set' if settings.TWILIO_AUTH_TOKEN else 'Not configured'}")
    print(f"Twilio Number: {settings.TWILIO_NUMBER}")
    print()
    
    # Test phone number (change this to your number)
    test_phone = input("Enter phone number to test (E.164 format, e.g., +17652590506): ").strip()
    if not test_phone:
        print("No phone number provided")
        return
    
    test_message = "Test message from DriverBuddy - SMS is working!"
    
    print(f"\nSending SMS to {test_phone}...")
    success, twilio_sid = send_sms(test_phone, test_message)
    
    if success:
        print(f"✓ SMS sent successfully!")
        print(f"Twilio Message SID: {twilio_sid}")
    else:
        print("✗ Failed to send SMS")
        print("\nCommon issues:")
        print("1. Twilio credentials not configured (check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER)")
        print("2. Phone number not verified (Twilio trial accounts can only send to verified numbers)")
        print("3. Invalid phone number format (must be E.164 format: +1234567890)")
        print("4. Twilio account has insufficient balance or restrictions")

if __name__ == "__main__":
    test_sms()

