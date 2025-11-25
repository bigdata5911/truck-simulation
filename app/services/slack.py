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
        print("Warning: Slack webhook URL not configured")
        return False
    
    try:
        payload = {
            "text": message
        }
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending Slack notification: {e}")
        return False

