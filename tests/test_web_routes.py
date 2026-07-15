from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ADMIN_PASSWORD", "admin123")

from app import create_app


def create_test_app():
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
        }
    )


def test_index_route_renders_html():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"Welcome to Xray" in response.data


def test_index_links_to_dashboard_and_calendar():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/")

    assert b"/dashboard" in response.data
    assert b"/calendar" in response.data


def test_dashboard_route_renders_html():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/dashboard")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"Xray Dashboard" in response.data


def test_dashboard_shows_status_panel():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/dashboard")

    assert b"\xe7\x8b\x80\xe6\x85\x8b\xe8\xa6\x96\xe7\xaa\x97" in response.data  # 狀態視窗
    assert b"Machine Status" in response.data
    assert b"X-Ray 1" in response.data
    assert b"online" in response.data


def test_dashboard_links_to_calendar():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/dashboard")

    assert b"/calendar" in response.data


def test_calendar_route_renders_html():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/calendar")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"\xe8\xa1\x8c\xe4\xba\x8b\xe6\x9b\x86" in response.data  # 行事曆
    assert b"Calendar" in response.data


def test_calendar_shows_schedule_grid():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/calendar")

    assert b"Mon" in response.data
    assert b"X-Ray" in response.data
