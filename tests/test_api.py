import os
import tempfile

os.environ["STUDENTS_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

import pytest
from fastapi.testclient import TestClient

from app.main import app

GOOD = {"name": "Test User", "date_of_birth": "2004-05-01", "email": "t@example.com", "course": "Python"}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_full_crud_cycle(client):
    r = client.post("/students", json=GOOD)
    assert r.status_code == 201
    sid = r.json()["id"]

    assert client.get(f"/students/{sid}").json()["name"] == "Test User"
    assert any(s["id"] == sid for s in client.get("/students").json())

    r = client.patch(f"/students/{sid}", json={"course": "Data Science"})
    assert r.status_code == 200 and r.json()["course"] == "Data Science"
    assert r.json()["name"] == "Test User"  # untouched

    r = client.put(f"/students/{sid}", json={**GOOD, "name": "Renamed User"})
    assert r.json()["name"] == "Renamed User"

    assert client.delete(f"/students/{sid}").status_code == 204
    assert client.get(f"/students/{sid}").status_code == 404


def test_validation(client):
    assert client.post("/students", json={**GOOD, "email": "bad"}).status_code == 422
    assert client.post("/students", json={"name": "No Contact", "date_of_birth": "2004-01-01"}).status_code == 422
    assert client.post("/students", json={**GOOD, "date_of_birth": "2999-01-01", "email": "f@e.com"}).status_code == 422
    assert client.post("/students", json={**GOOD, "phone": "abc", "email": "g@e.com"}).status_code == 422


def test_missing_and_duplicate(client):
    assert client.get("/students/99999").status_code == 404
    assert client.patch("/students/99999", json={"name": "Ghost"}).status_code == 404
    assert client.delete("/students/99999").status_code == 404
    client.post("/students", json={**GOOD, "email": "dup@example.com"})
    assert client.post("/students", json={**GOOD, "email": "dup@example.com"}).status_code == 409


def test_patch_cannot_remove_all_contacts(client):
    sid = client.post("/students", json={**GOOD, "email": "only@example.com"}).json()["id"]
    assert client.patch(f"/students/{sid}", json={"email": None}).status_code == 422


def test_filters(client):
    client.post("/students", json={"name": "Old One", "date_of_birth": "1999-01-01", "email": "o@e.com", "course": "Alpha"})
    client.post("/students", json={"name": "Young One", "date_of_birth": "2008-01-01", "email": "y@e.com", "course": "Beta"})
    assert [s["name"] for s in client.get("/students?born_after=2005-12-31&course=Beta").json()] == ["Young One"]
    assert all(s["date_of_birth"] < "2000-01-01" for s in client.get("/students?born_before=2000-01-01").json())


def test_ai_context_is_backend_built(client):
    from app import ai
    from app.database import _connect
    ctx, rows, strategy = ai.build_context(_connect(), "List students born after 2005")
    assert "Total students" in ctx and strategy.startswith("dob_filter")
    assert all(r["date_of_birth"] > "2005-12-31" for r in rows)


def test_ask_returns_503_without_ollama(client, monkeypatch):
    from app import ai
    monkeypatch.setattr(ai, "OLLAMA_URL", "http://127.0.0.1:9")
    assert client.post("/ask", json={"question": "How many students are there?"}).status_code == 503
