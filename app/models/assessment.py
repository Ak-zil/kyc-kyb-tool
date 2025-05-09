"""
Assessment models for the KYC/KYB application.
Contains models for risk assessments and third-party data.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, ForeignKey, JSON, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ThirdPartyData(Base):
    """
    Third-party data model representing data fetched from external sources.
    
    Attributes:
        id (UUID): Unique identifier for the third-party data
        created_at (DateTime): When the data was fetched
        assessment_id (UUID): Reference to the assessment this data is part of
        source (str): Source of the data (plugin name)
        data (JSON): The data fetched from the external source
        assessment (relationship): Relationship to the assessment this data belongs to
    """
    __tablename__ = "third_party_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Assessment relationship
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    
    # Data information
    source = Column(String, nullable=False)  # Name of the plugin or data source
    data = Column(JSON, nullable=False)
    
    # Relationship
    assessment = relationship("Assessment", back_populates="third_party_data")

    def __repr__(self):
        """String representation of the third-party data."""
        return f"<ThirdPartyData {self.source} for Assessment {self.assessment_id}>"


class Assessment(Base):
    """
    Assessment model representing a fraud/risk assessment for a user.
    
    Attributes:
        id (UUID): Unique identifier for the assessment
        created_at (DateTime): When the assessment was created
        updated_at (DateTime): When the assessment was last updated
        user_id (UUID): Reference to the user being assessed
        score (float): Risk score from 0-100
        status (str): Risk status (low, medium, high)
        reasoning (Text): Explanation for the risk assessment
        sift_score (float, optional): Score from Sift
        llm_response (JSON, optional): Full response from the LLM
        user (relationship): Relationship to the user being assessed
        third_party_data (relationship): Relationship to third-party data used for this assessment
    """
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Assessment results
    score = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # low, medium, high
    reasoning = Column(Text, nullable=False)
    
    # Component scores
    sift_score = Column(Float, nullable=True)
    
    # Raw LLM response
    llm_response = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="assessments")
    third_party_data = relationship("ThirdPartyData", back_populates="assessment", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of the assessment."""
        return f"<Assessment {self.score} ({self.status}) for User {self.user_id}>"