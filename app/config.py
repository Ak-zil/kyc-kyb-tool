"""
Configuration settings for the KYC/KYB application.
Loads environment variables and provides configuration objects for different components.
"""
import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, field_validator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    PROJECT_NAME: str = "KYC/KYB Onboarding API"
    API_V1_STR: str = "/api/v1"
    
    # CORS configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database configuration
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # AWS S3 configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_DEFAULT_REGION: str
    S3_BUCKET_NAME: str
    S3_DOCUMENT_EXPIRY_TIME: int = 3600  # Default link expiry in seconds

    # LLM configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    
    # Sift configuration
    SIFT_API_KEY: str
    
    # Security settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Plugin configuration
    ENABLED_PLUGINS_STR: str = "sift"  # Default plugins as string

    @property
    def ENABLED_PLUGINS(self) -> List[str]:
        """
        Parse ENABLED_PLUGINS_STR into a list of plugin names.
        
        Returns:
            List of plugin names
        """
        if not self.ENABLED_PLUGINS_STR:
            return []
        return [p.strip() for p in self.ENABLED_PLUGINS_STR.split(",")]

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()