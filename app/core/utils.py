"""
Utility functions for the KYC/KYB application.
Contains various helper functions used throughout the application.
"""
import os
import mimetypes
from typing import List, Optional


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate if a file has an allowed extension.
    
    Args:
        filename: Name of the file to validate
        allowed_extensions: List of allowed extensions (including the dot)
        
    Returns:
        True if file has an allowed extension, False otherwise
    """
    if not filename:
        return False
    
    # Get file extension
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    
    # Check if extension is allowed
    return ext in allowed_extensions


def get_content_type(filename: str) -> str:
    """
    Get the content type (MIME type) of a file.
    
    Args:
        filename: Name of the file
        
    Returns:
        Content type string
    """
    content_type, _ = mimetypes.guess_type(filename)
    
    # Default to binary if content type not found
    if not content_type:
        content_type = "application/octet-stream"
    
    return content_type


def get_risk_level_from_score(score: float) -> str:
    """
    Get risk level from a risk score.
    
    Args:
        score: Risk score (0-100)
        
    Returns:
        Risk level string (low, medium, high)
    """
    if score < 33.33:
        return "low"
    elif score < 66.67:
        return "medium"
    else:
        return "high"


def build_ag_grid_response(count: int, data: List[dict]) -> dict:
    """
    Build an AG Grid compatible response.
    
    Args:
        count: Total count of items
        data: List of items for the current page
        
    Returns:
        AG Grid compatible response dictionary
    """
    return {
        "rowCount": count,
        "rowData": data
    }


def sanitize_filter_value(value: str) -> str:
    """
    Sanitize a filter value for SQL queries to prevent injection.
    
    Args:
        value: Filter value to sanitize
        
    Returns:
        Sanitized filter value
    """
    # Remove SQL wildcard characters and escape single quotes
    sanitized = value.replace("%", "\\%").replace("_", "\\_").replace("'", "''")
    return sanitized