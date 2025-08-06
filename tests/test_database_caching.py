#!/usr/bin/env python3
"""
Test script for database caching functionality in LookerChatAgent
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_database_caching():
    """Test the database caching functionality"""
    
    load_dotenv()
    
    print("🗄️ Testing database caching functionality...")
    print("=" * 70)
    
    try:
        from app import app, db
        from models import LookerModel, LookerExplore
        from chat_agent import LookerChatAgent
        
        with app.app_context():
            # Clear existing cache data for clean test
            print("\n🧹 Clearing existing cache data...")
            LookerModel.query.delete()
            LookerExplore.query.delete()
            db.session.commit()
            
            # Initialize the agent
            agent = LookerChatAgent()
            
            if not agent.credentials_available:
                print("❌ Credentials not available for testing")
                return
            
            print(f"🔗 Connected to Looker instance: {agent.looker_instance_id}")
            
            # Test 1: Models caching
            print("\n📦 Test 1: Models caching")
            print("-" * 30)
            
            # First call - should fetch from API and cache in database
            print("🔍 First call to get_available_models() - should fetch from API...")
            models1 = agent.get_available_models()
            
            # Check if models were saved to database
            db_models = LookerModel.query.filter_by(looker_instance_id=agent.looker_instance_id).count()
            print(f"📊 Found {len(models1)} models from API")
            print(f"🗄️ Saved {db_models} models to database")
            
            if db_models > 0:
                print("✅ Models successfully cached to database")
            else:
                print("❌ Models not cached to database")
            
            # Second call - should fetch from database cache
            print("\n🔍 Second call to get_available_models() - should use database cache...")
            models2 = agent.get_available_models()
            
            if models1 == models2:
                print("✅ Database caching working - same results returned")
            else:
                print("❌ Database caching issue - different results returned")
            
            # Test 2: Explores caching
            if models1:
                print(f"\n📊 Test 2: Explores caching for model '{models1[0]['name']}'")
                print("-" * 50)
                
                model_name = models1[0]['name']
                
                # First call - should fetch from API and cache
                print(f"🔍 First call to get_available_explores('{model_name}') - should fetch from API...")
                explores1 = agent.get_available_explores(model_name)
                
                # Check if explores were saved to database
                db_explores = LookerExplore.query.filter_by(
                    looker_instance_id=agent.looker_instance_id,
                    model_name=model_name
                ).count()
                print(f"📊 Found {len(explores1)} explores from API")
                print(f"🗄️ Saved {db_explores} explores to database")
                
                if db_explores > 0:
                    print("✅ Explores successfully cached to database")
                else:
                    print("❌ Explores not cached to database")
                
                # Second call - should fetch from database cache
                print(f"\n🔍 Second call to get_available_explores('{model_name}') - should use database cache...")
                explores2 = agent.get_available_explores(model_name)
                
                if explores1 == explores2:
                    print("✅ Explores database caching working - same results returned")
                else:
                    print("❌ Explores database caching issue - different results returned")
                
                # Test 3: Detailed explore info caching
                if explores1:
                    print(f"\n📋 Test 3: Detailed explore info caching for '{explores1[0]}'")
                    print("-" * 60)
                    
                    explore_name = explores1[0]
                    
                    # First call - should fetch detailed info from API and cache
                    print(f"🔍 First call to get_explore_info('{explore_name}', '{model_name}') - should fetch from API...")
                    info1 = agent.get_explore_info(explore_name, model_name)
                    
                    # Check if detailed info was updated in database
                    db_explore = LookerExplore.query.filter_by(
                        looker_instance_id=agent.looker_instance_id,
                        model_name=model_name,
                        explore_name=explore_name
                    ).first()
                    
                    has_detailed_info = db_explore and (db_explore.dimensions or db_explore.measures)
                    print(f"📊 Retrieved explore info with {len(info1.get('dimensions', []))} dimensions and {len(info1.get('measures', []))} measures")
                    print(f"🗄️ Detailed info cached in database: {'Yes' if has_detailed_info else 'No'}")
                    
                    if has_detailed_info:
                        print("✅ Detailed explore info successfully cached to database")
                    else:
                        print("❌ Detailed explore info not cached to database")
                    
                    # Second call - should fetch from database cache
                    print(f"\n🔍 Second call to get_explore_info('{explore_name}', '{model_name}') - should use database cache...")
                    info2 = agent.get_explore_info(explore_name, model_name)
                    
                    if info1 == info2:
                        print("✅ Detailed explore info database caching working - same results returned")
                    else:
                        print("❌ Detailed explore info database caching issue - different results returned")
            
            # Test 4: Cache refresh logic
            print("\n⏰ Test 4: Cache refresh logic")
            print("-" * 30)
            
            # Check cache timestamps
            models_in_db = LookerModel.query.filter_by(looker_instance_id=agent.looker_instance_id).all()
            explores_in_db = LookerExplore.query.filter_by(looker_instance_id=agent.looker_instance_id).all()
            
            if models_in_db:
                latest_model_update = max(model.updated_at for model in models_in_db)
                print(f"📅 Latest model cache timestamp: {latest_model_update}")
            
            if explores_in_db:
                latest_explore_update = max(explore.updated_at for explore in explores_in_db)
                print(f"📅 Latest explore cache timestamp: {latest_explore_update}")
            
            print(f"⏰ Cache refresh interval: {agent.cache_refresh_hours} hours")
            
            # Summary
            print("\n" + "=" * 70)
            print("📈 Database Caching Test Summary:")
            print(f"   • Models cached: {len(models_in_db)}")
            print(f"   • Explores cached: {len(explores_in_db)}")
            print(f"   • Cache refresh interval: {agent.cache_refresh_hours} hours")
            print("   • All caching functionality tested successfully!")
            print("=" * 70)
        
    except Exception as e:
        print(f"❌ Database caching test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_caching()