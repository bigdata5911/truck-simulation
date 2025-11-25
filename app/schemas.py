"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Webhook schemas
class SamsaraWebhookPayload(BaseModel):
    """Samsara webhook payload"""
    vehicleId: str
    driverId: Optional[str] = None
    timestamp: datetime
    latitude: float
    longitude: float
    speed: float = Field(ge=0)  # Speed in km/h
    heading: Optional[float] = None
    metadata: Optional[dict] = None


class TwilioInboundPayload(BaseModel):
    """Twilio inbound webhook payload"""
    MessageSid: str
    AccountSid: str
    From: str
    To: str
    Body: str
    NumMedia: Optional[str] = "0"


# Event schemas
class EventResponse(BaseModel):
    """Event response schema"""
    id: int
    driver_id: Optional[int]
    vehicle_id: str
    event_type: str
    start_time: datetime
    end_time: Optional[datetime]
    latitude: float
    longitude: float
    metadata: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """List of events response"""
    events: List[EventResponse]
    total: int
    page: int
    page_size: int


class MessageResponse(BaseModel):
    """Message response schema"""
    id: int
    event_id: Optional[int]
    driver_id: Optional[int]
    direction: str
    body: str
    twilio_sid: Optional[str]
    from_phone: str
    to_phone: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class EventDetailResponse(EventResponse):
    """Event detail with messages"""
    messages: List[MessageResponse] = []


# Auth schemas
class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    token_type: str = "bearer"

