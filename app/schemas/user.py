"""
Pydantic schemas for user-related operations.
These schemas validate request/response data for user operations.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base schema with common user attributes."""
    email: EmailStr
    full_name: str
    is_business: bool = False
    business_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_business: Optional[bool] = None
    business_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    is_verified: Optional[bool] = None


class UserInDBBase(UserBase):
    """Base schema for users as they exist in the database."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    risk_score: Optional[float] = None
    risk_status: Optional[str] = None

    class Config:
        orm_mode = True


class User(UserInDBBase):
    """Schema for user information returned to clients."""
    pass


class UserDetail(User):
    """
    Detailed user information including related documents and assessments.
    Used for individual user API responses.
    """
    documents: List[Dict[str, Any]] = []
    latest_assessment: Optional[Dict[str, Any]] = None


class UserListItem(BaseModel):
    """
    Schema for user list items in AG Grid format.
    Contains minimal information for the user list view.
    """
    user_id: UUID
    user_name: str
    email: EmailStr
    score: Optional[float] = None
    status: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True