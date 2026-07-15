from pathlib import Path
import os
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ADMIN_PASSWORD", "admin123")

from app import create_app
from models import Booking, db


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
        }
    )
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def test_calendar_renders_add_booking_form(client):
    response = client.get("/calendar")
    assert response.status_code == 200
    assert b"Add New Booking" in response.data


def test_calendar_renders_machine_dropdown(client):
    response = client.get("/calendar")
    assert response.status_code == 200
    assert b"X-Ray" in response.data
    assert b"CT Scanner" in response.data


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_create_booking_redirects_on_success(client):
    response = client.post(
        "/calendar/bookings",
        data={"day": "10", "time": "09:00", "machine": "X-Ray 1", "patient": "Alice"},
    )
    assert response.status_code == 302
    assert "/calendar" in response.headers["Location"]


def test_create_booking_persists_in_db(client, app):
    client.post(
        "/calendar/bookings",
        data={"day": "10", "time": "09:00", "machine": "X-Ray 1", "patient": "Alice"},
    )
    with app.app_context():
        booking = Booking.query.filter_by(patient="Alice").first()
        assert booking is not None
        assert booking.day == 10
        assert booking.time == "09:00"
        assert booking.machine == "X-Ray 1"


def test_create_booking_shows_on_calendar(client):
    client.post(
        "/calendar/bookings",
        data={"day": "5", "time": "10:30", "machine": "CT Scanner", "patient": "Bob"},
    )
    response = client.get("/calendar", follow_redirects=True)
    assert b"CT Scanner" in response.data
    assert b"10:30" in response.data


def test_create_booking_flash_success(client):
    response = client.post(
        "/calendar/bookings",
        data={"day": "10", "time": "09:00", "machine": "X-Ray 1", "patient": "Alice"},
        follow_redirects=True,
    )
    assert b"Booking created successfully" in response.data


# ---------------------------------------------------------------------------
# Validation errors on create
# ---------------------------------------------------------------------------

def test_create_booking_missing_patient_shows_error(client):
    response = client.post(
        "/calendar/bookings",
        data={"day": "10", "time": "09:00", "machine": "X-Ray 1", "patient": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"valid day" in response.data or b"patient" in response.data.lower()


def test_create_booking_invalid_day_shows_error(client):
    response = client.post(
        "/calendar/bookings",
        data={"day": "99", "time": "09:00", "machine": "X-Ray 1", "patient": "Alice"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"valid day" in response.data


def test_create_booking_missing_machine_shows_error(client):
    response = client.post(
        "/calendar/bookings",
        data={"day": "10", "time": "09:00", "machine": "", "patient": "Alice"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"valid day" in response.data or b"machine" in response.data.lower()


# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

def _create_booking(client):
    client.post(
        "/calendar/bookings",
        data={"day": "12", "time": "08:00", "machine": "X-Ray 2", "patient": "Carol"},
    )


def test_edit_form_prepopulates(client, app):
    _create_booking(client)
    with app.app_context():
        booking = Booking.query.filter_by(patient="Carol").first()
        booking_id = booking.id

    response = client.get(f"/calendar?edit_id={booking_id}")
    assert response.status_code == 200
    assert b"Edit Booking" in response.data
    assert b"Carol" in response.data


def test_edit_booking_updates_db(client, app):
    _create_booking(client)
    with app.app_context():
        booking_id = Booking.query.filter_by(patient="Carol").first().id

    response = client.post(
        f"/calendar/bookings/{booking_id}/edit",
        data={"day": "13", "time": "11:00", "machine": "X-Ray 1", "patient": "Carol Updated"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Booking updated successfully" in response.data

    with app.app_context():
        booking = db.session.get(Booking, booking_id)
        assert booking.day == 13
        assert booking.time == "11:00"
        assert booking.patient == "Carol Updated"


def test_edit_booking_invalid_day_shows_error(client, app):
    _create_booking(client)
    with app.app_context():
        booking_id = Booking.query.filter_by(patient="Carol").first().id

    response = client.post(
        f"/calendar/bookings/{booking_id}/edit",
        data={"day": "0", "time": "11:00", "machine": "X-Ray 1", "patient": "Carol"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"valid day" in response.data


def test_edit_booking_not_found_returns_404(client):
    response = client.post(
        "/calendar/bookings/9999/edit",
        data={"day": "1", "time": "09:00", "machine": "X-Ray 1", "patient": "Ghost"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_booking_removes_from_db(client, app):
    _create_booking(client)
    with app.app_context():
        booking_id = Booking.query.filter_by(patient="Carol").first().id

    response = client.post(
        f"/calendar/bookings/{booking_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Booking deleted" in response.data

    with app.app_context():
        assert db.session.get(Booking, booking_id) is None


def test_delete_booking_not_found_returns_404(client):
    response = client.post("/calendar/bookings/9999/delete")
    assert response.status_code == 404
