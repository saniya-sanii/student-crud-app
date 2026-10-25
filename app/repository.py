"""Data Access Layer (Repository) for Students Database CRUD Application.

Executes 100% parameterized raw SQLite queries.
Endpoints never contain SQL, and the repository never references HTTP concepts.
"""

from datetime import date, datetime, timezone
import sqlite3
from typing import Any, Optional


class RepositoryError(Exception):
    """Base exception for repository layer errors."""
    pass


class DuplicateEmailError(RepositoryError):
    """Raised when an operation would violate unique email constraint."""
    pass


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a sqlite3.Row to a plain dictionary."""
    return dict(row)


def escape_like_pattern(text: str) -> str:
    r"""Escape special SQL LIKE wildcards (%, _) and escape character (\)."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def create_student(conn: sqlite3.Connection, data: dict[str, Any]) -> dict[str, Any]:
    """Insert a new student record using parameterized SQL.

    Args:
        conn: SQLite connection.
        data: Dict containing validated student fields.

    Returns:
        Dict of the newly created student record.

    Raises:
        DuplicateEmailError: If the email already exists in the database.
        RepositoryError: For any other database integrity or execution errors.
    """
    # Normalize dates to ISO string format if passed as date objects
    dob = data["date_of_birth"].isoformat() if isinstance(data["date_of_birth"], date) else data["date_of_birth"]
    enrollment = (
        data["enrollment_date"].isoformat()
        if isinstance(data.get("enrollment_date"), date)
        else data.get("enrollment_date")
    )

    query = """
    INSERT INTO students (name, date_of_birth, email, phone, course, address, enrollment_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        data["name"],
        dob,
        data.get("email"),
        data.get("phone"),
        data.get("course"),
        data.get("address"),
        enrollment,
    )

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        student_id = cursor.lastrowid
        assert student_id is not None
        student = get_student_by_id(conn, student_id)
        assert student is not None
        return student
    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "unique" in error_msg and "email" in error_msg:
            raise DuplicateEmailError("A student with this email already exists") from e
        raise RepositoryError(f"Database integrity error: {e}") from e
    except Exception as e:
        conn.rollback()
        raise RepositoryError(f"Database error: {e}") from e


def get_student_by_id(conn: sqlite3.Connection, student_id: int) -> Optional[dict[str, Any]]:
    """Retrieve a single student by primary key.

    Args:
        conn: SQLite connection.
        student_id: Positive integer ID.

    Returns:
        Dict representing the student if found, else None.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def get_student_by_email(conn: sqlite3.Connection, email: str) -> Optional[dict[str, Any]]:
    """Retrieve a single student by email (case-insensitive)."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE email = ? COLLATE NOCASE", (email.lower(),))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def list_students(
    conn: sqlite3.Connection,
    *,
    name: Optional[str] = None,
    course: Optional[str] = None,
    born_after: Optional[str] = None,
    born_before: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """List students with dynamic filtering and pagination.

    Args:
        conn: SQLite connection.
        name: Case-insensitive partial name match (wildcards escaped).
        course: Case-insensitive exact course match.
        born_after: Strictly after this date (YYYY-MM-DD).
        born_before: Strictly before this date (YYYY-MM-DD).
        limit: Max records to return (1-100).
        offset: Records to skip (>=0).

    Returns:
        Tuple of (items, total_count).
    """
    where_clauses: list[str] = []
    params: list[Any] = []

    if name is not None:
        escaped = escape_like_pattern(name)
        where_clauses.append("LOWER(name) LIKE LOWER(?) ESCAPE '\\'")
        params.append(f"%{escaped}%")

    if course is not None:
        where_clauses.append("course = ? COLLATE NOCASE")
        params.append(course)

    if born_after is not None:
        where_clauses.append("date_of_birth > ?")
        params.append(born_after)

    if born_before is not None:
        where_clauses.append("date_of_birth < ?")
        params.append(born_before)

    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cursor = conn.cursor()

    # Total matching records before pagination
    count_sql = f"SELECT COUNT(*) AS total FROM students{where_sql}"
    cursor.execute(count_sql, tuple(params))
    total_row = cursor.fetchone()
    total = total_row["total"] if total_row else 0

    # Paginated rows ordered by student_id ascending
    select_sql = f"SELECT * FROM students{where_sql} ORDER BY student_id ASC LIMIT ? OFFSET ?"
    query_params = tuple(params + [limit, offset])
    cursor.execute(select_sql, query_params)
    rows = cursor.fetchall()
    items = [_row_to_dict(r) for r in rows]

    return items, total


def update_student(
    conn: sqlite3.Connection,
    student_id: int,
    update_data: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """Update fields of an existing student.

    Args:
        conn: SQLite connection.
        student_id: Positive integer ID.
        update_data: Dict of fields to update.

    Returns:
        Updated student dict, or None if student does not exist.

    Raises:
        DuplicateEmailError: If updated email conflicts with another student.
        RepositoryError: On integrity or database errors.
    """
    # Allowed columns whitelist for safe dynamic query building
    allowed_columns = {
        "name",
        "date_of_birth",
        "email",
        "phone",
        "course",
        "address",
        "enrollment_date",
    }

    set_clauses: list[str] = []
    params: list[Any] = []

    for key, val in update_data.items():
        if key in allowed_columns:
            # Normalize date objects to ISO string
            if isinstance(val, date):
                val = val.isoformat()
            set_clauses.append(f"{key} = ?")
            params.append(val)

    if not set_clauses:
        # Nothing to update
        return get_student_by_id(conn, student_id)

    # Refresh updated_at UTC timestamp
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    set_clauses.append("updated_at = ?")
    params.append(utc_now)

    params.append(student_id)
    query = f"UPDATE students SET {', '.join(set_clauses)} WHERE student_id = ?"

    try:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        if cursor.rowcount == 0:
            conn.rollback()
            return None
        conn.commit()
        return get_student_by_id(conn, student_id)
    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "unique" in error_msg and "email" in error_msg:
            raise DuplicateEmailError("A student with this email already exists") from e
        raise RepositoryError(f"Database integrity error: {e}") from e
    except Exception as e:
        conn.rollback()
        raise RepositoryError(f"Database error: {e}") from e


def delete_student(conn: sqlite3.Connection, student_id: int) -> bool:
    """Permanently delete a student by primary key.

    Args:
        conn: SQLite connection.
        student_id: Positive integer ID.

    Returns:
        True if record was found and deleted, False if record did not exist.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    except Exception as e:
        conn.rollback()
        raise RepositoryError(f"Database error: {e}") from e
