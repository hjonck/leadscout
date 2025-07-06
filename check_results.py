#!/usr/bin/env python3
"""Read and display the test results."""

import pandas as pd

try:
    df = pd.read_excel("data/growfin/quick_llm_test_results.xlsx")
    print("📊 Quick LLM Test Results:")
    print("=" * 60)
    
    for idx, row in df.iterrows():
        print(f"{idx+1:2d}. {row['DirectorName']}")
        print(f"    → {row['Ethnicity']} (confidence: {row.get('Confidence', 'N/A')})")
        print(f"    → Method: {row['Method']}")
        print(f"    → Time: {row.get('ProcessingTime_ms', 0):.0f}ms")
        print()
    
    # Summary
    total = len(df)
    successful = len(df[df['Status'] == 'success'])
    
    methods = df['Method'].value_counts()
    
    print("📈 SUMMARY:")
    print(f"Success Rate: {successful}/{total} ({(successful/total)*100:.1f}%)")
    print("\nMethod Distribution:")
    for method, count in methods.items():
        percentage = (count/total)*100
        print(f"  {method}: {count} ({percentage:.1f}%)")
    
    # Performance
    if 'ProcessingTime_ms' in df.columns:
        avg_time = df['ProcessingTime_ms'].mean()
        print(f"\nAverage Processing Time: {avg_time:.0f}ms")
    
    # Save as CSV for easier reading
    df.to_csv("data/growfin/quick_llm_test_results.csv", index=False)
    print("\n💾 Also saved as CSV: data/growfin/quick_llm_test_results.csv")
    
except Exception as e:
    print(f"Error reading results: {e}")