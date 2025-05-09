"""
SiftScore model for the KYC/KYB application.
Contains information about user-uploaded Sift scores.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, DateTime, String, ForeignKey, JSON, Float, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SiftScore(Base):
    """
    SiftScore model representing user-uploaded Sift fraud scores.
    
    Attributes:
        id (UUID): Unique identifier for the Sift score
        created_at (DateTime): When the score was created
        user_id (UUID): Reference to the user this score belongs to
        score (float): Sift score value (0-100)
        risk_factors (List[str]): List of risk factors identified by Sift
        additional_data (Dict[str, Any]): Any additional data associated with the score
        user (relationship): Relationship to the user
    """
    __tablename__ = "sift_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Score data
    score = Column(Float, nullable=False)
    risk_factors = Column(ARRAY(String), nullable=True)
    additional_data = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sift_scores")

    def __repr__(self):
        """String representation of the Sift score."""
        return f"<SiftScore {self.score} for User {self.user_id}>"