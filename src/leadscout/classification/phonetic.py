"""Advanced phonetic matching for name classification.

This module implements multiple phonetic algorithms to match unknown names
against classified names in the cache. Uses the confidence scoring approach
from the research document with algorithm agreement weighting.

Key Features:
- Multiple algorithms: Soundex, Metaphone, Double Metaphone, NYSIIS, Jaro-Winkler
- Algorithm confidence weighting and agreement scoring
- South African linguistic pattern optimization
- Variant spelling detection and normalization
- Performance optimization with precomputed phonetic codes

Architecture Decision: Combines multiple algorithms with weighted confidence
scoring to handle the linguistic diversity of South African names effectively.
Academic research shows this approach achieves 85%+ accuracy.

Integration: Second layer in classification pipeline, uses Developer A's
cache to find phonetically similar names.
"""

import time
import logging
from typing import List, Optional, Dict, Tuple, Set, Any
from collections import Counter, defaultdict
from difflib import SequenceMatcher

# Import phonetic algorithms
try:
    import jellyfish
    JELLYFISH_AVAILABLE = True
except ImportError:
    JELLYFISH_AVAILABLE = False
    logging.warning("jellyfish library not available - phonetic matching will be limited")

from .dictionaries import EthnicityType, get_dictionaries
from .models import (
    Classification, ClassificationMethod, PhoneticClassificationDetails,
    PhoneticMatch, AlternativeClassification
)
from .exceptions import (
    PhoneticMatchingError, raise_phonetic_failure
)

logger = logging.getLogger(__name__)


