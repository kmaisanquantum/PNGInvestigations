import os
import tempfile

import pytest

# Configure environment BEFORE any app module is imported anywhere in the
# test session, since Settings/engine/Base are constructed at import time.
_tmp_dir = tempfile.mkdtemp(prefix="invplat-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_dir}/test.db"
os.environ["EVIDENCE_STORAGE_PATH"] = f"{_tmp_dir}/evidence"
os.environ["JWT_SECRET"] = "test-secret"

from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def client():
    # Fresh schema for every test — cheap with sqlite, keeps tests isolated.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_headers(client):
    client.post(
        "/api/auth/bootstrap-admin",
        json={"email": "admin@example.com", "full_name": "Admin", "password": "testpass123"},
    )
    r = client.post("/api/auth/login", data={"username": "admin@example.com", "password": "testpass123"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
