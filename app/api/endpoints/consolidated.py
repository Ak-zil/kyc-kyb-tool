"""
API endpoints for consolidated data uploads.
Handles creation and updating of users with documents and Sift score in a single request.
"""
import base64
import logging
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.utils import get_content_type, validate_file_extension
from app.models.assessment import Assessment
from app.models.document import Document
from app.models.user import User
from app.schemas.consolidated import (
    ConsolidatedUserCreateResponse,
    ConsolidatedUserUpdateResponse,
    ConsolidatedUserUpload,
)
from app.services.assessment_service import create_assessment_for_user
from app.services.document_extractor import extract_document_data
from app.services.s3_service import S3Service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/users/consolidated", response_model=ConsolidatedUserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user_consolidated(
    background_tasks: BackgroundTasks,
    user_data: ConsolidatedUserUpload,
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new user with documents and Sift score in a single request.
    
    Args:
        background_tasks: FastAPI background tasks
        user_data: Consolidated user data including profile, documents, and Sift score
        db: Database session
        
    Returns:
        Created user information
    """
    # Check if user with this email already exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Extract documents and Sift score
    documents = user_data.documents
    sift_score = user_data.sift_score
    
    # Remove documents and Sift score from user data
    user_dict = user_data.dict(exclude={"documents", "sift_score"})
    
    # Create new user
    db_user = User(**user_dict)
    
    # Set initial risk score based on Sift score if provided
    if sift_score is not None:
        db_user.risk_score = sift_score
        db_user.risk_status = get_risk_level(sift_score)
    
    db.add(db_user)
    db.flush()  # Get user ID without committing
    
    # Create S3 service
    s3_service = S3Service()
    
    # Process documents
    documents_processed = 0
    for doc in documents:
        try:
            # Decode base64 content
            file_content = base64.b64decode(doc.document_content)
            
            # Validate file extension from filename
            valid_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"]
            if not validate_file_extension(doc.file_name, valid_extensions):
                logger.warning(f"Skipping document with invalid extension: {doc.file_name}")
                continue
            
            # Upload file to S3
            document_type = doc.document_type.lower().replace(" ", "_")
            user_id_str = str(db_user.id)
            s3_key = f"documents/{user_id_str}/{document_type}/{doc.file_name}"
            
            s3_service.upload_file(
                file_content=file_content,
                key=s3_key,
                content_type=doc.content_type,
            )
            
            # Create document in database
            document = Document(
                user_id=db_user.id,
                document_type=doc.document_type,
                file_name=doc.file_name,
                content_type=doc.content_type,
                s3_key=s3_key,
                is_verified=False,
                is_processed=False,
            )
            
            db.add(document)
            db.flush()
            
            # Schedule background task to extract data from document
            background_tasks.add_task(
                extract_document_data,
                document_id=document.id,
            )
            
            documents_processed += 1
        except Exception as e:
            logger.error(f"Error processing document {doc.file_name}: {e}")
    
    # Create assessment placeholder
    assessment = Assessment(
        user_id=db_user.id,
        score=0,
        status="pending",
        reasoning="Assessment in progress...",
        sift_score=sift_score,
    )
    
    db.add(assessment)
    db.flush()
    
    # Schedule background task to create assessment
    background_tasks.add_task(
        create_assessment_for_user,
        assessment_id=assessment.id,
    )
    
    # Commit all changes
    db.commit()
    
    # Return response
    return ConsolidatedUserCreateResponse(
        user_id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        is_business=db_user.is_business,
        sift_score_processed=sift_score is not None,
        documents_processed=documents_processed,
        assessment_requested=True,
        assessment_id=assessment.id,
    )


@router.put("/users/{user_id}/consolidated", response_model=ConsolidatedUserUpdateResponse)
async def update_user_consolidated(
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user_data: ConsolidatedUserUpload,
    db: Session = Depends(get_db),
) -> Any:
    """
    Update an existing user with new documents and Sift score.
    
    Args:
        user_id: ID of the user to update
        background_tasks: FastAPI background tasks
        user_data: Updated user data including profile, documents, and Sift score
        db: Database session
        
    Returns:
        Updated user information
    """
    # Check if user exists
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Extract documents and Sift score
    documents = user_data.documents
    sift_score = user_data.sift_score
    
    # Remove documents and Sift score from user data
    user_dict = user_data.dict(exclude={"documents", "sift_score"})
    
    # Update user profile data
    for field, value in user_dict.items():
        if value is not None:  # Only update provided fields
            setattr(db_user, field, value)
    
    # Update Sift score if provided
    sift_score_updated = False
    if sift_score is not None:
        db_user.risk_score = sift_score
        db_user.risk_status = get_risk_level(sift_score)
        sift_score_updated = True
    
    # Create S3 service
    s3_service = S3Service()
    
    # Process documents
    documents_added = 0
    for doc in documents:
        try:
            # Decode base64 content
            file_content = base64.b64decode(doc.document_content)
            
            # Validate file extension from filename
            valid_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"]
            if not validate_file_extension(doc.file_name, valid_extensions):
                logger.warning(f"Skipping document with invalid extension: {doc.file_name}")
                continue
            
            # Upload file to S3
            document_type = doc.document_type.lower().replace(" ", "_")
            user_id_str = str(db_user.id)
            s3_key = f"documents/{user_id_str}/{document_type}/{doc.file_name}"
            
            s3_service.upload_file(
                file_content=file_content,
                key=s3_key,
                content_type=doc.content_type,
            )
            
            # Create document in database
            document = Document(
                user_id=db_user.id,
                document_type=doc.document_type,
                file_name=doc.file_name,
                content_type=doc.content_type,
                s3_key=s3_key,
                is_verified=False,
                is_processed=False,
            )
            
            db.add(document)
            db.flush()
            
            # Schedule background task to extract data from document
            background_tasks.add_task(
                extract_document_data,
                document_id=document.id,
            )
            
            documents_added += 1
        except Exception as e:
            logger.error(f"Error processing document {doc.file_name}: {e}")
    
    # Create assessment if documents were added or Sift score was updated
    assessment = None
    assessment_requested = False
    
    if documents_added > 0 or sift_score_updated:
        assessment = Assessment(
            user_id=db_user.id,
            score=0,
            status="pending",
            reasoning="Assessment in progress...",
            sift_score=sift_score,
        )
        
        db.add(assessment)
        db.flush()
        
        # Schedule background task to create assessment
        background_tasks.add_task(
            create_assessment_for_user,
            assessment_id=assessment.id,
        )
        
        assessment_requested = True
    
    # Commit all changes
    db.commit()
    
    # Return response
    return ConsolidatedUserUpdateResponse(
        user_id=db_user.id,
        email=db_user.email,
        documents_added=documents_added,
        sift_score_updated=sift_score_updated,
        assessment_requested=assessment_requested,
        assessment_id=assessment.id if assessment else None,
    )


def get_risk_level(score: float) -> str:
    """
    Get risk level from a risk score.
    
    Args:
        score: Risk score (0-100)
        
    Returns:
        Risk level string (low, medium, high)
    """
    if score < 33.33:
        return "low"
    elif score < 66.67:
        return "medium"
    else:
        return "high"