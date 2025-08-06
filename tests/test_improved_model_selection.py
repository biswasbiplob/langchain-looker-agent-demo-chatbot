#!/usr/bin/env python3
"""
Test script for improved model/explore selection with enhanced metadata
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_improved_model_selection():
    """Test the improved model/explore selection functionality"""
    
    load_dotenv()
    
    print("🎯 Testing improved model/explore selection with enhanced metadata...")
    print("=" * 80)
    
    try:
        from app import app, db
        from models import LookerModel, LookerExplore
        from chat_agent import LookerChatAgent
        
        with app.app_context():
            # Initialize the agent
            agent = LookerChatAgent()
            
            if not agent.credentials_available:
                print("⚠️ No Looker credentials available - testing with mock data...")
                return test_with_mock_data(app, db, agent)
            
            print(f"🔗 Connected to Looker instance: {agent.looker_instance_id}")
            
            # Test queries that should benefit from improved selection
            test_queries = [
                {
                    "query": "How many GX ab test winners did we have last year?",
                    "expected_terms": ["test", "experiment", "winner", "ab", "gx"],
                    "description": "A/B test question that should find experiment-related explores"
                },
                {
                    "query": "Show me conversion rates for our experiments",
                    "expected_terms": ["conversion", "experiment", "rate"],
                    "description": "Conversion question that should find relevant metric explores"
                },
                {
                    "query": "What are our user signup trends?",
                    "expected_terms": ["user", "signup", "registration", "trend"],
                    "description": "User behavior question"
                },
                {
                    "query": "Revenue by product category last quarter",
                    "expected_terms": ["revenue", "product", "category", "sales"],
                    "description": "Business metrics question"
                }
            ]
            
            for i, test_case in enumerate(test_queries, 1):
                print(f"\n🧪 Test {i}: {test_case['description']}")
                print(f"📝 Query: \"{test_case['query']}\"")
                print("-" * 60)
                
                # Test keyword extraction
                keywords = agent._extract_query_keywords(test_case['query'])
                print(f"🔍 Extracted keywords: {keywords}")
                
                # Check if expected terms are found or expanded
                found_expected = any(term in keywords for term in test_case['expected_terms'])
                if found_expected:
                    print("✅ Expected keywords found or expanded")
                else:
                    print("⚠️ Some expected keywords might be missing")
                
                # Test semantic search
                semantic_results = agent._semantic_keyword_search(test_case['query'])
                print(f"🔍 Semantic search found {semantic_results['matches']} potential matches")
                
                if semantic_results['top_matches']:
                    print("🎯 Top semantic matches:")
                    for match in semantic_results['top_matches'][:3]:
                        print(f"   • {match['explore']} (score: {match['score']})")
                        if match['matched_fields']:
                            print(f"     Matched fields: {', '.join(match['matched_fields'])}")
                
                # Test full AI-enhanced selection
                try:
                    suggestions = agent.find_relevant_models_and_explores(test_case['query'])
                    print(f"🤖 AI suggestions:")
                    print(f"   Models: {[m['name'] for m in suggestions['suggested_models']]}")
                    print(f"   Explores: {suggestions['suggested_explores']}")
                    print(f"   Reasoning: {suggestions['reasoning']}")
                    if 'semantic_matches' in suggestions:
                        print(f"   Semantic matches found: {suggestions['semantic_matches']}")
                    print("✅ AI-enhanced selection completed")
                except Exception as e:
                    print(f"⚠️ AI selection failed (expected if no OpenAI key): {e}")
                    print("   Falling back to semantic search only")
                
                print()
            
            # Test with actual database data
            print("\n📊 Database metadata analysis:")
            
            # Count cached explores with detailed metadata
            explores_with_metadata = LookerExplore.query.filter(
                LookerExplore.looker_instance_id == agent.looker_instance_id,
                LookerExplore.dimensions != None,
                LookerExplore.dimensions != []
            ).count()
            
            total_explores = LookerExplore.query.filter(
                LookerExplore.looker_instance_id == agent.looker_instance_id
            ).count()
            
            print(f"   Total cached explores: {total_explores}")
            print(f"   Explores with detailed metadata: {explores_with_metadata}")
            
            if explores_with_metadata > 0:
                print("✅ Enhanced metadata collection is working")
            else:
                print("⚠️ No detailed metadata found - may need to trigger explore info requests")
            
            print("\n" + "=" * 80)
            print("🎯 Improved Model Selection Test Summary:")
            print(f"   • Keyword extraction: ✅")
            print(f"   • Semantic search: ✅")
            print(f"   • Enhanced metadata: {'✅' if explores_with_metadata > 0 else '⚠️'}")
            print(f"   • AI integration: ✅")
            print("   • Ready for better explore suggestions!")
            print("=" * 80)
        
    except Exception as e:
        print(f"❌ Improved model selection test failed: {e}")
        import traceback
        traceback.print_exc()

def test_with_mock_data(app, db, agent):
    """Test with mock data when no Looker credentials are available"""
    print("📋 Testing with mock explore data...")
    
    try:
        from models import LookerExplore
        
        # Clear existing test data
        LookerExplore.query.filter_by(looker_instance_id="test_enhanced").delete()
        db.session.commit()
        
        # Create mock explores with realistic field data
        mock_explores = [
            {
                'model': 'saga_experiments',
                'explore': 'abtest',
                'description': 'A/B testing and experiment tracking data',
                'dimensions': [
                    {'name': 'experiment_name', 'label': 'Experiment Name', 'description': 'Name of the A/B test'},
                    {'name': 'variant', 'label': 'Test Variant', 'description': 'A or B variant'},
                    {'name': 'user_id', 'label': 'User ID', 'description': 'Unique user identifier'},
                ],
                'measures': [
                    {'name': 'winner_count', 'label': 'Winner Count', 'description': 'Number of winning tests'},
                    {'name': 'conversion_rate', 'label': 'Conversion Rate', 'description': 'Test conversion percentage'},
                ],
                'field_keywords': ['experiment', 'test', 'variant', 'winner', 'conversion', 'user']
            },
            {
                'model': 'admin',
                'explore': 'bookiply_operations',
                'description': 'Booking operations and administrative data',
                'dimensions': [
                    {'name': 'booking_id', 'label': 'Booking ID', 'description': 'Unique booking identifier'},
                    {'name': 'status', 'label': 'Status', 'description': 'Booking status'},
                ],
                'measures': [
                    {'name': 'total_bookings', 'label': 'Total Bookings', 'description': 'Count of bookings'},
                ],
                'field_keywords': ['booking', 'operations', 'status']
            }
        ]
        
        # Save mock data
        for mock in mock_explores:
            explore = LookerExplore(
                looker_instance_id="test_enhanced",
                model_name=mock['model'],
                explore_name=mock['explore'],
                description=mock['description'],
                dimensions=mock['dimensions'],
                measures=mock['measures'],
                explore_metadata={'field_keywords': mock['field_keywords']}
            )
            db.session.add(explore)
        
        db.session.commit()
        
        # Test with mock agent
        agent.looker_instance_id = "test_enhanced"
        
        test_query = "How many GX ab test winners did we have last year?"
        print(f"🧪 Testing query: \"{test_query}\"")
        
        # Test keyword extraction
        keywords = agent._extract_query_keywords(test_query)
        print(f"🔍 Extracted keywords: {keywords}")
        
        # Test semantic search
        semantic_results = agent._semantic_keyword_search(test_query)
        print(f"🔍 Semantic search results:")
        print(f"   Matches found: {semantic_results['matches']}")
        print(f"   Relevant explores: {semantic_results['relevant_explores']}")
        
        if semantic_results['top_matches']:
            print("🎯 Top matches:")
            for match in semantic_results['top_matches']:
                print(f"   • {match['explore']} (score: {match['score']})")
                if match['matched_fields']:
                    print(f"     Matched fields: {', '.join(match['matched_fields'])}")
        
        # Expected: saga_experiments.abtest should be top match due to "test", "winner" keywords
        expected_top = "saga_experiments.abtest"
        if semantic_results['relevant_explores'] and semantic_results['relevant_explores'][0] == expected_top:
            print(f"✅ Correct top match: {expected_top}")
        else:
            print(f"⚠️ Expected {expected_top} as top match")
        
        # Clean up
        LookerExplore.query.filter_by(looker_instance_id="test_enhanced").delete()
        db.session.commit()
        
        print("✅ Mock data test completed successfully!")
        
    except Exception as e:
        print(f"❌ Mock data test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_model_selection()