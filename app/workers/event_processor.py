"""
Background worker to process events from SQS
"""

import asyncio
import json
import boto3
from sqlalchemy.orm import Session
from typing import Optional

from app.database import SessionLocal
from app.models import Driver, Event, Message
from app.config import settings
from app.services.slack import send_slack_notification

sqs = boto3.client('sqs', region_name=settings.AWS_REGION)
_running = False
_task: Optional[asyncio.Task] = None


async def process_event_message(message_body: str):
    """
    Process a single event message from SQS
    
    Creates SMS job and sends Slack notification
    """
    try:
        event_data = json.loads(message_body)
        event_id = event_data.get("event_id")
        driver_id = event_data.get("driver_id")
        vehicle_id = event_data.get("vehicle_id")
        latitude = event_data.get("latitude")
        longitude = event_data.get("longitude")
        timestamp = event_data.get("timestamp")
        
        db = SessionLocal()
        try:
            # Get event
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                print(f"Event {event_id} not found")
                return
            
            # Get driver
            driver = None
            if driver_id:
                driver = db.query(Driver).filter(Driver.id == driver_id).first()
            
            if not driver or not driver.phone:
                print(f"Driver {driver_id} not found or has no phone number")
                return
            
            # Compose SMS message
            sms_body = (
                f"DriverBuddy: Vehicle {vehicle_id} stopped at "
                f"{latitude:.4f},{longitude:.4f} at {timestamp}. "
                f"Reply to this SMS."
            )
            
            # Create outbound message record
            message = Message(
                event_id=event_id,
                driver_id=driver_id,
                direction="outbound",
                body=sms_body,
                from_phone=settings.TWILIO_NUMBER,
                to_phone=driver.phone,
                status="pending"
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            # Enqueue SMS job to SMS queue
            queue_url = sqs.get_queue_url(QueueName=settings.SQS_SMS_QUEUE)['QueueUrl']
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({
                    "message_id": message.id,
                    "to_phone": driver.phone,
                    "body": sms_body,
                    "event_id": event_id
                })
            )
            
            # Send Slack notification
            slack_message = (
                f"🚛 Vehicle {vehicle_id} stopped\n"
                f"Driver: {driver.name} ({driver.phone})\n"
                f"Location: {latitude:.4f}, {longitude:.4f}\n"
                f"Time: {timestamp}"
            )
            send_slack_notification(slack_message)
            
        finally:
            db.close()
    
    except Exception as e:
        print(f"Error processing event message: {e}")


async def poll_sqs_queue():
    """
    Poll SQS queue for event messages
    """
    queue_url = sqs.get_queue_url(QueueName=settings.SQS_EVENTS_QUEUE)['QueueUrl']
    
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
                    await process_event_message(msg['Body'])
                    # Delete message after successful processing
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=msg['ReceiptHandle']
                    )
                except Exception as e:
                    print(f"Error processing message: {e}")
                    # Message will become visible again after visibility timeout
                    # and will be retried (up to maxReceiveCount)
        
        except Exception as e:
            print(f"Error polling SQS queue: {e}")
            await asyncio.sleep(5)


async def start():
    """Start the event processor worker"""
    global _running, _task
    _running = True
    _task = asyncio.create_task(poll_sqs_queue())
    print("Event processor worker started")


def stop():
    """Stop the event processor worker"""
    global _running
    _running = False
    if _task:
        _task.cancel()

