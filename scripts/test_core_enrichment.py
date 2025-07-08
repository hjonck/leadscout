#!/usr/bin/env python3
"""
Direct test of core enrichment functionality.

Since the CLI enrich command is not fully implemented, this script tests
the core classification system directly with the test dataset.
"""

import asyncio
import pandas as pd
import time
from pathlib import Path
from typing import List, Dict, Any

from leadscout.classification.classifier import NameClassifier
from leadscout.classification.models import ClassificationMethod


async def test_core_enrichment():
    """Test core classification system with full dataset."""
    print("🚀 Testing Core Enrichment System")
    print("=" * 50)
    
    # Load test dataset
    test_file = Path("data/test_runs/comprehensive_validation_test.xlsx")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    df = pd.read_excel(test_file)
    print(f"📊 Loaded {len(df)} leads for testing")
    
    # Initialize classifier
    classifier = NameClassifier()
    
    # Track results
    results = []
    start_time = time.time()
    
    # Process each director name
    print("\n🔍 Processing director names...")
    for idx, row in df.iterrows():
        director_name = row['DirectorName']
        
        try:
            # Classify the name
            classification = await classifier.classify_name(director_name)
            
            result = {
                'lead_id': idx + 1,
                'director_name': director_name,
                'ethnicity': classification.ethnicity.value,
                'confidence': classification.confidence,
                'method': classification.method.value,
                'processing_time_ms': classification.processing_time_ms or 0.0
            }
            
            results.append(result)
            
            # Show progress for first 10 and every 10th
            if idx < 10 or (idx + 1) % 10 == 0:
                method_symbol = "⚡" if classification.method == ClassificationMethod.RULE_BASED else ("📞" if classification.method == ClassificationMethod.PHONETIC else "🤖")
                print(f"  {idx+1:2d}. {method_symbol} {director_name[:30]:<30} → {classification.ethnicity.value:<8} ({classification.method.value})")
            
        except Exception as e:
            print(f"  ❌ {idx+1:2d}. ERROR: {director_name} - {e}")
            results.append({
                'lead_id': idx + 1,
                'director_name': director_name,
                'error': str(e)
            })
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful = [r for r in results if 'ethnicity' in r]
    errors = [r for r in results if 'error' in r]
    
    rule_based = [r for r in successful if r['method'] == 'rule_based']
    phonetic = [r for r in successful if r['method'] == 'phonetic']
    llm = [r for r in successful if r['method'] == 'llm']
    
    print(f"\n📈 Processing Results:")
    print(f"  Total leads: {len(df)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Success rate: {len(successful)/len(df)*100:.1f}%")
    
    print(f"\n🎯 Method Breakdown:")
    print(f"  Rule-based: {len(rule_based)} ({len(rule_based)/len(successful)*100:.1f}%)")
    print(f"  Phonetic: {len(phonetic)} ({len(phonetic)/len(successful)*100:.1f}%)")
    print(f"  LLM: {len(llm)} ({len(llm)/len(successful)*100:.1f}%)")
    
    print(f"\n⏱️ Performance:")
    print(f"  Total time: {total_time:.2f} seconds")
    print(f"  Average per lead: {total_time/len(df)*1000:.1f} ms")
    print(f"  Processing rate: {len(df)/total_time:.1f} leads/second")
    
    # Enhancement 2 specific validation
    enhancement2_names = [
        'ANDREAS PETRUS VAN DER MERWE',
        'HEINRICH ADRIAN TIMMIE', 
        'NOMVUYISEKO EUNICE MSINDO',
        'ALLISTER PIETERSEN',
        'MNCEDI NICHOLAS MAJIBANE'
    ]
    
    enhancement2_results = [r for r in successful if r['director_name'] in enhancement2_names]
    enhancement2_rule_hits = [r for r in enhancement2_results if r['method'] == 'rule_based']
    
    print(f"\n🎯 Enhancement 2 Validation:")
    print(f"  Enhancement 2 cases: {len(enhancement2_results)}/5")
    print(f"  Rule-based hits: {len(enhancement2_rule_hits)}/{len(enhancement2_results)}")
    print(f"  Enhancement 2 success: {'✅ PASS' if len(enhancement2_rule_hits) == 5 else '❌ FAIL'}")
    
    # Save enriched results
    output_df = df.copy()
    
    # Add classification results to dataframe
    for result in results:
        idx = result['lead_id'] - 1
        if 'ethnicity' in result:
            output_df.loc[idx, 'ethnicity_classification'] = result['ethnicity']
            output_df.loc[idx, 'classification_confidence'] = result['confidence']
            output_df.loc[idx, 'classification_method'] = result['method']
            output_df.loc[idx, 'processing_time_ms'] = result['processing_time_ms']
        else:
            output_df.loc[idx, 'classification_error'] = result.get('error', 'Unknown error')
    
    # Save output
    output_path = Path("data/test_runs/core_enrichment_output.xlsx")
    output_df.to_excel(output_path, index=False)
    print(f"\n💾 Saved enriched results to: {output_path}")
    
    # Overall assessment
    success = (
        len(successful) >= 45 and  # At least 90% success rate
        len(enhancement2_rule_hits) == 5 and  # All Enhancement 2 cases work
        len(rule_based) >= len(successful) * 0.8  # At least 80% rule-based
    )
    
    print(f"\n🎯 Overall Assessment: {'✅ PASS' if success else '❌ NEEDS ATTENTION'}")
    
    return {
        'total_leads': len(df),
        'successful': len(successful),
        'errors': len(errors),
        'success_rate': len(successful)/len(df),
        'rule_based_rate': len(rule_based)/len(successful) if successful else 0,
        'enhancement2_success': len(enhancement2_rule_hits) == 5,
        'processing_time': total_time,
        'leads_per_second': len(df)/total_time,
        'overall_pass': success
    }


if __name__ == "__main__":
    asyncio.run(test_core_enrichment())