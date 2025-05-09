"""
Assessment service for creating and managing risk assessments.
Coordinates the risk assessment process using various data sources and LLM.
"""
import logging
import uuid
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.assessment import Assessment, ThirdPartyData
from app.models.document import Document
from app.models.user import User
from app.services.llm_service import LLMService
from app.services.plugin_manager import PluginManager

# Configure logging
logger = logging.getLogger(__name__)


class AssessmentService:
    """
    Service for creating and managing risk assessments.
    
    Attributes:
        db: Database session
        llm_service: LLM service for risk analysis
        plugin_manager: Plugin manager for third-party data
    """
    
    def __init__(self, db: Session):
        """
        Initialize assessment service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.llm_service = LLMService()
        self.plugin_manager = PluginManager()
    
    def create_assessment(self, user_id: uuid.UUID) -> Optional[Assessment]:
        """
        Create a risk assessment for a user.
        
        Args:
            user_id: ID of the user to assess
            
        Returns:
            Created assessment or None if error
        """
        try:
            # Get user data
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found")
                return None
            
            # Get document data
            documents = self.db.query(Document).filter(
                Document.user_id == user_id,
                Document.is_processed == True
            ).all()
            
            documents_data = []
            for doc in documents:
                if doc.extracted_data and "error" not in doc.extracted_data:
                    doc_data = {
                        "document_type": doc.document_type,
                        "data": doc.extracted_data
                    }
                    documents_data.append(doc_data)
            
            # Get third-party data
            user_dict = {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_business": user.is_business,
                "business_name": user.business_name,
                "phone_number": user.phone_number,
                "address": user.address,
                "country": user.country,
                "tax_id": user.tax_id
            }
            
            third_party_data = self.plugin_manager.execute_all_plugins(user_dict)
            
            # Extract Sift score if available
            sift_score = None
            if "sift" in third_party_data and "score" in third_party_data["sift"]:
                sift_score = third_party_data["sift"]["score"]
            
            # Use LLM for risk analysis
            score, status, reasoning, llm_response = self.llm_service.analyze_risk(
                user_dict, documents_data, third_party_data
            )
            
            # Create assessment
            assessment = Assessment(
                user_id=user_id,
                score=score,
                status=status,
                reasoning=reasoning,
                sift_score=sift_score,
                llm_response=llm_response
            )
            
            self.db.add(assessment)
            self.db.flush()  # Get ID without committing
            
            # Add third-party data
            for source, data in third_party_data.items():
                third_party_data_entry = ThirdPartyData(
                    assessment_id=assessment.id,
                    source=source,
                    data=data
                )
                self.db.add(third_party_data_entry)
            
            # Update user risk score and status
            user.risk_score = score
            user.risk_status = status
            
            # Commit changes
            self.db.commit()
            self.db.refresh(assessment)
            
            return assessment
        except Exception as e:
            logger.error(f"Error creating assessment: {e}")
            self.db.rollback()
            return None
    
    def update_existing_assessment(self, assessment_id: uuid.UUID) -> Optional[Assessment]:
        """
        Update an existing assessment.
        
        Args:
            assessment_id: ID of the assessment to update
            
        Returns:
            Updated assessment or None if error
        """
        try:
            # Get assessment
            assessment = self.db.query(Assessment).filter(Assessment.id == assessment_id).first()
            if not assessment:
                logger.error(f"Assessment {assessment_id} not found")
                return None
            
            # Create a new assessment for the user
            new_assessment = self.create_assessment(assessment.user_id)
            
            # Update the existing assessment with new data
            if new_assessment:
                assessment.score = new_assessment.score
                assessment.status = new_assessment.status
                assessment.reasoning = new_assessment.reasoning
                assessment.sift_score = new_assessment.sift_score
                assessment.llm_response = new_assessment.llm_response
                
                # Delete old third-party data
                self.db.query(ThirdPartyData).filter(
                    ThirdPartyData.assessment_id == assessment_id
                ).delete()
                
                # Copy new third-party data
                for tpd in new_assessment.third_party_data:
                    new_tpd = ThirdPartyData(
                        assessment_id=assessment.id,
                        source=tpd.source,
                        data=tpd.data
                    )
                    self.db.add(new_tpd)
                
                # Delete the temporary assessment
                self.db.delete(new_assessment)
                
                # Commit changes
                self.db.commit()
                self.db.refresh(assessment)
            
            return assessment
        except Exception as e:
            logger.error(f"Error updating assessment: {e}")
            self.db.rollback()
            return None


def create_assessment_for_user(assessment_id: uuid.UUID) -> None:
    """
    Background task to create a risk assessment.
    
    Args:
        assessment_id: ID of the assessment to create/update
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Get assessment from database
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            logger.error(f"Assessment {assessment_id} not found")
            return
        
        # Create assessment service
        service = AssessmentService(db)
        
        # Update the assessment
        updated_assessment = service.update_existing_assessment(assessment_id)
        
        if not updated_assessment:
            logger.error(f"Failed to update assessment {assessment_id}")
            assessment.status = "failed"
            assessment.reasoning = "Failed to create assessment"
            db.commit()
    except Exception as e:
        logger.error(f"Error in create_assessment_for_user: {e}")
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if assessment:
            assessment.status = "failed"
            assessment.reasoning = f"Error: {str(e)}"
            db.commit()
    finally:
        db.close()