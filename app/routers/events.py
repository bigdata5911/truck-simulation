"""
Events API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import Event, Message
from app.schemas import EventResponse, EventListResponse, EventDetailResponse, MessageResponse
from app.auth import get_current_user

router = APIRouter()


@router.get("", response_model=EventListResponse)
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vehicle_id: Optional[str] = None,
    driver_id: Optional[int] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user)  # Uncomment when auth is implemented
):
    """
    List events with pagination and filters
    """
    query = db.query(Event)
    
    # Apply filters
    if vehicle_id:
        query = query.filter(Event.vehicle_id == vehicle_id)
    if driver_id:
        query = query.filter(Event.driver_id == driver_id)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    events = query.order_by(Event.start_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return EventListResponse(
        events=[EventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user)  # Uncomment when auth is implemented
):
    """
    Get event details with associated messages
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get messages for this event
    messages = db.query(Message).filter(Message.event_id == event_id).order_by(Message.created_at).all()
    
    event_detail = EventDetailResponse.model_validate(event)
    event_detail.messages = [MessageResponse.model_validate(m) for m in messages]
    
    return event_detail

