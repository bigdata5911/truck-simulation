"""
Database migration script
Creates all tables in the database
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, engine, Base
from app.models import Driver, Event, Message

if __name__ == "__main__":
    # First, ensure the database exists
    print("Checking if database exists...")
    try:
        # Try to create the database if it doesn't exist
        from scripts.create_db import create_database
        create_database()
    except Exception as e:
        print(f"Note: Could not auto-create database: {e}")
        print("Please ensure the database exists before running migrations.")
        print("You can run: python3 scripts/create_db.py")
    
    print("\nCreating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        sys.exit(1)

