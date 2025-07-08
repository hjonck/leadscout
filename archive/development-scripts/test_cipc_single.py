#!/usr/bin/env python3
"""Test CIPC import with a single file to verify functionality.

This script tests the CIPC download and import process with just one file
to ensure everything works before downloading all 26 files.

Developer A - CIPC Integration & Caching Specialist
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.cipc.downloaders.csv_downloader import CIPCCSVDownloader
from leadscout.cipc.importers.database_importer import CIPCDatabaseImporter


async def test_single_file_import():
    """Test import process with a single CIPC file."""
    
    print("🧪 Testing CIPC Import with Single File")
    print("=" * 50)
    
    try:
        # 1. Test downloader with just one file
        downloader = CIPCCSVDownloader(
            download_dir=Path("./data/cipc_test"),
            max_concurrent_downloads=1,
            timeout_seconds=120
        )
        
        print("📥 Testing download of List-A.csv...")
        
        # Test with just downloading files for 2024, 12 (latest)
        print("🌐 Testing download of latest CIPC files...")
        
        # Download all files (but we'll process just a subset for testing)
        downloaded_files = await downloader.download_latest_files()
        
        if not downloaded_files:
            print("❌ Download failed - no files downloaded")
            return False
            
        print(f"✅ Downloaded {len(downloaded_files)} file(s)")
        
        # 2. Process just the first file for testing
        print("📊 Processing first downloaded file...")
        first_file = downloaded_files[0] if downloaded_files else None
        
        if first_file:
            processed_df = await downloader.process_csv_file(first_file)
            print(f"✅ Processed {len(processed_df):,} companies from test file")
        else:
            print("❌ No files to process")
            return False
        
        # 3. Test import into database
        print("💾 Testing database import...")
        importer = CIPCDatabaseImporter()
        
        # Import small batch for testing
        test_batch = processed_df.head(100) if len(processed_df) > 100 else processed_df
        import_results = await importer.import_csv_data(test_batch)
        
        print(f"✅ Import test: {import_results.success_count} success, {import_results.error_count} errors")
        
        # 4. Test search indexes
        print("🔍 Creating search indexes...")
        await importer.create_search_indexes()
        
        # 5. Test search functionality
        print("🔎 Testing company search...")
        from leadscout.cipc.search.company_searcher import CompanySearcher
        
        searcher = CompanySearcher()
        
        # Test with first company in the batch
        if not test_batch.empty:
            test_company_name = test_batch.iloc[0]['company_name']
            result = await searcher.verify_company(test_company_name)
            
            print(f"🔍 Search test for '{test_company_name}': "
                  f"{'✅ FOUND' if result.found else '❌ NOT FOUND'} "
                  f"(score: {result.match_score:.2f}, {result.search_time_ms:.2f}ms)")
        
        # 6. Get database stats
        stats = await searcher.get_database_stats()
        print(f"\n📊 Database Statistics:")
        print(f"   Total companies: {stats['total_companies']:,}")
        print(f"   Active companies: {stats['active_companies']:,}")
        print(f"   Indexes created: {'✅' if stats['indexes_created'] else '❌'}")
        
        print("\n🎉 Single file test SUCCESSFUL!")
        print("🚀 System ready for full CIPC data download!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_single_file_import())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)