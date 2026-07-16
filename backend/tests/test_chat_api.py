"""会话 API：创建、列表、隔离（不调用真实 LLM）。"""


def _auth_headers(client, username: str, password: str) -> dict:
    if username == "admin":
        resp = client.post("/api/auth/login", json={"username": username, "password": password})
    else:
        resp = client.post("/api/auth/register", json={"username": username, "password": password})
        if resp.status_code != 200:
            resp = client.post("/api/auth/login", json={"username": username, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_list_rename_delete_conversation(client):
    headers = _auth_headers(client, "chat_user1", "123456")

    created = client.post("/api/chat/conversations", headers=headers, json={"title": "测试会话"})
    assert created.status_code == 201
    cid = created.json()["id"]

    listed = client.get("/api/chat/conversations", headers=headers)
    assert listed.status_code == 200
    assert any(i["id"] == cid for i in listed.json()["items"])

    renamed = client.patch(
        f"/api/chat/conversations/{cid}",
        headers=headers,
        json={"title": "改名会话"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "改名会话"

    deleted = client.delete(f"/api/chat/conversations/{cid}", headers=headers)
    assert deleted.status_code == 204


def test_conversation_isolation_between_users(client):
    h1 = _auth_headers(client, "iso_a", "123456")
    h2 = _auth_headers(client, "iso_b", "123456")

    c1 = client.post("/api/chat/conversations", headers=h1, json={"title": "A私密"}).json()
    # B 不能读 A 的消息列表
    resp = client.get(f"/api/chat/conversations/{c1['id']}/messages", headers=h2)
    assert resp.status_code == 404
