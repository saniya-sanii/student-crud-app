"""Tests for DELETE /students/{id} covering TC-D-01 through TC-D-06."""

from fastapi.testclient import TestClient


def test_tc_d_01_delete_existing_student_then_get(client: TestClient) -> None:
    res_c = client.post("/students", json={"name": "Aarav", "date_of_birth": "2005-01-01", "email": "aarav@example.com"})
    sid = res_c.json()["student_id"]

    res_del = client.delete(f"/students/{sid}")
    assert res_del.status_code == 204
    assert res_del.content == b""

    # Following GET returns 404
    res_get = client.get(f"/students/{sid}")
    assert res_get.status_code == 404


def test_tc_d_02_delete_same_id_twice(client: TestClient) -> None:
    res_c = client.post("/students", json={"name": "Aarav", "date_of_birth": "2005-01-01", "email": "aarav@example.com"})
    sid = res_c.json()["student_id"]

    res_del1 = client.delete(f"/students/{sid}")
    assert res_del1.status_code == 204

    # Second delete returns 404
    res_del2 = client.delete(f"/students/{sid}")
    assert res_del2.status_code == 404
    assert res_del2.json() == {"detail": "Student not found"}


def test_tc_d_03_delete_missing_id(client: TestClient) -> None:
    res = client.delete("/students/9999")
    assert res.status_code == 404
    assert res.json() == {"detail": "Student not found"}


def test_tc_d_04_delete_with_id_abc(client: TestClient) -> None:
    res = client.delete("/students/abc")
    assert res.status_code == 422


def test_tc_d_05_delete_one_of_three_students(client: TestClient) -> None:
    client.post("/students", json={"name": "Student A", "date_of_birth": "2005-01-01", "email": "a@example.com"})
    client.post("/students", json={"name": "Student B", "date_of_birth": "2005-01-02", "email": "b@example.com"})
    client.post("/students", json={"name": "Student C", "date_of_birth": "2005-01-03", "email": "c@example.com"})

    res_del = client.delete("/students/2")
    assert res_del.status_code == 204

    res_list = client.get("/students")
    items = res_list.json()["items"]
    assert len(items) == 2
    ids = [s["student_id"] for s in items]
    assert ids == [1, 3]


def test_tc_d_06_deleted_id_never_reassigned(client: TestClient) -> None:
    res_a = client.post("/students", json={"name": "Student A", "date_of_birth": "2005-01-01", "email": "a@example.com"})
    id_a = res_a.json()["student_id"]

    # Delete A
    client.delete(f"/students/{id_a}")

    # Create B
    res_b = client.post("/students", json={"name": "Student B", "date_of_birth": "2005-01-02", "email": "b@example.com"})
    id_b = res_b.json()["student_id"]

    assert id_b > id_a
