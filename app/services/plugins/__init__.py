"""
Plugin package for third-party data sources.
Contains base plugin interface and implementations.
"""
from app.services.plugins.base_plugin import BasePlugin
from app.services.plugins.sift_plugin import SiftPlugin

# Register all plugins here for easy import