def test_bootstrap_admin_only_works_once(client):
    r1 = client.post(
        "/api/auth/bootstrap-admin",
        json={"email": "admin@example.com", "full_name": "Admin", "password": "testpass123"},
    )
    assert r1.status_code == 200
    assert r1.json()["role"] == "admin"

    r2 = client.post(
        "/api/auth/bootstrap-admin",
        json={"email": "second@example.com", "full_name": "Second", "password": "testpass123"},
    )
    assert r2.status_code == 403


def test_login_success_and_failure(client, admin_headers):
    ok = client.post("/api/auth/login", data={"username": "admin@example.com", "password": "testpass123"})
    assert ok.status_code == 200
    assert "access_token" in ok.json()

    bad = client.post("/api/auth/login", data={"username": "admin@example.com", "password": "wrong"})
    assert bad.status_code == 401


def test_me_requires_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_register_requires_admin_role(client, admin_headers):
    r = client.post(
        "/api/auth/register",
        json={"email": "inv@example.com", "full_name": "Investigator", "password": "testpass123", "role": "investigator"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["role"] == "investigator"
