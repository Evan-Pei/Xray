# Xray

A Flask-based machine booking web application for managing equipment requests, schedules, and usage records.

## Features

- Calendar dashboard with month, week, and day views
- Create, update, and delete equipment booking requests directly from the calendar
- Multi-machine scheduling with conflict prevention
- User registration and login
- Booking status tracking and change history
- RESTful APIs backed by SQLite by default

## Project Structure

```text
/home/runner/work/Xray/Xray
├── app.py
├── config.py
├── requirements.txt
├── models/
├── routes/
├── static/
├── templates/
└── tests/
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 and register an account.

## Run tests

```bash
pytest
```
