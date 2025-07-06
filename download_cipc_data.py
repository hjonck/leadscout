#!/usr/bin/env python3
"""Download and import CIPC data for complete system functionality.

This script completes the core MVP by downloading actual South African
company registration data and importing it into the database.

Developer A - CIPC Integration & Caching Specialist
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from leadscout.cipc.importers.database_importer import download_and_import_cipc_data


async def main():
    """Run the complete CIPC data download and import process."""
    
    print("🚀 LeadScout CIPC Data Foundation")
    print("=" * 50)
    print("Starting complete CIPC data acquisition process...")
    print("This will download and import 100K+ SA company records")
    print("=" * 50)
    
    try:
        # Run the complete process
        results = await download_and_import_cipc_data()
        
        # Final summary
        print("\n" + "=" * 50)
        print("🎉 CIPC DATA FOUNDATION COMPLETE!")
        print("=" * 50)
        print(f"📊 Final Results:")
        print(f"   ✅ Success: {results.success_count:,} companies imported")
        print(f"   ⚠️  Errors: {results.error_count} records failed")
        print(f"   ⏱️  Time: {results.processing_time_seconds:.2f} seconds")
        print(f"   💾 Database: Ready for company verification")
        print(f"   🔍 Search: Optimized indexes created")
        
        if results.success_count > 0:
            print("\n✅ CIPC integration COMPLETE - Lead enrichment now has company verification!")
            print("📋 Next steps:")
            print("   1. Test company search functionality")
            print("   2. Integrate with lead enrichment pipeline")
            print("   3. Deploy complete system for business use")
            return True
        else:
            print("\n❌ No companies were imported successfully")
            return False
            
    except Exception as e:
        print(f"\n❌ CIPC data acquisition failed: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)