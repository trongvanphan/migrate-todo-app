def _register(client, email="a@example.com", password="secret123"):
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_and_me(client):
    token = _register(client)
    r = client.get("/auth/me", headers=_headers(token))
    assert r.status_code == 200
    assert r.json()["email"] == "a@example.com"


def test_register_duplicate(client):
    _register(client)
    r = client.post("/auth/register", json={"email": "a@example.com", "password": "secret123"})
    assert r.status_code == 409


def test_login_success_and_failure(client):
    _register(client)
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "secret123"})
    assert r.status_code == 200
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_task_crud(client):
    token = _register(client)
    h = _headers(token)

    r = client.post("/tasks", json={"title": "buy milk"}, headers=h)
    assert r.status_code == 201
    tid = r.json()["id"]
    assert r.json()["completed"] is False

    r = client.get("/tasks", headers=h)
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.patch(f"/tasks/{tid}", json={"completed": True}, headers=h)
    assert r.status_code == 200
    assert r.json()["completed"] is True

    r = client.get("/tasks?filter=active", headers=h)
    assert r.json() == []
    r = client.get("/tasks?filter=completed", headers=h)
    assert len(r.json()) == 1

    r = client.delete(f"/tasks/{tid}", headers=h)
    assert r.status_code == 204
    assert client.get("/tasks", headers=h).json() == []


def test_cross_user_isolation(client):
    token_a = _register(client, "a@example.com")
    token_b = _register(client, "b@example.com")

    r = client.post("/tasks", json={"title": "a's task"}, headers=_headers(token_a))
    a_task_id = r.json()["id"]

    # B cannot see A's tasks
    r = client.get("/tasks", headers=_headers(token_b))
    assert r.json() == []

    # B cannot patch or delete A's task
    assert client.patch(f"/tasks/{a_task_id}", json={"title": "hijack"}, headers=_headers(token_b)).status_code == 404
    assert client.delete(f"/tasks/{a_task_id}", headers=_headers(token_b)).status_code == 404


def test_unauthorized(client):
    assert client.get("/tasks").status_code == 401
    assert client.get("/auth/me").status_code == 401
