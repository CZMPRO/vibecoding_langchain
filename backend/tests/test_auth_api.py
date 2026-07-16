"""认证相关 API。"""


def test_login_admin_success(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["user"]["role"] == "admin"
    assert data["user"]["username"] == "admin"


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "bad"})
    assert resp.status_code == 401


def test_register_and_me(client):
    resp = client.post(
        "/api/auth/register",
        json={"username": "newbie", "password": "abcdef"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "newbie"
    assert me.json()["role"] == "user"


def test_register_admin_reserved(client):
    resp = client.post(
        "/api/auth/register",
        json={"username": "admin", "password": "abcdef"},
    )
    assert resp.status_code == 400


def test_change_password(client):
    # 先注册
    reg = client.post(
        "/api/auth/register",
        json={"username": "pwduser", "password": "oldpass1"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    bad = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"old_password": "wrong", "new_password": "newpass1"},
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"old_password": "oldpass1", "new_password": "newpass1"},
    )
    assert ok.status_code == 200

    # 旧密码不能登录，新密码可以
    assert (
        client.post("/api/auth/login", json={"username": "pwduser", "password": "oldpass1"}).status_code
        == 401
    )
    assert (
        client.post("/api/auth/login", json={"username": "pwduser", "password": "newpass1"}).status_code
        == 200
    )
