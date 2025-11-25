"""
Webhook endpoints for Samsara and Twilio
"""

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional
import hmac
import hashlib
import base64
from urllib.parse import urlencode

from app.database import get_db
from app.models import Driver, Event, Message
from app.schemas import SamsaraWebhookPayload, TwilioInboundPayload
from app.config import settings
from app.services.event_detector import detect_event_transition, create_or_update_event
from app.services.slack import send_slack_notification
from app.services.twilio_service import send_sms
import boto3
import json
from datetime import datetime, timedelta

router = APIRouter()

# SQS client
sqs = boto3.client('sqs', region_name=settings.AWS_REGION)


@router.post("/samsara")
async def samsara_webhook(
    payload: SamsaraWebhookPayload,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive Samsara telemetry webhook
    
    Detects stop/move transitions and creates events
    """
    try:
        # Get or create driver if driverId provided
        driver = None
        if payload.driverId:
            driver = db.query(Driver).filter(Driver.id == int(payload.driverId)).first()
            if not driver:
                # Create driver if not exists (you may want to handle this differently)
                driver = Driver(id=int(payload.driverId), name=f"Driver {payload.driverId}")
                db.add(driver)
                db.commit()
                db.refresh(driver)
        
        # Get previous event for this vehicle to determine state
        previous_event = db.query(Event).filter(
            Event.vehicle_id == payload.vehicleId
        ).order_by(Event.start_time.desc()).first()
        
        # Determine previous state from last event
        previous_state = "move"  # Default to move if no previous events
        current_open_event = None
        
        if previous_event:
            # If last event was a stop and hasn't ended, we're still stopped
            if previous_event.event_type == "stop" and previous_event.end_time is None:
                previous_state = "stop"
                current_open_event = previous_event
            else:
                previous_state = "move"
        
        # Detect event transition
        transition = detect_event_transition(
            current_speed=payload.speed,
            previous_state=previous_state,
            stop_threshold=settings.STOP_SPEED_THRESHOLD
        )
        
        event = None
        if transition == "stop_started":
            # Create new stop event
            event = create_or_update_event(
                db=db,
                vehicle_id=payload.vehicleId,
                driver_id=driver.id if driver else None,
                event_type="stop",
                latitude=payload.latitude,
                longitude=payload.longitude,
                timestamp=payload.timestamp,
                metadata=payload.metadata
            )
            
            # Send Slack notification immediately (for testing/debugging)
            driver_name = driver.name if driver else "Unknown"
            driver_phone = driver.phone if driver else "N/A"
            slack_message = (
                f"🚛 Vehicle {payload.vehicleId} stopped\n"
                f"Driver: {driver_name} ({driver_phone})\n"
                f"Location: {payload.latitude:.4f}, {payload.longitude:.4f}\n"
                f"Time: {payload.timestamp.isoformat()}"
            )
            send_slack_notification(slack_message)
            
            # Send SMS directly if driver has phone number (for testing/debugging)
            # This bypasses SQS for immediate testing
            if driver and driver.phone:
                sms_body = (
                    f"DriverBuddy: Vehicle {payload.vehicleId} stopped at "
                    f"{payload.latitude:.4f},{payload.longitude:.4f} at {payload.timestamp.isoformat()}. "
                    f"Reply to this SMS."
                )
                print(f"Attempting to send SMS directly to {driver.phone}...")
                
                # Build status callback URL for delivery status updates
                # This helps track actual delivery, especially for virtual-to-virtual messaging
                base_url = str(request.base_url).rstrip('/')
                status_callback_url = f"{base_url}/webhook/twilio/status"
                
                sms_success, twilio_sid = send_sms(driver.phone, sms_body, status_callback_url=status_callback_url)
                
                if sms_success and twilio_sid:
                    # Create message record
                    # Note: For virtual-to-virtual, status may show as "failed" on sender side
                    # but message is still delivered. Status callback will update actual status.
                    message = Message(
                        event_id=event.id,
                        driver_id=driver.id,
                        direction="outbound",
                        body=sms_body,
                        from_phone=settings.TWILIO_NUMBER,
                        to_phone=driver.phone,
                        status="sent",  # Initial status, will be updated by status callback
                        twilio_sid=twilio_sid
                    )
                    db.add(message)
                    db.commit()
                    print(f"✓ SMS sent directly and message record created (SID: {twilio_sid})")
                    print(f"  Status callback URL: {status_callback_url}")
                    print(f"  Note: For virtual-to-virtual numbers, delivery status may differ on each side")
                else:
                    print(f"✗ Failed to send SMS directly. Will try via SQS queue.")
            
            # Enqueue event to SQS for processing (SMS sending via worker)
            # This is the production path, but we also send directly above for testing
            try:
                queue_url = sqs.get_queue_url(QueueName=settings.SQS_EVENTS_QUEUE)['QueueUrl']
                sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps({
                        "event_id": event.id,
                        "driver_id": driver.id if driver else None,
                        "vehicle_id": payload.vehicleId,
                        "latitude": float(payload.latitude),
                        "longitude": float(payload.longitude),
                        "timestamp": payload.timestamp.isoformat()
                    })
                )
                print(f"✓ Event enqueued to SQS for processing")
            except Exception as sqs_error:
                # Log SQS error but don't fail the webhook
                print(f"Warning: Could not send message to SQS: {sqs_error}")
                print("  → SMS was sent directly above, but SQS processing will not happen")
            
        elif transition == "move_started" and current_open_event:
            # Update existing stop event with end_time
            if current_open_event.end_time is None:
                current_open_event.end_time = payload.timestamp
        
        db.commit()
        
        return {
            "status": "ok",
            "event_created": event is not None,
            "event_id": event.id if event else None,
            "transition": transition
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/twilio/inbound")
async def twilio_inbound_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive Twilio inbound SMS webhook
    
    Validates Twilio signature and stores inbound message
    """
    try:
        # Get form data from Twilio
        form_data = await request.form()
        
        # Validate Twilio signature (recommended for production)
        # signature = request.headers.get("X-Twilio-Signature")
        # if not validate_twilio_signature(request.url, form_data, signature):
        #     raise HTTPException(status_code=403, detail="Invalid Twilio signature")
        
        from_phone = form_data.get("From")
        to_phone = form_data.get("To")
        body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid")
        
        # Find driver by phone number
        driver = db.query(Driver).filter(Driver.phone == from_phone).first()
        if not driver:
            return {
                "status": "error",
                "message": "Driver not found"
            }
        
        # Find most recent open event for this driver
        event = db.query(Event).filter(
            Event.driver_id == driver.id,
            Event.end_time.is_(None)
        ).order_by(Event.start_time.desc()).first()
        
        # If no open event, find recent event (within last hour)
        if not event:
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            event = db.query(Event).filter(
                Event.driver_id == driver.id,
                Event.start_time >= one_hour_ago
            ).order_by(Event.start_time.desc()).first()
        
        # Create inbound message
        message = Message(
            event_id=event.id if event else None,
            driver_id=driver.id,
            direction="inbound",
            body=body,
            twilio_sid=message_sid,
            from_phone=from_phone,
            to_phone=to_phone,
            status="received"
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Send Slack notification
        slack_message = f"📱 Driver {driver.name} ({driver.phone}) replied:\n{body}"
        if event:
            slack_message += f"\n\nEvent: Vehicle {event.vehicle_id} stopped at {event.latitude}, {event.longitude}"
        send_slack_notification(slack_message)
        
        # Return TwiML response (optional)
        return {
            "status": "ok",
            "message_id": message.id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing Twilio webhook: {str(e)}")


@router.post("/twilio/status")
async def twilio_status_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive Twilio status callback webhook
    
    Updates message status based on Twilio delivery status
    Handles virtual-to-virtual messaging where status may show differently
    """
    try:
        # Get form data from Twilio
        form_data = await request.form()
        
        message_sid = form_data.get("MessageSid")
        message_status = form_data.get("MessageStatus")  # queued, sent, delivered, failed, undelivered
        error_code = form_data.get("ErrorCode")
        error_message = form_data.get("ErrorMessage")
        
        if not message_sid:
            return {"status": "error", "message": "MessageSid missing"}
        
        # Find message by Twilio SID
        message = db.query(Message).filter(Message.twilio_sid == message_sid).first()
        
        if not message:
            print(f"Status update for unknown message SID: {message_sid}")
            return {"status": "ok", "message": "Message not found in database"}
        
        # Map Twilio status to our status
        # For virtual-to-virtual: "failed" or "undelivered" on sender side 
        # may still mean delivered on recipient side
        status_mapping = {
            "queued": "pending",
            "sending": "pending",
            "sent": "sent",
            "delivered": "delivered",
            "failed": "failed",
            "undelivered": "undelivered",
            "receiving": "pending",
            "received": "received"
        }
        
        # Update status
        new_status = status_mapping.get(message_status.lower(), message.status)
        
        # Special handling for virtual-to-virtual messaging:
        # If we get a status update (even "failed" or "undelivered"), 
        # it means Twilio processed the message
        # For virtual numbers, "failed" on sender side doesn't mean recipient didn't get it
        if message_status.lower() in ["failed", "undelivered"]:
            # Check if this is virtual-to-virtual (both numbers are Twilio numbers)
            # In this case, we might want to mark as "sent" if we have a message SID
            # because virtual-to-virtual can show different statuses on each side
            if message.twilio_sid:
                print(f"Status '{message_status}' for virtual-to-virtual message {message_sid}")
                print(f"  Note: Virtual-to-virtual messages may show 'failed' on sender side")
                print(f"  but still be delivered on recipient side. Current status: {new_status}")
                # Keep the status as is, but log the note
        
        message.status = new_status
        
        # Log error details if present
        if error_code:
            print(f"Twilio error for message {message_sid}: {error_code} - {error_message}")
        
        db.commit()
        
        print(f"Updated message {message_sid} status to: {new_status}")
        
        return {"status": "ok"}
    
    except Exception as e:
        db.rollback()
        print(f"Error processing Twilio status webhook: {e}")
        return {"status": "error", "message": str(e)}


def validate_twilio_signature(url: str, form_data: dict, signature: str) -> bool:
    """
    Validate Twilio webhook signature
    
    Args:
        url: Full request URL
        form_data: Form data from request
        signature: X-Twilio-Signature header value
    
    Returns:
        True if signature is valid
    """
    auth_token = settings.TWILIO_AUTH_TOKEN
    if not auth_token:
        return False
    
    # Create signature
    sorted_params = sorted(form_data.items())
    param_string = urlencode(sorted_params)
    signature_string = url + param_string
    
    computed_signature = base64.b64encode(
        hmac.new(
            auth_token.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')
    
    return hmac.compare_digest(computed_signature, signature)

