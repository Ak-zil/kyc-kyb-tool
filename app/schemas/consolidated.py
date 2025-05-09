"""
Pydantic schemas for consolidated data upload.
These schemas support uploading user profile, documents, and Sift score in a single request.
"""
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from app.schemas.user import UserBase
from app.schemas.document import DocumentBase


class DocumentUploadItem(DocumentBase):
    """Schema for a document in the consolidated upload."""
    file_name: str
    content_type: str
    document_content: str = Field(..., description="Base64 encoded document content")


class ConsolidatedUserUpload(UserBase):
    """
    Schema for uploading all user data in a single request.
    Includes user information, documents, and Sift score.
    """
    # User profile fields are inherited from UserBase
    
    # Sift score (directly provided by user)
    sift_score: Optional[float] = Field(None, ge=0, le=100, description="User-provided Sift score (0-100)")
    
    # Documents to upload
    documents: List[DocumentUploadItem] = Field(default_factory=list, description="Documents to upload")
    
    @validator('sift_score')
    def validate_sift_score(cls, v):
        """Validate that the Sift score is within range."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Sift score must be between 0 and 100")
        return v


class ConsolidatedUserCreateResponse(BaseModel):
    """
    Schema for the response after creating a user with consolidated data.
    """
    user_id: UUID
    email: EmailStr
    full_name: str
    is_business: bool
    sift_score_processed: bool
    documents_processed: int
    assessment_requested: bool
    assessment_id: Optional[UUID] = None


class ConsolidatedUserUpdateResponse(BaseModel):
    """
    Schema for the response after updating a user with consolidated data.
    """
    user_id: UUID
    email: EmailStr
    documents_added: int
    sift_score_updated: bool
    assessment_requested: bool
    assessment_id: Optional[UUID] = None