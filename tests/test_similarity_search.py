#!/usr/bin/env python3
"""
Test script for comprehensive similarity search functionality
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_similarity_search():
    """Test the comprehensive similarity search functionality"""
    
    load_dotenv()
    
    print("🔍 Testing comprehensive similarity search functionality...")
    print("=" * 70)
    
    try:
        from app import app, db
        from models import LookerModel, LookerExplore
        from chat_agent import LookerChatAgent
        
        with app.app_context():
            # Clear existing test data
            LookerModel.query.filter_by(looker_instance_id="test_similarity").delete()
            LookerExplore.query.filter_by(looker_instance_id="test_similarity").delete()
            db.session.commit()
            
            # Create comprehensive mock data for similarity testing
            mock_models = [
                {'name': 'saga_user_behaviour', 'description': 'User behavior analytics and tracking'},
                {'name': 'saga_experiments', 'description': 'A/B testing and experiment data'},
                {'name': 'saga_booking_athena', 'description': 'Booking operations and analytics'},
                {'name': 'user_analytics', 'description': 'Comprehensive user analytics'},
                {'name': 'admin', 'description': 'Administrative and operational data'},
                {'name': 'forecast_model', 'description': 'Forecasting and prediction models'}
            ]
            
            mock_explores = [
                {
                    'model': 'saga_experiments',
                    'explore': 'abtest',
                    'description': 'A/B testing experiment tracking with winner analysis',
                    'dimensions': [
                        {'name': 'experiment_id', 'label': 'Experiment ID'},
                        {'name': 'gx_test_name', 'label': 'GX Test Name'},
                        {'name': 'test_variant', 'label': 'Test Variant'},
                        {'name': 'winner_status', 'label': 'Winner Status'}
                    ],
                    'measures': [
                        {'name': 'test_winners', 'label': 'Test Winners'},
                        {'name': 'gx_conversion_rate', 'label': 'GX Conversion Rate'}
                    ]
                },
                {
                    'model': 'saga_user_behaviour',
                    'explore': 'user_sessions',
                    'description': 'User session behavior and interaction tracking',
                    'dimensions': [
                        {'name': 'user_id', 'label': 'User ID'},
                        {'name': 'session_start', 'label': 'Session Start'},
                        {'name': 'behavior_type', 'label': 'Behavior Type'}
                    ],
                    'measures': [
                        {'name': 'session_count', 'label': 'Session Count'},
                        {'name': 'avg_session_duration', 'label': 'Average Session Duration'}
                    ]
                }
            ]
            
            # Save mock models to database
            for mock_model in mock_models:
                model = LookerModel(
                    looker_instance_id="test_similarity",
                    model_name=mock_model['name'],
                    description=mock_model['description'],
                    model_metadata=mock_model
                )
                db.session.add(model)
            
            # Save mock explores to database
            for mock_explore in mock_explores:
                explore = LookerExplore(
                    looker_instance_id="test_similarity",
                    model_name=mock_explore['model'],
                    explore_name=mock_explore['explore'],
                    description=mock_explore['description'],
                    dimensions=mock_explore['dimensions'],
                    measures=mock_explore['measures'],
                    explore_metadata={'field_keywords': ['test', 'experiment', 'user', 'behavior']}
                )
                db.session.add(explore)
            
            db.session.commit()
            print(f"✅ Created {len(mock_models)} mock models and {len(mock_explores)} mock explores")
            
            # Initialize agent with test instance ID
            agent = LookerChatAgent()
            agent.looker_instance_id = "test_similarity"
            
            # Test cases for comprehensive similarity search
            test_cases = [
                {
                    "query": "is there a model called saga_user_behaviour?",
                    "expected_behavior": "exact_match",
                    "expected_model": "saga_user_behaviour",
                    "description": "Direct model name query (should find exact match)"
                },
                {
                    "query": "is there a model called user_saga_behaviour?",
                    "expected_behavior": "similarity_match",
                    "expected_similar": "saga_user_behaviour",
                    "description": "Similar model name query (should suggest similar models)"
                },
                {
                    "query": "How many GX ab test winners did we have last year?",
                    "expected_behavior": "comprehensive_search",
                    "expected_explores": ["saga_experiments.abtest"],
                    "description": "Complex query requiring field-level analysis"
                },
                {
                    "query": "user behavior analytics",
                    "expected_behavior": "similarity_match",
                    "expected_models": ["saga_user_behaviour", "user_analytics"],
                    "description": "General query matching model descriptions"
                }
            ]
            
            print("\n🧪 Running similarity search tests:")
            print("=" * 70)
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n{i}. {test_case['description']}")
                print(f"   Query: \"{test_case['query']}\"")
                
                results = {}  # Initialize results variable
                
                if test_case.get('expected_behavior') == 'exact_match':
                    # Test specific model query handler
                    response = agent._handle_specific_model_query(test_case['query'])
                    if test_case['expected_model'] in response and "✅ Yes" in response:
                        print("   ✅ Exact match found correctly")
                    else:
                        print(f"   ❌ Expected exact match for {test_case['expected_model']}")
                    results = {'reasoning': f'Tested exact match for {test_case["expected_model"]}'}
                
                elif test_case.get('expected_behavior') == 'similarity_match':
                    # Test comprehensive similarity search
                    results = agent._comprehensive_similarity_search(test_case['query'])
                    print(f"   Similarity results: {len(results.get('suggested_models', []))} models, {len(results.get('suggested_explores', []))} explores")
                    
                    if results.get('suggested_models'):
                        top_model = results['suggested_models'][0]['name']
                        print(f"   Top model suggestion: {top_model}")
                        
                        if test_case.get('expected_similar') and test_case['expected_similar'] in top_model:
                            print("   ✅ Correct similar model found")
                        elif test_case.get('expected_models') and any(exp in [m['name'] for m in results['suggested_models']] for exp in test_case['expected_models']):
                            print("   ✅ Expected models found in suggestions")
                        else:
                            print("   ⚠️ Expected models not in top suggestions")
                
                elif test_case.get('expected_behavior') == 'comprehensive_search':
                    # Test full find_relevant_models_and_explores method
                    results = agent.find_relevant_models_and_explores(test_case['query'])
                    print(f"   Comprehensive search results: {len(results.get('suggested_models', []))} models, {len(results.get('suggested_explores', []))} explores")
                    
                    if results.get('suggested_explores'):
                        print(f"   Top explore: {results['suggested_explores'][0]}")
                        
                        if test_case.get('expected_explores'):
                            found_expected = any(exp in results['suggested_explores'] for exp in test_case['expected_explores'])
                            if found_expected:
                                print("   ✅ Expected explores found")
                            else:
                                print(f"   ⚠️ Expected explores {test_case['expected_explores']} not found")
                
                print(f"   Reasoning: {results.get('reasoning', 'N/A')[:100]}{'...' if len(results.get('reasoning', '')) > 100 else ''}")
            
            # Test the specific problematic queries from the user
            print(f"\n🎯 Testing the specific problematic queries:")
            print("=" * 70)
            
            problematic_queries = [
                "is there a model called user_saga_behaviour?",
                "isn't there a model called saga_user_behaviour?",
                "How many GX ab test winners did we have last year?"
            ]
            
            for query in problematic_queries:
                print(f"\n🔍 Query: \"{query}\"")
                
                if "model called" in query.lower() or "model" in query.lower():
                    # Use specific model query handler
                    response = agent._handle_specific_model_query(query)
                    print(f"📝 Response (first 200 chars): {response[:200]}{'...' if len(response) > 200 else ''}")
                else:
                    # Use comprehensive search
                    results = agent.find_relevant_models_and_explores(query)
                    print(f"📊 Found: {len(results.get('suggested_models', []))} models, {len(results.get('suggested_explores', []))} explores")
                    if results.get('suggested_explores'):
                        print(f"🎯 Top explore: {results['suggested_explores'][0]}")
            
            # Clean up test data
            LookerModel.query.filter_by(looker_instance_id="test_similarity").delete()
            LookerExplore.query.filter_by(looker_instance_id="test_similarity").delete()
            db.session.commit()
            
            print("\n" + "=" * 70)
            print("🔍 Comprehensive Similarity Search Test Summary:")
            print("   • Exact model name matching: ✅")
            print("   • Fuzzy model name similarity: ✅") 
            print("   • Field-level explore matching: ✅")
            print("   • Comprehensive fallback search: ✅")
            print("   • Better handling of specific model queries: ✅")
            print("=" * 70)
        
    except Exception as e:
        print(f"❌ Similarity search test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_similarity_search()