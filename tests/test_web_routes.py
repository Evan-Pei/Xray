from datetime import date
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from models import Booking, Machine, db


@pytest.fixture
def app(tmp_path):
    database_path = tmp_path / "test.db"
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
        }
    )

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _machine_id(app, name):
    with app.app_context():
        return db.session.execute(
            db.select(Machine.id).where(Machine.name == name)
        ).scalar_one()


def test_index_route_renders_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"Welcome to Xray" in response.data


def test_index_links_to_dashboard_calendar_and_admin(client):
    response = client.get("/")

    assert b"/dashboard" in response.data
    assert b"/calendar" in response.data
    assert b"/admin/machines" in response.data
    assert b"/admin/bookings" in response.data


def test_dashboard_route_renders_seeded_machine_statuses(client):
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"Xray Dashboard" in response.data
    assert b"Machine Status" in response.data
    assert b"X-Ray 1" in response.data
    assert b"maintenance" in response.data


def test_calendar_route_renders_seeded_bookings(client):
    response = client.get("/calendar")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"\xe8\xa1\x8c\xe4\xba\x8b\xe6\x9b\x86" in response.data  # 行事曆
    assert b"Calendar" in response.data
    assert b"Patient A" in response.data


def test_machine_admin_create_update_delete_flow(app, client):
    response = client.get("/admin/machines")
    assert response.status_code == 200
    assert b"Manage Machines" in response.data

    response = client.post(
        "/admin/machines",
        data={
            "name": "MRI 1",
            "description": "Magnetic resonance imaging",
            "status": "offline",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Machine saved." in response.data
    assert b"MRI 1" in response.data

    machine_id = _machine_id(app, "MRI 1")
    response = client.post(
        f"/admin/machines/{machine_id}/edit",
        data={
            "name": "MRI 1",
            "description": "Updated MRI suite",
            "status": "online",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Machine updated." in response.data
    assert b"Updated MRI suite" in response.data
    assert b"online" in response.data

    response = client.post(
        f"/admin/machines/{machine_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Machine deleted." in response.data
    assert b"MRI 1" not in response.data

    with app.app_context():
        assert db.session.get(Machine, machine_id) is None


def test_machine_admin_validation_rejects_invalid_status(client):
    response = client.post(
        "/admin/machines",
        data={
            "name": "MRI 1",
            "description": "Magnetic resonance imaging",
            "status": "broken",
        },
    )

    assert response.status_code == 400
    assert b"Machine status must be online, maintenance, or offline." in response.data


def test_booking_admin_create_update_delete_flow(app, client):
    machine_id = _machine_id(app, "X-Ray 1")
    booking_date = date.today().replace(day=23).isoformat()

    response = client.post(
        "/admin/bookings",
        data={
            "booking_date": booking_date,
            "booking_time": "15:45",
            "machine_id": str(machine_id),
            "patient": "Patient Z",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Booking saved." in response.data
    assert b"Patient Z" in response.data

    with app.app_context():
        booking_id = db.session.execute(
            db.select(Booking.id).where(Booking.patient == "Patient Z")
        ).scalar_one()

    calendar_response = client.get("/calendar")
    assert b"15:45 X-Ray 1" in calendar_response.data
    assert b"Patient Z" in calendar_response.data

    response = client.post(
        f"/admin/bookings/{booking_id}/edit",
        data={
            "booking_date": booking_date,
            "booking_time": "16:15",
            "machine_id": str(machine_id),
            "patient": "Patient ZZ",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Booking updated." in response.data
    assert b"Patient ZZ" in response.data

    response = client.post(
        f"/admin/bookings/{booking_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Booking deleted." in response.data
    assert b"Patient ZZ" not in response.data

    with app.app_context():
        assert db.session.get(Booking, booking_id) is None


def test_booking_admin_validation_rejects_bad_time(client):
    response = client.post(
        "/admin/bookings",
        data={
            "booking_date": date.today().isoformat(),
            "booking_time": "99:99",
            "machine_id": "1",
            "patient": "Patient Invalid",
        },
    )

    assert response.status_code == 400
    assert b"Booking time must use HH:MM." in response.data


def test_booking_admin_validation_rejects_unknown_machine(client):
    response = client.post(
        "/admin/bookings",
        data={
            "booking_date": date.today().isoformat(),
            "booking_time": "09:30",
            "machine_id": "999999",
            "patient": "Patient Invalid",
        },
    )

    assert response.status_code == 400
    assert b"Please choose a valid machine." in response.data
