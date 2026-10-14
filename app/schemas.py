"""Pydantic models = input validation + response shapes."""
import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-]{6,18}$")


def _validate_phone(v):
    if v is not None and not PHONE_RE.match(v):
        raise ValueError("phone must be 7-19 digits, optional leading +, spaces/dashes allowed")
    return v


def _validate_dob(v):
    if v is not None and v >= date.today():
        raise ValueError("date_of_birth must be in the past")
    return v


class StudentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    course: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    enrollment_date: Optional[date] = None

    _phone = field_validator("phone")(_validate_phone)
    _dob = field_validator("date_of_birth")(_validate_dob)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name must have at least 2 characters")
        return v

    @model_validator(mode="after")
    def _need_contact(self):
        if not self.email and not self.phone:
            raise ValueError("provide at least one contact: email or phone")
        return self


class StudentUpdate(BaseModel):
    """PATCH body: every field optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    course: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    enrollment_date: Optional[date] = None

    _phone = field_validator("phone")(_validate_phone)
    _dob = field_validator("date_of_birth")(_validate_dob)


class StudentOut(BaseModel):
    id: int
    name: str
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class AskResponse(BaseModel):
    question: str
    answer: str
    records_used: int
    context_strategy: str
