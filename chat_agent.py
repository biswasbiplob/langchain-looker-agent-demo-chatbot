import os
import logging
from typing import List, Dict, Any, Optional

class LookerChatAgent:
    """Chat agent that integrates with Looker BI using langchain-looker-agent"""
    
    def __init__(self):
        """Initialize the Looker agent with environment variables"""
        self.looker_base_url = os.getenv('LOOKER_BASE_URL')
        self.looker_client_id = os.getenv('LOOKER_CLIENT_ID')
        self.looker_client_secret = os.getenv('LOOKER_CLIENT_SECRET')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.lookml_model_name = os.getenv('LOOKML_MODEL_NAME')
        self.jdbc_driver_path = os.getenv('JDBC_DRIVER_PATH')
        
        # Check if we have the minimum required credentials
        self.credentials_available = bool(
            self.looker_base_url and 
            self.looker_client_id and 
            self.looker_client_secret and 
            self.openai_api_key and
            self.lookml_model_name and
            self.jdbc_driver_path
        )
        
        self.agent = None
        
        if self.credentials_available:
            try:
                self._initialize_agent()
            except Exception as e:
                logging.error(f"Failed to initialize Looker agent: {e}")
                self.credentials_available = False
        
    def _initialize_agent(self):
        """Initialize the actual Looker agent"""
        try:
            from langchain_looker_agent import create_looker_sql_agent, LookerSQLDatabase, LookerSQLToolkit
            from langchain_openai import OpenAI
            
            # Initialize the Looker database connection
            self.looker_db = LookerSQLDatabase(
                looker_instance_url=self.looker_base_url,
                lookml_model_name=self.lookml_model_name,
                client_id=self.looker_client_id,
                client_secret=self.looker_client_secret,
                jdbc_driver_path=self.jdbc_driver_path
            )
            
            # Initialize the OpenAI LLM with a model that supports larger context
            self.llm = OpenAI(
                api_key=self.openai_api_key,
                temperature=0,
                model="gpt-3.5-turbo-instruct",
                max_tokens=1000
            )
            
            # Create the Looker SQL toolkit
            toolkit = LookerSQLToolkit(db=self.looker_db, llm=self.llm)
            
            # Create the Looker SQL agent
            self.agent = create_looker_sql_agent(
                llm=self.llm,
                toolkit=toolkit,
                verbose=True
            )
            
            logging.info("Looker agent initialized successfully")
            
        except ImportError as e:
            logging.error(f"Failed to import required packages: {e}")
            raise
        except Exception as e:
            logging.error(f"Failed to initialize Looker agent: {e}")
            raise
    
    def get_response(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Get a response from the Looker agent for the user's analytical question
        
        Args:
            user_message: The user's question or request
            chat_history: Previous chat exchanges for context
            
        Returns:
            String response from the agent
        """
        # Check if credentials are available
        if not self.credentials_available:
            return self._get_credentials_error_message()
        
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
            if self.agent is not None:
                # Prepare chat history for the agent
                formatted_history = ""
                if chat_history:
                    recent_history = chat_history[-3:] if len(chat_history) > 3 else chat_history
                    for exchange in recent_history:
                        formatted_history += f"Human: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
                
                result = self.agent.invoke({
                    "input": user_message,
                    "chat_history": formatted_history
                })
                response = result.get("output", str(result)) if isinstance(result, dict) else str(result)
            else:
                return "Agent not properly initialized. Please check your Looker configuration."
            
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
    
    def _get_credentials_error_message(self) -> str:
        """Return an informative message about missing credentials"""
        missing_vars = []
        if not self.looker_base_url:
            missing_vars.append('LOOKER_BASE_URL')
        if not self.looker_client_id:
            missing_vars.append('LOOKER_CLIENT_ID')
        if not self.looker_client_secret:
            missing_vars.append('LOOKER_CLIENT_SECRET')
        if not self.openai_api_key:
            missing_vars.append('OPENAI_API_KEY')
        if not self.lookml_model_name:
            missing_vars.append('LOOKML_MODEL_NAME')
        if not self.jdbc_driver_path:
            missing_vars.append('JDBC_DRIVER_PATH')
        
        return f"""I'm unable to connect to your Looker BI platform because some required configuration is missing.

To enable data analysis, I need the following environment variables to be set:
• LOOKER_BASE_URL - Your Looker instance URL
• LOOKER_CLIENT_ID - Your Looker API client ID
• LOOKER_CLIENT_SECRET - Your Looker API client secret
• OPENAI_API_KEY - OpenAI API key for natural language processing
• LOOKML_MODEL_NAME - The LookML model to query
• JDBC_DRIVER_PATH - Path to the Looker JDBC driver

Missing: {', '.join(missing_vars)}

Please configure these credentials to start analyzing your data!"""
    
    def test_connection(self) -> bool:
        """
        Test the connection to Looker
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if not self.credentials_available:
                return False
                
            if self.agent is None:
                return False
                
            # Try a simple query to test connection
            result = self.agent.invoke({
                "input": "What data sources are available?",
                "chat_history": ""
            })
            return bool(result)
        except Exception as e:
            logging.error(f"Looker connection test failed: {e}")
            return False
