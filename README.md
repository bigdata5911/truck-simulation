# DriverBuddy FastAPI Backend

FastAPI backend application for DriverBuddy vehicle tracking and SMS notification system.

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `env.example` to `.env` and update with your configuration:

```bash
# Linux/Mac
cp env.example .env

# Windows
copy env.example .env
```

Then edit `.env` and fill in your actual values:
- Database credentials (DB_HOST, DB_USER, DB_PASSWORD, etc.)
- Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER)
- Slack webhook URL (optional)
- JWT secret key

Or set environment variables directly instead of using `.env` file.

### 3. Database Setup

Run the migration script to create database tables:

```bash
python scripts/migrate.py
```

Or manually run the SQL from the main README.

### 4. AWS Configuration

Ensure your EC2 instance has:
- IAM role with permissions for SQS
- Security group allowing inbound HTTP/HTTPS
- Access to RDS database in VPC

### 5. Run Application

Development:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Production (with gunicorn):
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Or use systemd service (see `deployment/` directory).

## API Endpoints

### Webhooks
- `POST /webhook/samsara` - Receive Samsara telemetry webhooks
- `POST /webhook/twilio/inbound` - Receive Twilio inbound SMS webhooks

### Events
- `GET /events` - List events (with pagination and filters)
- `GET /events/{id}` - Get event details with messages

### Authentication
- `POST /auth/login` - Login and get JWT token

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check

## Background Workers

The application runs two background workers:
1. **Event Processor** - Polls `driverbuddy-events-queue` and creates SMS jobs
2. **SMS Worker** - Polls `driverbuddy-sms-queue` and sends SMS via Twilio

Workers start automatically when the application starts.

## Testing

Run the fake trip simulator:

```bash
python scripts/fake_trip.py
```

Make sure to update `API_URL` in the script to point to your EC2 instance.

## Deployment on EC2

1. SSH into EC2 instance
2. Install Python 3.9+ and pip
3. Clone repository
4. Install dependencies: `pip install -r requirements.txt`
5. Configure environment variables (see `env.example` - copy to `.env` and fill in values)
6. Run migrations: `python scripts/migrate.py`
7. Start application with systemd or supervisor
8. Configure nginx as reverse proxy (optional)

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── app/
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database connection
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── auth.py            # Authentication utilities
│   ├── routers/           # API route handlers
│   │   ├── webhooks.py    # Webhook endpoints
│   │   ├── events.py      # Events API
│   │   └── auth.py        # Auth endpoints
│   ├── services/          # Business logic
│   │   ├── event_detector.py
│   │   ├── twilio_service.py
│   │   └── slack.py
│   └── workers/           # Background workers
│       ├── event_processor.py
│       └── sms_worker.py
├── scripts/
│   ├── migrate.py         # Database migration
│   └── fake_trip.py       # Test trip simulator
└── requirements.txt       # Python dependencies
```

