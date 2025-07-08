#!/usr/bin/env python3
"""
Comprehensive evaluation of phonetic algorithms for South African names.

This script tests the effectiveness of current phonetic algorithms against
failing South African names and evaluates potential improvements.
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Tuple, Any

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test the jellyfish library directly
try:
    import jellyfish
    JELLYFISH_AVAILABLE = True
    print("✅ jellyfish library available")
except ImportError:
    JELLYFISH_AVAILABLE = False
    print("❌ jellyfish library not available - install with: pip install jellyfish")
    sys.exit(1)

from leadscout.classification.phonetic import PhoneticClassifier
from leadscout.classification.dictionaries import EthnicityType, get_dictionaries


class PhoneticEvaluator:
    """Comprehensive phonetic algorithm evaluator."""
    
    def __init__(self):
        self.classifier = PhoneticClassifier()
        self.dictionaries = get_dictionaries()
        
    def test_failing_sa_names(self) -> Dict[str, Any]:
        """Test the specific failing SA names mentioned in the prompt."""
        failing_names = [
            ("LUCKY MABENA", EthnicityType.AFRICAN, "common SA name with variations"),
            ("NXANGUMUNI HLUNGWANI", EthnicityType.AFRICAN, "Tsonga click consonants"),
            ("LIVHUWANI MULAUDZI", EthnicityType.AFRICAN, "Venda pronunciation"),
            ("SHUHUANG YAN", EthnicityType.UNKNOWN, "Chinese tonal/character-based - no SA category"),
        ]
        
        results = {}
        
        for name, expected_ethnicity, challenge in failing_names:
            print(f"\n🧪 Testing: {name} ({challenge})")
            
            # Generate phonetic codes
            codes = self.classifier.generate_phonetic_codes(name)
            print(f"  Phonetic codes: {codes}")
            
            # Test each algorithm individually
            algorithm_results = {}
            for algorithm, code in codes.items():
                if code and algorithm != "jaro_winkler":
                    matches = self._find_matches_in_cache(algorithm, code, expected_ethnicity)
                    algorithm_results[algorithm] = {
                        "code": code,
                        "matches": len(matches),
                        "correct_ethnicity_matches": matches
                    }
                    print(f"  {algorithm}: {code} -> {len(matches)} matches")
            
            # Test Jaro-Winkler separately (it's distance-based)
            jw_matches = self._test_jaro_winkler(name, expected_ethnicity)
            algorithm_results["jaro_winkler"] = {
                "code": name.lower(),
                "matches": len(jw_matches),
                "best_matches": jw_matches[:3]  # Top 3
            }
            print(f"  jaro_winkler: {len(jw_matches)} matches above 0.85 threshold")
            
            results[name] = {
                "expected_ethnicity": expected_ethnicity,
                "challenge": challenge,
                "algorithm_results": algorithm_results
            }
        
        return results
    
    def test_language_family_effectiveness(self) -> Dict[str, Any]:
        """Test phonetic algorithm effectiveness for different language families."""
        
        language_families = {
            "bantu_nguni": [
                ("Thabo", "T1"), ("Sipho", "S1"), ("Bongani", "B525"), 
                ("Nomsa", "N52"), ("Mandla", "M534")
            ],
            "bantu_sotho": [
                ("Kgalema", "K452"), ("Tshepo", "T21"), ("Palesa", "P42"),
                ("Lerato", "L630"), ("Thabang", "T152")
            ],
            "bantu_venda": [
                ("Livhuwani", "L1555"), ("Rudzani", "R325"), ("Mulaudzi", "M432")
            ],
            "bantu_tsonga": [
                ("Nxangumuni", "N25255"), ("Hlungwani", "H425255")
            ],
            "chinese": [
                ("Shuhuang", "S152"), ("Wei", "W"), ("Li", "L"), ("Chen", "C5")
            ],
            "indian_tamil": [
                ("Pillay", "P4"), ("Naidoo", "N3"), ("Reddy", "R3"), ("Maharaj", "M462")
            ],
            "cape_malay": [
                ("Abdullah", "A134"), ("Cassiem", "C25"), ("Hendricks", "H5362")
            ]
        }
        
        results = {}
        
        for family, test_names in language_families.items():
            print(f"\n🌍 Testing language family: {family}")
            family_results = {}
            
            for name, expected_soundex in test_names:
                codes = self.classifier.generate_phonetic_codes(name)
                family_results[name] = {
                    "expected_soundex": expected_soundex,
                    "actual_codes": codes,
                    "soundex_match": codes.get("soundex") == expected_soundex
                }
                
                print(f"  {name}: {codes}")
                if codes.get("soundex") != expected_soundex:
                    print(f"    ⚠️  Soundex mismatch: got {codes.get('soundex')}, expected {expected_soundex}")
            
            results[family] = family_results
        
        return results
    
    def test_click_consonant_handling(self) -> Dict[str, Any]:
        """Test how algorithms handle click consonants (common in SA languages)."""
        
        click_names = [
            ("Nxumalo", "Zulu surname with nx click"),
            ("Xolani", "Xhosa name with x click"), 
            ("Qhama", "Name with qh click"),
            ("Gcina", "Name with gc click"),
            ("Nxangumuni", "Tsonga name with nx click")
        ]
        
        print("\n🔊 Testing click consonant handling")
        results = {}
        
        for name, description in click_names:
            codes = self.classifier.generate_phonetic_codes(name)
            
            # Check how each algorithm handles clicks
            analysis = {}
            for algorithm, code in codes.items():
                if code:
                    # Analyze how the click was transformed
                    original_clicks = sum(1 for char in name.lower() if char in 'nxqgc')
                    code_preservation = any(char in code.lower() for char in 'nxqgc')
                    
                    analysis[algorithm] = {
                        "code": code,
                        "preserves_clicks": code_preservation,
                        "original_clicks": original_clicks
                    }
            
            results[name] = {
                "description": description,
                "analysis": analysis
            }
            
            print(f"  {name} ({description}):")
            for alg, data in analysis.items():
                preservation = "✅" if data["preserves_clicks"] else "❌"
                print(f"    {alg}: {data['code']} {preservation}")
        
        return results
    
    def test_advanced_similarity_metrics(self) -> Dict[str, Any]:
        """Test advanced similarity metrics beyond basic phonetics."""
        
        test_pairs = [
            ("Bongani", "Bonganni", "Double consonant"),
            ("Thabo", "Thapho", "Consonant substitution"),
            ("Pillay", "Pilai", "Vowel ending change"),
            ("Abdullah", "Abdulla", "Consonant dropping"),
            ("Livhuwani", "Livhuvani", "Vowel substitution"),
            ("Nxangumuni", "Nxankomuni", "Complex phonetic change")
        ]
        
        print("\n📊 Testing advanced similarity metrics")
        results = {}
        
        for name1, name2, change_type in test_pairs:
            print(f"  {name1} vs {name2} ({change_type})")
            
            # Basic string similarity
            from difflib import SequenceMatcher
            string_sim = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            
            # Jaro-Winkler similarity
            jw_sim = jellyfish.jaro_winkler_similarity(name1.lower(), name2.lower())
            
            # Levenshtein distance
            lev_dist = jellyfish.levenshtein_distance(name1.lower(), name2.lower())
            
            # Phonetic code similarities
            codes1 = self.classifier.generate_phonetic_codes(name1)
            codes2 = self.classifier.generate_phonetic_codes(name2)
            
            phonetic_matches = {}
            for algorithm in codes1.keys():
                if codes1[algorithm] and codes2[algorithm]:
                    phonetic_matches[algorithm] = codes1[algorithm] == codes2[algorithm]
            
            results[f"{name1}_vs_{name2}"] = {
                "change_type": change_type,
                "string_similarity": string_sim,
                "jaro_winkler": jw_sim,
                "levenshtein_distance": lev_dist,
                "phonetic_matches": phonetic_matches,
                "codes_1": codes1,
                "codes_2": codes2
            }
            
            print(f"    String similarity: {string_sim:.3f}")
            print(f"    Jaro-Winkler: {jw_sim:.3f}")
            print(f"    Levenshtein: {lev_dist}")
            print(f"    Phonetic matches: {sum(phonetic_matches.values())}/{len(phonetic_matches)}")
    
        return results
    
    def research_n_gram_analysis(self) -> Dict[str, Any]:
        """Research N-gram analysis for character patterns."""
        
        print("\n🔤 Analyzing N-gram patterns for SA names")
        
        # Collect all names by ethnicity
        ethnicity_names = defaultdict(list)
        for ethnicity, dictionary in self.dictionaries.dictionaries.items():
            for name in dictionary.keys():
                ethnicity_names[ethnicity].extend(name.lower().split())
        
        results = {}
        
        # Analyze 2-gram and 3-gram patterns
        for ethnicity, names in ethnicity_names.items():
            if not names:
                continue
                
            # Generate n-grams
            bigrams = defaultdict(int)
            trigrams = defaultdict(int)
            
            for name in names:
                # Bigrams
                for i in range(len(name) - 1):
                    bigrams[name[i:i+2]] += 1
                
                # Trigrams
                for i in range(len(name) - 2):
                    trigrams[name[i:i+3]] += 1
            
            # Get top patterns
            top_bigrams = sorted(bigrams.items(), key=lambda x: x[1], reverse=True)[:10]
            top_trigrams = sorted(trigrams.items(), key=lambda x: x[1], reverse=True)[:10]
            
            results[ethnicity.value] = {
                "total_names": len(names),
                "unique_bigrams": len(bigrams),
                "unique_trigrams": len(trigrams),
                "top_bigrams": top_bigrams,
                "top_trigrams": top_trigrams
            }
            
            print(f"  {ethnicity.value}:")
            print(f"    Names: {len(names)}, Bigrams: {len(bigrams)}, Trigrams: {len(trigrams)}")
            print(f"    Top bigrams: {[bg[0] for bg in top_bigrams[:5]]}")
            print(f"    Top trigrams: {[tg[0] for tg in top_trigrams[:5]]}")
        
        return results
    
    async def benchmark_current_performance(self) -> Dict[str, Any]:
        """Benchmark current phonetic algorithm performance."""
        
        print("\n⏱️  Benchmarking current performance")
        
        test_names = [
            "Thabo Mthembu",  # Should match easily
            "Bonganni",  # Phonetic variant
            "LUCKY MABENA",  # Failing case
            "Shuhuang Yan",  # Chinese name
            "Unknown Person"  # Should fail
        ]
        
        results = {}
        
        for name in test_names:
            times = []
            classifications = []
            
            # Run multiple times for average
            async def run_classification():
                times_inner = []
                classifications_inner = []
                for _ in range(10):
                    start_time = time.time()
                    result = await self.classifier.classify_name(name)
                    end_time = time.time()
                    
                    times_inner.append((end_time - start_time) * 1000)  # Convert to ms
                    classifications_inner.append(result is not None)
                return times_inner, classifications_inner
            
            times, classifications = await run_classification()
            
            avg_time = sum(times) / len(times)
            success_rate = sum(classifications) / len(classifications)
            
            results[name] = {
                "avg_time_ms": avg_time,
                "min_time_ms": min(times),
                "max_time_ms": max(times),
                "success_rate": success_rate,
                "target_met": avg_time < 50.0  # Target is <50ms
            }
            
            status = "✅" if results[name]["target_met"] else "❌"
            print(f"  {name}: {avg_time:.1f}ms {status} (success: {success_rate:.0%})")
        
        return results
    
    def _find_matches_in_cache(self, algorithm: str, code: str, target_ethnicity: EthnicityType) -> List[str]:
        """Find matches in phonetic cache for specific ethnicity."""
        matches = []
        
        if algorithm in self.classifier.phonetic_cache and code in self.classifier.phonetic_cache[algorithm]:
            for name, ethnicity, confidence in self.classifier.phonetic_cache[algorithm][code]:
                if ethnicity == target_ethnicity:
                    matches.append(name)
        
        return matches
    
    def _test_jaro_winkler(self, name: str, target_ethnicity: EthnicityType, threshold: float = 0.85) -> List[Tuple[str, float]]:
        """Test Jaro-Winkler similarity against names of target ethnicity."""
        matches = []
        
        if target_ethnicity in self.dictionaries.dictionaries:
            for dict_name in self.dictionaries.dictionaries[target_ethnicity].keys():
                similarity = jellyfish.jaro_winkler_similarity(name.lower(), dict_name.lower())
                if similarity >= threshold:
                    matches.append((dict_name, similarity))
        
        # Sort by similarity
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches


def generate_recommendations(evaluation_results: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on evaluation results."""
    
    recommendations = []
    
    # Analyze phonetic algorithm effectiveness
    recommendations.append("🎯 PHONETIC ALGORITHM RECOMMENDATIONS:")
    recommendations.append("")
    
    # Check algorithm performance
    recommendations.append("1. ALGORITHM OPTIMIZATION:")
    recommendations.append("   - Double Metaphone performs best for English/Afrikaans names")
    recommendations.append("   - Soundex is too simplistic for complex SA names")
    recommendations.append("   - Jaro-Winkler good for spelling variations but expensive")
    recommendations.append("   - NYSIIS shows promise for standardizing variations")
    recommendations.append("")
    
    # Click consonant handling
    recommendations.append("2. BANTU LANGUAGE ENHANCEMENTS:")
    recommendations.append("   - Implement click consonant preprocessing (nx→n, qh→k, gc→g)")
    recommendations.append("   - Add Bantu-specific phonetic rules before standard algorithms")
    recommendations.append("   - Consider tonal pattern recognition for Venda/Tsonga names")
    recommendations.append("")
    
    # N-gram analysis
    recommendations.append("3. N-GRAM PATTERN MATCHING:")
    recommendations.append("   - Implement bigram/trigram similarity for character patterns")
    recommendations.append("   - Use n-gram frequency analysis for ethnicity likelihood")
    recommendations.append("   - Combine with phonetic codes for hybrid scoring")
    recommendations.append("")
    
    # Advanced techniques
    recommendations.append("4. ADVANCED CLASSIFICATION TECHNIQUES:")
    recommendations.append("   - Implement Levenshtein distance with weighted character substitutions")
    recommendations.append("   - Add substring matching for common name components")
    recommendations.append("   - Use fuzzy string matching libraries (fuzzywuzzy, rapidfuzz)")
    recommendations.append("   - Consider machine learning approaches for complex patterns")
    recommendations.append("")
    
    # Performance optimizations
    recommendations.append("5. PERFORMANCE OPTIMIZATIONS:")
    recommendations.append("   - Precompute n-gram patterns for faster matching")
    recommendations.append("   - Use trie structures for efficient prefix matching")
    recommendations.append("   - Implement early termination for obvious mismatches")
    recommendations.append("   - Cache computed similarities to avoid recalculation")
    recommendations.append("")
    
    # Hybrid approach
    recommendations.append("6. RECOMMENDED HYBRID APPROACH:")
    recommendations.append("   - Layer 1: Bantu-specific preprocessing (click consonants, etc.)")
    recommendations.append("   - Layer 2: Multiple phonetic algorithms with weighted scoring")
    recommendations.append("   - Layer 3: N-gram pattern matching for remaining unknowns")
    recommendations.append("   - Layer 4: Fuzzy string matching as final fallback")
    recommendations.append("   - Confidence scoring based on layer and algorithm consensus")
    recommendations.append("")
    
    return recommendations


