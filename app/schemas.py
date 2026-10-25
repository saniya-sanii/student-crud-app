"""Pydantic validation schemas for Students Database CRUD Application."""

from datetime import date
import re
from typing import Any, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

# Regex patterns
PHONE_REGEX = re.compile(r"^\+?[0-9]{10,15}$")
CONTROL_CHARS_REGEX = re.compile(r"[\x00-\x1f\x7f-\x9f]")
MIN_DATE_OF_BIRTH = date(1900, 1, 1)


def validate_and_normalize_name(v: Optional[str]) -> Optional[str]:
    """Validate and trim student name according to PRD Section 12.1."""
    if v is None:
        return None
    trimmed = v.strip()
    if not (2 <= len(trimmed) <= 100):
        raise ValueError("Name must be between 2 and 100 characters after trimming")
    if not any(c.isalpha() for c in trimmed):
        raise ValueError("Name must contain at least one letter")
    if CONTROL_CHARS_REGEX.search(trimmed):
        raise ValueError("Name must not contain control characters")
    return trimmed


def validate_and_normalize_phone(v: Optional[str]) -> Optional[str]:
    """Strip spaces/hyphens and validate phone number (PRD Section 12.1)."""
    if v is None:
        return None
    # Reject blank string if provided
    if not v.strip():
        raise ValueError("Phone number cannot be blank; use null or omit")
    # Remove whitespace and hyphens
    normalized = v.replace(" ", "").replace("-", "")
    if not PHONE_REGEX.match(normalized):
        raise ValueError(
            "Phone must be 10 to 15 digits with an optional leading plus sign"
        )
    return normalized


def validate_and_normalize_course(v: Optional[str]) -> Optional[str]:
    """Validate and trim course name (PRD Section 12.1)."""
    if v is None:
        return None
    trimmed = v.strip()
    if not trimmed:
        raise ValueError("Course cannot be blank; use null or omit the field")
    if not (2 <= len(trimmed) <= 100):
        raise ValueError("Course must be between 2 and 100 characters after trimming")
    return trimmed


def validate_and_normalize_address(v: Optional[str]) -> Optional[str]:
    """Validate and trim address (PRD Section 12.1)."""
    if v is None:
        return None
    trimmed = v.strip()
    if not trimmed:
        raise ValueError("Address cannot be blank; use null or omit the field")
    if not (1 <= len(trimmed) <= 255):
        raise ValueError("Address must be between 1 and 255 characters after trimming")
    return trimmed


def validate_date_of_birth(v: Optional[date]) -> Optional[date]:
    """Validate date of birth is between 1900-01-01 and today (PRD Section 12.1)."""
    if v is None:
        return None
    today = date.today()
    if v > today:
        raise ValueError("Date of birth cannot be in the future")
    if v < MIN_DATE_OF_BIRTH:
        raise ValueError(f"Date of birth cannot be before {MIN_DATE_OF_BIRTH.isoformat()}")
    return v


def validate_enrollment_date(v: Optional[date]) -> Optional[date]:
    """Validate enrollment date is not in the future (PRD Section 12.1)."""
    if v is None:
        return None
    today = date.today()
    if v > today:
        raise ValueError("Enrollment date cannot be in the future")
    return v


