"""
Base plugin interface for third-party data sources.
All data source plugins should inherit from this base class.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePlugin(ABC):
    """
    Base class for data source plugins.
    
    All plugins must implement the execute method to fetch
    data from their respective sources.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the plugin.
        
        Returns:
            Plugin name
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the plugin.
        
        Returns:
            Plugin description
        """
        pass
    
    @abstractmethod
    def execute(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plugin to fetch data.
        
        Args:
            user_data: User data to use for fetching third-party data
            
        Returns:
            Dictionary with fetched data
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate the response from the third-party source.
        
        Args:
            response: Response from the third-party source
            
        Returns:
            True if response is valid, False otherwise
        """
        pass