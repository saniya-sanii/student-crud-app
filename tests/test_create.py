"""Tests for POST /students endpoint covering TC-C-01 through TC-C-18 (PRD Section 17.2)."""

from datetime import date, timedelta
from fastapi.testclient import TestClient


def test_tc_c_01_valid_record_with_all_fields(client: TestClient) -> None:
    payload = {
        "name": "Aarav Sharma",
        "date_of_birth": "2005-08-14",
        "email": "aarav.sharma@example.com",
        "phone": "+91 90000-00001",
        "course": "Computer Science",
        "address": "12 Sample Street, Bengaluru",
        "enrollment_date": "2023-08-01",
    }
    res = client.post("/students", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["student_id"] == 1
    assert data["name"] == "Aarav Sharma"
    assert data["date_of_birth"] == "2005-08-14"
    assert data["email"] == "aarav.sharma@example.com"
    assert data["phone"] == "+919000000001"
    assert data["course"] == "Computer Science"
    assert data["address"] == "12 Sample Street, Bengaluru"
    assert data["enrollment_date"] == "2023-08-01"
    assert data["created_at"].endswith("Z")
    assert data["updated_at"].endswith("Z")


def test_tc_c_02_valid_record_with_only_name_dob_and_email(client: TestClient) -> None:
    payload = {
        "name": "Ananya Rao",
        "date_of_birth": "2006-03-22",
        "email": "ananya.rao@example.com",
    }
    res = client.post("/students", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["student_id"] == 1
    assert data["phone"] is None
    assert data["course"] is None
    assert data["address"] is None
    assert data["enrollment_date"] is None


def test_tc_c_03_valid_record_with_phone_no_email(client: TestClient) -> None:
    payload = {
        "name": "Isha Nair",
        "date_of_birth": "2005-01-30",
        "phone": "+919000000004",
    }
    res = client.post("/students", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] is None
    assert data["phone"] == "+919000000004"


def test_tc_c_04_missing_name(client: TestClient) -> None:
    payload = {"date_of_birth": "2005-08-14", "email": "aarav@example.com"}
    res = client.post("/students", json=payload)
    assert res.status_code == 422
    assert any("name" in str(loc) for err in res.json()["detail"] for loc in err["loc"])


def test_tc_c_05_missing_date_of_birth(client: TestClient) -> None:
    payload = {"name": "Aarav Sharma", "email": "aarav@example.com"}
    res = client.post("/students", json=payload)
    assert res.status_code == 422
    assert any("date_of_birth" in str(loc) for err in res.json()["detail"] for loc in err["loc"])


def test_tc_c_06_neither_email_nor_phone(client: TestClient) -> None:
    payload = {"name": "Aarav Sharma", "date_of_birth": "2005-08-14"}
    res = client.post("/students", json=payload)
    assert res.status_code == 422
    assert "Provide at least one of email or phone" in str(res.json()["detail"])


def test_tc_c_07_invalid_email(client: TestClient) -> None:
    payload = {"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "abc@"}
    res = client.post("/students", json=payload)
    assert res.status_code == 422


def test_tc_c_08_invalid_phone(client: TestClient) -> None:
    payload = {"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "phone": "12345"}
    res = client.post("/students", json=payload)
    assert res.status_code == 422


def test_tc_c_09_date_of_birth_in_future(client: TestClient) -> None:
    future_date = (date.today() + timedelta(days=1)).isoformat()
    payload = {"name": "Aarav Sharma", "date_of_birth": future_date, "email": "aarav@example.com"}
    res = client.post("/students", json=payload)
    assert res.status_code == 422


def test_tc_c_10_impossible_date(client: TestClient) -> None:
    payload = {"name": "Aarav Sharma", "date_of_birth": "2005-02-30", "email": "aarav@example.com"}
    res = client.post("/students", json=payload)
    assert res.status_code == 422


def test_tc_c_11_name_length_bounds(client: TestClient) -> None:
    # 1 character
    res1 = client.post("/students", json={"name": "A", "date_of_birth": "2005-01-01", "email": "a@example.com"})
    assert res1.status_code == 422
    # 101 characters
    res2 = client.post("/students", json={"name": "A" * 101, "date_of_birth": "2005-01-01", "email": "a@example.com"})
    assert res2.status_code == 422


def test_tc_c_12_duplicate_email_different_case(client: TestClient) -> None:
    payload1 = {"name": "Student One", "date_of_birth": "2005-01-01", "email": "aarav.sharma@example.com"}
    res1 = client.post("/students", json=payload1)
    assert res1.status_code == 201

    # Second create with same email in uppercase
    payload2 = {"name": "Student Two", "date_of_birth": "2006-01-01", "email": "AARAV.SHARMA@EXAMPLE.COM"}
    res2 = client.post("/students", json=payload2)
    assert res2.status_code == 409
    assert res2.json() == {"detail": "A student with this email already exists"}

    # Confirm count is unchanged (still 1)
    res_list = client.get("/students")
    assert res_list.json()["total"] == 1


def test_tc_c_13_body_includes_student_id(client: TestClient) -> None:
    payload = {"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com", "student_id": 99}
    res = client.post("/students", json=payload)
    assert res.status_code == 422


def test_tc_c_14_body_includes_unknown_field(client: TestClient) -> None:
    payload = {"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com", "nickname": "Ravi"}
    res = client.post("/students", json=payload)
    assert res.status_code == 422


def test_tc_c_15_malformed_json_body(client: TestClient) -> None:
    res = client.post("/students", content='{"name": "Aarav Sharma", ', headers={"Content-Type": "application/json"})
    assert res.status_code == 422


def test_tc_c_16_normalization_name_and_email(client: TestClient) -> None:
    payload = {
        "name": "  Aarav Sharma  ",
        "date_of_birth": "2005-08-14",
        "email": "AARAV@Example.com",
    }
    res = client.post("/students", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Aarav Sharma"
    assert data["email"] == "aarav@example.com"


def test_tc_c_17_sql_injection_attempt_in_name(client: TestClient) -> None:
    injection_name = "x'); DROP TABLE students;--"
    payload = {"name": injection_name, "date_of_birth": "2005-08-14", "email": "safe@example.com"}
    res = client.post("/students", json=payload)
    assert res.status_code == 201
    assert res.json()["name"] == injection_name

    # Table still works
    res_get = client.get(f"/students/{res.json()['student_id']}")
    assert res_get.status_code == 200


def test_tc_c_18_enrollment_date_earlier_than_dob(client: TestClient) -> None:
    payload = {
        "name": "Aarav Sharma",
        "date_of_birth": "2005-08-14",
        "email": "aarav@example.com",
        "enrollment_date": "2005-08-13",
    }
    res = client.post("/students", json=payload)
    assert res.status_code == 422
    assert "enrollment_date cannot be earlier than date_of_birth" in str(res.json()["detail"])
