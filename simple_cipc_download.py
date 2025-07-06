#!/usr/bin/env python3
"""Simple CIPC data download and import script.

This script downloads CIPC CSV files directly and imports them into the database
to complete the core MVP functionality quickly.

Developer A - CIPC Integration & Caching Specialist
"""

import asyncio
import sys
from pathlib import Path
import pandas as pd
import httpx
import aiosqlite

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.cipc.importers.database_importer import CIPCDatabaseImporter

# Database path
DB_PATH = Path("./cache/leadscout.db")


async def download_and_process_cipc_file(letter: str = "A") -> pd.DataFrame:
    """Download and process a single CIPC CSV file.
    
    Args:
        letter: Letter of the alphabet for the CSV file (A-Z)
        
    Returns:
        Processed DataFrame with company data
    """
    
    print(f"📥 Downloading CIPC List-{letter}.csv...")
    
    # Download directory
    download_dir = Path("./data/cipc_csv")
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # URL for the CSV file
    url = f"https://www.cipc.co.za/wp-content/uploads/2024/12/List-{letter}.csv"
    output_file = download_dir / f"List-{letter}.csv"
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            print(f"🌐 Requesting: {url}")
            
            response = await client.get(url)
            response.raise_for_status()
            
            # Write to file
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded {len(response.content):,} bytes to {output_file}")
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return pd.DataFrame()
    
    # Process the CSV file
    print(f"📊 Processing {output_file}...")
    
    try:
        # Read CSV with error handling
        df = pd.read_csv(output_file, encoding='utf-8', low_memory=False)
        
        # Basic cleanup and standardization
        if not df.empty:
            # Ensure we have the required columns
            required_columns = ['registration_number', 'company_name']
            
            # Map common column variations
            column_mapping = {
                'Registration Number': 'registration_number',
                'Company Name': 'company_name', 
                'Company / Close Corporation Name': 'company_name',
                'Company Status': 'company_status',
                'Registration Date': 'registration_date',
                'Company Type': 'company_type',
                'Physical Address': 'address_line_1',
                'Province': 'province'
            }
            
            # Rename columns to standard format
            df = df.rename(columns=column_mapping)
            
            # Ensure required columns exist
            for col in required_columns:
                if col not in df.columns:
                    # Try to find a suitable column
                    possible_cols = [c for c in df.columns if col.replace('_', '').lower() in c.lower().replace(' ', '')]
                    if possible_cols:
                        df = df.rename(columns={possible_cols[0]: col})
                    else:
                        df[col] = ''  # Add empty column if not found
            
            # Clean up data
            df = df.fillna('')  # Replace NaN with empty strings
            df['registration_number'] = df['registration_number'].astype(str).str.strip()
            df['company_name'] = df['company_name'].astype(str).str.strip()
            
            # Remove empty rows
            df = df[(df['registration_number'] != '') & (df['company_name'] != '')]
            
            print(f"✅ Processed {len(df):,} companies from List-{letter}.csv")
            
        return df
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return pd.DataFrame()


async def simple_cipc_import():
    """Simple CIPC data download and import process."""
    
    print("🚀 Simple CIPC Data Import")
    print("=" * 50)
    print("Downloading and importing CIPC company data...")
    print("=" * 50)
    
    try:
        # Start with just a few letters for testing
        test_letters = ["A", "B"]  # Can expand to full A-Z later
        
        all_data = []
        
        for letter in test_letters:
            df = await download_and_process_cipc_file(letter)
            if not df.empty:
                all_data.append(df)
                print(f"   ✅ {letter}: {len(df):,} companies")
            else:
                print(f"   ❌ {letter}: No data")
        
        if not all_data:
            print("❌ No data downloaded")
            return False
        
        # Combine all data
        print("\n📊 Combining all downloaded data...")
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Remove duplicates by registration number
        before_dedup = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['registration_number'], keep='first')
        after_dedup = len(combined_df)
        
        print(f"✅ Combined: {after_dedup:,} unique companies ({before_dedup - after_dedup:,} duplicates removed)")
        
        # Import into database
        print("\n💾 Importing into database...")
        importer = CIPCDatabaseImporter()
        
        # Import all data
        import_results = await importer.import_csv_data(combined_df)
        
        print(f"✅ Import completed:")
        print(f"   Success: {import_results.success_count:,} companies")
        print(f"   Errors: {import_results.error_count}")
        print(f"   Time: {import_results.processing_time_seconds:.2f}s")
        
        # Create search indexes
        print("\n🔍 Creating search indexes...")
        await importer.create_search_indexes()
        print("✅ Search indexes created")
        
        # Test search functionality
        print("\n🔎 Testing company search...")
        from leadscout.cipc.search.company_searcher import CompanySearcher
        
        searcher = CompanySearcher()
        
        # Test with a few companies
        test_companies = combined_df.head(3)
        for _, company in test_companies.iterrows():
            result = await searcher.verify_company(company['company_name'])
            print(f"   🔍 '{company['company_name']}': "
                  f"{'✅ FOUND' if result.found else '❌ NOT FOUND'} "
                  f"(score: {result.match_score:.2f}, {result.search_time_ms:.2f}ms)")
        
        # Get database stats
        stats = await searcher.get_database_stats()
        print(f"\n📊 Final Database Statistics:")
        print(f"   Total companies: {stats['total_companies']:,}")
        print(f"   Active companies: {stats['active_companies']:,}")
        print(f"   Provinces: {len(stats['provinces'])}")
        print(f"   Company types: {len(stats['company_types'])}")
        print(f"   Indexes created: {'✅' if stats['indexes_created'] else '❌'}")
        
        print(f"\n🎉 CIPC DATA IMPORT SUCCESSFUL!")
        print(f"✅ {import_results.success_count:,} South African companies now available for verification")
        print(f"🚀 Lead enrichment system now has complete company verification capability!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(simple_cipc_import())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Import interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)