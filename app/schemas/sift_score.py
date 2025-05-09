"""
Pydantic schemas for Sift score related operations.
These schemas validate request/response data for Sift score operations.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class SiftScoreBase(BaseModel):
    """Base schema with common Sift score attributes."""
    score: float = Field(..., ge=0, le=100, description="Sift score value (0-100)")
    risk_factors: Optional[List[str]] = Field(None, description="List of risk factors identified by Sift")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional data related to the score")


class SiftScoreCreate(SiftScoreBase):
    """Schema for creating a new Sift score."""
    user_id: UUID = Field(..., description="ID of the user this score belongs to")


class SiftScoreUpdate(SiftScoreBase):
    """Schema for updating an existing Sift score."""
    pass


class SiftScoreInDBBase(SiftScoreBase):
    """Base schema for Sift scores as they exist in the database."""
    id: UUID
    created_at: datetime
    user_id: UUID

    class Config:
        orm_mode = True


class SiftScore(SiftScoreInDBBase):
    """Schema for Sift score information returned to clients."""
    pass


class SiftScoreListItem(BaseModel):
    """
    Schema for Sift score list items.
    Used for listing multiple scores for a user.
    """
    id: UUID
    created_at: datetime
    score: float
    risk_factors: Optional[List[str]] = None

    class Config:
        orm_mode = True