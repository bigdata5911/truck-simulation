-- DriverBuddy Database Schema
-- Run this SQL script to create all tables

CREATE TABLE IF NOT EXISTS drivers (
  id SERIAL PRIMARY KEY,
  name TEXT,
  phone TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
  id BIGSERIAL PRIMARY KEY,
  driver_id INTEGER REFERENCES drivers(id),
  vehicle_id TEXT,
  event_type TEXT, -- 'stop', 'move', etc
  start_time TIMESTAMPTZ,
  end_time TIMESTAMPTZ,
  latitude NUMERIC(10, 7),
  longitude NUMERIC(10, 7),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
  id BIGSERIAL PRIMARY KEY,
  event_id BIGINT REFERENCES events(id),
  driver_id INTEGER REFERENCES drivers(id),
  direction TEXT, -- 'outbound' or 'inbound'
  body TEXT,
  twilio_sid TEXT,
  from_phone TEXT,
  to_phone TEXT,
  status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed'
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_vehicle_time ON events(vehicle_id, start_time);
CREATE INDEX IF NOT EXISTS idx_events_driver_time ON events(driver_id, start_time);
CREATE INDEX IF NOT EXISTS idx_events_vehicle_end_time ON events(vehicle_id, end_time) WHERE end_time IS NULL;
CREATE INDEX IF NOT EXISTS idx_messages_driver_time ON messages(driver_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_event ON messages(event_id);

-- Sample driver (for testing)
INSERT INTO drivers (id, name, phone) VALUES (1, 'Test Driver', '+17652590506')
ON CONFLICT (id) DO NOTHING;

