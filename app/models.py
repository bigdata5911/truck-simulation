"""
SQLAlchemy database models
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Numeric, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Driver(Base):
    """Driver model"""
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text)
    phone = Column(Text, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    events = relationship("Event", back_populates="driver")
    messages = relationship("Message", back_populates="driver")


class Event(Base):
    """Event model (stop/move events)"""
    __tablename__ = "events"
    
    id = Column(BigInteger, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    vehicle_id = Column(Text, index=True)
    event_type = Column(Text)  # 'stop', 'move', etc
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True), nullable=True)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    driver = relationship("Driver", back_populates="events")
    messages = relationship("Message", back_populates="event")


class Message(Base):
    """SMS message model"""
    __tablename__ = "messages"
    
    id = Column(BigInteger, primary_key=True, index=True)
    event_id = Column(BigInteger, ForeignKey("events.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    direction = Column(Text)  # 'outbound' or 'inbound'
    body = Column(Text)
    twilio_sid = Column(Text, nullable=True)
    from_phone = Column(Text)
    to_phone = Column(Text)
    status = Column(Text, default="pending")  # 'pending', 'sent', 'delivered', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    event = relationship("Event", back_populates="messages")
    driver = relationship("Driver", back_populates="messages")



