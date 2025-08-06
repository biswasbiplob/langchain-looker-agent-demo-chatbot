#!/usr/bin/env python3
"""
Script to list all explores for a given model using Looker SDK only
"""
import os
import sys
from dotenv import load_dotenv

def list_explores_for_model(model_name=None):
    """List all explores for a specific model using Looker API"""
    
    load_dotenv()
    
    # Use provided model or get from env
    model_name = model_name or os.getenv('LOOKML_MODEL_NAME', '')
    
    print(f"🔍 Listing explores for model: {model_name}")
    print("=" * 60)
    
    try:
        # Initialize Looker SDK
        import looker_sdk
        
        # Set environment variables for SDK
        base_url = os.getenv('LOOKER_BASE_URL', '')
        client_id = os.getenv('LOOKER_CLIENT_ID', '')
        client_secret = os.getenv('LOOKER_CLIENT_SECRET', '')
        
        if not all([base_url, client_id, client_secret]):
            print("❌ Missing required environment variables:")
            print("   - LOOKER_BASE_URL, LOOKER_CLIENT_ID, LOOKER_CLIENT_SECRET")
            return []
        
        os.environ['LOOKERSDK_BASE_URL'] = base_url
        os.environ['LOOKERSDK_CLIENT_ID'] = client_id
        os.environ['LOOKERSDK_CLIENT_SECRET'] = client_secret
        
        # Connect to Looker
        print("🔗 Connecting to Looker API...")
        sdk = looker_sdk.init40()
        print("🔍 Getting user info...")
        user = sdk.me()
        print(f"✅ Connected as: {user.display_name} ({user.email})")
        
        # Get model information
        try:
            print(f"🔍 Getting model info for: {model_name}")
            model_info = sdk.lookml_model(model_name)
            print(f"✅ Model '{model_name}' found")
            
            if model_info.explores:
                explores = [explore for explore in model_info.explores if explore.name]
                explore_names = [explore.name for explore in explores if explore.name]
                
                print(f"📊 Found {len(explore_names)} explores in '{model_name}':")
                print("-" * 40)
                
                for i, explore in enumerate(explores, 1):
                    explore_name = explore.name or 'unnamed'
                    description = explore.description or 'No description'
                    
                    print(f"{i:2d}. {explore_name}")
                    if description != 'No description':
                        print(f"    📝 {description[:80]}{'...' if len(description) > 80 else ''}")
                    print()
                
                return explore_names
            else:
                print(f"⚠️ Model '{model_name}' exists but no explores are accessible")
                print("💡 This could be due to:")
                print("   - No explores defined in the model")
                print("   - User permissions restricting access to explores")
                return []
                
        except Exception as model_error:
            print(f"❌ Model '{model_name}' not found or not accessible: {model_error}")
            print("💡 Available models might be:")
            
            # Try to list some available models
            try:
                models = sdk.all_lookml_models()
                available_models = [m.name for m in models if m.name][:10]
                if available_models:
                    print(f"   {', '.join(available_models)}")
                else:
                    print("   No models accessible to this user")
            except Exception:
                print("   Unable to list available models")
            
            return []
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return []

def list_all_models_and_explores():
    """List all available models and their explores"""
    
    load_dotenv()
    
    print("🌐 Discovering all available models and explores...")
    print("=" * 60)
    
    try:
        import looker_sdk
        
        # Set environment variables for SDK
        base_url = os.getenv('LOOKER_BASE_URL', '')
        client_id = os.getenv('LOOKER_CLIENT_ID', '')  
        client_secret = os.getenv('LOOKER_CLIENT_SECRET', '')
        
        os.environ['LOOKERSDK_BASE_URL'] = base_url
        os.environ['LOOKERSDK_CLIENT_ID'] = client_id
        os.environ['LOOKERSDK_CLIENT_SECRET'] = client_secret
        
        # Connect to Looker
        sdk = looker_sdk.init40()
        user = sdk.me()
        print(f"✅ Connected as: {user.display_name}")
        
        # Get all models
        try:
            models = sdk.all_lookml_models()
            accessible_models = [m for m in models if m.name]
            
            print(f"📋 Found {len(accessible_models)} accessible models:")
            print()
            
            models_with_explores = []
            
            for model in accessible_models:
                model_name = model.name or 'unnamed'
                print(f"📦 Model: {model_name}")
                
                if model.project_name:
                    print(f"   Project: {model.project_name}")
                
                # Get detailed model info to see explores
                try:
                    detailed_model = sdk.lookml_model(model_name)
                    if detailed_model.explores:
                        explores = [e for e in detailed_model.explores if e.name]
                        explore_count = len(explores)
                        
                        if explore_count > 0:
                            models_with_explores.append((model_name, explore_count))
                            print(f"   ✅ {explore_count} explores available")
                            
                            # Show first few explore names
                            explore_names = [e.name for e in explores[:5] if e.name]
                            if explore_names:
                                print(f"   📊 Explores: {', '.join(explore_names)}")
                                if explore_count > 5:
                                    print(f"       ... and {explore_count - 5} more")
                        else:
                            print("   ⚠️ No explores accessible")
                    else:
                        print("   ⚠️ No explores found")
                        
                except Exception as detail_error:
                    print(f"   ❌ Could not get details: {str(detail_error)[:50]}...")
                
                print()
            
            # Summary
            if models_with_explores:
                print("🎯 RECOMMENDED MODELS FOR CHATBOT:")
                print("-" * 40)
                # Sort by explore count (descending)
                models_with_explores.sort(key=lambda x: x[1], reverse=True)
                
                for model_name, explore_count in models_with_explores[:5]:
                    print(f"   • {model_name} ({explore_count} explores)")
                
                best_model = models_with_explores[0][0]
                print(f"\n💡 SUGGESTED: Update .env with LOOKML_MODEL_NAME={best_model}")
                
                return best_model
            else:
                print("🚨 No models with accessible explores found")
                return None
                
        except Exception as models_error:
            print(f"❌ Could not list models: {models_error}")
            return None
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def test_model_for_chatbot(model_name):
    """Test if a model would work well for the chatbot"""
    
    print(f"🧪 Testing model '{model_name}' for chatbot compatibility...")
    print("-" * 50)
    
    explores = list_explores_for_model(model_name)
    
    if not explores:
        print("❌ Model not suitable: No accessible explores")
        return False
    
    explore_count = len(explores)
    print(f"✅ Found {explore_count} explores")
    
    if explore_count < 3:
        print("⚠️ Limited explores - chatbot will have limited functionality")
    elif explore_count < 10:
        print("✅ Good number of explores - suitable for chatbot")
    else:
        print("🎉 Excellent! Many explores available - great for chatbot")
    
    return True

if __name__ == "__main__":
    load_dotenv()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            # List all models and explores
            best_model = list_all_models_and_explores()
            if best_model:
                print(f"\n🔍 Testing recommended model: {best_model}")
                test_model_for_chatbot(best_model)
        else:
            # Test specific model
            model_name = sys.argv[1]
            if test_model_for_chatbot(model_name):
                print(f"✅ Model '{model_name}' is ready for the chatbot!")
            else:
                print(f"❌ Model '{model_name}' won't work well for the chatbot")
    else:
        # Test current model in .env
        current_model = os.getenv('LOOKML_MODEL_NAME', '')
        if current_model:
            print(f"📋 Testing current model from .env: {current_model}")
            if not test_model_for_chatbot(current_model):
                print(f"\n🔄 Let's find a better model...")
                list_all_models_and_explores()
        else:
            print("📋 No model specified in .env, discovering available models...")
            list_all_models_and_explores()