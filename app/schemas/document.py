"""
Pydantic schemas for document-related operations.
These schemas validate request/response data for document operations.
"""
from datetime import datetime
from typing import Dict, Optional, Any, List
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base schema with common document attributes."""
    document_type: str = Field(..., description="Type of document (passport, id_card, utility_bill, etc.)")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    user_id: UUID = Field(..., description="ID of the user who owns this document")


class DocumentUpdate(BaseModel):
    """Schema for updating an existing document."""
    is_verified: Optional[bool] = None
    rejection_reason: Optional[str] = None


class DocumentInDBBase(DocumentBase):
    """Base schema for documents as they exist in the database."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    file_name: str
    content_type: str
    s3_key: str
    is_verified: bool
    is_processed: bool
    extracted_data: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None

    class Config:
        orm_mode = True


class Document(DocumentInDBBase):
    """Schema for document information returned to clients."""
    download_url: Optional[str] = None


class DocumentWithoutData(BaseModel):
    """
    Schema for document list items without the extracted data.
    Used for listing multiple documents where the extracted data isn't needed.
    """
    id: UUID
    user_id: UUID
    created_at: datetime
    document_type: str
    file_name: str
    is_verified: bool
    is_processed: bool
    download_url: Optional[str] = None

    class Config:
        orm_mode = True


class DocumentUpload(BaseModel):
    """
    Schema for document upload requests.
    Contains metadata about the document being uploaded.
    """
    user_id: UUID
    document_type: str