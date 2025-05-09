"""
LLM service for risk assessment reasoning.
Uses ChatGPT to analyze user data and generate risk assessments.
"""
import json
import logging
from typing import Dict, Any, List, Tuple

import openai

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for interacting with OpenAI's ChatGPT.
    
    Attributes:
        openai_client: OpenAI client
        model: ChatGPT model to use
    """
    
    def __init__(self):
        """Initialize LLM service with OpenAI client."""
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    def analyze_risk(
        self,
        user_data: Dict[str, Any],
        documents_data: List[Dict[str, Any]],
        third_party_data: Dict[str, Any]
    ) -> Tuple[float, str, str, Dict[str, Any]]:
        """
        Analyze risk using ChatGPT.
        
        Args:
            user_data: User information
            documents_data: Extracted data from user documents
            third_party_data: Data from third-party sources
            
        Returns:
            Tuple of (risk score, risk status, reasoning, raw response)
        """
        try:
            # Create prompt for risk analysis
            prompt = self._create_risk_analysis_prompt(user_data, documents_data, third_party_data)
            
            # Call ChatGPT API
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a fraud and risk analysis expert. Your task is to evaluate the risk level of a user based on their profile information, document data, and third-party data. Provide a detailed analysis and a risk score from 0-100."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temperature for more deterministic output
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Extract risk information
            score = float(result.get("risk_score", 0))
            status = result.get("risk_status", "low").lower()
            reasoning = result.get("reasoning", "No reasoning provided")
            
            # Ensure score is within 0-100 range
            score = max(0, min(100, score))
            
            # Ensure status is one of the allowed values
            if status not in ["low", "medium", "high"]:
                if score < 33.33:
                    status = "low"
                elif score < 66.67:
                    status = "medium"
                else:
                    status = "high"
            
            return score, status, reasoning, result
        except Exception as e:
            logger.error(f"Error analyzing risk with LLM: {e}")
            return 50.0, "medium", f"Error during risk analysis: {str(e)}", {"error": str(e)}
    
    def _create_risk_analysis_prompt(
        self,
        user_data: Dict[str, Any],
        documents_data: List[Dict[str, Any]],
        third_party_data: Dict[str, Any]
    ) -> str:
        """
        Create a prompt for risk analysis.
        
        Args:
            user_data: User information
            documents_data: Extracted data from user documents
            third_party_data: Data from third-party sources
            
        Returns:
            Prompt string for ChatGPT
        """
        prompt = """
        Please analyze the following user information for potential fraud and risk assessment.
        
        ## Task
        1. Analyze the user data, document data, and third-party data
        2. Identify any discrepancies, red flags, or suspicious patterns
        3. Provide a risk score (0-100, where 0 is no risk and 100 is highest risk)
        4. Assign a risk status ("low", "medium", or "high")
        5. Provide detailed reasoning for your assessment
        
        ## User Information
        ```json
        {0}
        ```
        
        ## Document Data
        ```json
        {1}
        ```
        
        ## Third-Party Data
        ```json
        {2}
        ```
        
        ## Response Format
        Return your analysis in the following JSON format:
        ```json
        {{
            "risk_score": 0-100,
            "risk_status": "low/medium/high",
            "reasoning": "Detailed explanation of risk assessment",
            "discrepancies": ["List of discrepancies found"],
            "red_flags": ["List of red flags identified"],
            "recommendations": ["Optional recommendations"]
        }}
        ```
        
        Your analysis must be thorough, fair, and based solely on the information provided.
        """
        
        # Format the prompt with JSON data
        formatted_prompt = prompt.format(
            json.dumps(user_data, indent=2),
            json.dumps(documents_data, indent=2),
            json.dumps(third_party_data, indent=2)
        )
        
        return formatted_prompt