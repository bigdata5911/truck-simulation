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
        return False, None
    
    try:
        from_number = settings.TWILIO_NUMBER
        if not from_number:
            print("Error: Twilio phone number not configured")
            return False, None
        
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_phone
        )
        
        return True, message.sid
    
    except Exception as e:
        print(f"Error sending SMS via Twilio: {e}")
        return False, None

