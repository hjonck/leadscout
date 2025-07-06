"""CIPC database import system using proven async patterns.

Completes the CIPC integration by importing processed CSV data
into the database with excellent error handling and performance patterns.

Developer A - CIPC Integration & Caching Specialist
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiosqlite
import pandas as pd
from pydantic import BaseModel, Field

from leadscout.models.cipc import CIPCCompany


logger = logging.getLogger(__name__)


# Database path
DB_PATH = Path("./cache/leadscout.db")


class ImportResults(BaseModel):
    """Results from CIPC data import operation."""
    
    success_count: int = Field(0, description="Number of successfully imported records")
    error_count: int = Field(0, description="Number of records that failed import")
    duplicate_count: int = Field(0, description="Number of duplicate records skipped")
    total_processed: int = Field(0, description="Total records processed")
    processing_time_seconds: float = Field(0.0, description="Total processing time")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ValidationResults(BaseModel):
    """Results from data integrity validation."""
    
    total_records: int = Field(0, description="Total records in database")
    valid_records: int = Field(0, description="Records passing validation")
    invalid_records: int = Field(0, description="Records failing validation")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    index_status: Dict[str, bool] = Field(default_factory=dict, description="Index creation status")


class CIPCDatabaseImporter:
    """Import CIPC data using proven database and async patterns.
    
    This class handles the import of processed CIPC CSV data into the database
    with batch optimization, comprehensive error handling, and performance monitoring.
    """
    
    def __init__(self, batch_size: int = 1000) -> None:
        """Initialize the database importer.
        
        Args:
            batch_size: Number of records to process per batch
        """
        self.batch_size = batch_size
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def import_csv_data(
        self, 
        processed_df: pd.DataFrame,
        batch_size: Optional[int] = None
    ) -> ImportResults:
        """Import processed CIPC data with batch optimization.
        
        Uses proven async patterns and error handling:
        - Batch processing for memory efficiency
        - Comprehensive error handling and logging
        - Progress tracking and monitoring
        - Database transaction management
        
        Args:
            processed_df: Processed CIPC data to import
            batch_size: Override default batch size
            
        Returns:
            Import results with statistics and error information
        """
        start_time = asyncio.get_event_loop().time()
        batch_size = batch_size or self.batch_size
        
        self.logger.info(f"Starting CIPC data import for {len(processed_df):,} records")
        
        results = ImportResults(total_processed=len(processed_df))
        
        try:
            # Ensure cache directory exists
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiosqlite.connect(DB_PATH) as db:
                # Create companies table if not exists
                await self._ensure_companies_table_exists(db)
                
                # Process data in batches
                for batch_start in range(0, len(processed_df), batch_size):
                    batch_end = min(batch_start + batch_size, len(processed_df))
                    batch_df = processed_df.iloc[batch_start:batch_end]
                    
                    batch_results = await self._import_batch(db, batch_df, batch_start)
                    
                    # Update overall results
                    results.success_count += batch_results.success_count
                    results.error_count += batch_results.error_count
                    results.duplicate_count += batch_results.duplicate_count
                    results.errors.extend(batch_results.errors)
                    
                    # Progress logging
                    progress = (batch_end / len(processed_df)) * 100
                    self.logger.info(
                        f"Import progress: {batch_end:,}/{len(processed_df):,} "
                        f"({progress:.1f}%) - "
                        f"Success: {results.success_count:,}, "
                        f"Errors: {results.error_count}"
                    )
                
                # Commit final transaction
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"CIPC import failed: {e}", exc_info=True)
            results.errors.append(f"Import failed: {str(e)}")
            
        finally:
            results.processing_time_seconds = asyncio.get_event_loop().time() - start_time
            
        self.logger.info(
            f"CIPC import completed: {results.success_count:,} success, "
            f"{results.error_count} errors, {results.duplicate_count} duplicates "
            f"in {results.processing_time_seconds:.2f}s"
        )
        
        return results
    
    async def _ensure_companies_table_exists(self, db) -> None:
        """Ensure the companies table exists with proper schema."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS cipc_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_number TEXT UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            company_status TEXT,
            registration_date TEXT,
            business_start_date TEXT,
            company_type TEXT,
            company_sub_type TEXT,
            address_line_1 TEXT,
            address_line_2 TEXT,
            postal_code TEXT,
            province TEXT,
            main_business_activity TEXT,
            sic_code TEXT,
            filing_status TEXT,
            annual_return_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        await db.execute(create_table_sql)
        self.logger.debug("CIPC companies table ensured")
    
    async def _import_batch(
        self, 
        db, 
        batch_df: pd.DataFrame, 
        batch_start: int
    ) -> ImportResults:
        """Import a batch of records with error handling.
        
        Args:
            db: Database connection
            batch_df: Batch data to import
            batch_start: Starting index for progress tracking
            
        Returns:
            Import results for this batch
        """
        batch_results = ImportResults()
        
        for idx, row in batch_df.iterrows():
            try:
                # Convert pandas row to CIPCCompany model
                company = self._row_to_company(row)
                
                # Insert or update company record
                await self._upsert_company(db, company)
                batch_results.success_count += 1
                
            except ValueError as e:
                # Data validation error
                error_msg = f"Row {batch_start + idx}: Data validation error: {e}"
                batch_results.errors.append(error_msg)
                batch_results.error_count += 1
                self.logger.warning(error_msg)
                
            except Exception as e:
                # Unexpected error
                error_msg = f"Row {batch_start + idx}: Unexpected error: {e}"
                batch_results.errors.append(error_msg)
                batch_results.error_count += 1
                self.logger.error(error_msg, exc_info=True)
        
        return batch_results
    
    def _row_to_company(self, row: pd.Series) -> CIPCCompany:
        """Convert pandas row to CIPCCompany model with validation.
        
        Args:
            row: Pandas row from processed DataFrame
            
        Returns:
            Validated CIPCCompany instance
            
        Raises:
            ValueError: If data validation fails
        """
        try:
            # Create company from row data
            company_data = {
                'registration_number': str(row.get('registration_number', '')).strip(),
                'company_name': str(row.get('company_name', '')).strip(),
                'company_status': str(row.get('company_status', '')).strip() or None,
                'registration_date': str(row.get('registration_date', '')).strip() or None,
                'business_start_date': str(row.get('business_start_date', '')).strip() or None,
                'company_type': str(row.get('company_type', '')).strip() or None,
                'company_sub_type': str(row.get('company_sub_type', '')).strip() or None,
                'address_line_1': str(row.get('address_line_1', '')).strip() or None,
                'address_line_2': str(row.get('address_line_2', '')).strip() or None,
                'postal_code': str(row.get('postal_code', '')).strip() or None,
                'province': str(row.get('province', '')).strip() or None,
                'main_business_activity': str(row.get('main_business_activity', '')).strip() or None,
                'sic_code': str(row.get('sic_code', '')).strip() or None,
                'filing_status': str(row.get('filing_status', '')).strip() or None,
                'annual_return_date': str(row.get('annual_return_date', '')).strip() or None,
            }
            
            # Validate required fields
            if not company_data['registration_number']:
                raise ValueError("Registration number is required")
            if not company_data['company_name']:
                raise ValueError("Company name is required")
            
            return CIPCCompany(**company_data)
            
        except Exception as e:
            raise ValueError(f"Failed to convert row to company: {e}")
    
    async def _upsert_company(self, db, company: CIPCCompany) -> None:
        """Insert or update company record in database.
        
        Args:
            db: Database connection
            company: Company data to upsert
        """
        upsert_sql = """
        INSERT INTO cipc_companies (
            registration_number, company_name, company_status, 
            registration_date, business_start_date, company_type, company_sub_type,
            address_line_1, address_line_2, postal_code, province,
            main_business_activity, sic_code, filing_status, annual_return_date,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(registration_number) DO UPDATE SET
            company_name = excluded.company_name,
            company_status = excluded.company_status,
            registration_date = excluded.registration_date,
            business_start_date = excluded.business_start_date,
            company_type = excluded.company_type,
            company_sub_type = excluded.company_sub_type,
            address_line_1 = excluded.address_line_1,
            address_line_2 = excluded.address_line_2,
            postal_code = excluded.postal_code,
            province = excluded.province,
            main_business_activity = excluded.main_business_activity,
            sic_code = excluded.sic_code,
            filing_status = excluded.filing_status,
            annual_return_date = excluded.annual_return_date,
            updated_at = CURRENT_TIMESTAMP
        """
        
        await db.execute(upsert_sql, (
            company.registration_number,
            company.company_name,
            company.company_status,
            company.registration_date,
            company.business_start_date,
            company.company_type,
            company.company_sub_type,
            company.address_line_1,
            company.address_line_2,
            company.postal_code,
            company.province,
            company.main_business_activity,
            company.sic_code,
            company.filing_status,
            company.annual_return_date,
        ))
    
    async def create_search_indexes(self) -> None:
        """Create optimized indexes for company search.
        
        Indexes needed for fast search:
        - Company name (full-text search capability)
        - Registration number (exact match)
        - Province (geographic filtering)
        - Company status (active/inactive filtering)
        """
        self.logger.info("Creating search indexes for CIPC companies")
        
        indexes = [
            # Primary search indexes
            "CREATE INDEX IF NOT EXISTS idx_company_name ON cipc_companies(company_name)",
            "CREATE INDEX IF NOT EXISTS idx_registration_number ON cipc_companies(registration_number)",
            "CREATE INDEX IF NOT EXISTS idx_province ON cipc_companies(province)",
            "CREATE INDEX IF NOT EXISTS idx_company_status ON cipc_companies(company_status)",
            
            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_name_province ON cipc_companies(company_name, province)",
            "CREATE INDEX IF NOT EXISTS idx_status_province ON cipc_companies(company_status, province)",
            
            # Full-text search support
            "CREATE INDEX IF NOT EXISTS idx_company_name_fts ON cipc_companies(company_name COLLATE NOCASE)",
        ]
        
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                for index_sql in indexes:
                    await db.execute(index_sql)
                await db.commit()
                
            self.logger.info(f"Successfully created {len(indexes)} search indexes")
            
        except Exception as e:
            self.logger.error(f"Failed to create search indexes: {e}", exc_info=True)
            raise
    
    async def validate_import_integrity(self) -> ValidationResults:
        """Validate imported data integrity using validation patterns.
        
        Returns:
            Validation results with statistics and error information
        """
        self.logger.info("Starting CIPC data integrity validation")
        
        results = ValidationResults()
        
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row  # Enable dict-like access
                # Count total records
                total_result = await db.execute("SELECT COUNT(*) FROM cipc_companies")
                results.total_records = (await total_result.fetchone())[0]
                
                # Validate required fields
                valid_result = await db.execute("""
                    SELECT COUNT(*) FROM cipc_companies 
                    WHERE registration_number IS NOT NULL 
                    AND registration_number != ''
                    AND company_name IS NOT NULL 
                    AND company_name != ''
                """)
                results.valid_records = (await valid_result.fetchone())[0]
                
                results.invalid_records = results.total_records - results.valid_records
                
                # Check for duplicate registration numbers
                duplicate_result = await db.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT registration_number 
                        FROM cipc_companies 
                        GROUP BY registration_number 
                        HAVING COUNT(*) > 1
                    )
                """)
                duplicate_count = (await duplicate_result.fetchone())[0]
                
                if duplicate_count > 0:
                    results.validation_errors.append(
                        f"Found {duplicate_count} duplicate registration numbers"
                    )
                
                # Validate index creation
                indexes_result = await db.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name LIKE 'idx_%'
                """)
                indexes = await indexes_result.fetchall()
                
                expected_indexes = [
                    'idx_company_name', 'idx_registration_number', 'idx_province',
                    'idx_company_status', 'idx_name_province', 'idx_status_province',
                    'idx_company_name_fts'
                ]
                
                for index_name in expected_indexes:
                    results.index_status[index_name] = any(
                        idx[0] == index_name for idx in indexes
                    )
                
        except Exception as e:
            self.logger.error(f"Validation failed: {e}", exc_info=True)
            results.validation_errors.append(f"Validation error: {str(e)}")
        
        self.logger.info(
            f"Validation completed: {results.valid_records:,}/{results.total_records:,} "
            f"valid records ({len(results.validation_errors)} errors)"
        )
        
        return results


