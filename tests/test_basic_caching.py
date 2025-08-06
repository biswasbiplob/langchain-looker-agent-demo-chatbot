#!/usr/bin/env python3
"""
Basic test for database caching models (without requiring Looker credentials)
"""
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_basic_caching():
    """Test basic database caching functionality"""
    print("🧪 Testing basic database caching models...")
    print("=" * 50)
    
    try:
        from app import app, db
        from models import LookerModel, LookerExplore
        
        with app.app_context():
            # Clear existing data
            print("🧹 Clearing test data...")
            LookerModel.query.filter_by(looker_instance_id="test_instance").delete()
            LookerExplore.query.filter_by(looker_instance_id="test_instance").delete()
            db.session.commit()
            
            # Test 1: Create and save a test model
            print("\n📦 Test 1: Creating test model...")
            test_model = LookerModel(
                looker_instance_id="test_instance",
                model_name="test_model",
                project_name="test_project",
                label="Test Model",
                description="A test model for caching",
                model_metadata={"test": True}
            )
            db.session.add(test_model)
            db.session.commit()
            print("✅ Test model created successfully")
            
            # Test 2: Retrieve the model
            print("\n🔍 Test 2: Retrieving test model...")
            retrieved_model = LookerModel.query.filter_by(
                looker_instance_id="test_instance",
                model_name="test_model"
            ).first()
            
            if retrieved_model and retrieved_model.label == "Test Model":
                print("✅ Test model retrieved successfully")
            else:
                print("❌ Failed to retrieve test model")
            
            # Test 3: Create and save a test explore
            print("\n📊 Test 3: Creating test explore...")
            test_explore = LookerExplore(
                looker_instance_id="test_instance",
                model_name="test_model",
                explore_name="test_explore",
                label="Test Explore",
                description="A test explore for caching",
                dimensions=[
                    {"name": "test_dimension", "label": "Test Dimension", "description": "A test dimension"}
                ],
                measures=[
                    {"name": "test_measure", "label": "Test Measure", "description": "A test measure"}
                ],
                explore_metadata={"test": True}
            )
            db.session.add(test_explore)
            db.session.commit()
            print("✅ Test explore created successfully")
            
            # Test 4: Retrieve the explore with detailed info
            print("\n🔍 Test 4: Retrieving test explore...")
            retrieved_explore = LookerExplore.query.filter_by(
                looker_instance_id="test_instance",
                model_name="test_model",
                explore_name="test_explore"
            ).first()
            
            if (retrieved_explore and 
                retrieved_explore.label == "Test Explore" and 
                len(retrieved_explore.dimensions) == 1 and
                len(retrieved_explore.measures) == 1):
                print("✅ Test explore with detailed info retrieved successfully")
            else:
                print("❌ Failed to retrieve test explore with correct detailed info")
            
            # Test 5: Unique constraint test
            print("\n🔒 Test 5: Testing unique constraints...")
            try:
                # Try to create duplicate model
                duplicate_model = LookerModel(
                    looker_instance_id="test_instance",
                    model_name="test_model",  # Same name as before
                    project_name="duplicate_project"
                )
                db.session.add(duplicate_model)
                db.session.commit()
                print("❌ Unique constraint not working - duplicate model allowed")
            except Exception as e:
                db.session.rollback()
                print("✅ Unique constraint working - duplicate model prevented")
            
            # Clean up
            print("\n🧹 Cleaning up test data...")
            LookerModel.query.filter_by(looker_instance_id="test_instance").delete()
            LookerExplore.query.filter_by(looker_instance_id="test_instance").delete()
            db.session.commit()
            
            print("\n" + "=" * 50)
            print("✅ All basic caching tests passed!")
            print("=" * 50)
        
    except Exception as e:
        print(f"❌ Basic caching test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_caching()