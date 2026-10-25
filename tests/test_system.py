"""System, persistence, health, and error handling tests covering TC-S-01 through TC-S-08."""

import os
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.database import get_connection, get_db, init_db
from app.main import app
from scripts.seed_data import seed_database


def test_tc_s_01_persistence_across_instances(tmp_path: Path) -> None:
    db_file = str(tmp_path / "persist.db")
    init_db(db_file)

    def override_get_db():
        conn = get_connection(db_file)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db

    # Instance 1: Create student
    with TestClient(app) as client1:
        res = client1.post(
            "/students",
            json={"name": "Persistent Student", "date_of_birth": "2005-01-01", "email": "persist@example.com"},
        )
        assert res.status_code == 201
        sid = res.json()["student_id"]

    # Instance 2: Connect with new client to the same database file
    with TestClient(app) as client2:
        res_fetch = client2.get(f"/students/{sid}")
        assert res_fetch.status_code == 200
        assert res_fetch.json()["name"] == "Persistent Student"

    app.dependency_overrides.clear()


def test_tc_s_02_docs_and_openapi(client: TestClient) -> None:
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200

    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    paths = res_openapi.json()["paths"]
    assert "/students" in paths
    assert "/students/{student_id}" in paths
    assert "/health" in paths


def test_tc_s_03_start_with_no_database_file(tmp_path: Path) -> None:
    db_file = str(tmp_path / "fresh" / "students.db")
    assert not os.path.exists(db_file)
    init_db(db_file)
    assert os.path.exists(db_file)

    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students';")
    assert cursor.fetchone() is not None
    conn.close()


def test_tc_s_04_run_seed_script_twice(tmp_path: Path) -> None:
    db_file = str(tmp_path / "seed_test.db")
    # First seed run
    count1 = seed_database(db_file)
    assert count1 >= 10

    # Second seed run (must insert 0 new records, count unchanged)
    count2 = seed_database(db_file)
    assert count2 == 0

    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM students;")
    total = cursor.fetchone()["total"]
    conn.close()
    assert total == count1


def test_tc_s_05_invalid_cases_never_return_500(client: TestClient) -> None:
    # Run through invalid scenarios: none should trigger 500
    invalid_payloads = [
        {},
        {"date_of_birth": "2005-01-01"},
        {"name": "A", "date_of_birth": "2005-01-01", "email": "a@example.com"},
        {"name": "Valid", "date_of_birth": "2005-01-01", "email": "bad@"},
        {"name": "Valid", "date_of_birth": "2005-01-01", "phone": "123"},
        {"name": "Valid", "date_of_birth": "2099-01-01", "email": "future@example.com"},
        {"name": "Valid", "date_of_birth": "2005-02-30", "email": "impossible@example.com"},
    ]
    for p in invalid_payloads:
        res = client.post("/students", json=p)
        assert res.status_code != 500

    assert client.get("/students?limit=0").status_code != 500
    assert client.get("/students/0").status_code != 500
    assert client.get("/students/abc").status_code != 500


def test_tc_s_06_generic_500_with_no_stack_trace(client: TestClient) -> None:
    # Force an unexpected internal error in repository
    client_no_raise = TestClient(app, raise_server_exceptions=False)
    with patch("app.routers.students.get_student_by_id", side_effect=RuntimeError("Simulated secret database failure")):
        res = client_no_raise.get("/students/1")
        assert res.status_code == 500
        assert res.json() == {"detail": "Internal server error"}
        assert "Simulated secret database failure" not in res.text
        assert "Traceback" not in res.text


def test_tc_s_07_health_check(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_tc_s_08_no_pii_in_server_logs(client: TestClient, caplog) -> None:
    with caplog.at_level("INFO"):
        client.post(
            "/students",
            json={"name": "SecretName", "date_of_birth": "2005-01-01", "email": "secret@example.com", "phone": "+919000000001"},
        )
        log_text = caplog.text
        assert "SecretName" not in log_text
        assert "secret@example.com" not in log_text
        assert "+919000000001" not in log_text
