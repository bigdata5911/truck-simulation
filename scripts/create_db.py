"""
Database creation script
Creates the database if it doesn't exist
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def create_database():
    """Create the database if it doesn't exist"""
    # Connect to PostgreSQL server (using default 'postgres' database)
    # We need to connect without specifying the target database
    db_host = settings.DB_HOST
    db_port = settings.DB_PORT
    db_user = settings.DB_USER
    db_password = settings.DB_PASSWORD
    db_name = settings.DB_NAME
    
    # Connect to default postgres database to create our database
    admin_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"
    
    print(f"Connecting to PostgreSQL server at {db_host}:{db_port}...")
    
    try:
        admin_engine = create_engine(
            admin_url,
            isolation_level="AUTOCOMMIT"  # Required for CREATE DATABASE
        )
        
        with admin_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            exists = result.fetchone() is not None
            
            if exists:
                print(f"Database '{db_name}' already exists.")
            else:
                print(f"Creating database '{db_name}'...")
                # Create database
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"Database '{db_name}' created successfully!")
        
        admin_engine.dispose()
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

if __name__ == "__main__":
    if create_database():
        print("Database setup complete!")
        sys.exit(0)
    else:
        print("Failed to create database.")
        sys.exit(1)

