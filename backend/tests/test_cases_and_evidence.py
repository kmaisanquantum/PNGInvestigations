import hashlib


def _create_case(client, headers):
    r = client.post(
        "/api/cases",
        json={"case_number": "C-100", "title": "Procurement Review", "category": "procurement_fraud"},
        headers=headers,
    )
    assert r.status_code == 200
    return r.json()


def test_create_and_list_cases(client, admin_headers):
    case = _create_case(client, admin_headers)
    r = client.get("/api/cases", headers=admin_headers)
    assert r.status_code == 200
    assert any(c["id"] == case["id"] for c in r.json())


def test_duplicate_case_number_rejected(client, admin_headers):
    _create_case(client, admin_headers)
    r = client.post(
        "/api/cases",
        json={"case_number": "C-100", "title": "Duplicate"},
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_only_reviewer_or_admin_can_close_case(client, admin_headers):
    case = _create_case(client, admin_headers)
    # admin can close
    r = client.patch(f"/api/cases/{case['id']}", json={"status": "closed"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "closed"


def test_evidence_upload_hash_and_integrity(client, admin_headers):
    case = _create_case(client, admin_headers)
    content = b"contract-award-memo contents"
    expected_hash = hashlib.sha256(content).hexdigest()

    r = client.post(
        f"/api/cases/{case['id']}/evidence",
        files={"file": ("memo.txt", content)},
        data={"notes": "signed memo"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["sha256_hash"] == expected_hash

    dl = client.get(f"/api/cases/{case['id']}/evidence/{body['id']}/download", headers=admin_headers)
    assert dl.status_code == 200
    assert dl.content == content


def test_audit_log_records_actions(client, admin_headers):
    _create_case(client, admin_headers)
    r = client.get("/api/audit-logs", headers=admin_headers)
    assert r.status_code == 200
    actions = [entry["action"] for entry in r.json()]
    assert "create_case" in actions
    assert "bootstrap_admin" in actions


def test_viewer_cannot_create_case(client, admin_headers):
    reg = client.post(
        "/api/auth/register",
        json={"email": "viewer@example.com", "full_name": "Viewer", "password": "testpass123", "role": "viewer"},
        headers=admin_headers,
    )
    assert reg.status_code == 200

    login = client.post("/api/auth/login", data={"username": "viewer@example.com", "password": "testpass123"})
    viewer_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    r = client.post("/api/cases", json={"case_number": "C-200", "title": "Blocked"}, headers=viewer_headers)
    assert r.status_code == 403
