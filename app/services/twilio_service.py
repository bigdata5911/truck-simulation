"""
Twilio SMS service
"""

from twilio.rest import Client
from typing import Optional, Tuple
from app.config import settings


def get_twilio_client() -> Optional[Client]:
    """
    Get Twilio client with credentials from environment variables
    
    Returns:
        Twilio Client instance or None if credentials not available
    """
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    
    if not account_sid or not auth_token:
        return None
    
    return Client(account_sid, auth_token)


def send_sms(to_phone: str, message_body: str) -> Tuple[bool, Optional[str]]:
    """
    Send SMS via Twilio
    
    Args:
        to_phone: Recipient phone number (E.164 format)
        message_body: SMS message text
    
    Returns:
        Tuple of (success: bool, message_sid: Optional[str])
    """
    client = get_twilio_client()
    if not client:
        print("Error: Twilio client not available. Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
        return False, None
    
    try:
        from_number = settings.TWILIO_NUMBER
        if not from_number:
            print("Error: Twilio phone number not configured. Set TWILIO_NUMBER environment variable")
            return False, None
        
        print(f"Attempting to send SMS from {from_number} to {to_phone}...")
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_phone
        )
        
        print(f"✓ SMS sent successfully! SID: {message.sid}")
        return True, message.sid
    
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Error sending SMS via Twilio: {error_msg}")
        
        # Provide helpful error messages
        if "not verified" in error_msg.lower() or "unverified" in error_msg.lower():
            print("  → Twilio trial accounts can only send to verified numbers.")
            print("  → Verify the number in Twilio Console or upgrade your account.")
        elif "invalid" in error_msg.lower() and "phone" in error_msg.lower():
            print("  → Phone number format is invalid. Use E.164 format: +1234567890")
        elif "insufficient" in error_msg.lower() or "balance" in error_msg.lower():
            print("  → Twilio account has insufficient balance.")
        
        return False, None

