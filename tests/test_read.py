"""Tests for GET /students and GET /students/{id} covering TC-R-01 through TC-R-16."""

from fastapi.testclient import TestClient


def test_tc_r_01_list_empty_database(client: TestClient) -> None:
    res = client.get("/students")
    assert res.status_code == 200
    assert res.json() == {"total": 0, "limit": 20, "offset": 0, "items": []}


def test_tc_r_02_list_after_creating_three_students_ordered(client: TestClient) -> None:
    client.post("/students", json={"name": "Student A", "date_of_birth": "2005-01-01", "email": "a@example.com"})
    client.post("/students", json={"name": "Student B", "date_of_birth": "2005-01-02", "email": "b@example.com"})
    client.post("/students", json={"name": "Student C", "date_of_birth": "2005-01-03", "email": "c@example.com"})

    res = client.get("/students")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 3
    assert items[0]["student_id"] == 1
    assert items[1]["student_id"] == 2
    assert items[2]["student_id"] == 3


def test_tc_r_03_pagination_limit_and_offset(client: TestClient) -> None:
    client.post("/students", json={"name": "Student A", "date_of_birth": "2005-01-01", "email": "a@example.com"})
    client.post("/students", json={"name": "Student B", "date_of_birth": "2005-01-02", "email": "b@example.com"})
    client.post("/students", json={"name": "Student C", "date_of_birth": "2005-01-03", "email": "c@example.com"})

    res = client.get("/students?limit=2&offset=1")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 1
    items = data["items"]
    assert len(items) == 2
    assert items[0]["student_id"] == 2
    assert items[1]["student_id"] == 3


def test_tc_r_04_pagination_invalid_limits(client: TestClient) -> None:
    assert client.get("/students?limit=0").status_code == 422
    assert client.get("/students?limit=101").status_code == 422
    assert client.get("/students?offset=-1").status_code == 422


def test_tc_r_05_filter_name_partial_case_insensitive(client: TestClient) -> None:
    client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com"})
    client.post("/students", json={"name": "Ananya Rao", "date_of_birth": "2006-03-22", "email": "ananya@example.com"})

    res = client.get("/students?name=aa")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Aarav Sharma"


def test_tc_r_06_filter_course_exact_case_insensitive(client: TestClient) -> None:
    client.post("/students", json={"name": "Student 1", "date_of_birth": "2005-01-01", "email": "1@example.com", "course": "Computer Science"})
    client.post("/students", json={"name": "Student 2", "date_of_birth": "2005-01-01", "email": "2@example.com", "course": "Civil Engineering"})

    res = client.get("/students?course=computer science")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["course"] == "Computer Science"


def test_tc_r_07_filter_born_after_strictly_after(client: TestClient) -> None:
    client.post("/students", json={"name": "Border Student", "date_of_birth": "2005-12-31", "email": "border@example.com"})
    client.post("/students", json={"name": "Younger Student", "date_of_birth": "2006-01-01", "email": "younger@example.com"})

    res = client.get("/students?born_after=2005-12-31")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Younger Student"


def test_tc_r_08_filter_born_before_strictly_before(client: TestClient) -> None:
    client.post("/students", json={"name": "Older Student", "date_of_birth": "2004-12-31", "email": "older@example.com"})
    client.post("/students", json={"name": "Border Student", "date_of_birth": "2005-01-01", "email": "border@example.com"})

    res = client.get("/students?born_before=2005-01-01")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Older Student"


def test_tc_r_09_combined_filters_with_and_logic(client: TestClient) -> None:
    client.post("/students", json={"name": "CS Student Old", "date_of_birth": "2004-01-01", "email": "cs_old@example.com", "course": "Computer Science"})
    client.post("/students", json={"name": "CS Student Young", "date_of_birth": "2006-01-01", "email": "cs_young@example.com", "course": "Computer Science"})
    client.post("/students", json={"name": "Bio Student Young", "date_of_birth": "2006-01-01", "email": "bio_young@example.com", "course": "Bioengineering"})

    res = client.get("/students?course=Computer%20Science&born_after=2005-01-01")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "CS Student Young"


def test_tc_r_10_invalid_filter_date(client: TestClient) -> None:
    res = client.get("/students?born_after=banana")
    assert res.status_code == 422


def test_tc_r_11_born_after_later_than_born_before(client: TestClient) -> None:
    res = client.get("/students?born_after=2006-01-01&born_before=2005-01-01")
    assert res.status_code == 422


def test_tc_r_12_filter_with_no_matches_returns_200_empty(client: TestClient) -> None:
    client.post("/students", json={"name": "Student A", "date_of_birth": "2005-01-01", "email": "a@example.com", "course": "Physics"})
    res = client.get("/students?course=Music")
    assert res.status_code == 200
    assert res.json() == {"total": 0, "limit": 20, "offset": 0, "items": []}


def test_tc_r_13_literal_wildcard_escaping(client: TestClient) -> None:
    client.post("/students", json={"name": "Student%Special", "date_of_birth": "2005-01-01", "email": "special@example.com"})
    client.post("/students", json={"name": "Normal Student", "date_of_birth": "2005-01-01", "email": "normal@example.com"})

    # Searching for % should ONLY match Student%Special
    res = client.get("/students?name=%")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Student%Special"


def test_tc_r_14_get_student_by_id_existing(client: TestClient) -> None:
    res_create = client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com"})
    student_id = res_create.json()["student_id"]

    res = client.get(f"/students/{student_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["student_id"] == student_id
    assert data["name"] == "Aarav Sharma"


def test_tc_r_15_get_student_by_id_missing_returns_404(client: TestClient) -> None:
    res = client.get("/students/9999")
    assert res.status_code == 404
    assert res.json() == {"detail": "Student not found"}


def test_tc_r_16_get_student_invalid_ids(client: TestClient) -> None:
    for bad_id in ["abc", "0", "-1"]:
        res = client.get(f"/students/{bad_id}")
        assert res.status_code == 422
