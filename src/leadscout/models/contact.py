"""Contact information validation models."""

import re
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class ContactInfo(BaseModel):
    """Contact information structure.

    Standardized representation of contact information with
    validation and normalization.

    Attributes:
        email: Email address
        phone: Primary phone number
        mobile: Mobile phone number
        validated: Whether contact info has been validated
        validation_timestamp: When validation was performed
    """

    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Primary phone number")
    mobile: Optional[str] = Field(None, description="Mobile phone number")
    validated: bool = Field(False, description="Validation status")
    validation_timestamp: Optional[datetime] = Field(
        None, description="Validation timestamp"
    )

    @validator("email")
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate email address format."""
        if v is None or not v.strip():
            return None

        email = v.strip().lower()

        # Basic email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            return None  # Return None for invalid emails rather than raising

        return email

    @validator("phone", "mobile")
    def validate_phone_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize phone number format."""
        if v is None or not v.strip():
            return None

        # Clean phone number
        phone = re.sub(r"[^\d+]", "", v.strip())

        # Normalize South African numbers
        if phone.startswith("+27"):
            phone = "0" + phone[3:]
        elif phone.startswith("27") and len(phone) >= 10:
            phone = "0" + phone[2:]

        # Validate format
        if not re.match(r"^0[1-9]\d{8}$", phone):
            return None  # Return None for invalid numbers

        return phone


class ContactValidation(BaseModel):
    """Contact validation results.

    Contains detailed validation results for contact information
    including reachability and quality scores.

    Attributes:
        email_valid: Email format validation result
        email_deliverable: Email deliverability check (if performed)
        phone_valid: Phone number format validation
        phone_reachable: Phone reachability check (if performed)
        mobile_valid: Mobile number format validation
        mobile_reachable: Mobile reachability check (if performed)
        overall_score: Overall contact quality score (0-100)
        validation_method: Method used for validation
        validated_at: When validation was performed
        notes: Additional validation notes
    """

    # Email validation
    email_valid: bool = Field(False, description="Email format is valid")
    email_deliverable: Optional[bool] = Field(
        None, description="Email deliverability status"
    )

    # Phone validation
    phone_valid: bool = Field(False, description="Phone format is valid")
    phone_reachable: Optional[bool] = Field(
        None, description="Phone reachability status"
    )

    # Mobile validation
    mobile_valid: bool = Field(False, description="Mobile format is valid")
    mobile_reachable: Optional[bool] = Field(
        None, description="Mobile reachability status"
    )

    # Overall metrics
    overall_score: float = Field(
        0.0, ge=0, le=100, description="Overall contact quality score"
    )
    validation_method: str = Field(
        "format", description="Validation method used"
    )
    validated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Validation timestamp"
    )
    notes: list[str] = Field(
        default_factory=list, description="Validation notes"
    )

    @validator("validation_method")
    def validate_method(cls, v: str) -> str:
        """Validate the validation method."""
        valid_methods = {"format", "api", "manual", "combined"}
        if v not in valid_methods:
            raise ValueError(
                f"Invalid validation method. Must be one of: {valid_methods}"
            )
        return v

    def calculate_score(self) -> float:
        """Calculate overall contact quality score.

        Scoring weights:
        - Email valid: 40 points
        - Email deliverable: +10 points
        - Phone valid: 30 points
        - Phone reachable: +10 points
        - Mobile valid: 20 points
        - Mobile reachable: +10 points

        Returns:
            Contact quality score (0-100)
        """
        score = 0.0

        # Email scoring (up to 50 points)
        if self.email_valid:
            score += 40
            if self.email_deliverable:
                score += 10

        # Phone scoring (up to 40 points)
        if self.phone_valid:
            score += 30
            if self.phone_reachable:
                score += 10

        # Mobile scoring (up to 30 points)
        if self.mobile_valid:
            score += 20
            if self.mobile_reachable:
                score += 10

        # Cap at 100
        return min(score, 100.0)

    def update_score(self) -> None:
        """Update the overall score based on current validation results."""
        self.overall_score = self.calculate_score()

    def add_note(self, note: str) -> None:
        """Add a validation note.

        Args:
            note: Validation note to add
        """
        self.notes.append(note)

    def is_high_quality(self, threshold: float = 70.0) -> bool:
        """Check if contact information meets high quality threshold.

        Args:
            threshold: Minimum quality score (default 70.0)

        Returns:
            True if contact quality meets threshold
        """
        return self.overall_score >= threshold

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results.

        Returns:
            Dictionary containing validation summary
        """
        return {
            "email_status": "valid" if self.email_valid else "invalid",
            "phone_status": "valid" if self.phone_valid else "invalid",
            "mobile_status": "valid" if self.mobile_valid else "invalid",
            "overall_score": self.overall_score,
            "quality_level": self.get_quality_level(),
            "has_deliverable_email": self.email_deliverable is True,
            "has_reachable_phone": self.phone_reachable is True
            or self.mobile_reachable is True,
            "note_count": len(self.notes),
        }

    def get_quality_level(self) -> str:
        """Get human-readable quality level description.

        Returns:
            Quality level string
        """
        if self.overall_score >= 90:
            return "Excellent"
        elif self.overall_score >= 75:
            return "Good"
        elif self.overall_score >= 50:
            return "Fair"
        elif self.overall_score >= 25:
            return "Poor"
        else:
            return "Very Poor"

    def get_missing_contact_types(self) -> list[str]:
        """Get list of missing or invalid contact types.

        Returns:
            List of contact types that are missing or invalid
        """
        missing = []

        if not self.email_valid:
            missing.append("email")
        if not self.phone_valid:
            missing.append("phone")
        if not self.mobile_valid:
            missing.append("mobile")

        return missing

    def has_any_valid_contact(self) -> bool:
        """Check if at least one contact method is valid.

        Returns:
            True if any contact method is valid
        """
        return self.email_valid or self.phone_valid or self.mobile_valid
