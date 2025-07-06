#!/usr/bin/env python3
"""
Test LLM fallback with 50 logistics leads to verify functionality and performance.

This is a smaller test to validate the LLM integration before running the full 500 leads.
"""

import asyncio
import os
import sys
from pathlib import Path
import time
from datetime import datetime
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.classification.classifier import NameClassifier

async def test_50_leads():
    """Test 50 logistics leads with LLM fallback."""
    
    print("🧪 Testing 50 Logistics Leads with LLM Fallback")
    print("=" * 60)
    
    # Load data
    excel_path = "data/growfin/CIPC Data PostDMA 20250702.xlsx"
    print(f"📁 Loading data from: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
        print(f"✅ Loaded {len(df):,} total leads")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    # Filter for logistics
    logistics_keywords = ["LOGISTICS", "TRANSPORT", "SUPPLY"]
    logistics_filter = df['Keyword'].str.upper().str.contains('|'.join(logistics_keywords), na=False)
    logistics_df = df[logistics_filter]
    
    print(f"🎯 Found {len(logistics_df):,} logistics leads")
    
    # Take first 50 for testing
    test_df = logistics_df.head(50).copy()
    print(f"📊 Testing with {len(test_df)} leads")
    
    # Initialize classifier
    classifier = NameClassifier()
    
    # Enable LLM
    if classifier.enable_llm():
        print("✅ LLM enabled successfully")
    else:
        print("❌ LLM enable failed")
        return
    
    # Process leads
    print("\n🔧 Processing leads...")
    start_time = time.time()
    results = []
    stats = {
        'total': 0,
        'successful': 0,
        'failed': 0,
        'no_director': 0,
        'methods': {},
        'processing_times': []
    }
    
    for idx, row in test_df.iterrows():
        stats['total'] += 1
        
        try:
            # Extract director name
            director_name = str(row.get('DirectorName', '')).strip()
            
            if not director_name or director_name.lower() in ['nan', 'none', '']:
                stats['no_director'] += 1
                results.append({
                    'EntityName': row.get('EntityName', ''),
                    'DirectorName': 'NO_DIRECTOR_NAME',
                    'Status': 'no_director_name'
                })
                continue
            
            # Classify the director name
            classification = await classifier.classify_name(director_name)
            
            if classification:
                stats['successful'] += 1
                
                ethnicity = classification.ethnicity.value if hasattr(classification.ethnicity, 'value') else str(classification.ethnicity)
                method = classification.method.value if hasattr(classification.method, 'value') else str(classification.method)
                
                # Update statistics
                stats['methods'][method] = stats['methods'].get(method, 0) + 1
                if classification.processing_time_ms:
                    stats['processing_times'].append(classification.processing_time_ms)
                
                results.append({
                    'EntityName': row.get('EntityName', ''),
                    'DirectorName': director_name,
                    'Ethnicity': ethnicity,
                    'Confidence': classification.confidence,
                    'Method': method,
                    'ProcessingTime_ms': classification.processing_time_ms or 0.0,
                    'Status': 'success'
                })
                
                print(f"  {stats['total']:2d}. ✅ {director_name[:30]:<30} → {ethnicity:<10} ({method})")
                
            else:
                stats['failed'] += 1
                results.append({
                    'EntityName': row.get('EntityName', ''),
                    'DirectorName': director_name,
                    'Status': 'classification_failed'
                })
                print(f"  {stats['total']:2d}. ❌ {director_name[:30]:<30} → FAILED")
                
        except Exception as e:
            stats['failed'] += 1
            print(f"  {stats['total']:2d}. ❌ {row.get('DirectorName', 'Unknown')[:30]:<30} → ERROR: {e}")
    
    total_time = time.time() - start_time
    
    # Results summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    # Performance metrics
    print(f"⏱️  Processing Time: {total_time:.1f} seconds")
    print(f"📈 Processing Rate: {(stats['total']/total_time):.1f} leads/second")
    
    if stats['processing_times']:
        avg_time = sum(stats['processing_times']) / len(stats['processing_times'])
        print(f"🔧 Avg Classification Time: {avg_time:.1f}ms")
    
    # Success metrics
    success_rate = (stats['successful'] / stats['total']) * 100
    print(f"\n✅ SUCCESS METRICS:")
    print(f"   Success Rate: {success_rate:.1f}% ({stats['successful']}/{stats['total']})")
    print(f"   Failed: {stats['failed']}")
    print(f"   No Director: {stats['no_director']}")
    
    # Method distribution
    if stats['methods']:
        print(f"\n🔧 METHOD DISTRIBUTION:")
        for method, count in stats['methods'].items():
            percentage = (count / stats['successful']) * 100
            print(f"   {method.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    
    # Save results
    if results:
        output_path = "data/growfin/test_50_leads_results.xlsx"
        results_df = pd.DataFrame(results)
        results_df.to_excel(output_path, index=False)
        print(f"\n💾 Results saved to: {output_path}")
    
    return success_rate, stats

if __name__ == "__main__":
    asyncio.run(test_50_leads())