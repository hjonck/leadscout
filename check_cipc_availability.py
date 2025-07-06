#!/usr/bin/env python3
"""Check CIPC file availability across different months.

This script checks what CIPC CSV files are actually available
to find the correct URLs for downloading.

Developer A - CIPC Integration & Caching Specialist
"""

import asyncio
import httpx
from datetime import datetime, timedelta


async def check_file_availability():
    """Check CIPC file availability across different time periods."""
    
    print("🔍 Checking CIPC File Availability")
    print("=" * 50)
    
    # Test different months
    test_periods = [
        (2024, 12),  # December 2024
        (2024, 11),  # November 2024  
        (2024, 10),  # October 2024
        (2024, 9),   # September 2024
        (2024, 8),   # August 2024
        (2024, 7),   # July 2024
    ]
    
    test_letters = ["A", "B", "C"]  # Test first few letters
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for year, month in test_periods:
            print(f"\n📅 Testing {year}-{month:02d}:")
            
            available_files = []
            
            for letter in test_letters:
                url = f"https://www.cipc.co.za/wp-content/uploads/{year}/{month:02d}/List-{letter}.csv"
                
                try:
                    response = await client.head(url)  # Use HEAD to check without downloading
                    if response.status_code == 200:
                        content_length = response.headers.get('content-length', 'unknown')
                        print(f"   ✅ List-{letter}.csv: Available ({content_length} bytes)")
                        available_files.append(letter)
                    else:
                        print(f"   ❌ List-{letter}.csv: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ List-{letter}.csv: Error ({e})")
            
            if available_files:
                print(f"   🎯 Found {len(available_files)} files for {year}-{month:02d}: {', '.join(available_files)}")
                
                # Test downloading one file to verify it works
                test_letter = available_files[0]
                test_url = f"https://www.cipc.co.za/wp-content/uploads/{year}/{month:02d}/List-{test_letter}.csv"
                
                try:
                    print(f"   🧪 Testing download of List-{test_letter}.csv...")
                    response = await client.get(test_url)
                    response.raise_for_status()
                    
                    content_size = len(response.content)
                    print(f"   ✅ Successfully downloaded {content_size:,} bytes")
                    
                    # Try to parse as CSV
                    content_text = response.content.decode('utf-8', errors='ignore')
                    lines = content_text.split('\n')
                    
                    if len(lines) > 1:
                        header = lines[0]
                        sample_row = lines[1] if len(lines) > 1 else ""
                        
                        print(f"   📊 CSV Header: {header[:100]}...")
                        print(f"   📊 Sample Row: {sample_row[:100]}...")
                        print(f"   📊 Total Lines: {len(lines):,}")
                        
                        # This looks good - return the working period
                        return year, month
                    
                except Exception as e:
                    print(f"   ❌ Download test failed: {e}")
            else:
                print(f"   ❌ No files available for {year}-{month:02d}")
    
    print("\n❌ No CIPC files found in any tested period")
    return None, None


async def main():
    """Main function to check availability and report findings."""
    
    year, month = await check_file_availability()
    
    if year and month:
        print(f"\n🎉 SUCCESS!")
        print(f"✅ Found working CIPC files for {year}-{month:02d}")
        print(f"🚀 Use this period for downloading CIPC data")
        
        # Generate all URLs for this period
        print(f"\n📋 Complete URL list for {year}-{month:02d}:")
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            url = f"https://www.cipc.co.za/wp-content/uploads/{year}/{month:02d}/List-{letter}.csv"
            print(f"   {letter}: {url}")
            
    else:
        print(f"\n❌ FAILURE!")
        print(f"No CIPC files found - may need to check the CIPC website manually")


if __name__ == "__main__":
    asyncio.run(main())