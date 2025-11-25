"""
Slack notification service
"""

import requests
from app.config import settings


def send_slack_notification(message: str) -> bool:
    """
    Send notification to Slack via webhook
    
    Args:
        message: Message text to send
    
    Returns:
        True if successful, False otherwise
    """
    webhook_url = settings.SLACK_WEBHOOK_URL
    if not webhook_url:
        print("Warning: Slack webhook URL not configured. Set SLACK_WEBHOOK_URL environment variable.")
        return False
    
    try:
        payload = {
            "text": message
        }
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
        print(f"✓ Slack notification sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending Slack notification: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return False
    except Exception as e:
        print(f"Unexpected error sending Slack notification: {e}")
        return False

