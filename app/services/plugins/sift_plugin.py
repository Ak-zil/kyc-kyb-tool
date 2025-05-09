"""
Simplified Sift plugin for handling user-provided Sift scores.
Instead of connecting to Sift API, this plugin processes manually uploaded scores.
"""
import logging
from typing import Dict, Any

from app.services.plugins.base_plugin import BasePlugin

# Configure logging
logger = logging.getLogger(__name__)


class SiftPlugin(BasePlugin):
    """
    Plugin for handling user-provided Sift scores.
    
    This plugin doesn't connect to the Sift API directly but instead
    processes scores that users upload manually.
    """
    
    @property
    def name(self) -> str:
        """
        Get the name of the plugin.
        
        Returns:
            Plugin name
        """
        return "sift"
    
    @property
    def description(self) -> str:
        """
        Get the description of the plugin.
        
        Returns:
            Plugin description
        """
        return "Manual Sift score processor"
    
    def execute(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the user-provided Sift score.
        
        Args:
            user_data: User data including the Sift score
            
        Returns:
            Dictionary with Sift score and risk factors
        """
        try:
            # Extract Sift score from user data
            sift_score = user_data.get("sift_score")
            
            # If no score is provided, return a default response
            if sift_score is None:
                logger.warning(f"No Sift score provided for user {user_data.get('id', 'unknown')}")
                return {
                    "score": 0.0,
                    "risk_factors": ["No Sift score provided"],
                    "has_score": False
                }
            
            # Ensure score is a float between 0 and 100
            try:
                score = float(sift_score)
                score = max(0, min(100, score))
            except (ValueError, TypeError):
                logger.error(f"Invalid Sift score format: {sift_score}")
                return {
                    "score": 0.0,
                    "risk_factors": ["Invalid Sift score format"],
                    "has_score": False
                }
            
            # Determine risk factors based on score ranges
            risk_factors = []
            if score > 80:
                risk_factors.append("Very high Sift risk score")
            elif score > 60:
                risk_factors.append("High Sift risk score")
            elif score > 40:
                risk_factors.append("Medium Sift risk score")
            elif score > 20:
                risk_factors.append("Low Sift risk score")
            else:
                risk_factors.append("Very low Sift risk score")
            
            return {
                "score": score,
                "risk_factors": risk_factors,
                "has_score": True
            }
        except Exception as e:
            logger.error(f"Error processing Sift score: {e}")
            return {
                "score": 0.0,
                "risk_factors": ["Error processing Sift score"],
                "has_score": False,
                "error": str(e)
            }
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate the processed response.
        
        Args:
            response: Processed Sift score response
            
        Returns:
            True if response is valid, False otherwise
        """
        return isinstance(response, dict) and "score" in response and "risk_factors" in response