#\!/usr/bin/env python3
"""
Test script for the updated chatbot agent
"""
import os
from dotenv import load_dotenv
from chat_agent import LookerChatAgent

def test_chatbot():
    """Test the chatbot with various queries"""
    
    load_dotenv()
    
    print("🧪 Testing the updated Looker chatbot with dynamic model discovery...")
    print("=" * 70)
    
    try:
        # Initialize the agent
        agent = LookerChatAgent()
        
        if not agent.credentials_available:
            print("❌ Credentials not available")
            return
        
        # Test queries (updated for dynamic model discovery)
        test_queries = [
            "What models are available?",
            "What explores are available?", 
            "What dimensions are available to 'session' explore?",
            "How many users came to the website?",
            "Tell me about the session explore",
            "What data is available for analyzing user behavior?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query}")
            print("-" * 50)
            
            try:
                response = agent.get_response(query)
                print(f"🤖 Response: {response}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 70)
        print("✅ Testing complete\!")
        
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatbot()
EOF < /dev/null