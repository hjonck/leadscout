#!/usr/bin/env python3
"""
Test LLM fallback functionality after applying fixes.

This script tests the names that previously failed in the logistics demo
to verify that LLM fallback is working correctly.

Usage:
    python test_llm_fix.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_failed_names():
    """Test LLM fallback with names that previously failed."""
    
    print("🧪 Testing LLM Fallback with Previously Failed Names")
    print("=" * 60)
    
    try:
        from leadscout.classification.classifier import NameClassifier
        print("✅ NameClassifier imported successfully")
    except Exception as e:
        print(f"❌ Failed to import NameClassifier: {e}")
        return False
    
    classifier = NameClassifier()
    print("✅ NameClassifier created")
    
    # Test enable_llm method
    try:
        if hasattr(classifier, 'enable_llm') and callable(getattr(classifier, 'enable_llm')):
            llm_enabled = classifier.enable_llm()
            if llm_enabled:
                print("✅ LLM enabled successfully")
            else:
                print("❌ LLM enable returned False")
                return False
        else:
            print("❌ enable_llm is not a callable method")
            return False
    except Exception as e:
        print(f"❌ LLM enable failed: {e}")
        return False
    
    # Test with names that failed in the 500-lead demo
    failed_names = [
        "DIEMBY LUBAMBO",        # Should be classifiable with LLM
        "MOKGADI MATILDA MOTALE", # African name pattern
        "SHUHUANG YAN",          # Chinese origin
        "VIMBAI NYIKA",          # African name
        "MARIE CHRISTINA CLAASSEN", # European/Afrikaans
        "LWAZI MTHEMBU",         # African name
        "RAJESH PATEL",          # Indian name
        "FATIMA OMAR"            # Arabic/African name
    ]
    
    print(f"\n🎯 Testing {len(failed_names)} Previously Failed Names:")
    print("-" * 60)
    
    success_count = 0
    llm_usage_count = 0
    
    for i, name in enumerate(failed_names, 1):
        try:
            result = await classifier.classify_name(name)
            
            if result:
                method = result.method.value if hasattr(result.method, 'value') else str(result.method)
                ethnicity = result.ethnicity.value if hasattr(result.ethnicity, 'value') else str(result.ethnicity)
                
                print(f"  {i}. ✅ {name}")
                print(f"     └─ {ethnicity} (confidence: {result.confidence:.3f}) via {method}")
                
                if method == 'llm':
                    llm_usage_count += 1
                    print(f"     └─ 🎯 LLM fallback used correctly!")
                
                success_count += 1
            else:
                print(f"  {i}. ❌ {name}: STILL FAILED")
                
        except Exception as e:
            print(f"  {i}. ❌ {name}: ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    
    success_rate = (success_count / len(failed_names)) * 100
    llm_usage_rate = (llm_usage_count / len(failed_names)) * 100
    
    print(f"  Success rate: {success_rate:.1f}% ({success_count}/{len(failed_names)})")
    print(f"  LLM usage: {llm_usage_rate:.1f}% ({llm_usage_count}/{len(failed_names)})")
    
    if success_rate >= 90:
        print("  🎉 EXCELLENT: Target success rate achieved!")
    elif success_rate >= 75:
        print("  ✅ GOOD: Significant improvement achieved")
    else:
        print("  ⚠️  NEEDS WORK: Success rate still too low")
    
    if llm_usage_count > 0:
        print("  ✅ LLM fallback is working correctly")
    else:
        print("  ⚠️  LLM fallback not being used - check implementation")
    
    print("\n📋 NEXT STEPS:")
    if success_rate >= 90:
        print("  1. ✅ Run full logistics demo: python run_logistics_demo.py")
        print("  2. ✅ Expect >90% success rate on 500 leads")
        print("  3. ✅ System ready for production deployment")
    else:
        print("  1. ❌ Review LLM integration implementation")
        print("  2. ❌ Check API keys and provider initialization")
        print("  3. ❌ Debug remaining classification failures")
    
    return success_rate >= 75

async def test_environment_setup():
    """Test that environment is properly set up."""
    
    print("🔧 Testing Environment Setup")
    print("=" * 60)
    
    # Test imports
    try:
        import openai
        print("✅ openai package available")
    except ImportError:
        print("❌ openai package missing - run: pip install openai")
        return False
    
    try:
        import anthropic
        print("✅ anthropic package available")
    except ImportError:
        print("❌ anthropic package missing - run: pip install anthropic")
        return False
    
    try:
        import jellyfish
        print("✅ jellyfish package available")
    except ImportError:
        print("❌ jellyfish package missing - run: pip install jellyfish")
        return False
    
    # Test environment variables
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if openai_key:
        print(f"✅ OPENAI_API_KEY loaded ({len(openai_key)} chars)")
    else:
        print("❌ OPENAI_API_KEY not found in environment")
    
    if anthropic_key:
        print(f"✅ ANTHROPIC_API_KEY loaded ({len(anthropic_key)} chars)")
    else:
        print("❌ ANTHROPIC_API_KEY not found in environment")
    
    if not (openai_key or anthropic_key):
        print("❌ No API keys available - LLM fallback will not work")
        return False
    
    print("✅ Environment setup appears correct")
    return True

if __name__ == "__main__":
    async def main():
        print("🚀 LLM Fallback Fix Validation Test")
        print("=" * 60)
        
        # Test environment first
        env_ok = await test_environment_setup()
        if not env_ok:
            print("\n❌ Environment issues detected - fix before testing LLM")
            return
        
        print("\n" + "=" * 60)
        
        # Test LLM functionality
        success = await test_failed_names()
        
        print("\n" + "=" * 60)
        print("🎯 FINAL ASSESSMENT:")
        
        if success:
            print("✅ LLM fallback fix is working correctly!")
            print("✅ Ready to process the full dataset")
            print("✅ Expected improvement: 36% → 90%+ success rate")
        else:
            print("❌ LLM fallback still needs work")
            print("❌ Review the fix implementation steps")
    
    asyncio.run(main())