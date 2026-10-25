# Students Database CRUD Application

A robust, beginner-friendly backend REST API built with **Python 3**, **FastAPI**, and **SQLite** for managing student records. This project demonstrates clean layered architecture, strict schema validation using **Pydantic v2**, parameterized database queries to prevent SQL injection, unified error formatting, and a complete automated test suite using **pytest**.

---

## Features

- **Full CRUD Operations**:
  - `POST /students`: Create student profiles with server-generated auto-increment IDs and UTC timestamps.
  - `GET /students`: List all students with pagination (`limit`, `offset`) and multi-parameter filtering (`name`, `course`, `born_after`, `born_before`).
  - `GET /students/{student_id}`: Retrieve full profile for a single student.
  - `PATCH /students/{student_id}`: Partially update student records with merged cross-field validation.
  - `PUT /students/{student_id}`: Fully replace editable student attributes.
  - `DELETE /students/{student_id}`: Permanently delete student records (IDs are never reused).
- **Health Check**:
  - `GET /health`: Liveness endpoint returning `{"status": "ok"}`.
- **Strict Validation & Data Integrity**:
  - Double-layer protection: Pydantic v2 schemas reject malformed input before database access; SQLite CHECK and UNIQUE constraints safeguard persistent storage.
  - Case-insensitive email uniqueness (`COLLATE NOCASE`).
  - Cross-field rules: requires at least one contact method (email or phone) and validates that `enrollment_date` is not earlier than `date_of_birth`.
  - Rejects unknown fields (`extra="forbid"`) and blank strings for optional text fields.
- **Security & Privacy**:
  - 100% parameterized SQL queries protecting against SQL injection attacks.
  - Zero PII (Personally Identifiable Information) written to application logs.
  - Generic `500 Internal Server Error` responses preventing stack trace or internal path leakage.
  - Uses only fictional dummy student data.
- **Interactive Documentation**:
  - Built-in Swagger UI at `/docs` and ReDoc at `/redoc`.
- **Automated Testing & Seeding**:
  - 60 automated tests covering all PRD specifications and error cases.
  - Idempotent seed script (`scripts/seed_data.py`) inserting 10 fictional dummy students.

---

## Prerequisites

- **Python**: Version 3.10 or newer (tested with Python 3.13)
- **pip**: Python package installer (bundled with Python)
- **Git**: For version control
- **Terminal**: Command Prompt, PowerShell, or bash/zsh
- **SQLite**: Built into Python standard library (no external installation required)

---

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd students-crud-app
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

