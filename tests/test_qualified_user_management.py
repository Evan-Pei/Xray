from pathlib import Path
import os
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ADMIN_PASSWORD", "admin123")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from models import Booking, Machine, User, db

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


def _set_machine_status(app, machine_id, status):
    with app.app_context():
        machine = db.session.get(Machine, machine_id)
        assert machine is not None
        previous_status = machine.status
        machine.status = status
        db.session.commit()
        return previous_status


def _get_machine(app, name):
    with app.app_context():
        machine = Machine.query.filter_by(name=name).first()
        assert machine is not None
        return {"id": machine.id, "name": machine.name, "status": machine.status}


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


def test_calendar_renders_machine_filter_ui(client):
    _login(client)

    response = client.get("/calendar")

    assert response.status_code == 200
    assert b'id="machineFilterSelect"' in response.data
    assert b"All Machines" in response.data
    assert b"cal_selected_machine_id" in response.data
    assert b'id="machineStatusLegend"' in response.data


def test_calendar_includes_day_view_sidebar_markup(client):
    _login(client)

    response = client.get("/calendar")

    assert response.status_code == 200
    assert b'id="dayViewOverlay"' in response.data
    assert b'id="dayViewList"' in response.data
    assert b'id="dayViewFooter"' in response.data
    assert b"openDayBookings(" in response.data


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


def test_create_booking_rejects_offline_machine(client, app):
    machine = _get_machine(app, "X-Ray 1")
    previous_status = _set_machine_status(app, machine["id"], "offline")
    try:
        _login(client)

        response = client.post(
            "/api/bookings",
            json={
                "start": "2026-07-30T09:00:00",
                "end": "2026-07-30T10:00:00",
                "machine_id": machine["id"],
                "purpose": "offline machine",
            },
        )

        assert response.status_code == 409
        assert response.get_json()["error"] == f'machine "{machine["name"]}" is currently offline'
    finally:
        _set_machine_status(app, machine["id"], previous_status)


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


def test_non_admin_login_redirects_to_calendar(client, app):
    _create_user(app, "calendar-user", "pw7", True)

    response = client.post(
        "/auth/login",
        data={"username": "calendar-user", "password": "pw7"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/calendar" in response.headers["Location"]


def test_non_admin_cannot_access_admin_routes(client, app):
    _create_user(app, "regular-admin-page", "pw8", True)
    _login(client, "regular-admin-page", "pw8")

    response = client.get("/admin/machines")

    assert response.status_code == 403


def test_non_admin_cannot_update_or_delete_other_users_booking(client, app):
    _create_user(app, "owner-user", "pw9", True)
    _create_user(app, "other-user", "pw10", True)

    _login(client, "owner-user", "pw9")
    created = client.post(
        "/api/bookings",
        json={
            "start": "2026-07-31T09:00:00",
            "end": "2026-07-31T10:00:00",
            "machine_id": 1,
            "purpose": "owner booking",
        },
    )
    assert created.status_code == 201
    booking_id = created.get_json()["id"]
    client.post("/auth/logout")

    _login(client, "other-user", "pw10")
    update_response = client.put(
        f"/api/bookings/{booking_id}",
        json={"purpose": "forbidden update"},
    )
    delete_response = client.delete(f"/api/bookings/{booking_id}")

    assert update_response.status_code == 403
    assert delete_response.status_code == 403


def test_admin_and_evan_can_update_or_delete_other_users_booking(client, app):
    _create_user(app, "owner-admin-case", "pw11", True)
    _create_user(app, "Evan", "pw12", True)

    _login(client, "owner-admin-case", "pw11")
    created = client.post(
        "/api/bookings",
        json={
            "start": "2026-07-31T10:00:00",
            "end": "2026-07-31T11:00:00",
            "machine_id": 1,
            "purpose": "owner booking 2",
        },
    )
    assert created.status_code == 201
    booking_id = created.get_json()["id"]
    client.post("/auth/logout")

    _login(client)
    admin_update = client.put(
        f"/api/bookings/{booking_id}",
        json={"purpose": "admin updated"},
    )
    assert admin_update.status_code == 200
    client.post("/auth/logout")

    _login(client, "Evan", "pw12")
    admin_page = client.get("/admin/machines")
    evan_delete = client.delete(f"/api/bookings/{booking_id}")

    assert admin_page.status_code == 200
    assert evan_delete.status_code == 200


def test_booking_can_edit_flag_respects_owner_and_admin(client, app):
    _create_user(app, "booking-owner", "pw13", True)
    _create_user(app, "booking-viewer", "pw14", True)

    _login(client, "booking-owner", "pw13")
    created = client.post(
        "/api/bookings",
        json={
            "start": "2026-07-31T12:00:00",
            "end": "2026-07-31T13:00:00",
            "machine_id": 1,
            "purpose": "can-edit check",
        },
    )
    assert created.status_code == 201
    booking_id = created.get_json()["id"]
    client.post("/auth/logout")

    _login(client, "booking-viewer", "pw14")
    viewer_list = client.get("/api/bookings")
    viewer_booking = next(item for item in viewer_list.get_json() if item["id"] == booking_id)
    assert viewer_booking["can_edit"] is False
    client.post("/auth/logout")

    _login(client)
    admin_list = client.get("/api/bookings")
    admin_booking = next(item for item in admin_list.get_json() if item["id"] == booking_id)
    assert admin_booking["can_edit"] is True


def test_calendar_injects_frontend_permission_flags(client, app):
    _create_user(app, "unqualified-ui-user", "pw15", False)
    _login(client, "unqualified-ui-user", "pw15")

    regular_calendar = client.get("/calendar")
    assert regular_calendar.status_code == 200
    assert b"const CURRENT_USER_IS_ADMIN = false;" in regular_calendar.data
    assert b"const CURRENT_USER_IS_QUALIFIED = false;" in regular_calendar.data
    client.post("/auth/logout")

    _login(client)
    admin_calendar = client.get("/calendar")
    assert admin_calendar.status_code == 200
    assert b"const CURRENT_USER_IS_ADMIN = true;" in admin_calendar.data
    assert b"const CURRENT_USER_IS_QUALIFIED = true;" in admin_calendar.data


def test_update_booking_rejects_maintenance_machine(client, app):
    _login(client)
    source_machine = _get_machine(app, "X-Ray 1")
    target_machine = _get_machine(app, "X-Ray 2")

    create_response = client.post(
        "/api/bookings",
        json={
            "start": "2026-07-30T12:00:00",
            "end": "2026-07-30T13:00:00",
            "machine_id": source_machine["id"],
            "purpose": "baseline booking",
        },
    )
    assert create_response.status_code == 201
    booking_id = create_response.get_json()["id"]

    previous_status = _set_machine_status(app, target_machine["id"], "maintenance")
    try:
        response = client.put(
            f"/api/bookings/{booking_id}",
            json={
                "start": "2026-07-30T12:30:00",
                "end": "2026-07-30T13:30:00",
                "machine_id": target_machine["id"],
                "purpose": "move booking",
            },
        )

        assert response.status_code == 409
        assert response.get_json()["error"] == f'machine "{target_machine["name"]}" is currently under maintenance'

        with app.app_context():
            booking = db.session.get(Booking, booking_id)
            assert booking is not None
            assert booking.machine_id == source_machine["id"]
    finally:
        _set_machine_status(app, target_machine["id"], previous_status)
