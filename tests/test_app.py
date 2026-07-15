def register(client, username, passwd="secret123"):
    return client.post(
        "/register",
        data={"username": username, "password": passwd},
        follow_redirects=True,
    )


def login(client, username, passwd="secret123"):
    return client.post(
        "/login",
        data={"username": username, "password": passwd},
        follow_redirects=True,
    )


def logout(client):
    return client.post("/logout", follow_redirects=True)


def test_index_requires_login(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_create_booking_and_prevent_conflicts(client):
    register(client, "alice")

    machines = client.get("/api/machines").get_json()
    machine_id = machines[0]["id"]
    payload = {
        "title": "樣品檢測",
        "machine_id": machine_id,
        "start": "2026-06-27T09:00",
        "end": "2026-06-27T10:00",
        "purpose": "X-ray 檢測",
        "status": "pending",
    }

    create_response = client.post("/api/bookings", json=payload)
    assert create_response.status_code == 201
    booking = create_response.get_json()
    assert booking["machine_id"] == machine_id
    assert booking["status"] == "pending"

    conflict_response = client.post(
        "/api/bookings",
        json={**payload, "start": "2026-06-27T09:30", "end": "2026-06-27T10:30"},
    )
    assert conflict_response.status_code == 409

    history_response = client.get(f"/api/bookings/{booking['id']}/history")
    history = history_response.get_json()
    assert [item["action"] for item in history] == ["created"]


def test_only_owner_can_update_or_delete_booking(app, client):
    register(client, "alice")
    machine_id = client.get("/api/machines").get_json()[0]["id"]
    booking = client.post(
        "/api/bookings",
        json={
            "title": "原始申請",
            "machine_id": machine_id,
            "start": "2026-06-27T11:00",
            "end": "2026-06-27T12:00",
            "purpose": "初次拍攝",
            "status": "pending",
        },
    ).get_json()

    logout(client)
    other_client = app.test_client()
    register(other_client, "bob")

    forbidden_response = other_client.put(
        f"/api/bookings/{booking['id']}",
        json={"purpose": "嘗試修改", "start": "2026-06-27T11:00", "end": "2026-06-27T12:00"},
    )
    assert forbidden_response.status_code == 403

    login(client, "alice")
    update_response = client.put(
        f"/api/bookings/{booking['id']}",
        json={
            "title": "更新申請",
            "machine_id": machine_id,
            "start": "2026-06-27T12:00",
            "end": "2026-06-27T13:00",
            "purpose": "追加拍攝",
            "status": "approved",
        },
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["status"] == "approved"

    delete_response = client.delete(f"/api/bookings/{booking['id']}")
    assert delete_response.status_code == 200

    list_response = client.get("/api/bookings")
    assert list_response.get_json() == []

    history = client.get(f"/api/bookings/{booking['id']}/history").get_json()
    assert [item["action"] for item in history] == ["created", "updated", "deleted"]
