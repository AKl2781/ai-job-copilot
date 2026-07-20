"""Candidate profile request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator


class ProfileFields(BaseModel):
    """Fields shared by profile write operations."""

    name: str = Field(min_length=1, max_length=200)
    target_role: str | None = Field(default=None, max_length=200)
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)

    @field_validator("name", "target_role", "summary")
    @classmethod
    def strip_text(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped and info.field_name == "name":
            raise ValueError("name must not be blank")
        return stripped

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, skills: list[str]) -> list[str]:
        normalized = [skill.strip() for skill in skills]
        if any(not skill for skill in normalized):
            raise ValueError("skills must not contain blank values")
        return normalized


class ProfileCreate(ProfileFields):
    """Create the current user's profile."""


class ProfileUpdate(BaseModel):
    """Update only the supplied current-user profile fields."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    target_role: str | None = Field(default=None, max_length=200)
    summary: str | None = None
    skills: list[str] | None = None

    @field_validator("name", "target_role", "summary")
    @classmethod
    def strip_text(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped and info.field_name == "name":
            raise ValueError("name must not be blank")
        return stripped

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, skills: list[str] | None) -> list[str] | None:
        if skills is None:
            return None
        normalized = [skill.strip() for skill in skills]
        if any(not skill for skill in normalized):
            raise ValueError("skills must not contain blank values")
        return normalized

    @model_validator(mode="after")
    def require_changes(self) -> "ProfileUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one profile field is required")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        if "skills" in self.model_fields_set and self.skills is None:
            raise ValueError("skills cannot be null")
        return self


class ProfileRead(ProfileFields):
    """Persisted candidate profile."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
