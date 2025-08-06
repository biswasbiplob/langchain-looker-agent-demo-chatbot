#!/usr/bin/env python3
"""
Quick debug test to see what's actually happening with the queries
"""
import os
from dotenv import load_dotenv
load_dotenv()

from chat_agent import LookerChatAgent

def debug_queries():
    agent = LookerChatAgent()
    
    print("=== DEBUG: Testing specific problematic queries ===")
    
    # Test the GX ab test query
    print("\n1. Testing: 'How many GX ab test winners did we have last year?'")
    results = agent.find_relevant_models_and_explores("How many GX ab test winners did we have last year?")
    print(f"Results: {results}")
    
    # Test the user response generation  
    print("\n2. Testing full response for GX ab test query:")
    response = agent.get_response("How many GX ab test winners did we have last year?")
    print(f"Response: {response}")
    
    # Test cost dashboard query
    print("\n3. Testing: 'Is there a dashboards for bi weekly cost check?'")
    response = agent.get_response("Is there a dashboards for bi weekly cost check?")
    print(f"Response: {response}")

if __name__ == "__main__":
    debug_queries()