async def download_and_import_cipc_data() -> ImportResults:
    """Download and import complete CIPC dataset.
    
    This function orchestrates the complete CIPC data acquisition process:
    1. Download all 26 CSV files using proven downloader
    2. Process files into standardized format
    3. Import into database with comprehensive error handling
    4. Create search indexes for optimal performance
    
    Returns:
        Import results with comprehensive statistics
    """
    from leadscout.cipc.downloaders.csv_downloader import CIPCCSVDownloader
    
    logger.info("🚀 Starting complete CIPC data acquisition process")
    start_time = asyncio.get_event_loop().time()
    
    try:
        # 1. Download all 26 CSV files using proven downloader
        downloader = CIPCCSVDownloader(
            download_dir=Path("./data/cipc_csv"),
            max_concurrent_downloads=3,  # Conservative for CIPC servers
            timeout_seconds=300
        )
        
        print("🚀 Starting CIPC CSV download (26 files: Lists A-Z)...")
        downloaded_files = await downloader.download_latest_files()
        
        print(f"✅ Downloaded {len(downloaded_files)} files successfully")
        
        # 2. Process all downloaded files using existing processor
        print("📊 Processing CSV files into standardized format...")
        combined_df = await downloader.process_all_files(downloaded_files)
        
        print(f"✅ Processed {len(combined_df):,} unique companies")
        
        # 3. Import into database
        print("💾 Importing into database...")
        importer = CIPCDatabaseImporter()
        import_results = await importer.import_csv_data(combined_df)
        
        print(f"✅ Imported {import_results.success_count:,} companies")
        print(f"⚠️  {import_results.error_count} import errors")
        
        # 4. Create search indexes for performance
        print("🔍 Creating search indexes...")
        await importer.create_search_indexes()
        
        # 5. Validate data integrity
        print("✅ Validating data integrity...")
        validation_results = await importer.validate_import_integrity()
        
        print(f"✅ Validation: {validation_results.valid_records:,}/{validation_results.total_records:,} valid records")
        
        total_time = asyncio.get_event_loop().time() - start_time
        print(f"🎉 CIPC data foundation complete in {total_time:.2f}s!")
        
        return import_results
        
    except Exception as e:
        logger.error(f"CIPC data acquisition failed: {e}", exc_info=True)
        print(f"❌ CIPC data acquisition failed: {e}")
        raise


if __name__ == "__main__":
    # Run the complete CIPC data acquisition process
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    results = asyncio.run(download_and_import_cipc_data())
    print(f"\n📊 Final Results:")
    print(f"   Success: {results.success_count:,} companies")
    print(f"   Errors: {results.error_count}")
    print(f"   Processing time: {results.processing_time_seconds:.2f}s")