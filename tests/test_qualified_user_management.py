from pathlib import Path
import os
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ADMIN_PASSWORD", "admin123")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from models import Booking, User, db

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


@pytest.fixture()
def app():
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
        }
    )


@pytest.fixture()
def client(app):
    return app.test_client()


def _login(client, username=ADMIN_USERNAME, pwd=ADMIN_PASSWORD):
    return client.post(
        "/auth/login",
        data={"username": username, "password": pwd},
        follow_redirects=True,
    )


def _create_user(app, username, password, is_qualified):
    with app.app_context():
        user = User(username=username, is_qualified=is_qualified)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def test_seed_admin_is_qualified(app):
    with app.app_context():
        admin = User.query.filter_by(username=ADMIN_USERNAME).first()
        assert admin is not None
        assert admin.is_qualified is True


def test_admin_user_page_create_and_toggle(client):
    _login(client)

    create_response = client.post(
        "/admin/users",
        data={"username": "tech1", "password": "pw123", "is_qualified": "on"},
        follow_redirects=True,
    )
    assert create_response.status_code == 200
    assert b"tech1" in create_response.data
    assert "\u2713".encode() in create_response.data

    with client.application.app_context():
        created_user = User.query.filter_by(username="tech1").first()
        assert created_user is not None
        user_id = created_user.id

    toggle_response = client.post(
        f"/admin/users/{user_id}/toggle-qualified",
        follow_redirects=True,
    )
    assert toggle_response.status_code == 200
    assert "\u2717".encode() in toggle_response.data


def test_admin_cannot_delete_self(client, app):
    _login(client)
    with app.app_context():
        admin = User.query.filter_by(username=ADMIN_USERNAME).first()
        assert admin is not None
        admin_id = admin.id

    response = client.post(f"/admin/users/{admin_id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"You cannot delete your own account." in response.data

    with app.app_context():
        assert User.query.filter_by(username=ADMIN_USERNAME).first() is not None


def test_admin_can_edit_user(client, app):
    user_id = _create_user(app, "edit-me", "pw-edit", False)
    _login(client)

    response = client.post(
        f"/admin/users/{user_id}/edit",
        data={"username": "edited-user", "password": "", "is_qualified": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"edited-user" in response.data

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.username == "edited-user"
        assert user.is_qualified is True


def test_api_returns_only_qualified_users(client, app):
    _create_user(app, "qualified-user", "pw1", True)
    _create_user(app, "unqualified-user", "pw2", False)
    _login(client)

    response = client.get("/api/qualified-users")
    assert response.status_code == 200
    data = response.get_json()
    usernames = {item["username"] for item in data}
    assert "qualified-user" in usernames
    assert "unqualified-user" not in usernames


def test_calendar_user_dropdown_shows_only_qualified_users(client, app):
    _create_user(app, "qualified-ui", "pw-ui-1", True)
    _create_user(app, "unqualified-ui", "pw-ui-2", False)
    _login(client)

    response = client.get("/calendar")
    assert response.status_code == 200
    assert b'id="fUser"' in response.data
    assert b"qualified-ui" in response.data
    assert b"unqualified-ui" not in response.data


def test_create_booking_rejects_unqualified_selected_user(client, app):
    target_user_id = _create_user(app, "not-qualified", "pw3", False)
    _login(client)

    response = client.post(
        "/api/bookings",
        json={
            "start": "2026-07-30T09:00:00",
            "end": "2026-07-30T10:00:00",
            "machine_id": 1,
            "user_id": target_user_id,
            "purpose": "test",
        },
    )
    assert response.status_code == 403


def test_non_admin_cannot_book_for_another_user(client, app):
    user_a_id = _create_user(app, "user-a", "pw4", True)
    user_b_id = _create_user(app, "user-b", "pw5", True)
    _login(client, "user-a", "pw4")

    response = client.post(
        "/api/bookings",
        json={
            "start": "2026-07-30T10:00:00",
            "end": "2026-07-30T11:00:00",
            "machine_id": 1,
            "user_id": user_b_id,
            "purpose": "cross booking",
        },
    )
    assert response.status_code == 403

    with app.app_context():
        assert Booking.query.filter_by(user_id=user_a_id).count() == 0
        assert Booking.query.filter_by(user_id=user_b_id).count() == 0


def test_admin_can_book_for_another_qualified_user(client, app):
    target_user_id = _create_user(app, "qualified-target", "pw6", True)
    _login(client)

    response = client.post(
        "/api/bookings",
        json={
            "start": "2026-07-30T12:00:00",
            "end": "2026-07-30T13:00:00",
            "machine_id": 1,
            "user_id": target_user_id,
            "purpose": "delegated booking",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["user_id"] == target_user_id
    assert data["applicant_name"] == "qualified-target"
