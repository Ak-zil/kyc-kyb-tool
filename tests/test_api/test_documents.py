"""
Tests for the documents API endpoints.
"""
import io
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.models.document import Document


def test_upload_document(client: TestClient, test_user, mock_s3_service, db):
    """Test uploading a document."""
    # Test file content
    file_content = b"test file content"
    
    # Create form data
    files = {"file": ("test_passport.jpg", io.BytesIO(file_content), "image/jpeg")}
    form_data = {"user_id": str(test_user.id), "document_type": "passport"}
    
    # Make request
    response = client.post("/api/v1/documents/upload", files=files, data=form_data)
    
    # Check response
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["user_id"] == str(test_user.id)
    assert response_data["document_type"] == "passport"
    assert response_data["file_name"] == "test_passport.jpg"
    assert response_data["is_processed"] is False
    assert "download_url" in response_data
    
    # Check database
    document = db.query(Document).filter(Document.id == uuid.UUID(response_data["id"])).first()
    assert document is not None
    assert document.document_type == "passport"
    assert document.user_id == test_user.id


def test_upload_document_invalid_extension(client: TestClient, test_user):
    """Test uploading a document with invalid extension."""
    # Test file content
    file_content = b"test file content"
    
    # Create form data with invalid extension
    files = {"file": ("test_document.xyz", io.BytesIO(file_content), "application/octet-stream")}
    form_data = {"user_id": str(test_user.id), "document_type": "passport"}
    
    # Make request
    response = client.post("/api/v1/documents/upload", files=files, data=form_data)
    
    # Check response
    assert response.status_code == 400
    assert "extension not allowed" in response.json()["detail"]


def test_upload_document_user_not_found(client: TestClient):
    """Test uploading a document for a non-existent user."""
    # Test file content
    file_content = b"test file content"
    
    # Create form data with non-existent user
    random_id = uuid.uuid4()
    files = {"file": ("test_passport.jpg", io.BytesIO(file_content), "image/jpeg")}
    form_data = {"user_id": str(random_id), "document_type": "passport"}
    
    # Make request
    response = client.post("/api/v1/documents/upload", files=files, data=form_data)
    
    # Check response
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_get_document(client: TestClient, test_document, mock_s3_service):
    """Test getting a document by ID."""
    # Make request
    response = client.get(f"/api/v1/documents/{test_document.id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_document.id)
    assert data["user_id"] == str(test_document.user_id)
    assert data["document_type"] == test_document.document_type
    assert data["file_name"] == test_document.file_name
    assert "download_url" in data
    assert data["extracted_data"] is not None


def test_get_document_not_found(client: TestClient):
    """Test getting a non-existent document."""
    # Random UUID that doesn't exist
    random_id = uuid.uuid4()
    
    # Make request
    response = client.get(f"/api/v1/documents/{random_id}")
    
    # Check response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_user_documents(client: TestClient, test_user, test_document, mock_s3_service):
    """Test getting all documents for a user."""
    # Make request
    response = client.get(f"/api/v1/documents/user/{test_user.id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(test_document.id)
    assert data[0]["document_type"] == test_document.document_type
    assert "download_url" in data[0]
    
    # Verify extracted_data is not included (to keep response size manageable)
    assert "extracted_data" not in data[0]


def test_get_user_documents_user_not_found(client: TestClient):
    """Test getting documents for a non-existent user."""
    # Random UUID that doesn't exist
    random_id = uuid.uuid4()
    
    # Make request
    response = client.get(f"/api/v1/documents/user/{random_id}")
    
    # Check response
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_delete_document(client: TestClient, db, test_document, mock_s3_service):
    """Test deleting a document."""
    # Make request
    response = client.delete(f"/api/v1/documents/{test_document.id}")
    
    # Check response
    assert response.status_code == 204
    
    # Check database
    document = db.query(Document).filter(Document.id == test_document.id).first()
    assert document is None


def test_reprocess_document(client: TestClient, test_document, mock_s3_service):
    """Test reprocessing a document."""
    # Make request
    with patch("app.api.endpoints.documents.extract_document_data") as mock_extract:
        response = client.post(f"/api/v1/documents/reprocess/{test_document.id}")
        
        # Check background task was called
        mock_extract.assert_called_once_with(document_id=test_document.id)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_document.id)
    assert data["is_processed"] is False  # Reset to False for reprocessing
    assert data["extracted_data"] is None  # Cleared for reprocessing