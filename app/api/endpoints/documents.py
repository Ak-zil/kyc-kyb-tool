"""
API endpoints for document management.
Handles document upload, retrieval, and processing.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.utils import validate_file_extension, get_content_type
from app.models.document import Document
from app.models.user import User
from app.schemas.document import Document as DocumentSchema, DocumentCreate, DocumentUpload, DocumentWithoutData
from app.services.document_extractor import extract_document_data
from app.services.s3_service import S3Service

router = APIRouter()


@router.post("/upload", response_model=DocumentSchema, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    document_data: DocumentUpload = Depends(),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Any:
    """
    Upload a document for a user.
    
    Args:
        background_tasks: FastAPI background tasks
        document_data: Document metadata
        file: Uploaded file
        db: Database session
        
    Returns:
        Uploaded document information
    """
    # Check if user exists
    user = db.query(User).filter(User.id == document_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Validate file extension
    valid_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"]
    if not validate_file_extension(file.filename, valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension not allowed. Allowed extensions: {', '.join(valid_extensions)}",
        )
    
    # Get file content
    file_content = await file.read()
    
    # Create S3 service
    s3_service = S3Service()
    
    # Upload file to S3
    document_type = document_data.document_type.lower().replace(" ", "_")
    user_id_str = str(document_data.user_id)
    s3_key = f"documents/{user_id_str}/{document_type}/{file.filename}"
    
    s3_service.upload_file(
        file_content=file_content,
        key=s3_key,
        content_type=get_content_type(file.filename),
    )
    
    # Create document in database
    document = Document(
        user_id=document_data.user_id,
        document_type=document_data.document_type,
        file_name=file.filename,
        content_type=get_content_type(file.filename),
        s3_key=s3_key,
        is_verified=False,
        is_processed=False,
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Get download URL
    download_url = s3_service.get_download_url(s3_key)
    
    # Schedule background task to extract data from document
    background_tasks.add_task(
        extract_document_data,
        document_id=document.id,
    )
    
    # Return document with download URL
    document_dict = DocumentSchema.from_orm(document).dict()
    document_dict["download_url"] = download_url
    
    return document_dict


@router.get("/{document_id}", response_model=DocumentSchema)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get document by ID.
    
    Args:
        document_id: ID of the document
        db: Database session
        
    Returns:
        Document information with download URL
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Get download URL
    s3_service = S3Service()
    download_url = s3_service.get_download_url(document.s3_key)
    
    # Return document with download URL
    document_dict = DocumentSchema.from_orm(document).dict()
    document_dict["download_url"] = download_url
    
    return document_dict


@router.get("/user/{user_id}", response_model=List[DocumentWithoutData])
def get_user_documents(
    user_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all documents for a user.
    
    Args:
        user_id: ID of the user
        db: Database session
        
    Returns:
        List of documents for the user (without extracted data)
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Get documents
    documents = db.query(Document).filter(Document.user_id == user_id).all()
    
    # Get download URLs
    s3_service = S3Service()
    document_list = []
    
    for document in documents:
        document_dict = DocumentWithoutData.from_orm(document).dict()
        document_dict["download_url"] = s3_service.get_download_url(document.s3_key)
        document_list.append(document_dict)
    
    return document_list


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a document.
    
    Args:
        document_id: ID of the document to delete
        db: Database session
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Delete file from S3
    s3_service = S3Service()
    s3_service.delete_file(document.s3_key)
    
    # Delete document from database
    db.delete(document)
    db.commit()


@router.post("/reprocess/{document_id}", response_model=DocumentSchema)
def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    """
    Reprocess a document to extract data.
    
    Args:
        document_id: ID of the document to reprocess
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Updated document information
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Reset processing status
    document.is_processed = False
    document.extracted_data = None
    db.commit()
    db.refresh(document)
    
    # Get download URL
    s3_service = S3Service()
    download_url = s3_service.get_download_url(document.s3_key)
    
    # Schedule background task to extract data
    background_tasks.add_task(
        extract_document_data,
        document_id=document.id,
    )
    
    # Return document with download URL
    document_dict = DocumentSchema.from_orm(document).dict()
    document_dict["download_url"] = download_url
    
    return document_dict