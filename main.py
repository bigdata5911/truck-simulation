"""
DriverBuddy FastAPI Application
Main entry point for the simplified MVP backend
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from typing import Optional

from app.database import init_db, get_db
from app.routers import webhooks, events, auth
from app.workers import event_processor, sms_worker
from app.config import settings

# Background tasks
background_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("Starting DriverBuddy FastAPI application...")
    init_db()
    
    # Start background workers
    event_task = asyncio.create_task(event_processor.start())
    sms_task = asyncio.create_task(sms_worker.start())
    background_tasks.extend([event_task, sms_task])
    
    print("Background workers started")
    yield
    
    # Shutdown
    print("Shutting down background workers...")
    event_processor.stop()
    sms_worker.stop()
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    print("Application shut down")


app = FastAPI(
    title="DriverBuddy API",
    description="Vehicle Tracking & SMS Notification System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhooks.router, prefix="/webhook", tags=["webhooks"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "DriverBuddy API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB health check
        "workers": {
            "event_processor": "running",
            "sms_worker": "running"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )

