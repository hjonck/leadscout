#!/usr/bin/env python3
"""Test LLM fallback with a subset of failed names to confirm improvement."""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_subset_validation():
    """Test LLM fallback with 20 failed names to confirm dramatic improvement."""
    
    from leadscout.classification.classifier import NameClassifier
    
    print("🚀 LLM Fallback Subset Validation Test")
    print("=" * 60)
    
    classifier = NameClassifier()
    
    # Enable LLM
    if classifier.enable_llm():
        print("✅ LLM enabled successfully")
    else:
        print("❌ LLM enable failed")
        return
    
    # 20 names that were failing in the 500-lead demo
    failed_names = [
        "DIEMBY LUBAMBO",
        "MOKGADI MATILDA MOTALE", 
        "SHUHUANG YAN",
        "VIMBAI NYIKA",
        "MARIE CHRISTINA CLAASSEN",
        "MLONDI MARQUES CIBANE",
        "CORNELIA MASELLO MADIBA",
        "MPHO OLGA MUNWANA",
        "MUVHULAWA NEMUKONDENI",
        "ROBERT SOLLY THWALA",
        "GERHARDT DAWIE VAN WYNGAARDT",
        "JOSEPH TOLO MSIZA",
        "RYAN JASON VAN DEVENTER",
        "REMEMBER LEPHEFO MOKGOPE",
        "SIBUSISO SIPHIWE SIBISI",
        "TECIOUS TLOU MOLOTO",
        "NANDIPHA NICHOLINA KEWUTI",
        "ANELISA MANYELA",
        "NSHIMBA TSHITENDE",
        "NOSIVIWE TAMARA NTANDULUKA"
    ]
    
    print(f"\n🧪 Testing {len(failed_names)} Previously Failed Names:")
    print("-" * 60)
    
    start_time = time.time()
    success_count = 0
    llm_count = 0
    rule_count = 0
    phonetic_count = 0
    
    for i, name in enumerate(failed_names, 1):
        try:
            result = await classifier.classify_name(name)
            
            if result:
                method = result.method.value if hasattr(result.method, 'value') else str(result.method)
                ethnicity = result.ethnicity.value if hasattr(result.ethnicity, 'value') else str(result.ethnicity)
                
                print(f"  {i:2d}. ✅ {name}")
                print(f"      └─ {ethnicity} (confidence: {result.confidence:.3f}) via {method}")
                
                # Count method usage
                if method == 'llm':
                    llm_count += 1
                elif method == 'rule_based':
                    rule_count += 1
                elif method == 'phonetic':
                    phonetic_count += 1
                    
                success_count += 1
            else:
                print(f"  {i:2d}. ❌ {name}: STILL FAILED")
                
        except Exception as e:
            print(f"  {i:2d}. ❌ {name}: ERROR: {str(e)[:50]}...")
    
    elapsed_time = time.time() - start_time
    success_rate = (success_count / len(failed_names)) * 100
    llm_usage_rate = (llm_count / success_count * 100) if success_count > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 SUBSET VALIDATION RESULTS:")
    print("=" * 60)
    print(f"  Success rate: {success_rate:.1f}% ({success_count}/{len(failed_names)})")
    print(f"  Processing time: {elapsed_time:.1f} seconds")
    print(f"  Average per name: {elapsed_time/len(failed_names):.2f} seconds")
    print(f"  \n  Method breakdown:")
    print(f"    Rule-based: {rule_count} ({rule_count/len(failed_names)*100:.1f}%)")
    print(f"    Phonetic: {phonetic_count} ({phonetic_count/len(failed_names)*100:.1f}%)")
    print(f"    LLM fallback: {llm_count} ({llm_count/len(failed_names)*100:.1f}%)")
    
    print(f"\n🎯 EXPECTED PRODUCTION IMPACT:")
    print(f"  Before fix: 36% success rate (180/500 leads)")
    print(f"  After fix: ~{success_rate:.0f}% success rate ({success_rate/100*500:.0f}/500 leads)")
    print(f"  Additional successful leads: +{(success_rate/100*500) - 180:.0f}")
    
    if success_rate >= 90:
        print(f"\n✅ SUCCESS: Target 90%+ success rate achieved!")
        print(f"✅ LLM fallback integration working correctly")
        print(f"✅ Ready for production deployment")
    else:
        print(f"\n⚠️  NEEDS WORK: Success rate below 90% target")
        print(f"❌ Additional investigation required")

if __name__ == "__main__":
    asyncio.run(test_subset_validation())