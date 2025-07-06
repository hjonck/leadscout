#!/usr/bin/env python3
"""
Diagnose LLM fallback integration issue.

This script isolates the LLM integration problem causing 64% classification failures.
Run this first to identify the exact issue before implementing fixes.

Usage:
    python diagnose_llm_fallback.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_environment():
    """Test environment variable loading."""
    print("🔧 Environment Variables:")
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    print(f"  OpenAI: {'✅ SET' if openai_key else '❌ MISSING'}")
    print(f"  Anthropic: {'✅ SET' if anthropic_key else '❌ MISSING'}")
    
    if openai_key:
        print(f"  OpenAI key length: {len(openai_key)} chars")
        print(f"  OpenAI key starts with: {openai_key[:10]}...")
    
    if anthropic_key:
        print(f"  Anthropic key length: {len(anthropic_key)} chars")
        print(f"  Anthropic key starts with: {anthropic_key[:10]}...")
    
    return bool(openai_key or anthropic_key)

def test_dotenv_loading():
    """Test .env file loading explicitly."""
    print("\n🔧 Testing .env File Loading:")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print(f"  ✅ .env file exists at: {env_file.absolute()}")
        
        # Read and parse .env manually
        with open(env_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if 'API_KEY' in key:
                    print(f"  📄 Found in .env: {key} = {value[:10]}...")
    else:
        print(f"  ❌ .env file not found at: {env_file.absolute()}")
    
    # Try loading with python-dotenv
    try:
        from dotenv import load_dotenv
        result = load_dotenv()
        print(f"  🔧 load_dotenv() result: {result}")
        
        # Check if environment changed after load_dotenv
        openai_after = os.getenv('OPENAI_API_KEY')
        anthropic_after = os.getenv('ANTHROPIC_API_KEY')
        
        print(f"  📊 After load_dotenv:")
        print(f"    OpenAI: {'✅ SET' if openai_after else '❌ MISSING'}")
        print(f"    Anthropic: {'✅ SET' if anthropic_after else '❌ MISSING'}")
        
    except ImportError:
        print("  ❌ python-dotenv not installed")
    except Exception as e:
        print(f"  ❌ Error loading .env: {e}")

def test_config_loading():
    """Test LeadScout config loading."""
    print("\n🔧 LeadScout Config:")
    try:
        from leadscout.core.config import get_settings
        settings = get_settings()
        
        # Check settings attributes
        openai_configured = bool(getattr(settings, 'openai_api_key', None))
        anthropic_configured = bool(getattr(settings, 'claude_api_key', None) or getattr(settings, 'anthropic_api_key', None))
        
        print(f"  OpenAI in config: {'✅ SET' if openai_configured else '❌ MISSING'}")
        print(f"  Anthropic in config: {'✅ SET' if anthropic_configured else '❌ MISSING'}")
        
        # Check settings attributes
        print(f"  Settings object type: {type(settings)}")
        print(f"  Available attributes: {[attr for attr in dir(settings) if not attr.startswith('_')]}")
        
        return openai_configured or anthropic_configured
        
    except Exception as e:
        print(f"❌ Config loading error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_classifier():
    """Test LLM classifier initialization."""
    print("\n🔧 LLM Classifier:")
    try:
        from leadscout.classification.llm import LLMClassifier
        
        print("✅ LLMClassifier imported successfully")
        
        # Test initialization with API keys from config (proper way)
        from leadscout.core.config import get_settings
        settings = get_settings()
        claude_key = settings.get_anthropic_key()
        openai_key = settings.get_openai_key()
        
        if claude_key or openai_key:
            llm = LLMClassifier(
                claude_api_key=claude_key,
                openai_api_key=openai_key
            )
            print(f"✅ LLMClassifier created: {type(llm)}")
            
            # Check if it has expected methods
            methods = [method for method in dir(llm) if not method.startswith('_')]
            print(f"  Available methods: {methods}")
        else:
            print("❌ No API keys available for LLM classifier")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Classifier error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_classifier():
    """Test main classifier LLM integration."""
    print("\n🔧 Main Classifier:")
    try:
        from leadscout.classification.classifier import NameClassifier
        
        print("✅ NameClassifier imported successfully")
        classifier = NameClassifier()
        print("✅ NameClassifier created")
        
        # Check enable_llm method
        enable_llm_attr = getattr(classifier, 'enable_llm', None)
        print(f"  enable_llm exists: {'✅' if enable_llm_attr else '❌'}")
        print(f"  enable_llm type: {type(enable_llm_attr)}")
        
        # Check if it's a property vs method
        if hasattr(classifier.__class__, 'enable_llm'):
            class_attr = getattr(classifier.__class__, 'enable_llm')
            is_property = isinstance(class_attr, property)
            print(f"  enable_llm is property: {is_property}")
        
        # Try to call enable_llm
        try:
            if callable(enable_llm_attr):
                result = classifier.enable_llm()
                print(f"✅ enable_llm() called successfully: {result}")
            else:
                print(f"❌ enable_llm is not callable (it's a {type(enable_llm_attr)})")
                # If it's a property, try accessing it
                if hasattr(classifier.__class__, 'enable_llm') and isinstance(getattr(classifier.__class__, 'enable_llm'), property):
                    result = classifier.enable_llm
                    print(f"  enable_llm property value: {result}")
        except Exception as e:
            print(f"❌ enable_llm() failed: {e}")
            import traceback
            traceback.print_exc()
            
        return True
        
    except Exception as e:
        print(f"❌ Main Classifier error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_clients():
    """Test direct API client initialization."""
    print("\n🔧 API Client Testing:")
    
    # Test OpenAI client
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            print("✅ OpenAI client created successfully")
            
            # Test a simple API call (optional - costs money)
            # models = client.models.list()
            # print(f"✅ OpenAI API connection verified")
            
        except Exception as e:
            print(f"❌ OpenAI client error: {e}")
    else:
        print("⏭️ OpenAI key not available - skipping client test")
    
    # Test Anthropic client
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            print("✅ Anthropic client created successfully")
            
        except Exception as e:
            print(f"❌ Anthropic client error: {e}")
    else:
        print("⏭️ Anthropic key not available - skipping client test")

if __name__ == "__main__":
    print("🚀 LLM Fallback Diagnostic")
    print("=" * 50)
    
    env_ok = test_environment()
    test_dotenv_loading()
    config_ok = test_config_loading()
    llm_ok = test_llm_classifier()
    main_ok = test_main_classifier()
    test_api_clients()
    
    print("\n📊 Diagnostic Summary:")
    print(f"  Environment: {'✅' if env_ok else '❌'}")
    print(f"  Config: {'✅' if config_ok else '❌'}")
    print(f"  LLM Module: {'✅' if llm_ok else '❌'}")
    print(f"  Main Classifier: {'✅' if main_ok else '❌'}")
    
    print("\n🔧 Next Steps:")
    if not env_ok:
        print("  1. Fix environment variable loading")
    if not config_ok:
        print("  2. Fix config system to load API keys")
    if not main_ok:
        print("  3. Fix enable_llm method (likely property vs method issue)")
    
    print("\n📋 Run this diagnostic first, then apply fixes based on results.")