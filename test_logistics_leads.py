#!/usr/bin/env python3
"""Test script for processing 100 logistics leads from the provided data.

This script:
1. Loads the Excel file with lead data
2. Filters for logistics/transport/supply keywords
3. Processes 100 leads through the classification system
4. Outputs results to enhanced Excel file

Usage:
    python test_logistics_leads.py
"""

import asyncio
import os
import sys
from pathlib import Path

import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.classification.classifier import NameClassifier
from leadscout.models.lead import Lead


async def test_logistics_leads():
    """Test lead enrichment with 100 logistics leads."""
    
    print("🚀 LeadScout Logistics Test Run")
    print("=" * 50)
    
    # 1. Load the Excel file
    excel_path = "data/growfin/CIPC Data PostDMA 20250702.xlsx"
    print(f"📁 Loading leads from: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
        print(f"✅ Loaded {len(df):,} total leads")
    except Exception as e:
        print(f"❌ Error loading Excel file: {e}")
        return
    
    # 2. Filter for logistics/transport/supply
    logistics_keywords = ["LOGISTICS", "TRANSPORT", "SUPPLY"]
    logistics_filter = df['Keyword'].str.upper().str.contains('|'.join(logistics_keywords), na=False)
    logistics_df = df[logistics_filter]
    
    print(f"📊 Found {len(logistics_df):,} logistics/transport/supply leads")
    
    # 3. Take first 100 for testing
    test_df = logistics_df.head(100).copy()
    print(f"🎯 Testing with {len(test_df)} leads")
    
    # 4. Initialize classifier
    print("\n🔧 Initializing classification system...")
    classifier = NameClassifier()
    
    # Check if LLM is available
    try:
        # Try to enable LLM for fallback
        if os.getenv('OPENAI_API_KEY') or os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY'):
            classifier.enable_llm()
            print("✅ LLM fallback enabled")
        else:
            print("⚠️  No API keys found - will use rule-based and phonetic only")
    except Exception as e:
        print(f"⚠️  LLM not available: {e}")
    
    # 5. Process leads
    print("\n📊 Processing leads...")
    results = []
    successful_classifications = 0
    failed_classifications = 0
    
    for idx, row in test_df.iterrows():
        try:
            # Extract director name
            director_name = str(row.get('DirectorName', '')).strip()
            
            if not director_name or director_name.lower() in ['nan', 'none', '']:
                results.append({
                    'EntityName': row.get('EntityName', ''),
                    'DirectorName': 'NO_DIRECTOR_NAME',
                    'Keyword': row.get('Keyword', ''),
                    'Province': row.get('RegisteredAddressProvince', ''),
                    'Ethnicity': 'unknown',
                    'Confidence': 0.0,
                    'Method': 'no_name',
                    'ProcessingTime_ms': 0.0,
                    'Status': 'no_director_name'
                })
                continue
            
            # Classify the director name
            print(f"  Processing: {director_name}", end="")
            
            classification = await classifier.classify_name(director_name)
            
            if classification:
                print(f" → {classification.ethnicity} ({classification.confidence:.3f})")
                successful_classifications += 1
                
                results.append({
                    'EntityName': row.get('EntityName', ''),
                    'DirectorName': director_name,
                    'Keyword': row.get('Keyword', ''),
                    'Province': row.get('RegisteredAddressProvince', ''),
                    'Ethnicity': classification.ethnicity.value if hasattr(classification.ethnicity, 'value') else classification.ethnicity,
                    'Confidence': classification.confidence,
                    'Method': classification.method.value if hasattr(classification.method, 'value') else classification.method,
                    'ProcessingTime_ms': classification.processing_time_ms or 0.0,
                    'Status': 'success'
                })
            else:
                print(" → FAILED")
                failed_classifications += 1
                
                results.append({
                    'EntityName': row.get('EntityName', ''),
                    'DirectorName': director_name,
                    'Keyword': row.get('Keyword', ''),
                    'Province': row.get('RegisteredAddressProvince', ''),
                    'Ethnicity': 'unknown',
                    'Confidence': 0.0,
                    'Method': 'failed',
                    'ProcessingTime_ms': 0.0,
                    'Status': 'classification_failed'
                })
                
        except Exception as e:
            print(f" → ERROR: {e}")
            failed_classifications += 1
            
            results.append({
                'EntityName': row.get('EntityName', ''),
                'DirectorName': row.get('DirectorName', ''),
                'Keyword': row.get('Keyword', ''),
                'Province': row.get('RegisteredAddressProvince', ''),
                'Ethnicity': 'error',
                'Confidence': 0.0,
                'Method': 'error',
                'ProcessingTime_ms': 0.0,
                'Status': f'error: {str(e)[:100]}'
            })
    
    # 6. Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # 7. Generate output file
    output_path = "data/growfin/logistics_test_results.xlsx"
    print(f"\n💾 Saving results to: {output_path}")
    
    try:
        results_df.to_excel(output_path, index=False)
        print("✅ Results saved successfully")
    except Exception as e:
        print(f"❌ Error saving results: {e}")
    
    # 8. Show summary
    print("\n📈 RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total leads processed: {len(results)}")
    print(f"Successful classifications: {successful_classifications}")
    print(f"Failed classifications: {failed_classifications}")
    print(f"Success rate: {(successful_classifications/len(results)*100):.1f}%")
    
    # Show ethnicity distribution
    if successful_classifications > 0:
        print("\n🎯 Ethnicity Distribution:")
        ethnicity_counts = results_df[results_df['Status'] == 'success']['Ethnicity'].value_counts()
        for ethnicity, count in ethnicity_counts.items():
            percentage = (count / successful_classifications) * 100
            print(f"  {ethnicity}: {count} ({percentage:.1f}%)")
    
    # Show method distribution
    method_counts = results_df['Method'].value_counts()
    print("\n⚙️ Classification Methods Used:")
    for method, count in method_counts.items():
        percentage = (count / len(results)) * 100
        print(f"  {method}: {count} ({percentage:.1f}%)")
    
    # Show performance stats
    successful_results = results_df[results_df['Status'] == 'success']
    if len(successful_results) > 0:
        avg_time = successful_results['ProcessingTime_ms'].mean()
        avg_confidence = successful_results['Confidence'].mean()
        print(f"\n⚡ Performance:")
        print(f"  Average processing time: {avg_time:.2f}ms")
        print(f"  Average confidence: {avg_confidence:.3f}")
    
    print(f"\n🎉 Test complete! Results saved to {output_path}")
    
    return results_df


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_logistics_leads())