*(If PowerShell script execution is restricted, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` before activating, or use Command Prompt: `.venv\Scripts\activate.bat`)*

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Configuration

Settings are managed via environment variables with safe defaults:

| Variable | Default Value | Description |
|---|---|---|
| `DATABASE_PATH` | `data/students.db` | Path to persistent SQLite database file |
| `HOST` | `127.0.0.1` | Host interface to bind server to |
| `PORT` | `8000` | Port to run server on |

A template file `.env.example` is included:
```bash
DATABASE_PATH=data/students.db
```

---

## Running the Application

### 1. Start the API Server
```bash
uvicorn app.main:app --reload
```
The server starts locally at `http://127.0.0.1:8000`.

### 2. Load Dummy Seed Data (Optional)
To populate the database with 10 sample fictional students:
```bash
python -m scripts.seed_data
```
*Note: This script is idempotent—running it multiple times will not duplicate students.*

### 3. Open Documentation
- **Swagger UI (Interactive API tester)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Reference

| Method | Endpoint | Status | Description | Example Payload / Params |
|---|---|---|---|---|
| `GET` | `/health` | `200` | Health check | None |
| `POST` | `/students` | `201` | Create a student | `{"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav.sharma@example.com", "phone": "+919000000001", "course": "Computer Science"}` |
| `GET` | `/students` | `200` | List students with pagination and filters | `?course=Computer%20Science&born_after=2004-12-31&limit=10&offset=0` |
| `GET` | `/students/{student_id}` | `200` | Retrieve student by ID | Path param: `/students/1` |
| `PATCH` | `/students/{student_id}` | `200` | Partially update student | `{"course": "Bioengineering", "address": null}` |
| `PUT` | `/students/{student_id}` | `200` | Replace student profile | `{"name": "Aarav Sharma", "date_of_birth": "2005-08-14", "email": "aarav@example.com", "course": "Robotics"}` |
| `DELETE` | `/students/{student_id}` | `204` | Permanently delete student | Path param: `/students/1` |

### Error Responses
- **`404 Not Found`**:
  ```json
  {"detail": "Student not found"}
  ```
- **`409 Conflict`**:
  ```json
  {"detail": "A student with this email already exists"}
  ```
- **`422 Unprocessable Entity`**: FastAPI standard list of field-level validation errors detailing failing field, input, and rule.
- **`500 Internal Server Error`**: Generic error message without leaking internal details:
  ```json
  {"detail": "Internal server error"}
  ```

---

## API Testing Instructions

### 1. Interactive Testing via Swagger UI
1. Open `http://127.0.0.1:8000/docs`.
2. Expand `POST /students`, click **Try it out**, edit the sample JSON body, and click **Execute**. Confirm status `201 Created` and note the returned `student_id`.
3. Expand `GET /students`, click **Try it out**, enter query parameters (e.g. `name`, `course`, or `limit`), and verify the response list.
4. Expand `GET /students/{student_id}`, provide the `student_id` created earlier, and verify the record is returned.
5. Expand `PATCH /students/{student_id}`, update a single field (such as `course`), and verify `updated_at` refreshes while `created_at` remains unchanged.
6. Expand `DELETE /students/{student_id}`, execute the deletion, and confirm status `204 No Content`.
7. Re-run `GET /students/{student_id}` for the deleted ID and confirm status `404 Not Found`.
8. Test invalid inputs (e.g. invalid email format or ID `0`) to confirm `422 Unprocessable Entity`.

### 2. Testing via cURL

**Create Student:**
```bash
curl -X POST http://127.0.0.1:8000/students \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Aarav Sharma\", \"date_of_birth\": \"2005-08-14\", \"email\": \"aarav.sharma@example.com\", \"phone\": \"+919000000001\", \"course\": \"Computer Science\"}"
```

**List Students:**
```bash
curl "http://127.0.0.1:8000/students?course=Computer%20Science&limit=10"
```

**Get Student by ID:**
```bash
curl http://127.0.0.1:8000/students/1
```

**Partial Update:**
```bash
curl -X PATCH http://127.0.0.1:8000/students/1 \
  -H "Content-Type: application/json" \
  -d "{\"course\": \"Bioengineering\"}"
```

**Delete Student:**
```bash
curl -i -X DELETE http://127.0.0.1:8000/students/1
```

### 3. Automated Test Suite (pytest)
Run the entire suite of 60 automated tests:
```bash
pytest -v
```
All tests execute in isolated temporary databases, ensuring `data/students.db` is never affected.

---

## Project Structure

```text
students-crud-app/
├── app/
│   ├── __init__.py           # Marks app as a Python package
│   ├── main.py               # FastAPI entrypoint, lifespan event, exception handlers
│   ├── config.py             # Application configuration and environment variables
│   ├── database.py           # SQLite connection, DDL schema, and request dependency
│   ├── schemas.py            # Pydantic v2 models for validation and serialization
│   ├── repository.py         # Data Access Layer with parameterized SQL queries
│   └── routers/
│       ├── __init__.py       # Marks routers as a package
│       └── students.py       # CRUD REST endpoints and HTTP status codes
├── scripts/
│   ├── __init__.py           # Marks scripts as a package
│   └── seed_data.py          # Populates 10 fictional dummy student records idempotently
├── tests/
│   ├── conftest.py           # Pytest fixtures and isolated temporary database setup
│   ├── test_create.py        # 18 test cases for POST /students (TC-C-01 to TC-C-18)
│   ├── test_read.py          # 16 test cases for GET /students & GET /{id} (TC-R-01 to TC-R-16)
│   ├── test_update.py        # 12 test cases for PATCH & PUT (TC-U-01 to TC-U-12)
│   ├── test_delete.py        # 6 test cases for DELETE (TC-D-01 to TC-D-06)
│   └── test_system.py        # 8 test cases for system, persistence, and errors (TC-S-01 to TC-S-08)
├── data/
│   └── .gitkeep              # Keeps data/ folder in Git while ignoring *.db files
├── .env.example              # Template for environment configuration
├── .gitignore                # Excludes *.db, .env, .venv/, __pycache__/, .pytest_cache/
├── pytest.ini                # Pytest configuration settings
├── requirements.txt          # Pinned runtime and testing dependencies
└── README.md                 # Complete project documentation
```

---

## Security & Privacy Notes

- **Dummy Data Only**: All sample and seeded student records are strictly fictional, using the reserved `example.com` domain and fake phone numbers. No real personal data should ever be added.
- **Local Development Only**: The API has no authentication or authorization layer (as defined in PRD Section 6.2). It binds to `127.0.0.1` by default and is intended solely for local development and academic evaluation.
- **SQL Injection Prevention**: All database operations use parameter substitution (`?`). Dynamic strings are never concatenated into SQL statements.
- **Data Protection & Logs**: Server logs record operational events without logging student names, emails, phone numbers, or residential addresses.

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---|---|---|
| `ModuleNotFoundError` | Virtual environment is not activated or dependencies are not installed. | Activate `.venv` (`.venv\Scripts\Activate.ps1` or `source .venv/bin/activate`) and run `pip install -r requirements.txt`. |
| `Address already in use` | Another service is using port 8000. | Start server on an alternative port: `uvicorn app.main:app --reload --port 8001`. |
| PowerShell script execution blocked | PowerShell execution policy prevents running local scripts. | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your PowerShell session, or use `.venv\Scripts\activate.bat` in Command Prompt. |
| `database is locked` | Another process has SQLite file open in write mode. | Close any SQLite inspection GUI tools or other running server instances and retry. |
| Import error running seed script | Script was run directly rather than as a module from project root. | Execute from the repository root using `python -m scripts.seed_data`. |

---

## Submission Checklist Verification

- [x] All 5 core CRUD endpoints implemented and functional.
- [x] Input validation with custom Pydantic validators (`VR-01` to `VR-09`).
- [x] SQLite persistence with table constraints, indexes, and UTC timestamp defaults.
- [x] Pinned `requirements.txt` installs cleanly in a fresh virtual environment.
- [x] `.gitignore` excludes `*.db`, `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`.
- [x] Full test suite (60 tests) runs and passes via `pytest`.
- [x] Idempotent seed script (`scripts/seed_data.py`) functional.
- [x] No personal data, real student data, or secrets committed.
- [x] Documentation complete with setup, execution, and API testing instructions.
