"""
User model for the KYC/KYB application.
Contains information about users in the system.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, String, Integer, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """
    User model representing an individual or business entity going through KYC/KYB process.
    
    Attributes:
        id (UUID): Unique identifier for the user
        created_at (DateTime): When the user was created
        updated_at (DateTime): When the user was last updated
        email (str): User's email address
        full_name (str): User's full name
        is_business (bool): Whether this is a business entity (KYB) or individual (KYC)
        business_name (str, optional): Name of the business if is_business is True
        phone_number (str, optional): User's phone number
        address (str, optional): User's address
        country (str, optional): User's country
        tax_id (str, optional): Tax ID or SSN
        is_verified (bool): Whether the user's identity has been verified
        risk_score (float, optional): Risk score from 0-100
        risk_status (str, optional): Risk status (low, medium, high)
        documents (relationship): Relationship to documents uploaded by the user
        assessments (relationship): Relationship to risk assessments for the user
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Basic user information
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    is_business = Column(Boolean, default=False)
    business_name = Column(String, nullable=True)
    
    # Contact and location
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
    # Identification
    tax_id = Column(String, nullable=True)
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    
    # Risk assessment
    risk_score = Column(Float, nullable=True)
    risk_status = Column(String, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    sift_scores = relationship("SiftScore", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of the user."""
        return f"<User {self.email}>"