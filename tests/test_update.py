"""Tests for PATCH and PUT endpoints covering TC-U-01 through TC-U-12."""

import time
from fastapi.testclient import TestClient


def test_tc_u_01_patch_one_field(client: TestClient) -> None:
    res_c = client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com", "course": "Physics"},
    )
    student_id = res_c.json()["student_id"]
    original_created = res_c.json()["created_at"]

    time.sleep(1)
    res_p = client.patch(f"/students/{student_id}", json={"course": "Bioengineering"})
    assert res_p.status_code == 200
    data = res_p.json()
    assert data["course"] == "Bioengineering"
    assert data["name"] == "Aarav Sharma"
    assert data["created_at"] == original_created
    assert data["updated_at"] >= original_created


def test_tc_u_02_patch_several_valid_fields(client: TestClient) -> None:
    res_c = client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com"},
    )
    student_id = res_c.json()["student_id"]
    original_created = res_c.json()["created_at"]

    res_p = client.patch(
        f"/students/{student_id}",
        json={"course": "Robotics", "address": "New Address", "phone": "+919000000099"},
    )
    assert res_p.status_code == 200
    data = res_p.json()
    assert data["course"] == "Robotics"
    assert data["address"] == "New Address"
    assert data["phone"] == "+919000000099"
    assert data["created_at"] == original_created


def test_tc_u_03_patch_invalid_email(client: TestClient) -> None:
    res_c = client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com"})
    student_id = res_c.json()["student_id"]

    res_p = client.patch(f"/students/{student_id}", json={"email": "bad-email"})
    assert res_p.status_code == 422

    # Check record is unchanged
    res_get = client.get(f"/students/{student_id}")
    assert res_get.json()["email"] == "aarav@example.com"


def test_tc_u_04_patch_missing_id(client: TestClient) -> None:
    res = client.patch("/students/9999", json={"course": "Art"})
    assert res.status_code == 404
    assert res.json() == {"detail": "Student not found"}


def test_tc_u_05_patch_another_students_email(client: TestClient) -> None:
    client.post("/students", json={"name": "Student One", "date_of_birth": "2005-01-01", "email": "one@example.com"})
    res2 = client.post("/students", json={"name": "Student Two", "date_of_birth": "2005-01-02", "email": "two@example.com"})
    id2 = res2.json()["student_id"]

    res_p = client.patch(f"/students/{id2}", json={"email": "one@example.com"})
    assert res_p.status_code == 409
    assert res_p.json() == {"detail": "A student with this email already exists"}


def test_tc_u_06_patch_own_current_email(client: TestClient) -> None:
    res_c = client.post("/students", json={"name": "Aarav", "date_of_birth": "2005-01-01", "email": "aarav@example.com"})
    sid = res_c.json()["student_id"]

    res_p = client.patch(f"/students/{sid}", json={"email": "aarav@example.com"})
    assert res_p.status_code == 200


def test_tc_u_07_patch_empty_body(client: TestClient) -> None:
    res_c = client.post("/students", json={"name": "Aarav", "date_of_birth": "2005-01-01", "email": "aarav@example.com"})
    sid = res_c.json()["student_id"]

    res_p = client.patch(f"/students/{sid}", json={})
    assert res_p.status_code == 422


def test_tc_u_08_patch_clear_optional_field(client: TestClient) -> None:
    res_c = client.post("/students", json={"name": "Aarav", "date_of_birth": "2005-01-01", "email": "aarav@example.com", "address": "Some Address"})
    sid = res_c.json()["student_id"]

    res_p = client.patch(f"/students/{sid}", json={"address": None})
    assert res_p.status_code == 200
    assert res_p.json()["address"] is None


def test_tc_u_09_patch_name_null(client: TestClient) -> None:
    res_c = client.post("/students", json={"name": "Aarav", "date_of_birth": "2005-01-01", "email": "aarav@example.com"})
    sid = res_c.json()["student_id"]

    res_p = client.patch(f"/students/{sid}", json={"name": None})
    assert res_p.status_code == 422


def test_tc_u_10_patch_leaving_neither_email_nor_phone(client: TestClient) -> None:
    # Student with only email
    res_c = client.post("/students", json={"name": "Aarav", "date_of_birth": "2005-01-01", "email": "aarav@example.com"})
    sid = res_c.json()["student_id"]

    res_p = client.patch(f"/students/{sid}", json={"email": None})
    assert res_p.status_code == 422


def test_tc_u_11_patch_containing_student_id(client: TestClient) -> None:
    res_c = client.post("/students", json={"name": "Aarav", "date_of_birth": "2005-01-01", "email": "aarav@example.com"})
    sid = res_c.json()["student_id"]

    res_p = client.patch(f"/students/{sid}", json={"student_id": 999})
    assert res_p.status_code == 422


def test_tc_u_12_put_full_update(client: TestClient) -> None:
    res_c = client.post("/students", json={"name": "Aarav", "date_of_birth": "2005-01-01", "email": "aarav@example.com", "course": "CS"})
    sid = res_c.json()["student_id"]

    # Valid PUT
    put_body = {
        "name": "Aarav Kumar",
        "date_of_birth": "2005-01-01",
        "email": "aarav.kumar@example.com",
        "phone": "+919000000001",
        "course": "Math",
    }
    res_put = client.put(f"/students/{sid}", json=put_body)
    assert res_put.status_code == 200
    assert res_put.json()["name"] == "Aarav Kumar"
    assert res_put.json()["course"] == "Math"

    # PUT missing required field (name) -> 422
    bad_put = {"date_of_birth": "2005-01-01", "email": "bad@example.com"}
    res_bad = client.put(f"/students/{sid}", json=bad_put)
    assert res_bad.status_code == 422
