"""
API endpoints for risk assessment management.
Handles creation, retrieval, and management of risk assessments.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.assessment import Assessment, ThirdPartyData
from app.models.user import User
from app.schemas.assessment import (
    Assessment as AssessmentSchema,
    AssessmentRequest,
    AssessmentWithThirdPartyData,
)
from app.services.assessment_service import create_assessment_for_user

router = APIRouter()


@router.post("/", response_model=AssessmentSchema, status_code=status.HTTP_202_ACCEPTED)
def request_assessment(
    assessment_request: AssessmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    """
    Request a new risk assessment for a user.
    
    Args:
        assessment_request: Assessment request data
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Newly created assessment (processing will happen in background)
    """
    # Check if user exists
    user = db.query(User).filter(User.id == assessment_request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Create placeholder assessment
    assessment = Assessment(
        user_id=user.id,
        score=0,
        status="pending",
        reasoning="Assessment in progress...",
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    # Schedule background task to create assessment
    background_tasks.add_task(
        create_assessment_for_user,
        assessment_id=assessment.id,
    )
    
    return assessment


@router.get("/{assessment_id}", response_model=AssessmentWithThirdPartyData)
def get_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get assessment by ID.
    
    Args:
        assessment_id: ID of the assessment
        db: Database session
        
    Returns:
        Assessment with third-party data
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    
    return assessment


@router.get("/user/{user_id}", response_model=List[AssessmentSchema])
def get_user_assessments(
    user_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all assessments for a user.
    
    Args:
        user_id: ID of the user
        db: Database session
        
    Returns:
        List of assessments for the user
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Get assessments ordered by creation date (newest first)
    assessments = (
        db.query(Assessment)
        .filter(Assessment.user_id == user_id)
        .order_by(Assessment.created_at.desc())
        .all()
    )
    
    return assessments


@router.get("/latest/user/{user_id}", response_model=AssessmentWithThirdPartyData)
def get_latest_user_assessment(
    user_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get the latest assessment for a user.
    
    Args:
        user_id: ID of the user
        db: Database session
        
    Returns:
        Latest assessment with third-party data
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Get latest assessment
    assessment = (
        db.query(Assessment)
        .filter(Assessment.user_id == user_id)
        .order_by(Assessment.created_at.desc())
        .first()
    )
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessments found for this user",
        )
    
    return assessment


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete an assessment.
    
    Args:
        assessment_id: ID of the assessment to delete
        db: Database session
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    
    db.delete(assessment)
    db.commit()