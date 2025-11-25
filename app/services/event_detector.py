"""
Event detection logic for stop/move transitions
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.models import Event
from app.config import settings


def detect_event_transition(
    current_speed: float,
    previous_state: str,
    stop_threshold: float = None
) -> Optional[str]:
    """
    Detect transition from previous state to current state
    
    Returns:
        'stop_started' if vehicle stopped
        'move_started' if vehicle started moving
        None if no transition
    """
    if stop_threshold is None:
        stop_threshold = settings.STOP_SPEED_THRESHOLD
    
    is_stopped = current_speed < stop_threshold
    
    if previous_state == "move" and is_stopped:
        return "stop_started"
    elif previous_state == "stop" and not is_stopped:
        return "move_started"
    
    return None


def create_or_update_event(
    db: Session,
    vehicle_id: str,
    driver_id: Optional[int],
    event_type: str,
    latitude: float,
    longitude: float,
    timestamp: datetime,
    metadata: Optional[dict] = None
) -> Event:
    """
    Create a new event in the database
    """
    event = Event(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        event_type=event_type,
        start_time=timestamp,
        latitude=latitude,
        longitude=longitude,
        metadata=metadata
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

