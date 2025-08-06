#!/usr/bin/env python3
"""
Test runner for all chatbot tests
"""
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_all_tests():
    """Run all available tests"""
    print("🚀 Running all chatbot tests with dynamic model discovery and database caching...")
    print("=" * 70)
    
    try:
        # Run direct query test
        print("\n1️⃣ Running direct Looker query test...")
        from test_direct_query import test_direct_looker_query
        test_direct_looker_query()
        
        print("\n" + "=" * 70)
        
        # Run chatbot test
        print("\n2️⃣ Running chatbot agent test...")
        from test_chatbot import test_chatbot
        test_chatbot()
        
        print("\n" + "=" * 70)
        
        # Run basic caching test (no credentials needed)
        print("\n3️⃣ Running basic database caching test...")
        from test_basic_caching import test_basic_caching
        test_basic_caching()
        
        print("\n" + "=" * 70)
        
        # Run semantic search test (no credentials needed)
        print("\n4️⃣ Running semantic search test...")
        from test_semantic_search import test_semantic_search
        test_semantic_search()
        
        print("\n" + "=" * 70)
        
        # Run similarity search test (no credentials needed)
        print("\n5️⃣ Running comprehensive similarity search test...")
        from test_similarity_search import test_similarity_search
        test_similarity_search()
        
        print("\n" + "=" * 70)
        
        # Run full database caching test (requires credentials)
        print("\n6️⃣ Running full database caching test...")
        from test_database_caching import test_database_caching
        test_database_caching()
        
        print("\n" + "=" * 70)
        
        # Run dashboard context integration test (no credentials needed)
        print("\n7️⃣ Running dashboard context integration test...")
        from test_dashboard_context import test_dashboard_context
        test_dashboard_context()
        
        print("\n" + "=" * 70)
        
        # Run dashboard query test (no credentials needed)
        print("\n8️⃣ Running dashboard query handling test...")
        from test_dashboard_query import test_dashboard_query
        test_dashboard_query()
        
        print("\n" + "=" * 70)
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()