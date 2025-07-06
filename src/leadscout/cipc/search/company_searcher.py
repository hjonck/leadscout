"""Company search using imported CIPC data.

Provides the missing piece to complete lead enrichment:
company verification against SA company registry.

Developer A - CIPC Integration & Caching Specialist
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from difflib import SequenceMatcher

import aiosqlite
from pydantic import BaseModel, Field

from leadscout.models.cipc import CIPCCompany


logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path("./cache/leadscout.db")


class CompanyVerificationResult(BaseModel):
    """Result from company verification against CIPC registry."""
    
    search_name: str = Field(..., description="Original company name searched")
    found: bool = Field(False, description="Whether company was found")
    company: Optional[CIPCCompany] = Field(None, description="Found company data")
    match_score: float = Field(0.0, ge=0, le=1, description="Match confidence score")
    match_method: str = Field("none", description="How the match was found")
    search_time_ms: float = Field(0.0, description="Search time in milliseconds")
    alternatives: List[CIPCCompany] = Field(default_factory=list, description="Alternative matches")


class CompanySearcher:
    """Search imported CIPC data for company verification.
    
    This class provides fast, intelligent search capabilities for verifying
    company existence and details against the CIPC registry data.
    """
    
    def __init__(self) -> None:
        """Initialize the company searcher."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def verify_company(
        self,
        company_name: str,
        province: Optional[str] = None
    ) -> CompanyVerificationResult:
        """Verify company exists in CIPC registry.
        
        Target Performance:
        - <100ms search response time
        - Fuzzy matching for name variations
        - Province filtering for accuracy
        - Confidence scoring for match quality
        
        Args:
            company_name: Company name to search for
            province: Optional province filter for accuracy
            
        Returns:
            Verification result with match details
        """
        start_time = asyncio.get_event_loop().time()
        
        self.logger.debug(f"Verifying company: '{company_name}' in province: '{province}'")
        
        result = CompanyVerificationResult(
            search_name=company_name,
            match_method="none"
        )
        
        try:
            # Clean and normalize search term
            clean_name = self._normalize_company_name(company_name)
            
            if not clean_name:
                result.search_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                return result
            
            # Try exact match first (fastest)
            company = await self._exact_match_search(clean_name, province)
            if company:
                result.found = True
                result.company = company
                result.match_score = 1.0
                result.match_method = "exact"
            else:
                # Try fuzzy matching
                fuzzy_result = await self._fuzzy_match_search(clean_name, province)
                if fuzzy_result:
                    result.found = True
                    result.company = fuzzy_result["company"]
                    result.match_score = fuzzy_result["score"]
                    result.match_method = "fuzzy"
                    result.alternatives = fuzzy_result.get("alternatives", [])
            
        except Exception as e:
            self.logger.error(f"Company verification failed for '{company_name}': {e}", exc_info=True)
        
        finally:
            result.search_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            
        self.logger.debug(
            f"Company verification completed: {result.found} "
            f"(score: {result.match_score:.2f}, {result.search_time_ms:.2f}ms)"
        )
        
        return result
    
    async def get_company_details(
        self,
        registration_number: str
    ) -> Optional[CIPCCompany]:
        """Get complete company details by registration number.
        
        Args:
            registration_number: CIPC registration number
            
        Returns:
            Company details if found, None otherwise
        """
        self.logger.debug(f"Getting company details for registration: {registration_number}")
        
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row  # Enable dict-like access
                result = await db.execute(
                    """
                    SELECT * FROM cipc_companies 
                    WHERE registration_number = ?
                    """,
                    (registration_number,)
                )
                
                row = await result.fetchone()
                if row:
                    # Convert row to CIPCCompany
                    company_data = dict(row)
                    return CIPCCompany(**company_data)
                
        except Exception as e:
            self.logger.error(f"Failed to get company details for {registration_number}: {e}")
        
        return None
    
    async def search_companies_by_name(
        self,
        company_name: str,
        limit: int = 10,
        province: Optional[str] = None
    ) -> List[CIPCCompany]:
        """Search for companies by name with fuzzy matching.
        
        Args:
            company_name: Company name to search for
            limit: Maximum number of results
            province: Optional province filter
            
        Returns:
            List of matching companies
        """
        self.logger.debug(f"Searching companies by name: '{company_name}' (limit: {limit})")
        
        clean_name = self._normalize_company_name(company_name)
        if not clean_name:
            return []
        
        companies = []
        
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row  # Enable dict-like access
                # Build query with optional province filter
                query = """
                    SELECT * FROM cipc_companies 
                    WHERE company_name LIKE ? COLLATE NOCASE
                """
                params = [f"%{clean_name}%"]
                
                if province:
                    query += " AND province = ? COLLATE NOCASE"
                    params.append(province)
                
                query += " ORDER BY company_name LIMIT ?"
                params.append(limit)
                
                result = await db.execute(query, params)
                rows = await result.fetchall()
                
                for row in rows:
                    try:
                        company_data = dict(row)
                        companies.append(CIPCCompany(**company_data))
                    except Exception as e:
                        self.logger.warning(f"Failed to parse company row: {e}")
                        continue
                
        except Exception as e:
            self.logger.error(f"Company search failed: {e}", exc_info=True)
        
        self.logger.debug(f"Found {len(companies)} matching companies")
        return companies
    
    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for consistent searching.
        
        Args:
            name: Raw company name
            
        Returns:
            Normalized name suitable for search
        """
        if not name:
            return ""
        
        # Basic normalization
        normalized = name.strip().upper()
        
        # Remove common company suffixes for better matching
        suffixes = [
            " (PTY) LTD", " PTY LTD", " (PTY)LTD", " PTYLTD",
            " PROPRIETARY LIMITED", " PROP LTD", " LTD",
            " CC", " CLOSE CORPORATION", " INC", " INCORPORATED",
            " NPC", " NON PROFIT COMPANY", " RF", " REGISTERED FUND"
        ]
        
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
                break
        
        return normalized
    
    async def _exact_match_search(
        self,
        clean_name: str,
        province: Optional[str] = None
    ) -> Optional[CIPCCompany]:
        """Perform exact match search.
        
        Args:
            clean_name: Normalized company name
            province: Optional province filter
            
        Returns:
            Exact matching company if found
        """
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row  # Enable dict-like access
                # Try exact match on normalized name
                query = """
                    SELECT * FROM cipc_companies 
                    WHERE UPPER(company_name) = ? COLLATE NOCASE
                """
                params = [clean_name]
                
                if province:
                    query += " AND UPPER(province) = ? COLLATE NOCASE"
                    params.append(province.upper())
                
                query += " LIMIT 1"
                
                result = await db.execute(query, params)
                row = await result.fetchone()
                
                if row:
                    company_data = dict(row)
                    return CIPCCompany(**company_data)
                
        except Exception as e:
            self.logger.error(f"Exact match search failed: {e}")
        
        return None
    
    async def _fuzzy_match_search(
        self,
        clean_name: str,
        province: Optional[str] = None,
        min_score: float = 0.6
    ) -> Optional[dict]:
        """Perform fuzzy match search with scoring.
        
        Args:
            clean_name: Normalized company name
            province: Optional province filter
            min_score: Minimum similarity score for matches
            
        Returns:
            Best fuzzy match with score and alternatives
        """
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row  # Enable dict-like access
                # Get potential matches using LIKE
                query = """
                    SELECT * FROM cipc_companies 
                    WHERE company_name LIKE ? COLLATE NOCASE
                """
                params = [f"%{clean_name[:10]}%"]  # Use first 10 chars for broad search
                
                if province:
                    query += " AND UPPER(province) = ? COLLATE NOCASE"
                    params.append(province.upper())
                
                query += " LIMIT 50"  # Limit candidates for fuzzy matching
                
                result = await db.execute(query, params)
                rows = await result.fetchall()
                
                # Score each candidate
                candidates = []
                for row in rows:
                    try:
                        company_data = dict(row)
                        company = CIPCCompany(**company_data)
                        
                        # Calculate similarity score
                        normalized_db_name = self._normalize_company_name(company.company_name)
                        score = SequenceMatcher(None, clean_name, normalized_db_name).ratio()
                        
                        if score >= min_score:
                            candidates.append({
                                "company": company,
                                "score": score
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to process candidate: {e}")
                        continue
                
                if not candidates:
                    return None
                
                # Sort by score (best first)
                candidates.sort(key=lambda x: x["score"], reverse=True)
                
                # Return best match with alternatives
                best = candidates[0]
                alternatives = [c["company"] for c in candidates[1:6]]  # Top 5 alternatives
                
                return {
                    "company": best["company"],
                    "score": best["score"],
                    "alternatives": alternatives
                }
                
        except Exception as e:
            self.logger.error(f"Fuzzy match search failed: {e}")
        
        return None
    
    async def get_database_stats(self) -> dict:
        """Get database statistics for monitoring.
        
        Returns:
            Database statistics including record counts and index status
        """
        stats = {
            "total_companies": 0,
            "active_companies": 0,
            "provinces": [],
            "company_types": [],
            "indexes_created": False
        }
        
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                # Total companies
                result = await db.execute("SELECT COUNT(*) FROM cipc_companies")
                stats["total_companies"] = (await result.fetchone())[0]
                
                # Active companies
                result = await db.execute(
                    "SELECT COUNT(*) FROM cipc_companies WHERE company_status = 'Active'"
                )
                stats["active_companies"] = (await result.fetchone())[0]
                
                # Provinces
                result = await db.execute(
                    "SELECT DISTINCT province FROM cipc_companies WHERE province IS NOT NULL ORDER BY province"
                )
                provinces = await result.fetchall()
                stats["provinces"] = [p[0] for p in provinces]
                
                # Company types
                result = await db.execute(
                    "SELECT DISTINCT company_type FROM cipc_companies WHERE company_type IS NOT NULL ORDER BY company_type"
                )
                types = await result.fetchall()
                stats["company_types"] = [t[0] for t in types]
                
                # Check for indexes
                result = await db.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
                )
                index_count = (await result.fetchone())[0]
                stats["indexes_created"] = index_count >= 5  # We create 7 indexes
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
        
        return stats


async def test_company_search():
    """Test function for company search functionality."""
    searcher = CompanySearcher()
    
    test_companies = [
        "Shoprite Holdings Limited",
        "Pick n Pay Stores Limited", 
        "Sasol Limited",
        "Bidvest Group Limited",
        "MTN Group Limited"
    ]
    
    print("🔍 Testing CIPC company search functionality...")
    
    for company_name in test_companies:
        result = await searcher.verify_company(company_name)
        print(f"   {company_name}: {'✅ FOUND' if result.found else '❌ NOT FOUND'} "
              f"(score: {result.match_score:.2f}, {result.search_time_ms:.2f}ms)")
    
    # Test database stats
    stats = await searcher.get_database_stats()
    print(f"\n📊 Database Statistics:")
    print(f"   Total companies: {stats['total_companies']:,}")
    print(f"   Active companies: {stats['active_companies']:,}")
    print(f"   Provinces: {len(stats['provinces'])}")
    print(f"   Company types: {len(stats['company_types'])}")
    print(f"   Indexes created: {'✅' if stats['indexes_created'] else '❌'}")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    asyncio.run(test_company_search())