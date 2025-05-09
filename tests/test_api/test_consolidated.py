"""
Tests for the consolidated data upload endpoints.
"""
import base64
import io
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.models.document import Document
from app.models.user import User


def test_create_user_consolidated(client: TestClient, db, mock_s3_service):
    """Test creating a new user with documents and Sift score."""
    # Create test document content
    document_content = b"test document content"
    base64_content = base64.b64encode(document_content).decode('utf-8')
    
    # Test data
    user_data = {
        "email": "consolidated_new@example.com",
        "full_name": "Consolidated New User",
        "is_business": False,
        "phone_number": "123-456-7890",
        "address": "123 Main St, Anytown, US",
        "country": "US",
        "sift_score": 42.5,
        "documents": [
            {
                "document_type": "passport",
                "file_name": "passport.jpg",
                "content_type": "image/jpeg",
                "document_content": base64_content
            },
            {
                "document_type": "utility_bill",
                "file_name": "bill.pdf",
                "content_type": "application/pdf",
                "document_content": base64_content
            }
        ]
    }
    
    # Make request
    with patch("app.api.endpoints.consolidated.extract_document_data") as mock_extract:
        with patch("app.api.endpoints.consolidated.create_assessment_for_user") as mock_assessment:
            response = client.post("/api/v1/users/consolidated", json=user_data)
            
            # Check background tasks were called
            assert mock_extract.call_count == 2  # Two documents
            assert mock_assessment.called  # Assessment requested
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert data["sift_score_processed"] is True
    assert data["documents_processed"] == 2
    assert data["assessment_requested"] is True
    assert "assessment_id" in data and data["assessment_id"] is not None
    
    # Check database
    db_user = db.query(User).filter(User.email == user_data["email"]).first()
    assert db_user is not None
    assert db_user.risk_score == user_data["sift_score"]
    
    # Check documents
    documents = db.query(Document).filter(Document.user_id == db_user.id).all()
    assert len(documents) == 2
    assert {doc.document_type for doc in documents} == {"passport", "utility_bill"}


def test_update_user_consolidated(client: TestClient, test_user, db, mock_s3_service):
    """Test updating an existing user with new documents and Sift score."""
    # Create test document content
    document_content = b"test document content"
    base64_content = base64.b64encode(document_content).decode('utf-8')
    
    # Test data
    user_data = {
        "email": test_user.email,
        "full_name": "Updated Consolidated User",
        "is_business": test_user.is_business,
        "sift_score": 75.0,
        "documents": [
            {
                "document_type": "id_card",
                "file_name": "id_card.jpg",
                "content_type": "image/jpeg",
                "document_content": base64_content
            }
        ]
    }
    
    # Make request
    with patch("app.api.endpoints.consolidated.extract_document_data") as mock_extract:
        with patch("app.api.endpoints.consolidated.create_assessment_for_user") as mock_assessment:
            response = client.put(f"/api/v1/users/{test_user.id}/consolidated", json=user_data)
            
            # Check background tasks were called
            assert mock_extract.called  # Document extraction
            assert mock_assessment.called  # Assessment requested
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["sift_score_updated"] is True
    assert data["documents_added"] == 1
    assert data["assessment_requested"] is True
    assert "assessment_id" in data and data["assessment_id"] is not None
    
    # Check database
    db_user = db.query(User).filter(User.id == test_user.id).first()
    assert db_user is not None
    assert db_user.full_name == "Updated Consolidated User"
    assert db_user.risk_score == user_data["sift_score"]
    
    # Check documents
    document = db.query(Document).filter(
        Document.user_id == test_user.id,
        Document.document_type == "id_card"
    ).first()
    assert document is not None
    assert document.file_name == "id_card.jpg"


def test_update_user_consolidated_user_not_found(client: TestClient):
    """Test updating a non-existent user."""
    # Random UUID that doesn't exist
    random_id = uuid.uuid4()
    
    # Test data
    user_data = {
        "email": "nonexistent@example.com",
        "full_name": "Nonexistent User",
        "is_business": False,
        "sift_score": 50.0,
        "documents": []
    }
    
    # Make request
    response = client.put(f"/api/v1/users/{random_id}/consolidated", json=user_data)
    
    # Check response
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_create_user_consolidated_duplicate_email(client: TestClient, test_user):
    """Test creating a user with an existing email."""
    # Test data using an existing email
    user_data = {
        "email": test_user.email,  # Duplicate email
        "full_name": "Duplicate User",
        "is_business": False,
        "sift_score": 30.0,
        "documents": []
    }
    
    # Make request
    response = client.post("/api/v1/users/consolidated", json=user_data)
    
    # Check response
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]