"""
Pydantic schemas for assessment-related operations.
These schemas validate request/response data for risk assessment operations.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ThirdPartyDataBase(BaseModel):
    """Base schema for third-party data."""
    source: str
    data: Dict[str, Any]


class ThirdPartyDataCreate(ThirdPartyDataBase):
    """Schema for creating new third-party data."""
    assessment_id: UUID


class ThirdPartyDataInDB(ThirdPartyDataBase):
    """Schema for third-party data as it exists in the database."""
    id: UUID
    assessment_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True


class AssessmentBase(BaseModel):
    """Base schema with common assessment attributes."""
    user_id: UUID
    score: float = Field(..., ge=0, le=100, description="Risk score from 0-100")
    status: str = Field(..., description="Risk status (low, medium, high)")
    reasoning: str = Field(..., description="Explanation for the risk assessment")


class AssessmentCreate(AssessmentBase):
    """Schema for creating a new assessment."""
    sift_score: Optional[float] = Field(None, ge=0, le=100, description="Score from Sift (0-100)")
    llm_response: Optional[Dict[str, Any]] = None


class AssessmentUpdate(BaseModel):
    """Schema for updating an existing assessment."""
    score: Optional[float] = Field(None, ge=0, le=100)
    status: Optional[str] = None
    reasoning: Optional[str] = None
    sift_score: Optional[float] = Field(None, ge=0, le=100)
    llm_response: Optional[Dict[str, Any]] = None


class AssessmentInDBBase(AssessmentBase):
    """Base schema for assessments as they exist in the database."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    sift_score: Optional[float] = None
    llm_response: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class Assessment(AssessmentInDBBase):
    """Schema for assessment information returned to clients."""
    pass


class AssessmentWithThirdPartyData(Assessment):
    """
    Detailed assessment information including third-party data.
    Used for individual assessment API responses.
    """
    third_party_data: List[ThirdPartyDataInDB] = []


class AssessmentRequest(BaseModel):
    """
    Schema for requesting a new assessment.
    Contains the user ID to create an assessment for.
    """
    user_id: UUID


class AssessmentResult(BaseModel):
    """
    Schema for assessment results.
    Contains the score, status, and reasoning.
    """
    score: float = Field(..., ge=0, le=100)
    status: str
    reasoning: str
    
    @validator('status')
    def status_must_be_valid(cls, v):
        """Validate that status is one of the allowed values."""
        allowed = ['low', 'medium', 'high']
        if v.lower() not in allowed:
            raise ValueError(f'Status must be one of {allowed}')
        return v.lower()