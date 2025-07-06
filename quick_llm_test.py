#!/usr/bin/env python3
"""
Quick LLM test with just 10 leads to verify functionality.
Output results to file immediately for inspection.
"""

import asyncio
import sys
import time
from pathlib import Path
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.classification.classifier import NameClassifier

async def quick_llm_test():
    """Test LLM with just 10 leads and save results immediately."""
    
    print("🧪 Quick LLM Test - 10 Leads")
    
    # Load data
    excel_path = "data/growfin/CIPC Data PostDMA 20250702.xlsx"
    df = pd.read_excel(excel_path)
    
    # Filter for logistics and take first 10
    logistics_keywords = ["LOGISTICS", "TRANSPORT", "SUPPLY"]
    logistics_filter = df['Keyword'].str.upper().str.contains('|'.join(logistics_keywords), na=False)
    logistics_df = df[logistics_filter]
    test_df = logistics_df.head(10).copy()
    
    print(f"Testing {len(test_df)} logistics leads")
    
    # Initialize classifier
    classifier = NameClassifier()
    
    if not classifier.enable_llm():
        print("❌ LLM enable failed")
        return
    
    print("✅ LLM enabled")
    
    # Process leads
    results = []
    for idx, row in test_df.iterrows():
        director_name = str(row.get('DirectorName', '')).strip()
        
        if not director_name or director_name.lower() in ['nan', 'none', '']:
            continue
            
        print(f"Processing: {director_name}")
        start_time = time.time()
        
        try:
            classification = await classifier.classify_name(director_name)
            processing_time = (time.time() - start_time) * 1000
            
            if classification:
                ethnicity = classification.ethnicity.value if hasattr(classification.ethnicity, 'value') else str(classification.ethnicity)
                method = classification.method.value if hasattr(classification.method, 'value') else str(classification.method)
                
                result = {
                    'EntityName': row.get('EntityName', ''),
                    'DirectorName': director_name,
                    'Ethnicity': ethnicity,
                    'Confidence': classification.confidence,
                    'Method': method,
                    'ProcessingTime_ms': processing_time,
                    'Status': 'success'
                }
                
                print(f"  ✅ {ethnicity} ({method}) - {processing_time:.0f}ms")
            else:
                result = {
                    'EntityName': row.get('EntityName', ''),
                    'DirectorName': director_name,
                    'Status': 'failed'
                }
                print(f"  ❌ Classification failed")
                
            results.append(result)
            
            # Save results after each one (in case of timeout)
            if results:
                results_df = pd.DataFrame(results)
                results_df.to_excel("data/growfin/quick_llm_test_results.xlsx", index=False)
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            break
    
    # Final summary
    if results:
        results_df = pd.DataFrame(results)
        results_df.to_excel("data/growfin/quick_llm_test_results.xlsx", index=False)
        
        successful = len([r for r in results if r.get('Status') == 'success'])
        print(f"\n📊 Results: {successful}/{len(results)} successful")
        print(f"💾 Saved to: data/growfin/quick_llm_test_results.xlsx")
        
        # Show method distribution
        methods = {}
        for r in results:
            if r.get('Method'):
                methods[r['Method']] = methods.get(r['Method'], 0) + 1
        
        print("🔧 Methods used:")
        for method, count in methods.items():
            print(f"  {method}: {count}")

if __name__ == "__main__":
    asyncio.run(quick_llm_test())