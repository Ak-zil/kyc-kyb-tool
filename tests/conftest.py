"""
Test configuration and fixtures for the KYC/KYB application.
"""
import os
import uuid
from typing import Dict, Generator, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.models.document import Document
from app.models.assessment import Assessment, ThirdPartyData

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db() -> Generator:
    """
    Create a fresh database for each test.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Use our test database
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db) -> Generator:
    """
    Create a test client with the test database.
    """
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    
    # Remove the override
    app.dependency_overrides = {}


@pytest.fixture
def test_user(db) -> User:
    """
    Create a test user.
    """
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        is_business=False,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_business_user(db) -> User:
    """
    Create a test business user.
    """
    user = User(
        id=uuid.uuid4(),
        email="business@example.com",
        full_name="Test Business Owner",
        is_business=True,
        business_name="Test Business LLC",
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_document(db, test_user) -> Document:
    """
    Create a test document.
    """
    document = Document(
        id=uuid.uuid4(),
        user_id=test_user.id,
        document_type="passport",
        file_name="test_passport.jpg",
        content_type="image/jpeg",
        s3_key=f"documents/{test_user.id}/passport/test_passport.jpg",
        is_verified=False,
        is_processed=True,
        extracted_data={
            "full_name": "Test User",
            "passport_number": "AB123456",
            "nationality": "United States",
            "date_of_birth": "1990-01-01",
        }
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@pytest.fixture
def test_assessment(db, test_user) -> Assessment:
    """
    Create a test assessment.
    """
    assessment = Assessment(
        id=uuid.uuid4(),
        user_id=test_user.id,
        score=25.5,
        status="low",
        reasoning="Low risk profile based on documents and verification",
        sift_score=20.0,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    # Add third-party data
    third_party_data = ThirdPartyData(
        id=uuid.uuid4(),
        assessment_id=assessment.id,
        source="sift",
        data={
            "score": 20.0,
            "risk_factors": ["new_account"]
        }
    )
    db.add(third_party_data)
    db.commit()
    
    return assessment


@pytest.fixture
def mock_s3_service(monkeypatch):
    """
    Mock S3 service for tests.
    """
    class MockS3Service:
        def upload_file(self, file_content, key, content_type=None):
            return True
        
        def get_download_url(self, key, expiry=None):
            return f"https://test-bucket.s3.amazonaws.com/{key}"
        
        def delete_file(self, key):
            return True
        
        def check_file_exists(self, key):
            return True
    
    from app.services.s3_service import S3Service
    monkeypatch.setattr("app.services.s3_service.S3Service", MockS3Service)
    return MockS3Service()


@pytest.fixture
def mock_llm_service(monkeypatch):
    """
    Mock LLM service for tests.
    """
    class MockLLMService:
        def analyze_risk(self, user_data, documents_data, third_party_data):
            return 25.5, "low", "Low risk profile based on documents and verification", {
                "risk_score": 25.5,
                "risk_status": "low",
                "reasoning": "Low risk profile based on documents and verification",
                "discrepancies": [],
                "red_flags": []
            }
    
    from app.services.llm_service import LLMService
    monkeypatch.setattr("app.services.llm_service.LLMService", MockLLMService)
    return MockLLMService()