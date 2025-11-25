"""
Background worker to send SMS messages via Twilio
"""

import asyncio
import json
import boto3
from sqlalchemy.orm import Session
from typing import Optional

from app.database import SessionLocal
from app.models import Message
from app.config import settings
from app.services.twilio_service import send_sms

sqs = boto3.client('sqs', region_name=settings.AWS_REGION)
_running = False
_task: Optional[asyncio.Task] = None


async def process_sms_message(message_body: str):
    """
    Process a single SMS message from SQS
    
    Sends SMS via Twilio and updates message record
    """
    try:
        sms_data = json.loads(message_body)
        message_id = sms_data.get("message_id")
        to_phone = sms_data.get("to_phone")
        body = sms_data.get("body")
        event_id = sms_data.get("event_id")
        
        db = SessionLocal()
        try:
            # Get message record
            message = db.query(Message).filter(Message.id == message_id).first()
            if not message:
                print(f"Message {message_id} not found")
                return
            
            # Send SMS via Twilio
            success, twilio_sid = send_sms(to_phone, body)
            
            if success and twilio_sid:
                message.twilio_sid = twilio_sid
                message.status = "sent"
                print(f"SMS sent successfully: {twilio_sid}")
            else:
                message.status = "failed"
                print(f"Failed to send SMS to {to_phone}")
            
            db.commit()
        
        finally:
            db.close()
    
    except Exception as e:
        print(f"Error processing SMS message: {e}")


async def poll_sqs_queue():
    """
    Poll SQS queue for SMS messages
    """
    queue_url = sqs.get_queue_url(QueueName=settings.SQS_SMS_QUEUE)['QueueUrl']
    
    while _running:
        try:
            # Receive messages from SQS
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,  # Long polling
                VisibilityTimeout=60
            )
            
            messages = response.get('Messages', [])
            for msg in messages:
                try:
                    await process_sms_message(msg['Body'])
                    # Delete message after successful processing
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=msg['ReceiptHandle']
                    )
                except Exception as e:
                    print(f"Error processing SMS message: {e}")
                    # Message will become visible again after visibility timeout
                    # and will be retried (up to maxReceiveCount)
        
        except Exception as e:
            print(f"Error polling SQS queue: {e}")
            await asyncio.sleep(5)


async def start():
    """Start the SMS worker"""
    global _running, _task
    _running = True
    _task = asyncio.create_task(poll_sqs_queue())
    print("SMS worker started")


def stop():
    """Stop the SMS worker"""
    global _running
    _running = False
    if _task:
        _task.cancel()