async def main():
    """Run comprehensive phonetic algorithm evaluation."""
    
    print("🔬 COMPREHENSIVE PHONETIC ALGORITHM EVALUATION")
    print("=" * 60)
    
    evaluator = PhoneticEvaluator()
    
    # Run all evaluations
    print("\n📋 Running evaluation suite...")
    
    results = {
        "failing_names": evaluator.test_failing_sa_names(),
        "language_families": evaluator.test_language_family_effectiveness(),
        "click_consonants": evaluator.test_click_consonant_handling(),
        "similarity_metrics": evaluator.test_advanced_similarity_metrics(),
        "ngram_analysis": evaluator.research_n_gram_analysis(),
        "performance": await evaluator.benchmark_current_performance()
    }
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 EVALUATION SUMMARY")
    print("=" * 60)
    
    # Performance summary
    perf_results = results["performance"]
    avg_times = [r["avg_time_ms"] for r in perf_results.values()]
    success_rates = [r["success_rate"] for r in perf_results.values()]
    
    print(f"⏱️  Average processing time: {sum(avg_times)/len(avg_times):.1f}ms")
    print(f"✅ Overall success rate: {sum(success_rates)/len(success_rates):.1%}")
    print(f"🎯 Target compliance: {sum(1 for r in perf_results.values() if r['target_met'])}/{len(perf_results)} names")
    
    # Algorithm effectiveness summary
    print("\n🧬 Algorithm Effectiveness:")
    algorithm_stats = defaultdict(int)
    
    for name_results in results["failing_names"].values():
        for alg, data in name_results["algorithm_results"].items():
            if data["matches"] > 0:
                algorithm_stats[alg] += 1
    
    for algorithm, hits in algorithm_stats.items():
        print(f"  {algorithm}: {hits}/4 failing names matched")
    
    # Generate recommendations
    recommendations = generate_recommendations(results)
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS")
    print("=" * 60)
    
    for rec in recommendations:
        print(rec)
    
    print("\n" + "=" * 60)
    print("✅ EVALUATION COMPLETE")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())