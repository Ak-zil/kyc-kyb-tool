"""
Tests for the users API endpoints.
"""
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


def test_create_user(client: TestClient, db):
    """Test creating a new user."""
    # Test data
    user_data = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "is_business": False,
        "business_name": None,
        "phone_number": "123-456-7890",
        "address": "123 Main St, Anytown, US",
        "country": "US",
    }
    
    # Make request
    response = client.post("/api/v1/users/", json=user_data)
    
    # Check response
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["email"] == user_data["email"]
    assert response_data["full_name"] == user_data["full_name"]
    assert response_data["is_business"] == user_data["is_business"]
    assert response_data["phone_number"] == user_data["phone_number"]
    assert response_data["address"] == user_data["address"]
    assert response_data["country"] == user_data["country"]
    assert "id" in response_data
    
    # Check database
    db_user = db.query(User).filter(User.email == user_data["email"]).first()
    assert db_user is not None
    assert str(db_user.id) == response_data["id"]


def test_create_user_duplicate_email(client: TestClient, test_user):
    """Test creating a user with an existing email."""
    # Test data using an existing email
    user_data = {
        "email": test_user.email,  # Duplicate email
        "full_name": "Duplicate User",
        "is_business": False,
    }
    
    # Make request
    response = client.post("/api/v1/users/", json=user_data)
    
    # Check response
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_user(client: TestClient, test_user, test_document, test_assessment):
    """Test getting a user by ID."""
    # Make request
    response = client.get(f"/api/v1/users/{test_user.id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    
    # Check documents
    assert len(data["documents"]) == 1
    assert data["documents"][0]["document_type"] == test_document.document_type
    
    # Check assessment
    assert data["latest_assessment"] is not None
    assert data["latest_assessment"]["score"] == test_assessment.score
    assert data["latest_assessment"]["status"] == test_assessment.status


def test_get_user_not_found(client: TestClient):
    """Test getting a non-existent user."""
    # Random UUID that doesn't exist
    random_id = uuid.uuid4()
    
    # Make request
    response = client.get(f"/api/v1/users/{random_id}")
    
    # Check response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_user(client: TestClient, test_user):
    """Test updating a user."""
    # Test data
    update_data = {
        "full_name": "Updated Name",
        "phone_number": "987-654-3210",
        "is_verified": True,
    }
    
    # Make request
    response = client.put(f"/api/v1/users/{test_user.id}", json=update_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["phone_number"] == update_data["phone_number"]
    assert data["is_verified"] == update_data["is_verified"]
    
    # Ensure other fields remain unchanged
    assert data["email"] == test_user.email
    assert data["is_business"] == test_user.is_business


def test_delete_user(client: TestClient, db, test_user):
    """Test deleting a user."""
    # Make request
    response = client.delete(f"/api/v1/users/{test_user.id}")
    
    # Check response
    assert response.status_code == 204
    
    # Check database
    db_user = db.query(User).filter(User.id == test_user.id).first()
    assert db_user is None


def test_list_users_ag_grid(client: TestClient, db):
    """Test listing users with AG Grid format."""
    # Create multiple users
    for i in range(5):
        user = User(
            id=uuid.uuid4(),
            email=f"user{i}@example.com",
            full_name=f"User {i}",
            is_business=False,
            is_verified=i % 2 == 0,  # Every other user is verified
        )
        db.add(user)
    db.commit()
    
    # AG Grid request
    ag_grid_request = {
        "startRow": 0,
        "endRow": 10,
        "rowGroupCols": [],
        "valueCols": [],
        "pivotCols": [],
        "pivotMode": False,
        "groupKeys": [],
        "filterModel": {},
        "sortModel": []
    }
    
    # Make request
    response = client.post("/api/v1/users/list", json=ag_grid_request)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "rowCount" in data
    assert "rowData" in data
    assert data["rowCount"] >= 5  # At least the 5 users we created
    assert len(data["rowData"]) >= 5
    
    # Check data structure
    for user in data["rowData"]:
        assert "user_id" in user
        assert "user_name" in user
        assert "email" in user
        assert "created_at" in user


def test_list_users_ag_grid_filtering(client: TestClient, db):
    """Test listing users with AG Grid filtering."""
    # Create users
    for i in range(10):
        risk_status = "low" if i < 3 else ("medium" if i < 7 else "high")
        user = User(
            id=uuid.uuid4(),
            email=f"user{i}@example.com",
            full_name=f"User {i}",
            is_business=False,
            is_verified=True,
            risk_score=i * 10,
            risk_status=risk_status
        )
        db.add(user)
    db.commit()
    
    # AG Grid request with filter
    ag_grid_request = {
        "startRow": 0,
        "endRow": 10,
        "rowGroupCols": [],
        "valueCols": [],
        "pivotCols": [],
        "pivotMode": False,
        "groupKeys": [],
        "filterModel": {
            "risk_status": {
                "filterType": "text",
                "type": "equals",
                "filter": "high"
            }
        },
        "sortModel": []
    }
    
    # Make request
    response = client.post("/api/v1/users/list", json=ag_grid_request)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["rowCount"] == 3  # We created 3 users with high risk
    assert len(data["rowData"]) == 3
    
    # Check filtered data
    for user in data["rowData"]:
        assert user["status"] == "high"


def test_list_users_ag_grid_sorting(client: TestClient, db):
    """Test listing users with AG Grid sorting."""
    # Create users
    for i in range(5):
        user = User(
            id=uuid.uuid4(),
            email=f"user{i}@example.com",
            full_name=f"User {i}",
            is_business=False,
            is_verified=True,
            risk_score=i * 20  # 0, 20, 40, 60, 80
        )
        db.add(user)
    db.commit()
    
    # AG Grid request with sorting
    ag_grid_request = {
        "startRow": 0,
        "endRow": 10,
        "rowGroupCols": [],
        "valueCols": [],
        "pivotCols": [],
        "pivotMode": False,
        "groupKeys": [],
        "filterModel": {},
        "sortModel": [
            {
                "colId": "risk_score",
                "sort": "desc"
            }
        ]
    }
    
    # Make request
    response = client.post("/api/v1/users/list", json=ag_grid_request)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Check sorted data (should be highest score first)
    scores = [user.get("score", 0) for user in data["rowData"]]
    assert scores == sorted(scores, reverse=True)


def test_list_users_ag_grid_pagination(client: TestClient, db):
    """Test listing users with AG Grid pagination."""
    # Create 20 users
    for i in range(20):
        user = User(
            id=uuid.uuid4(),
            email=f"user{i}@example.com",
            full_name=f"User {i}",
            is_business=False,
            is_verified=True
        )
        db.add(user)
    db.commit()
    
    # First page (5 users)
    ag_grid_request_1 = {
        "startRow": 0,
        "endRow": 5,
        "rowGroupCols": [],
        "valueCols": [],
        "pivotCols": [],
        "pivotMode": False,
        "groupKeys": [],
        "filterModel": {},
        "sortModel": []
    }
    
    # Second page (5 users)
    ag_grid_request_2 = {
        "startRow": 5,
        "endRow": 10,
        "rowGroupCols": [],
        "valueCols": [],
        "pivotCols": [],
        "pivotMode": False,
        "groupKeys": [],
        "filterModel": {},
        "sortModel": []
    }
    
    # Make first page request
    response_1 = client.post("/api/v1/users/list", json=ag_grid_request_1)
    data_1 = response_1.json()
    
    # Make second page request
    response_2 = client.post("/api/v1/users/list", json=ag_grid_request_2)
    data_2 = response_2.json()
    
    # Check both responses
    assert response_1.status_code == 200
    assert response_2.status_code == 200
    
    # Check pagination
    assert data_1["rowCount"] >= 20  # Total count should be at least 20
    assert data_2["rowCount"] >= 20  # Total count should be the same
    
    assert len(data_1["rowData"]) == 5  # First page has 5 users
    assert len(data_2["rowData"]) == 5  # Second page has 5 users
    
    # Check different users on different pages
    user_ids_1 = {user["user_id"] for user in data_1["rowData"]}
    user_ids_2 = {user["user_id"] for user in data_2["rowData"]}
    
    # No overlap between pages
    assert len(user_ids_1.intersection(user_ids_2)) == 0