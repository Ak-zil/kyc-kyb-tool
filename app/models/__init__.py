"""
Package for SQLAlchemy models.
Import all models here for explicit import in other modules.
"""
from app.models.user import User
from app.models.document import Document
from app.models.assessment import Assessment, ThirdPartyData
from app.models.sift_score import SiftScore

# Import models here makes them available when importing from app.models
# This helps with circular imports and explicit model registration