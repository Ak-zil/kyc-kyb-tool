"""
API endpoints for user management.
Handles CRUD operations for users and AG Grid integration.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.api.deps import get_db, get_ag_grid_params
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, User as UserSchema, UserDetail, UserListItem
from app.schemas.ag_grid import AgGridRequest, AgGridResponse

router = APIRouter()


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new user.
    
    Args:
        user_in: User data
        db: Database session
        
    Returns:
        Created user
    """
    # Check if user with this email already exists
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Create new user
    db_user = User(**user_in.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/{user_id}", response_model=UserDetail)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get detailed information about a specific user.
    
    Args:
        user_id: ID of the user
        db: Database session
        
    Returns:
        User details with documents and assessment
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Create user detail response
    user_dict = UserSchema.from_orm(db_user).dict()
    
    # Add documents
    user_dict["documents"] = [
        {
            "id": doc.id,
            "document_type": doc.document_type,
            "file_name": doc.file_name,
            "created_at": doc.created_at,
            "is_verified": doc.is_verified,
            "is_processed": doc.is_processed,
            "extracted_data": doc.extracted_data,
            "rejection_reason": doc.rejection_reason,
        }
        for doc in db_user.documents
    ]
    
    # Add latest assessment if exists
    if db_user.assessments and len(db_user.assessments) > 0:
        latest_assessment = sorted(db_user.assessments, key=lambda x: x.created_at, reverse=True)[0]
        user_dict["latest_assessment"] = {
            "id": latest_assessment.id,
            "created_at": latest_assessment.created_at,
            "score": latest_assessment.score,
            "status": latest_assessment.status,
            "reasoning": latest_assessment.reasoning,
            "third_party_data": [
                {
                    "source": tpd.source,
                    "data": tpd.data,
                }
                for tpd in latest_assessment.third_party_data
            ],
        }
    else:
        user_dict["latest_assessment"] = None
    
    return user_dict


@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a user.
    
    Args:
        user_id: ID of the user to update
        user_in: Updated user data
        db: Database session
        
    Returns:
        Updated user
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update user attributes
    update_data = user_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a user.
    
    Args:
        user_id: ID of the user to delete
        db: Database session
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    db.delete(db_user)
    db.commit()


@router.post("/list", response_model=AgGridResponse)
def list_users_ag_grid(
    ag_grid_params: AgGridRequest,
    db: Session = Depends(get_db),
) -> Any:
    """
    List users with AG Grid server-side row model.
    Supports filtering, sorting, and pagination.
    
    Args:
        ag_grid_params: AG Grid request parameters
        db: Database session
        
    Returns:
        Users in AG Grid format
    """
    # Start building the query
    query = db.query(User)
    
    # Apply filters
    if ag_grid_params.filterModel:
        for col, filter_info in ag_grid_params.filterModel.items():
            filter_type = filter_info.get("filterType")
            
            if filter_type == "text":
                filter_value = filter_info.get("filter", "")
                filter_operator = filter_info.get("type", "contains")
                
                if filter_operator == "contains":
                    query = query.filter(getattr(User, col).ilike(f"%{filter_value}%"))
                elif filter_operator == "equals":
                    query = query.filter(getattr(User, col) == filter_value)
                elif filter_operator == "startsWith":
                    query = query.filter(getattr(User, col).ilike(f"{filter_value}%"))
                elif filter_operator == "endsWith":
                    query = query.filter(getattr(User, col).ilike(f"%{filter_value}"))
            
            elif filter_type == "number":
                filter_value = filter_info.get("filter")
                filter_operator = filter_info.get("type")
                
                if filter_operator == "equals":
                    query = query.filter(getattr(User, col) == filter_value)
                elif filter_operator == "greaterThan":
                    query = query.filter(getattr(User, col) > filter_value)
                elif filter_operator == "lessThan":
                    query = query.filter(getattr(User, col) < filter_value)
                elif filter_operator == "greaterThanOrEqual":
                    query = query.filter(getattr(User, col) >= filter_value)
                elif filter_operator == "lessThanOrEqual":
                    query = query.filter(getattr(User, col) <= filter_value)
    
    # Get total count (before pagination)
    total_count = query.count()
    
    # Apply sorting
    if ag_grid_params.sortModel:
        for sort_info in ag_grid_params.sortModel:
            col_id = sort_info.get("colId")
            sort_dir = sort_info.get("sort")
            
            if sort_dir == "asc":
                query = query.order_by(getattr(User, col_id))
            else:
                query = query.order_by(desc(getattr(User, col_id)))
    else:
        # Default sort by created_at desc
        query = query.order_by(desc(User.created_at))
    
    # Apply pagination
    query = query.offset(ag_grid_params.startRow).limit(
        ag_grid_params.endRow - ag_grid_params.startRow
    )
    
    # Execute query
    users = query.all()
    
    # Format results for AG Grid
    user_data = [
        {
            "user_id": user.id,
            "user_name": user.full_name,
            "email": user.email,
            "score": user.risk_score,
            "status": user.risk_status,
            "created_at": user.created_at,
        }
        for user in users
    ]
    
    return AgGridResponse(rowCount=total_count, rowData=user_data)