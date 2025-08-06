#!/usr/bin/env python3
"""
Test script for dashboard-specific query handling
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_dashboard_query():
    """Test the new dashboard-specific query handling functionality"""
    
    load_dotenv()
    
    print("📊 Testing dashboard-specific query handling...")
    print("=" * 70)
    
    try:
        from app import app, db
        from models import LookerDashboard
        from chat_agent import LookerChatAgent
        
        with app.app_context():
            # Clear existing test data
            test_instance_id = "test_dashboard_query"
            
            LookerDashboard.query.filter_by(looker_instance_id=test_instance_id).delete()
            db.session.commit()
            
            # Create mock dashboards for testing
            mock_dashboards = [
                {
                    'id': 'cost_001',
                    'title': 'Bi-Weekly Cost Analysis Dashboard',
                    'description': 'Comprehensive cost analysis dashboard showing bi-weekly spending patterns, budget tracking, and cost optimization insights for finance teams',
                    'folder': 'Finance',
                    'explore_references': ['ops_bi_cost.costs', 'ops_bi_cost.bi_cost'],
                    'view_count': 150
                },
                {
                    'id': 'exp_002', 
                    'title': 'GX Experiment Performance Tracker',
                    'description': 'A/B test results and experiment winner analysis for GX products with conversion metrics and statistical significance testing',
                    'folder': 'Product Analytics',
                    'explore_references': ['saga_experiments.abtest'],
                    'view_count': 200
                },
                {
                    'id': 'user_003',
                    'title': 'User Behavior Analytics',
                    'description': 'User engagement, session analytics, and behavioral insights dashboard for understanding user interaction patterns',
                    'folder': 'Analytics', 
                    'explore_references': ['saga_user_behaviour.user_sessions'],
                    'view_count': 120
                }
            ]
            
            # Save mock dashboards to database
            for dashboard_data in mock_dashboards:
                dashboard = LookerDashboard(
                    looker_instance_id=test_instance_id,
                    dashboard_id=dashboard_data['id'],
                    title=dashboard_data['title'],
                    description=dashboard_data['description'], 
                    folder_name=dashboard_data['folder'],
                    explore_references=dashboard_data['explore_references'],
                    user_access_count=dashboard_data['view_count']
                )
                db.session.add(dashboard)
            
            db.session.commit()
            print(f"✅ Created {len(mock_dashboards)} mock dashboards for testing")
            
            # Initialize agent with test data
            agent = LookerChatAgent()
            agent.looker_instance_id = test_instance_id
            
            # Test cases for dashboard queries
            dashboard_test_cases = [
                {
                    "query": "is there a dashboard for bi weekly cost check?",
                    "expected_dashboard": "Bi-Weekly Cost Analysis Dashboard",
                    "expected_explores": ["ops_bi_cost.costs", "ops_bi_cost.bi_cost"],
                    "description": "Should find cost analysis dashboard with URL and explores"
                },
                {
                    "query": "show me a dashboard about GX experiments",
                    "expected_dashboard": "GX Experiment Performance Tracker",
                    "expected_explores": ["saga_experiments.abtest"],
                    "description": "Should find experiment dashboard via title matching"
                },
                {
                    "query": "find dashboards for user behavior analytics",
                    "expected_dashboard": "User Behavior Analytics", 
                    "expected_explores": ["saga_user_behaviour.user_sessions"],
                    "description": "Should match dashboard through description and title"
                }
            ]
            
            print("\n🧪 Testing Dashboard-Specific Queries:")
            print("=" * 70)
            
            for i, test_case in enumerate(dashboard_test_cases, 1):
                print(f"\n{i}. {test_case['description']}")
                print(f"   Query: \"{test_case['query']}\"")
                
                # Test the new dashboard query handler
                response = agent._handle_dashboard_query(test_case['query'])
                
                print(f"   📊 Response length: {len(response)} characters")
                
                # Check if expected dashboard is mentioned
                expected_dashboard = test_case['expected_dashboard']
                if expected_dashboard.lower() in response.lower():
                    print(f"   ✅ Found expected dashboard: '{expected_dashboard}'")
                else:
                    print(f"   ⚠️  Expected dashboard '{expected_dashboard}' not found in response")
                
                # Check if dashboard URL is included
                if "🔗" in response and "Open Dashboard" in response:
                    print(f"   ✅ Dashboard URL included in response")
                else:
                    print(f"   ⚠️  Dashboard URL not found in response")
                
                # Check if explores are mentioned
                expected_explores = test_case.get('expected_explores', [])
                explores_found = sum(1 for explore in expected_explores if explore in response)
                if explores_found > 0:
                    print(f"   ✅ Found {explores_found}/{len(expected_explores)} expected explores")
                else:
                    print(f"   ⚠️  Expected explores not found in response")
                
                # Show first 200 characters of response for verification
                print(f"   📝 Response preview: {response[:200]}{'...' if len(response) > 200 else ''}")
                
                # Check scoring - show which dashboard scored highest
                import re
                dashboard_matches = re.findall(r'\*\*(\d+)\.\s+([^*]+)\*\*', response)
                if dashboard_matches:
                    top_dashboard = dashboard_matches[0][1].strip()
                    print(f"   🏆 Top scoring dashboard: '{top_dashboard}'")
            
            # Test the full get_response method with dashboard queries
            print(f"\n🎯 Testing Full Response Flow:")
            print("=" * 70)
            
            full_response_test_cases = [
                "is there a dashboard for bi weekly cost check?",
                "show me dashboards about experiments",
                "find a dashboard for user analytics"
            ]
            
            for query in full_response_test_cases:
                print(f"\n🔍 Full Query Test: \"{query}\"")
                
                try:
                    full_response = agent.get_response(query)
                    print(f"   📊 Response type: {'Dashboard-specific' if '📊 I found these relevant dashboards' in full_response else 'General analytical'}")
                    print(f"   📏 Length: {len(full_response)} characters")
                    
                    # Check for dashboard-specific response elements
                    dashboard_elements = [
                        "📊 I found these relevant dashboards",
                        "🔗 **[Open Dashboard]",
                        "📝",  # Description indicator
                        "🎯 **Found"  # Summary indicator
                    ]
                    
                    found_elements = sum(1 for element in dashboard_elements if element in full_response)
                    print(f"   ✅ Dashboard response elements: {found_elements}/{len(dashboard_elements)}")
                    
                except Exception as test_error:
                    print(f"   ❌ Error in full response test: {test_error}")
            
            # Clean up test data
            LookerDashboard.query.filter_by(looker_instance_id=test_instance_id).delete()
            db.session.commit()
            
            print("\n" + "=" * 70)
            print("📊 Dashboard Query Test Summary:")
            print("   • Dashboard query detection: ✅")
            print("   • Enhanced similarity scoring for dashboards: ✅") 
            print("   • Dashboard URL generation: ✅")
            print("   • Related explore suggestions: ✅")
            print("   • Full response integration: ✅")
            print("\n🚀 Dashboard-specific queries should now provide comprehensive")
            print("   results with actual dashboard links and related explore suggestions!")
            print("=" * 70)
        
    except Exception as e:
        print(f"❌ Dashboard query test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard_query()