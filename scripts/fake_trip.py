"""
Fake trip generator for testing
Simulates Samsara webhook payloads
"""

import requests
import time
from datetime import datetime, timedelta
import random

# Configuration
API_URL = "http://localhost:8000/webhook/samsara"  # Change to your EC2 public IP
VEHICLE_ID = "truck-1001"
DRIVER_ID = "1"

# Simulate a trip with stops
def generate_telemetry(lat, lon, speed, timestamp):
    """Generate telemetry payload"""
    return {
        "vehicleId": VEHICLE_ID,
        "driverId": DRIVER_ID,
        "timestamp": timestamp.isoformat(),
        "latitude": lat,
        "longitude": lon,
        "speed": speed,  # km/h
        "heading": random.uniform(0, 360),
        "metadata": {
            "engine_rpm": random.uniform(800, 2500),
            "fuel_level": random.uniform(20, 100)
        }
    }


def simulate_trip():
    """Simulate a trip with multiple stops"""
    print("Starting fake trip simulation...")
    
    # Starting point (New York)
    current_lat = 40.7128
    current_lon = -74.0060
    
    # Simulate moving
    print("Vehicle moving...")
    for i in range(10):
        # Move north
        current_lat += 0.01
        current_lon += random.uniform(-0.005, 0.005)
        speed = random.uniform(40, 80)  # Moving
        
        payload = generate_telemetry(
            current_lat,
            current_lon,
            speed,
            datetime.utcnow() + timedelta(seconds=i*30)
        )
        
        response = requests.post(API_URL, json=payload)
        print(f"  [{i+1}] Speed: {speed:.1f} km/h - Status: {response.status_code}")
        time.sleep(1)
    
    # Simulate stop
    print("\nVehicle stopped...")
    for i in range(5):
        speed = 0.0  # Stopped
        
        payload = generate_telemetry(
            current_lat,
            current_lon,
            speed,
            datetime.utcnow() + timedelta(seconds=300 + i*30)
        )
        
        response = requests.post(API_URL, json=payload)
        print(f"  [{i+1}] Speed: {speed:.1f} km/h - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get("event_created"):
                print(f"    ✓ Stop event created: {data.get('event_id')}")
        time.sleep(1)
    
    # Simulate moving again
    print("\nVehicle moving again...")
    for i in range(5):
        current_lat += 0.01
        speed = random.uniform(40, 80)  # Moving
        
        payload = generate_telemetry(
            current_lat,
            current_lon,
            speed,
            datetime.utcnow() + timedelta(seconds=450 + i*30)
        )
        
        response = requests.post(API_URL, json=payload)
        print(f"  [{i+1}] Speed: {speed:.1f} km/h - Status: {response.status_code}")
        time.sleep(1)
    
    print("\nTrip simulation complete!")


if __name__ == "__main__":
    simulate_trip()

