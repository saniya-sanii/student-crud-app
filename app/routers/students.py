"""Student resource router handling HTTP endpoints, status codes, and error formatting."""

from datetime import date
import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app.database import get_db
from app.repository import (
    DuplicateEmailError,
    create_student,
    delete_student,
    get_student_by_id,
    list_students,
    update_student,
)
from app.schemas import (
    StudentCreate,
    StudentListResponse,
    StudentResponse,
    StudentUpdate,
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a student",
    description="Creates a new student record. Returns 201 with generated student_id and UTC timestamps.",
    responses={
        201: {"description": "Student created successfully"},
        409: {"description": "Email already belongs to another student"},
        422: {"description": "Validation error or unknown fields"},
    },
)
def create_student_endpoint(
    student_in: StudentCreate,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """Create a new student in the database."""
    try:
        new_student = create_student(conn, student_in.model_dump())
        return new_student
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this email already exists",
        ) from e


@router.get(
    "",
    response_model=StudentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List and filter students",
    description="Returns a paginated list of students ordered by student_id ascending. Supports multiple query filters combined with AND logic.",
    responses={
        200: {"description": "List of students with pagination metadata"},
        422: {"description": "Invalid query parameters or date range"},
    },
)
def list_students_endpoint(
    name: Optional[str] = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Case-insensitive partial name match",
    ),
    course: Optional[str] = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Case-insensitive exact course match",
    ),
    born_after: Optional[date] = Query(
        default=None,
        description="Matches students born strictly after this date (YYYY-MM-DD)",
    ),
    born_before: Optional[date] = Query(
        default=None,
        description="Matches students born strictly before this date (YYYY-MM-DD)",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Page limit (1 to 100)"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """List students with filtering and pagination."""
    # VR-03: When both are supplied, born_after must be earlier than born_before
    if born_after and born_before and born_after >= born_before:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "type": "value_error",
                    "loc": ["query", "born_after"],
                    "msg": "born_after must be earlier than born_before",
                }
            ],
        )

    items, total = list_students(
        conn,
        name=name,
        course=course,
        born_after=born_after.isoformat() if born_after else None,
        born_before=born_before.isoformat() if born_before else None,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve one student",
    description="Returns the full profile for a single student by positive integer ID.",
    responses={
        200: {"description": "Student found"},
        404: {"description": "Student not found"},
        422: {"description": "Invalid ID (must be a positive integer)"},
    },
)
def get_student_endpoint(
    student_id: int = Path(..., ge=1, description="Positive integer student ID"),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """Retrieve one student by student_id."""
    student = get_student_by_id(conn, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    return student


@router.patch(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a student",
    description="Updates only the supplied fields of an existing student. Re-validates merged state against business rules.",
    responses={
        200: {"description": "Student updated successfully"},
        404: {"description": "Student not found"},
        409: {"description": "Email already belongs to another student"},
        422: {"description": "Validation error or invalid merged record"},
    },
)
def patch_student_endpoint(
    update_in: StudentUpdate,
    student_id: int = Path(..., ge=1, description="Positive integer student ID"),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """Partially update student record."""
    existing = get_student_by_id(conn, student_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    update_dict = update_in.model_dump(exclude_unset=True)
    merged = {**existing, **update_dict}

    # Cross-field re-check (PRD Section 10.4): at least one of email or phone must remain
    if not merged.get("email") and not merged.get("phone"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "type": "value_error",
                    "loc": ["body"],
                    "msg": "An update cannot leave both email and phone empty",
                }
            ],
        )

    # Cross-field re-check (PRD Section 10.4): enrollment_date not before date_of_birth
    merged_dob = merged.get("date_of_birth")
    merged_enrollment = merged.get("enrollment_date")
    if merged_dob and merged_enrollment and str(merged_enrollment) < str(merged_dob):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "type": "value_error",
                    "loc": ["body", "enrollment_date"],
                    "msg": "enrollment_date cannot be earlier than date_of_birth",
                }
            ],
        )

    try:
        updated = update_student(conn, student_id, update_dict)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )
        return updated
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this email already exists",
        ) from e


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Replace a student's editable fields (PUT)",
    description="Full update: requires all mandatory fields (name, date_of_birth, contact) and sets omitted optional fields to null.",
    responses={
        200: {"description": "Student updated successfully"},
        404: {"description": "Student not found"},
        409: {"description": "Email belongs to another student"},
        422: {"description": "Missing required fields or invalid data"},
    },
)
def put_student_endpoint(
    student_in: StudentCreate,
    student_id: int = Path(..., ge=1, description="Positive integer student ID"),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """Full update replacing all editable fields of a student."""
    existing = get_student_by_id(conn, student_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # In PUT, optional fields omitted from input are explicitly set to None
    put_data = {
        "name": student_in.name,
        "date_of_birth": student_in.date_of_birth,
        "email": student_in.email,
        "phone": student_in.phone,
        "course": student_in.course,
        "address": student_in.address,
        "enrollment_date": student_in.enrollment_date,
    }

    try:
        updated = update_student(conn, student_id, put_data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )
        return updated
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this email already exists",
        ) from e


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a student",
    description="Permanently deletes the student record. Returns 204 No Content. Returns 404 if the record does not exist or was already deleted.",
    responses={
        204: {"description": "Student successfully deleted"},
        404: {"description": "Student not found"},
        422: {"description": "Invalid student_id"},
    },
)
def delete_student_endpoint(
    student_id: int = Path(..., ge=1, description="Positive integer student ID"),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    """Delete a student record permanently."""
    deleted = delete_student(conn, student_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
