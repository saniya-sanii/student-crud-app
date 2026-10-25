"""Database seed script populating at least 10 fictional dummy student records.

Uses fictional dummy data with reserved example.com domain and fake phone numbers (PRD Section 12.4).
Idempotent: safe to run repeatedly without creating duplicates (PRD FR-DB-05).
"""

import sys
from typing import Any, Optional

from app.database import get_connection, init_db

# Fictional dummy students (strictly non-real data with example.com)
DUMMY_STUDENTS: list[dict[str, Any]] = [
    {
        "name": "Aarav Sharma",
        "date_of_birth": "2005-08-14",
        "email": "aarav.sharma@example.com",
        "phone": "+919000000001",
        "course": "Computer Science",
        "address": "12 Sample Street, Bengaluru",
        "enrollment_date": "2023-08-01",
    },
    {
        "name": "Ananya Rao",
        "date_of_birth": "2006-03-22",
        "email": "ananya.rao@example.com",
        "phone": "+919000000002",
        "course": "Bioengineering",
        "address": "45 Green Park, Hyderabad",
        "enrollment_date": "2024-07-15",
    },
    {
        "name": "Rohan Mehta",
        "date_of_birth": "2004-11-05",
        "email": "rohan.mehta@example.com",
        "phone": None,
        "course": "Computer Science",
        "address": "88 Marine Lines, Mumbai",
        "enrollment_date": "2022-08-10",
    },
    {
        "name": "Isha Nair",
        "date_of_birth": "2005-01-30",
        "email": None,
        "phone": "+919000000004",
        "course": "Biotechnology",
        "address": "14 Lake Road, Kochi",
        "enrollment_date": "2023-09-01",
    },
    {
        "name": "Karthik Iyer",
        "date_of_birth": "2007-06-18",
        "email": "karthik.iyer@example.com",
        "phone": "+919000000005",
        "course": "Information Science",
        "address": "22 Temple View, Chennai",
        "enrollment_date": "2025-01-10",
    },
    {
        "name": "Priya Patel",
        "date_of_birth": "2004-05-12",
        "email": "priya.patel@example.com",
        "phone": "+919000000006",
        "course": "Mathematics",
        "address": "7 Ring Road, Ahmedabad",
        "enrollment_date": "2022-07-20",
    },
    {
        "name": "Vikram Singh",
        "date_of_birth": "2006-09-09",
        "email": "vikram.singh@example.com",
        "phone": None,
        "course": "Mechanical Engineering",
        "address": "101 Civil Lines, Jaipur",
        "enrollment_date": "2024-08-01",
    },
    {
        "name": "Neha Gupta",
        "date_of_birth": "2007-12-04",
        "email": None,
        "phone": "+919000000008",
        "course": "Physics",
        "address": "55 Mall Road, Delhi",
        "enrollment_date": "2025-02-01",
    },
    {
        "name": "Devendra Joshi",
        "date_of_birth": "2003-04-19",
        "email": "devendra.joshi@example.com",
        "phone": "+919000000009",
        "course": "Computer Science",
        "address": "33 Hill Road, Pune",
        "enrollment_date": "2021-08-15",
    },
    {
        "name": "Meera Menon",
        "date_of_birth": "2006-11-28",
        "email": "meera.menon@example.com",
        "phone": "+919000000010",
        "course": "Economics",
        "address": "19 Beach Walk, Kozhikode",
        "enrollment_date": "2024-09-01",
    },
]


def seed_database(db_path: Optional[str] = None) -> int:
    """Seed the database with dummy students idempotently.

    Args:
        db_path: Path to database; defaults to config.DATABASE_PATH.

    Returns:
        Number of newly inserted students.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    inserted_count = 0

    try:
        cursor = conn.cursor()
        for student in DUMMY_STUDENTS:
            # Check for existing record to maintain idempotency
            if student["email"]:
                cursor.execute(
                    "SELECT student_id FROM students WHERE email = ? COLLATE NOCASE",
                    (student["email"],),
                )
                if cursor.fetchone():
                    continue
            elif student["phone"]:
                cursor.execute(
                    "SELECT student_id FROM students WHERE phone = ?",
                    (student["phone"],),
                )
                if cursor.fetchone():
                    continue

            cursor.execute(
                """
                INSERT INTO students (name, date_of_birth, email, phone, course, address, enrollment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student["name"],
                    student["date_of_birth"],
                    student["email"],
                    student["phone"],
                    student["course"],
                    student["address"],
                    student["enrollment_date"],
                ),
            )
            inserted_count += 1

        conn.commit()
    finally:
        conn.close()

    return inserted_count


if __name__ == "__main__":
    count = seed_database()
    print(f"Seed finished: {count} new students added.")
