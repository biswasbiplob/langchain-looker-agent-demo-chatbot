import os
import logging
from typing import List, Dict, Any

try:
    from langchain_looker_agent import LookerAgent
except ImportError as e:
    logging.error(f"Failed to import langchain_looker_agent: {e}")
    logging.error("Please ensure the package is installed: pip install langchain-looker-agent")
    raise

class LookerChatAgent:
    """Chat agent that integrates with Looker BI using langchain-looker-agent"""
    
    def __init__(self):
        """Initialize the Looker agent with environment variables"""
        self.looker_base_url = os.getenv('LOOKER_BASE_URL')
        self.looker_client_id = os.getenv('LOOKER_CLIENT_ID')
        self.looker_client_secret = os.getenv('LOOKER_CLIENT_SECRET')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Validate required environment variables
        required_vars = {
            'LOOKER_BASE_URL': self.looker_base_url,
            'LOOKER_CLIENT_ID': self.looker_client_id,
            'LOOKER_CLIENT_SECRET': self.looker_client_secret,
            'OPENAI_API_KEY': self.openai_api_key
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Initialize the Looker agent
            self.agent = LookerAgent(
                looker_base_url=self.looker_base_url,
                looker_client_id=self.looker_client_id,
                looker_client_secret=self.looker_client_secret,
                openai_api_key=self.openai_api_key
            )
            logging.info("Looker agent initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Looker agent: {e}")
            raise
    
    def get_response(self, user_message: str, chat_history: List[Dict[str, str]] = None) -> str:
        """
        Get a response from the Looker agent for the user's analytical question
        
        Args:
            user_message: The user's question or request
            chat_history: Previous chat exchanges for context
            
        Returns:
            String response from the agent
        """
        try:
            # Prepare context from chat history
            context = ""
            if chat_history:
                # Include last few exchanges for context
                recent_history = chat_history[-3:] if len(chat_history) > 3 else chat_history
                for exchange in recent_history:
                    context += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
            
            # Combine context with current message
            full_message = f"{context}User: {user_message}" if context else user_message
            
            # Get response from Looker agent
            response = self.agent.run(full_message)
            
            # Ensure response is a string
            if isinstance(response, dict):
                response = response.get('output', str(response))
            elif not isinstance(response, str):
                response = str(response)
            
            # Basic response validation and enhancement
            if not response or response.strip() == "":
                response = "I apologize, but I couldn't generate a meaningful response to your question. Could you please rephrase or provide more specific details about the data you're looking for?"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error getting response from Looker agent: {e}")
            error_msg = "I encountered an issue while processing your request. "
            
            if "authentication" in str(e).lower():
                error_msg += "There seems to be an authentication problem with Looker. Please check the connection settings."
            elif "timeout" in str(e).lower():
                error_msg += "The query took too long to process. Please try a more specific question or try again later."
            elif "not found" in str(e).lower():
                error_msg += "I couldn't find the requested data or dashboard. Please verify the data source exists."
            else:
                error_msg += "Please try rephrasing your question or contact support if the issue persists."
            
            return error_msg
    
    def test_connection(self) -> bool:
        """
        Test the connection to Looker
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try a simple query to test connection
            test_response = self.agent.run("What data sources are available?")
            return bool(test_response)
        except Exception as e:
            logging.error(f"Looker connection test failed: {e}")
            return False
