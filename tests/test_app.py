from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path: Path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def make_payload(**overrides):
    payload = {
        "applicant_name": "Alice",
        "machine_name": "Xray-01",
        "purpose": "Routine scan",
        "status": "pending",
        "start_time": "2026-06-27T09:00:00",
        "end_time": "2026-06-27T10:00:00",
        "actual_start": None,
        "actual_end": None,
        "usage_notes": None,
    }
    payload.update(overrides)
    return payload


def test_create_and_list_monthly_schedule(client: TestClient):
    create_response = client.post("/api/bookings", json=make_payload())
    assert create_response.status_code == 201

    list_response = client.get("/api/bookings", params={"year": 2026, "month": 6})
    assert list_response.status_code == 200
    events = list_response.json()
    assert len(events) == 1
    assert events[0]["title"] == "Xray-01 · Alice"
    assert events[0]["extendedProps"]["status"] == "pending"


def test_rejects_overlapping_booking_for_same_machine(client: TestClient):
    assert client.post("/api/bookings", json=make_payload()).status_code == 201

    conflict_response = client.post(
        "/api/bookings",
        json=make_payload(
            applicant_name="Bob",
            start_time="2026-06-27T09:30:00",
            end_time="2026-06-27T10:30:00",
        ),
    )
    assert conflict_response.status_code == 409
    assert "already booked" in conflict_response.json()["detail"]


def test_update_and_delete_booking(client: TestClient):
    create_response = client.post("/api/bookings", json=make_payload())
    booking_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/bookings/{booking_id}",
        json=make_payload(
            status="approved",
            purpose="Approved scan",
            actual_start="2026-06-27T09:05:00",
            actual_end="2026-06-27T09:55:00",
            usage_notes="Completed successfully",
        ),
    )
    assert update_response.status_code == 200
    body = update_response.json()
    assert body["status"] == "approved"
    assert body["usage_notes"] == "Completed successfully"

    delete_response = client.delete(f"/api/bookings/{booking_id}")
    assert delete_response.status_code == 204
    get_response = client.get(f"/api/bookings/{booking_id}")
    assert get_response.status_code == 404


def test_rejects_invalid_time_window(client: TestClient):
    response = client.post(
        "/api/bookings",
        json=make_payload(
            start_time="2026-06-27T10:00:00",
            end_time="2026-06-27T09:00:00",
        ),
    )
    assert response.status_code == 422


def test_month_listing_handles_december_boundary(client: TestClient):
    create_response = client.post(
        "/api/bookings",
        json=make_payload(
            start_time="2026-12-31T23:00:00",
            end_time="2027-01-01T01:00:00",
        ),
    )
    assert create_response.status_code == 201

    december_response = client.get("/api/bookings", params={"year": 2026, "month": 12})
    january_response = client.get("/api/bookings", params={"year": 2027, "month": 1})

    assert december_response.status_code == 200
    assert january_response.status_code == 200
    assert len(december_response.json()) == 1
    assert len(january_response.json()) == 1
