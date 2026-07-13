from pathlib import Path
import sys

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from routes.web import web_bp


def create_test_app():
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    app.register_blueprint(web_bp)
    return app


def test_index_route_renders_html():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"Welcome to Xray" in response.data


def test_dashboard_route_renders_html():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/dashboard")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"xray_bookings" in response.data
    assert b"localStorage.setItem(BOOKINGS_KEY, JSON.stringify(bookingsByDate))" in response.data
    assert "月行事曆".encode("utf-8") in response.data
