"""
Base SQLAlchemy models and imports for the application.
This module imports all models to ensure they are registered with SQLAlchemy.
"""
from sqlalchemy.ext.declarative import declarative_base

# Create a base class for SQLAlchemy models
Base = declarative_base()

# Import all models here to ensure they are registered with SQLAlchemy
# This is used for managing migrations and creating tables

from app.models.user import User  # noqa
from app.models.document import Document  # noqa
from app.models.assessment import Assessment, ThirdPartyData  # noqa