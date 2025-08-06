#!/usr/bin/env python3
"""
Direct test of Looker SDK connectivity and model discovery
"""
import os
import sys
from dotenv import load_dotenv

def test_direct_looker_query():
    """Test direct Looker SDK connectivity and model discovery"""
    
    load_dotenv()
    
    try:
        print("🔍 Testing direct Looker SDK connectivity...")
        
        # Test Looker SDK connection
        import looker_sdk
        
        # Configure Looker SDK
        os.environ['LOOKERSDK_BASE_URL'] = os.getenv('LOOKER_BASE_URL')
        os.environ['LOOKERSDK_CLIENT_ID'] = os.getenv('LOOKER_CLIENT_ID')
        os.environ['LOOKERSDK_CLIENT_SECRET'] = os.getenv('LOOKER_CLIENT_SECRET')
        
        # Initialize Looker SDK
        sdk = looker_sdk.init40()
        
        # Test connection
        user = sdk.me()
        print(f"✅ Connected to Looker as: {user.display_name} ({user.email})")
        
        # Test model discovery
        print(f"\n📦 Discovering available models...")
        models = sdk.all_lookml_models()
        
        if not models:
            print("❌ No models found - check permissions")
            return []
        
        print(f"📊 Found {len(models)} models:")
        all_explores = []
        
        for i, model in enumerate(models, 1):
            print(f"\n{i:2d}. Model: {model.name}")
            if model.project_name:
                print(f"    Project: {model.project_name}")
            
            # Get explores for this model
            try:
                model_detail = sdk.lookml_model(model.name)
                if model_detail.explores:
                    explores = [e.name for e in model_detail.explores if e.name]
                    print(f"    Explores ({len(explores)}): {', '.join(explores[:5])}")
                    if len(explores) > 5:
                        print(f"                      ... and {len(explores) - 5} more")
                    
                    # Track all explores with model prefix
                    for explore in explores:
                        all_explores.append(f"{model.name}.{explore}")
                else:
                    print(f"    Explores: None found")
                    
            except Exception as e:
                print(f"    Explores: Error retrieving ({str(e)[:50]}...)")
        
        print(f"\n✨ Total: {len(models)} models, {len(all_explores)} explores")
        print(f"\n💡 Dynamic model discovery working - no LOOKML_MODEL_NAME needed!")
        
        return all_explores
        
    except ImportError:
        print("❌ Looker SDK not installed. Install with: uv add looker-sdk")
        return []
    except Exception as e:
        print(f"❌ Direct Looker SDK test failed: {e}")
        
        # Common error suggestions
        if "401" in str(e) or "unauthorized" in str(e).lower():
            print("💡 Check your LOOKER_CLIENT_ID and LOOKER_CLIENT_SECRET")
        elif "404" in str(e) or "not found" in str(e).lower():
            print("💡 Check your LOOKER_BASE_URL format (should include https://)")
        elif "timeout" in str(e).lower():
            print("💡 Check your network connection and Looker instance availability")
        
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_direct_looker_query()