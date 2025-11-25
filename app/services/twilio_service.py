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


def send_sms(to_phone: str, message_body: str, status_callback_url: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Send SMS via Twilio
    
    Args:
        to_phone: Recipient phone number (E.164 format)
        message_body: SMS message text
        status_callback_url: Optional URL for status callbacks (for delivery status updates)
    
    Returns:
        Tuple of (success: bool, message_sid: Optional[str])
        
    Note: For virtual-to-virtual messaging, Twilio may return a message SID
    even if status shows as "failed" on sender side. The message may still
    be delivered on recipient side. Use status callbacks to track actual delivery.
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
        
        # Build message parameters
        message_params = {
            "body": message_body,
            "from_": from_number,
            "to": to_phone
        }
        
        # Add status callback if provided and valid
        # This allows us to track delivery status updates
        # Note: Invalid callback URLs can cause Twilio to reject the message
        if status_callback_url:
            # Validate that it's a proper HTTP/HTTPS URL
            if status_callback_url.startswith(('http://', 'https://')):
                message_params["status_callback"] = status_callback_url
                print(f"  Status callback URL: {status_callback_url}")
            else:
                print(f"  Warning: Invalid status callback URL format, skipping: {status_callback_url}")
        
        message = client.messages.create(**message_params)
        
        # If we got a message SID, Twilio accepted the message
        # For virtual-to-virtual, this means it was processed even if status shows differently
        print(f"✓ SMS accepted by Twilio! SID: {message.sid}")
        print(f"  Status: {message.status}")
        print(f"  Note: For virtual-to-virtual numbers, status may show differently on each side")
        print(f"  Use status callbacks to track actual delivery status")
        
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

