"""
Tests for the assessments API endpoints.
"""
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.models.assessment import Assessment


def test_request_assessment(client: TestClient, test_user, db):
    """Test requesting a new assessment."""
    # Test data
    assessment_request = {
        "user_id": str(test_user.id)
    }
    
    # Make request
    with patch("app.api.endpoints.assessments.create_assessment_for_user") as mock_create:
        response = client.post("/api/v1/assessments/", json=assessment_request)
        
        # Check background task was called
        assert mock_create.called
    
    # Check response
    assert response.status_code == 202
    data = response.json()
    assert data["user_id"] == str(test_user.id)
    assert data["status"] == "pending"
    
    # Check database
    assessment = db.query(Assessment).filter(Assessment.id == uuid.UUID(data["id"])).first()
    assert assessment is not None
    assert assessment.user_id == test_user.id


def test_request_assessment_user_not_found(client: TestClient):
    """Test requesting an assessment for a non-existent user."""
    # Random UUID that doesn't exist
    random_id = uuid.uuid4()
    
    # Test data
    assessment_request = {
        "user_id": str(random_id)
    }
    
    # Make request
    response = client.post("/api/v1/assessments/", json=assessment_request)
    
    # Check response
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_get_assessment(client: TestClient, test_assessment):
    """Test getting an assessment by ID."""
    # Make request
    response = client.get(f"/api/v1/assessments/{test_assessment.id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_assessment.id)
    assert data["user_id"] == str(test_assessment.user_id)
    assert data["score"] == test_assessment.score
    assert data["status"] == test_assessment.status
    assert data["reasoning"] == test_assessment.reasoning
    
    # Check third-party data
    assert "third_party_data" in data
    assert len(data["third_party_data"]) == 1
    assert data["third_party_data"][0]["source"] == "sift"


def test_get_assessment_not_found(client: TestClient):
    """Test getting a non-existent assessment."""
    # Random UUID that doesn't exist
    random_id = uuid.uuid4()
    
    # Make request
    response = client.get(f"/api/v1/assessments/{random_id}")
    
    # Check response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_user_assessments(client: TestClient, test_user, test_assessment, db):
    """Test getting all assessments for a user."""
    # Create another assessment for the same user
    another_assessment = Assessment(
        id=uuid.uuid4(),
        user_id=test_user.id,
        score=75.0,
        status="high",
        reasoning="High risk profile based on recent activities",
    )
    db.add(another_assessment)
    db.commit()
    
    # Make request
    response = client.get(f"/api/v1/assessments/user/{test_user.id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Both assessments
    
    # Results should be ordered by creation date (newest first)
    assert data[0]["id"] == str(another_assessment.id)
    assert data[1]["id"] == str(test_assessment.id)


def test_get_user_assessments_user_not_found(client: TestClient):
    """Test getting assessments for a non-existent user."""
    # Random UUID that doesn't exist
    random_id = uuid.uuid4()
    
    # Make request
    response = client.get(f"/api/v1/assessments/user/{random_id}")
    
    # Check response
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_get_latest_user_assessment(client: TestClient, test_user, test_assessment, db):
    """Test getting the latest assessment for a user."""
    # Create a newer assessment
    newer_assessment = Assessment(
        id=uuid.uuid4(),
        user_id=test_user.id,
        score=80.0,
        status="high",
        reasoning="High risk profile based on recent activities",
        created_at=test_assessment.created_at.replace(microsecond=test_assessment.created_at.microsecond + 1),
    )
    db.add(newer_assessment)
    db.commit()
    
    # Make request
    response = client.get(f"/api/v1/assessments/latest/user/{test_user.id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(newer_assessment.id)  # Should get the newest assessment


def test_get_latest_user_assessment_no_assessments(client: TestClient, test_user, db):
    """Test getting the latest assessment for a user with no assessments."""
    # Delete any existing assessments
    db.query(Assessment).filter(Assessment.user_id == test_user.id).delete()
    db.commit()
    
    # Make request
    response = client.get(f"/api/v1/assessments/latest/user/{test_user.id}")
    
    # Check response
    assert response.status_code == 404
    assert "No assessments found" in response.json()["detail"]


def test_delete_assessment(client: TestClient, db, test_assessment):
    """Test deleting an assessment."""
    # Make request
    response = client.delete(f"/api/v1/assessments/{test_assessment.id}")
    
    # Check response
    assert response.status_code == 204
    
    # Check database
    assessment = db.query(Assessment).filter(Assessment.id == test_assessment.id).first()
    assert assessment is None