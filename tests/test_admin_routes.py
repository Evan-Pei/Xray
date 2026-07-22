from pathlib import Path
import os
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ADMIN_PASSWORD", "admin123")

from app import create_app
from models import Machine, db

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


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


def _login(client):
    return client.post(
        "/auth/login",
        data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        follow_redirects=True,
    )


def test_login_page_renders_html(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"Admin Login" in response.data


def test_admin_route_requires_authentication(client):
    response = client.get("/admin/machines")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_login_shows_management_list(client):
    response = _login(client)
    assert response.status_code == 200
    assert b"Machine Management" in response.data
    assert b"X-Ray 1" in response.data


def test_machine_crud_and_status_toggle(client, app):
    _login(client)

    create_response = client.post(
        "/admin/machines",
        data={"name": "Portable X-Ray", "description": "Bedside machine", "status": "online"},
        follow_redirects=True,
    )
    assert create_response.status_code == 200
    assert b"Portable X-Ray" in create_response.data

    with app.app_context():
        machine = Machine.query.filter_by(name="Portable X-Ray").first()
        assert machine is not None
        machine_id = machine.id

    toggle_response = client.post(f"/admin/machines/{machine_id}/toggle-status", follow_redirects=True)
    assert toggle_response.status_code == 200
    assert b"offline" in toggle_response.data

    edit_page = client.get(f"/admin/machines/{machine_id}/edit")
    assert edit_page.status_code == 200
    assert f'value="{machine_id}"'.encode() in edit_page.data

    edit_response = client.post(
        f"/admin/machines/{machine_id}/edit",
        data={
            "id": str(machine_id + 10),
            "name": "Portable X-Ray v2",
            "description": "Updated",
            "status": "online",
        },
        follow_redirects=True,
    )
    assert edit_response.status_code == 200
    assert b"Portable X-Ray v2" in edit_response.data

    with app.app_context():
        updated_machine = Machine.query.filter_by(name="Portable X-Ray v2").first()
        assert updated_machine is not None
        assert updated_machine.id == machine_id + 10
        assert db.session.get(Machine, machine_id) is None

    delete_response = client.post(f"/admin/machines/{machine_id + 10}/delete", follow_redirects=True)
    assert delete_response.status_code == 200
    assert b"Portable X-Ray v2" not in delete_response.data


def test_machine_edit_id_conflict_shows_error(client, app):
    _login(client)

    with app.app_context():
        machines = Machine.query.order_by(Machine.id.asc()).all()
        assert len(machines) >= 2
        target_machine = machines[0]
        conflicting_machine = machines[1]
        original_id = target_machine.id

    response = client.post(
        f"/admin/machines/{original_id}/edit",
        data={
            "id": str(conflicting_machine.id),
            "name": "X-Ray 1 Updated",
            "description": "Keep original id on conflict",
            "status": "online",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Machine ID is already in use." in response.data

    with app.app_context():
        unchanged_machine = db.session.get(Machine, original_id)
        assert unchanged_machine is not None
        assert unchanged_machine.name == "X-Ray 1"