class StudentCreate(BaseModel):
    """Schema for creating a new student record (POST /students)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Student full name (2-100 characters)")
    date_of_birth: date = Field(..., description="Date of birth in YYYY-MM-DD format")
    email: Optional[EmailStr] = Field(default=None, description="Unique email address")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    course: Optional[str] = Field(default=None, description="Enrolled course")
    address: Optional[str] = Field(default=None, description="Residential address")
    enrollment_date: Optional[date] = Field(default=None, description="Enrollment date in YYYY-MM-DD format")

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        res = validate_and_normalize_name(v)
        assert res is not None
        return res

    @field_validator("email")
    @classmethod
    def check_email(cls, v: Optional[EmailStr]) -> Optional[str]:
        if v is None:
            return None
        email_str = str(v).lower()
        if len(email_str) > 254:
            raise ValueError("Email must be at most 254 characters")
        return email_str

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_and_normalize_phone(v)

    @field_validator("course")
    @classmethod
    def check_course(cls, v: Optional[str]) -> Optional[str]:
        return validate_and_normalize_course(v)

    @field_validator("address")
    @classmethod
    def check_address(cls, v: Optional[str]) -> Optional[str]:
        return validate_and_normalize_address(v)

    @field_validator("date_of_birth")
    @classmethod
    def check_dob(cls, v: date) -> date:
        res = validate_date_of_birth(v)
        assert res is not None
        return res

    @field_validator("enrollment_date")
    @classmethod
    def check_enrollment(cls, v: Optional[date]) -> Optional[date]:
        return validate_enrollment_date(v)

    @model_validator(mode="after")
    def validate_cross_field_rules(self) -> "StudentCreate":
        # Rule VR-01: At least one of email or phone must be provided
        if not self.email and not self.phone:
            raise ValueError("Provide at least one of email or phone")

        # Rule VR-02: enrollment_date must not be before date_of_birth
        if self.enrollment_date and self.date_of_birth:
            if self.enrollment_date < self.date_of_birth:
                raise ValueError("enrollment_date cannot be earlier than date_of_birth")

        return self


class StudentUpdate(BaseModel):
    """Schema for partially updating a student record (PATCH /students/{id})."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, description="Updated name")
    date_of_birth: Optional[date] = Field(default=None, description="Updated date of birth")
    email: Optional[EmailStr] = Field(default=None, description="Updated email")
    phone: Optional[str] = Field(default=None, description="Updated phone")
    course: Optional[str] = Field(default=None, description="Updated course")
    address: Optional[str] = Field(default=None, description="Updated address")
    enrollment_date: Optional[date] = Field(default=None, description="Updated enrollment date")

    @model_validator(mode="before")
    @classmethod
    def check_patch_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # VR-06: Empty body {} returns 422
        if len(data) == 0:
            raise ValueError("A PATCH body must contain at least one field")
        # VR-07: name and date_of_birth cannot be set to null
        if "name" in data and data["name"] is None:
            raise ValueError("name cannot be set to null")
        if "date_of_birth" in data and data["date_of_birth"] is None:
            raise ValueError("date_of_birth cannot be set to null")
        return data

    @field_validator("name")
    @classmethod
    def check_name(cls, v: Optional[str]) -> Optional[str]:
        return validate_and_normalize_name(v)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: Optional[EmailStr]) -> Optional[str]:
        if v is None:
            return None
        email_str = str(v).lower()
        if len(email_str) > 254:
            raise ValueError("Email must be at most 254 characters")
        return email_str

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_and_normalize_phone(v)

    @field_validator("course")
    @classmethod
    def check_course(cls, v: Optional[str]) -> Optional[str]:
        return validate_and_normalize_course(v)

    @field_validator("address")
    @classmethod
    def check_address(cls, v: Optional[str]) -> Optional[str]:
        return validate_and_normalize_address(v)

    @field_validator("date_of_birth")
    @classmethod
    def check_dob(cls, v: Optional[date]) -> Optional[date]:
        return validate_date_of_birth(v)

    @field_validator("enrollment_date")
    @classmethod
    def check_enrollment(cls, v: Optional[date]) -> Optional[date]:
        return validate_enrollment_date(v)


class StudentResponse(BaseModel):
    """Schema representing a stored student record in responses."""

    model_config = ConfigDict(from_attributes=True)

    student_id: int
    name: str
    date_of_birth: str
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[str] = None
    created_at: str
    updated_at: str


class StudentListResponse(BaseModel):
    """Schema for paginated student list responses."""

    total: int = Field(..., description="Total matching records before pagination")
    limit: int = Field(..., description="Maximum records requested")
    offset: int = Field(..., description="Number of records skipped")
    items: list[StudentResponse] = Field(..., description="List of student records")


class StudentFilterParams(BaseModel):
    """Query parameters for GET /students list and filter endpoint."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    course: Optional[str] = Field(default=None, min_length=1, max_length=100)
    born_after: Optional[date] = None
    born_before: Optional[date] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_filter_dates(self) -> "StudentFilterParams":
        # VR-03: When both are supplied, born_after must be earlier than born_before
        if self.born_after and self.born_before:
            if self.born_after >= self.born_before:
                raise ValueError("born_after must be earlier than born_before")
        return self
