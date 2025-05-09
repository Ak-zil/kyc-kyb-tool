"""
Plugin manager service for handling third-party data sources.
Manages loading and executing plugins.
"""
import importlib
import logging
from typing import Dict, List, Any, Type

from app.config import settings
from app.services.plugins.base_plugin import BasePlugin

# Configure logging
logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manager for handling data source plugins.
    
    Attributes:
        _plugins: Dictionary of loaded plugins
    """
    
    def __init__(self):
        """Initialize plugin manager and load enabled plugins."""
        self._plugins: Dict[str, BasePlugin] = {}
        self._load_enabled_plugins()
    
    def _load_enabled_plugins(self) -> None:
        """Load all enabled plugins from configuration."""
        for plugin_name in settings.ENABLED_PLUGINS:
            try:
                # Import the plugin module
                module_path = f"app.services.plugins.{plugin_name}_plugin"
                module = importlib.import_module(module_path)
                
                # Find the plugin class
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type) 
                        and issubclass(attr, BasePlugin) 
                        and attr is not BasePlugin
                    ):
                        # Initialize plugin
                        plugin_instance = attr()
                        self._plugins[plugin_name] = plugin_instance
                        logger.info(f"Loaded plugin: {plugin_name}")
                        break
                else:
                    logger.warning(f"No plugin class found in module: {module_path}")
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
    
    def get_plugin(self, plugin_name: str) -> BasePlugin:
        """
        Get a plugin by name.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance
            
        Raises:
            KeyError: If plugin is not found
        """
        if plugin_name not in self._plugins:
            raise KeyError(f"Plugin not found: {plugin_name}")
        return self._plugins[plugin_name]
    
    def get_available_plugins(self) -> List[str]:
        """
        Get list of available plugins.
        
        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())
    
    def execute_all_plugins(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all loaded plugins for a user.
        
        Args:
            user_data: User data to pass to plugins
            
        Returns:
            Dictionary with plugin results
        """
        results = {}
        for plugin_name, plugin in self._plugins.items():
            try:
                results[plugin_name] = plugin.execute(user_data)
            except Exception as e:
                logger.error(f"Error executing plugin {plugin_name}: {e}")
                results[plugin_name] = {"error": str(e)}
        
        return results
    
    def execute_plugin(self, plugin_name: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific plugin for a user.
        
        Args:
            plugin_name: Name of the plugin to execute
            user_data: User data to pass to the plugin
            
        Returns:
            Plugin result
            
        Raises:
            KeyError: If plugin is not found
        """
        plugin = self.get_plugin(plugin_name)
        return plugin.execute(user_data)