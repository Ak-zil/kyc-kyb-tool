"""
Document model for the KYC/KYB application.
Contains information about documents uploaded by users.
"""
import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, DateTime, String, ForeignKey, JSON, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Document(Base):
    """
    Document model representing uploaded KYC/KYB documents.
    
    Attributes:
        id (UUID): Unique identifier for the document
        created_at (DateTime): When the document was created
        updated_at (DateTime): When the document was last updated
        user_id (UUID): Reference to the user who uploaded this document
        document_type (str): Type of document (passport, id_card, utility_bill, etc.)
        file_name (str): Original file name
        content_type (str): MIME type of the file
        s3_key (str): Key to access the file in S3
        is_verified (bool): Whether the document has been verified
        extracted_data (JSON): Data extracted from the document
        rejection_reason (str, optional): Reason for rejection if not verified
        user (relationship): Relationship to the user who uploaded this document
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Document information
    document_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    
    # Extracted information from document
    extracted_data = Column(JSON, nullable=True)
    
    # Rejection information
    rejection_reason = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")

    def __repr__(self):
        """String representation of the document."""
        return f"<Document {self.document_type} for User {self.user_id}>"