class PhoneticClassifier:
    """Advanced phonetic name classifier using multiple algorithms."""
    
    def __init__(self):
        """Initialize phonetic classifier with algorithm weights."""
        # Algorithm weights based on performance for SA names
        self.algorithm_weights = {
            'soundex': 0.15,      # Basic but fast
            'metaphone': 0.20,    # Good for English/Afrikaans
            'dmetaphone': 0.25,   # Best overall performance
            'nysiis': 0.20,       # Good for variants
            'jaro_winkler': 0.20  # Good for spelling variations
        }
        
        # Minimum similarity thresholds for each algorithm
        self.similarity_thresholds = {
            'soundex': 1.0,       # Exact match for soundex (binary)
            'metaphone': 1.0,     # Exact match for metaphone
            'dmetaphone': 1.0,    # Exact match for double metaphone
            'nysiis': 1.0,        # Exact match for nysiis
            'jaro_winkler': 0.85  # High threshold for jaro-winkler
        }
        
        # Load dictionaries for phonetic preprocessing
        self.dictionaries = get_dictionaries()
        self._precompute_phonetic_cache()
        
        logger.info("PhoneticClassifier initialized with 5 algorithms")
    
    def _precompute_phonetic_cache(self) -> None:
        """Precompute phonetic codes for all dictionary names for performance."""
        self.phonetic_cache = defaultdict(lambda: defaultdict(set))
        
        logger.info("Precomputing phonetic codes for all dictionary names...")
        
        for ethnicity, dictionary in self.dictionaries.dictionaries.items():
            for name, entry in dictionary.items():
                phonetic_codes = self.generate_phonetic_codes(name)
                
                # Store mapping from phonetic code to (name, ethnicity, confidence)
                for algorithm, code in phonetic_codes.items():
                    if code:  # Only store valid codes
                        self.phonetic_cache[algorithm][code].add((name, ethnicity, entry.confidence))
        
        total_cached = sum(
            len(codes) for algorithm_cache in self.phonetic_cache.values() 
            for codes in algorithm_cache.values()
        )
        logger.info(f"Precomputed {total_cached} phonetic mappings across {len(self.algorithm_weights)} algorithms")
    
    def generate_phonetic_codes(self, name: str) -> Dict[str, str]:
        """Generate phonetic codes for a name using all algorithms."""
        if not JELLYFISH_AVAILABLE:
            logger.warning("Jellyfish not available - using basic algorithms only")
            return {"basic": name.lower().replace(" ", "")}
        
        name_clean = self._normalize_for_phonetics(name)
        codes = {}
        
        try:
            # Soundex
            codes['soundex'] = jellyfish.soundex(name_clean)
        except Exception as e:
            logger.debug(f"Soundex failed for '{name}': {e}")
            codes['soundex'] = ""
        
        try:
            # Metaphone
            codes['metaphone'] = jellyfish.metaphone(name_clean)
        except Exception as e:
            logger.debug(f"Metaphone failed for '{name}': {e}")
            codes['metaphone'] = ""
        
        try:
            # Double Metaphone (returns tuple, take first)
            dmetaphone_result = jellyfish.dmetaphone(name_clean)
            codes['dmetaphone'] = dmetaphone_result[0] if dmetaphone_result[0] else ""
        except Exception as e:
            logger.debug(f"Double Metaphone failed for '{name}': {e}")
            codes['dmetaphone'] = ""
        
        try:
            # NYSIIS
            codes['nysiis'] = jellyfish.nysiis(name_clean)
        except Exception as e:
            logger.debug(f"NYSIIS failed for '{name}': {e}")
            codes['nysiis'] = ""
        
        # Jaro-Winkler is a distance measure, not a code generator
        # We'll compute it during matching
        codes['jaro_winkler'] = name_clean.lower()
        
        return codes
    
    def _normalize_for_phonetics(self, name: str) -> str:
        """Normalize name for better phonetic matching."""
        # Remove common prefixes/suffixes that can interfere
        normalized = name.strip().lower()
        
        # Handle South African specific patterns
        # Remove common prefixes
        prefixes_to_remove = ['van der ', 'van ', 'de ', 'du ', 'le ']
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
        
        # Handle apostrophes (common in some SA names)
        normalized = normalized.replace("'", "")
        
        # Remove hyphens and spaces for core phonetic matching
        normalized = normalized.replace("-", "").replace(" ", "")
        
        # Ensure we have something to work with
        if not normalized:
            normalized = name.strip().replace(" ", "")
        
        return normalized
    
    async def classify_name(self, name: str) -> Optional[Classification]:
        """Classify a name using phonetic matching against cached names."""
        start_time = time.time()
        
        try:
            # Generate phonetic codes for the input name
            phonetic_codes = self.generate_phonetic_codes(name)
            
            # Find matches for each algorithm
            all_matches = []
            algorithm_results = {}
            
            for algorithm, code in phonetic_codes.items():
                if not code:
                    continue
                
                matches = self._find_matches_for_algorithm(algorithm, code, name)
                all_matches.extend(matches)
                algorithm_results[algorithm] = len(matches)
            
            if not all_matches:
                return None  # No phonetic matches found
            
            # Analyze matches and determine best classification
            classification = self._analyze_matches(name, all_matches, phonetic_codes, start_time)
            
            # Add detailed phonetic information
            classification.phonetic_details = PhoneticClassificationDetails(
                phonetic_codes=phonetic_codes,
                matches=all_matches,
                algorithm_weights=self.algorithm_weights,
                consensus_score=self._calculate_consensus_score(all_matches),
                top_algorithm=self._get_top_algorithm(all_matches),
                cached_names_searched=sum(algorithm_results.values())
            )
            
            return classification
            
        except Exception as e:
            logger.error(f"Phonetic classification failed for '{name}': {e}")
            raise PhoneticMatchingError(
                f"Phonetic matching failed for '{name}': {str(e)}",
                name=name,
                failed_algorithms=list(phonetic_codes.keys())
            )
    
    def _find_matches_for_algorithm(
        self, 
        algorithm: str, 
        code: str, 
        original_name: str
    ) -> List[PhoneticMatch]:
        """Find matches for a specific algorithm."""
        matches = []
        
        if algorithm == 'jaro_winkler':
            # Special handling for Jaro-Winkler (distance-based)
            matches = self._find_jaro_winkler_matches(original_name)
        else:
            # Exact phonetic code matches
            if code in self.phonetic_cache[algorithm]:
                for cached_name, ethnicity, confidence in self.phonetic_cache[algorithm][code]:
                    # Calculate string similarity for additional confidence
                    similarity = SequenceMatcher(None, original_name.lower(), cached_name).ratio()
                    
                    match = PhoneticMatch(
                        matched_name=cached_name,
                        matched_ethnicity=ethnicity,
                        algorithm=algorithm,
                        similarity_score=similarity,
                        phonetic_code=code,
                        original_confidence=confidence
                    )
                    matches.append(match)
        
        return matches
    
    def _find_jaro_winkler_matches(self, name: str) -> List[PhoneticMatch]:
        """Find matches using Jaro-Winkler distance."""
        if not JELLYFISH_AVAILABLE:
            return []
        
        matches = []
        threshold = self.similarity_thresholds['jaro_winkler']
        
        # Check against all cached names (this is expensive but thorough)
        for ethnicity, dictionary in self.dictionaries.dictionaries.items():
            for cached_name, entry in dictionary.items():
                try:
                    distance = jellyfish.jaro_winkler_similarity(
                        name.lower(), 
                        cached_name.lower()
                    )
                    
                    if distance >= threshold:
                        match = PhoneticMatch(
                            matched_name=cached_name,
                            matched_ethnicity=ethnicity,
                            algorithm='jaro_winkler',
                            similarity_score=distance,
                            phonetic_code=cached_name.lower(),
                            original_confidence=entry.confidence
                        )
                        matches.append(match)
                        
                except Exception as e:
                    logger.debug(f"Jaro-Winkler failed for '{name}' vs '{cached_name}': {e}")
                    continue
        
        # Sort by similarity score (highest first) and limit results
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:10]  # Limit to top 10 matches
    
    def _analyze_matches(
        self, 
        name: str, 
        matches: List[PhoneticMatch], 
        phonetic_codes: Dict[str, str],
        start_time: float
    ) -> Classification:
        """Analyze phonetic matches to determine best classification."""
        
        # Group matches by ethnicity
        ethnicity_scores = defaultdict(list)
        for match in matches:
            # Calculate weighted score
            algorithm_weight = self.algorithm_weights[match.algorithm]
            weighted_score = (
                match.similarity_score * algorithm_weight * match.original_confidence
            )
            ethnicity_scores[match.matched_ethnicity].append(weighted_score)
        
        # Calculate final scores for each ethnicity
        final_scores = {}
        for ethnicity, scores in ethnicity_scores.items():
            # Use average of top scores to avoid bias toward ethnicities with more matches
            top_scores = sorted(scores, reverse=True)[:3]  # Top 3 scores
            final_scores[ethnicity] = sum(top_scores) / len(top_scores)
        
        # Get the best ethnicity
        best_ethnicity = max(final_scores.keys(), key=lambda e: final_scores[e])
        best_score = final_scores[best_ethnicity]
        
        # Calculate confidence based on score and consensus
        confidence = min(best_score, 0.95)  # Cap at 95% for phonetic matches
        
        # Apply consensus bonus
        consensus_score = self._calculate_consensus_score(matches)
        confidence *= (0.8 + 0.2 * consensus_score)  # Boost if multiple algorithms agree
        
        # Ensure minimum confidence for phonetic matches
        confidence = max(confidence, 0.60)  # Minimum 60% for phonetic matches
        
        # Create alternative classifications for other ethnicities
        alternatives = []
        for ethnicity, score in final_scores.items():
            if ethnicity != best_ethnicity and score > 0.5:
                alternatives.append(AlternativeClassification(
                    ethnicity=ethnicity,
                    confidence=min(score, 0.90),
                    method=ClassificationMethod.PHONETIC,
                    reasoning=f"Phonetic match with {len(ethnicity_scores[ethnicity])} algorithm(s)"
                ))
        
        processing_time = (time.time() - start_time) * 1000
        
        return Classification(
            name=name,
            ethnicity=best_ethnicity,
            confidence=confidence,
            method=ClassificationMethod.PHONETIC,
            processing_time_ms=processing_time,
            alternative_classifications=alternatives
        )
    
    def _calculate_consensus_score(self, matches: List[PhoneticMatch]) -> float:
        """Calculate how much the algorithms agree on ethnicity."""
        if not matches:
            return 0.0
        
        # Count ethnicity votes by algorithm
        algorithm_votes = defaultdict(set)
        for match in matches:
            algorithm_votes[match.algorithm].add(match.matched_ethnicity)
        
        # Calculate agreement score
        total_algorithms = len(algorithm_votes)
        if total_algorithms <= 1:
            return 1.0
        
        # Find the most common ethnicity
        ethnicity_counts = Counter()
        for match in matches:
            ethnicity_counts[match.matched_ethnicity] += 1
        
        if not ethnicity_counts:
            return 0.0
        
        most_common_ethnicity = ethnicity_counts.most_common(1)[0][0]
        
        # Count how many algorithms found this ethnicity
        agreeing_algorithms = sum(
            1 for alg_ethnicities in algorithm_votes.values()
            if most_common_ethnicity in alg_ethnicities
        )
        
        return agreeing_algorithms / total_algorithms
    
    def _get_top_algorithm(self, matches: List[PhoneticMatch]) -> str:
        """Get the algorithm that produced the best matches."""
        if not matches:
            return "none"
        
        # Score algorithms by their best match quality
        algorithm_scores = defaultdict(float)
        for match in matches:
            score = match.similarity_score * match.original_confidence
            algorithm_scores[match.algorithm] = max(
                algorithm_scores[match.algorithm], 
                score
            )
        
        return max(algorithm_scores.keys(), key=lambda a: algorithm_scores[a])
    
    def find_similar_names(
        self, 
        name: str, 
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[PhoneticMatch]:
        """Find phonetically similar names for few-shot learning."""
        try:
            phonetic_codes = self.generate_phonetic_codes(name)
            all_matches = []
            
            for algorithm, code in phonetic_codes.items():
                if not code:
                    continue
                matches = self._find_matches_for_algorithm(algorithm, code, name)
                all_matches.extend(matches)
            
            # Filter by minimum similarity and remove duplicates
            filtered_matches = []
            seen_names = set()
            
            for match in all_matches:
                if (match.similarity_score >= min_similarity and 
                    match.matched_name not in seen_names):
                    filtered_matches.append(match)
                    seen_names.add(match.matched_name)
            
            # Sort by similarity and limit results
            filtered_matches.sort(key=lambda x: x.similarity_score, reverse=True)
            return filtered_matches[:limit]
            
        except Exception as e:
            logger.warning(f"Error finding similar names for '{name}': {e}")
            return []
    
    def get_phonetic_stats(self) -> Dict[str, Any]:
        """Get statistics about phonetic matching performance."""
        stats = {
            "algorithms_available": list(self.algorithm_weights.keys()),
            "jellyfish_available": JELLYFISH_AVAILABLE,
            "cached_phonetic_mappings": {},
            "algorithm_weights": self.algorithm_weights,
            "similarity_thresholds": self.similarity_thresholds
        }
        
        for algorithm, cache in self.phonetic_cache.items():
            stats["cached_phonetic_mappings"][algorithm] = len(cache)
        
        return stats