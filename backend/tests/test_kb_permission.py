"""知识库权限：仅管理员可访问。"""


def _login(client, username: str, password: str) -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_admin_can_list_documents(client):
    token = _login(client, "admin", "123456")
    resp = client.get("/api/kb/documents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "meta" in body


def test_user_cannot_list_documents(client):
    reg = client.post(
        "/api/auth/register",
        json={"username": "normal_u", "password": "123456"},
    )
    token = reg.json()["access_token"]
    resp = client.get("/api/kb/documents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_user_cannot_access_stats(client):
    reg = client.post(
        "/api/auth/register",
        json={"username": "normal_s", "password": "123456"},
    )
    token = reg.json()["access_token"]
    resp = client.get("/api/stats/overview", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_admin_stats_ok(client):
    token = _login(client, "admin", "123456")
    resp = client.get("/api/stats/overview", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "user_count" in data
    assert data["user_count"] >= 1
