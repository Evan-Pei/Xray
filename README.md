# Machine Usage Scheduler

A self-contained FastAPI application for machine usage requests, monthly scheduling, approvals, and usage record tracking.

## Features
- Monthly calendar home page powered by FullCalendar
- Create, edit, and delete machine usage applications directly from the calendar
- Conflict checking for overlapping bookings on the same machine
- Booking lifecycle states: `pending`, `approved`, and `rejected`
- Usage record fields for actual start/end times and notes
- SQLite storage via SQLAlchemy
- JSON CRUD APIs for calendar and record management

## Project Structure
- `app/main.py` – FastAPI entrypoint and routes
- `app/models.py` – SQLAlchemy models
- `app/crud.py` – booking and conflict-check logic
- `app/templates/index.html` – calendar UI
- `app/static/` – frontend assets
- `tests/test_app.py` – focused API tests

## Setup
```bash
cd <project-root>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Locally
```bash
cd <project-root>
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000> to view the monthly schedule calendar.

The app stores data in `machine_usage.db` in the repository root by default. Override with `DATABASE_URL` if needed.

## API Endpoints
- `GET /api/bookings?year=2026&month=6` – list monthly calendar events
- `GET /api/bookings/all` – list all booking records
- `GET /api/bookings/{id}` – get one booking record
- `POST /api/bookings` – create a booking/application
- `PUT /api/bookings/{id}` – update a booking/application or usage record
- `DELETE /api/bookings/{id}` – delete a booking/application

## Test
```bash
cd <project-root>
python -m pytest
```
