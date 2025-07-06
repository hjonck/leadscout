"""CIPC (Companies and Intellectual Property Commission) data models.

This module defines the data models for South African company information
from the CIPC registry system.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CIPCCompany(BaseModel):
    """CIPC company registration data model.
    
    Represents company information from the South African
    Companies and Intellectual Property Commission registry.
    """
    
    registration_number: str = Field(..., description="CIPC registration number")
    company_name: str = Field(..., description="Official company name")
    company_status: Optional[str] = Field(None, description="Company status (Active, Inactive, etc.)")
    registration_date: Optional[str] = Field(None, description="Date of registration")
    business_start_date: Optional[str] = Field(None, description="Business start date")
    company_type: Optional[str] = Field(None, description="Type of company (Pty Ltd, etc.)")
    company_sub_type: Optional[str] = Field(None, description="Company sub-type")
    address_line_1: Optional[str] = Field(None, description="Address line 1")
    address_line_2: Optional[str] = Field(None, description="Address line 2")
    postal_code: Optional[str] = Field(None, description="Postal code")
    province: Optional[str] = Field(None, description="Province")
    main_business_activity: Optional[str] = Field(None, description="Main business activity")
    sic_code: Optional[str] = Field(None, description="Standard Industrial Classification code")
    filing_status: Optional[str] = Field(None, description="Filing status")
    annual_return_date: Optional[str] = Field(None, description="Annual return date")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record update timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }