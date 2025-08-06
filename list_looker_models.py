#!/usr/bin/env python3
"""
Script to list available LookML models in a Looker instance
"""
import os
import sys
from dotenv import load_dotenv

def list_looker_models():
    """List all available LookML models from Looker instance"""
    
    # Load environment variables
    load_dotenv()
    
    looker_base_url = os.getenv('LOOKER_BASE_URL')
    looker_client_id = os.getenv('LOOKER_CLIENT_ID')
    looker_client_secret = os.getenv('LOOKER_CLIENT_SECRET')
    
    if not all([looker_base_url, looker_client_id, looker_client_secret]):
        print("❌ Missing Looker credentials in .env file")
        print("Required: LOOKER_BASE_URL, LOOKER_CLIENT_ID, LOOKER_CLIENT_SECRET")
        return []
    
    print(f"🔗 Connecting to Looker at: {looker_base_url}")
    
    try:
        import looker_sdk
        
        # Configure Looker SDK
        os.environ['LOOKERSDK_BASE_URL'] = looker_base_url
        os.environ['LOOKERSDK_CLIENT_ID'] = looker_client_id
        os.environ['LOOKERSDK_CLIENT_SECRET'] = looker_client_secret
        
        # Initialize Looker SDK
        sdk = looker_sdk.init40()
        
        # Get current user to test connection
        user = sdk.me()
        print(f"✅ Connected as: {user.display_name} ({user.email})")
        
        # Get all LookML models
        print("\n📋 Available LookML Models:")
        print("-" * 50)
        
        models = sdk.all_lookml_models()
        
        if not models:
            print("No models found. You might not have access to any models.")
            return []
        
        model_names = []
        for model in models:
            print(f"📦 Model: {model.name}")
            if model.project_name:
                print(f"   Project: {model.project_name}")
            if model.allowed_db_connection_names:
                print(f"   Connections: {', '.join(model.allowed_db_connection_names)}")
            
            # Get explores for this model
            try:
                explores = sdk.lookml_model(model.name).explores
                if explores:
                    explore_names = [explore.name for explore in explores if explore.name]
                    if explore_names:
                        print(f"   Explores: {', '.join(explore_names[:5])}" + 
                              (f" (and {len(explore_names)-5} more)" if len(explore_names) > 5 else ""))
            except Exception as e:
                print(f"   Explores: Unable to fetch ({str(e)[:50]}...)")
            
            print()
            model_names.append(model.name)
        
        print(f"\n✨ Found {len(model_names)} models total")
        print(f"📝 Model names for .env: {', '.join(model_names)}")
        
        # Suggest first model for .env file
        if model_names:
            print(f"\n💡 Suggested LOOKML_MODEL_NAME for .env file: {model_names[0]}")
        
        return model_names
        
    except ImportError:
        print("❌ Looker SDK not installed. Install with: uv add looker-sdk")
        print("   Alternative: pip install looker-sdk")
        return []
    except Exception as e:
        print(f"❌ Error connecting to Looker: {str(e)}")
        
        # Common error suggestions
        if "401" in str(e) or "unauthorized" in str(e).lower():
            print("💡 Check your LOOKER_CLIENT_ID and LOOKER_CLIENT_SECRET")
        elif "404" in str(e) or "not found" in str(e).lower():
            print("💡 Check your LOOKER_BASE_URL format (should include https://)")
        elif "timeout" in str(e).lower():
            print("💡 Check your network connection and Looker instance availability")
        
        return []

if __name__ == "__main__":
    models = list_looker_models()
    
    if models:
        print(f"\n🚀 You can now update your .env file with any of these model names:")
        for i, model in enumerate(models, 1):
            print(f"   {i}. LOOKML_MODEL_NAME={model}")
    else:
        print("\n🔍 Try the web interface method:")
        print("   1. Log into your Looker instance")
        print("   2. Go to 'Develop' menu")
        print("   3. Browse your projects to see available models")