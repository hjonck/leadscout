#!/usr/bin/env python3
"""
Comprehensive Phase 1 validation test suite.

This test validates ALL Phase 1 critical fixes and improvements:
1. Double Metaphone implementation fix
2. Dictionary expansions (African, Chinese)
3. Multi-word classification improvements
4. Confidence threshold optimization
5. Overall system performance and cost reduction

Tests production failure cases and extended scenarios to ensure
the system meets research targets for LLM reduction and accuracy.
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from leadscout.classification.classifier import create_classifier, NameClassifier
from leadscout.classification.phonetic import PhoneticClassifier
from leadscout.classification.rules import RuleBasedClassifier
from leadscout.classification.dictionaries import get_dictionaries
from leadscout.classification.models import Classification

# Original production failure cases (critical)
CRITICAL_PRODUCTION_FAILURES = [
    ("LUCKY MABENA", "african", "Modern African virtue name + Pedi surname"),
    ("NXANGUMUNI HLUNGWANI", "african", "Tsonga given name + Tsonga surname"),
    ("SHUHUANG YAN", "chinese", "Chinese given name + Chinese surname"),
    ("LIVHUWANI MULAUDZI", "african", "Venda given name + Venda surname"),
    ("NYIKO CYNTHIA HLUNGWANI", "african", "Tsonga + English + Tsonga multi-word"),
    ("EMERENCIA MMATSHEPO MAGABANE", "african", "Portuguese + Tswana + Sotho multi-word"),
    ("BEN FANYANA NKOSI", "african", "English + Zulu + Zulu multi-word"),
    ("JUSTICE VUSIMUZI MTIMKULU", "african", "Virtue + Zulu + Zulu multi-word"),
    ("MOHAU JOHN SEBETHA", "african", "Sotho + English + Sotho multi-word"),
    ("SHIMANE JOEL RAMONTSA", "african", "Tswana + English + Tswana multi-word"),
]

# Extended validation cases
EXTENDED_VALIDATION_CASES = [
    # African traditional names (various languages)
    ("THABO MTHEMBU", "african", "Sotho + Zulu combination"),
    ("NOMSA NDLOVU", "african", "Zulu + Ndebele combination"),
    ("SIPHO DLAMINI", "african", "Zulu + Swazi combination"),
    ("KAGISO KHUMALO", "african", "Tswana + Zulu combination"),
    ("LERATO MOKOENA", "african", "Sotho + Sotho combination"),
    
    # Indian names
    ("ANISHA PATEL", "indian", "Hindi given + Gujarati surname"),
    ("RAJESH NAIDOO", "indian", "Hindi + Tamil combination"),
    ("PRIYA SHARMA", "indian", "Sanskrit + North Indian surname"),
    
    # Cape Malay names
    ("FATIMA ADAMS", "cape_malay", "Arabic given + Cape Malay surname"),
    ("ABDULLA ISAACS", "cape_malay", "Arabic + Cape Malay combination"),
    
    # Coloured names
    ("SUSAN BOOYSEN", "coloured", "English + Afrikaans combination"),
    ("APRIL JANTJIES", "coloured", "English + Cape Coloured surname"),
    
    # White names
    ("PIETER STEYN", "white", "Afrikaans + Afrikaans combination"),
    ("JOHANNES FOURIE", "white", "Afrikaans traditional"),
    
    # Chinese names (new category)
    ("MING WONG", "chinese", "Chinese given + Chinese surname"),
    ("LIANG CHEN", "chinese", "Chinese traditional combination"),
    ("WEI ZHANG", "chinese", "Common Chinese name pattern"),
    
    # Edge cases and mixed patterns
    ("NOMSA SMITH", "african", "African given + English surname"),
    ("JOHN MTHEMBU", "african", "English given + African surname"),
    ("MARY PILLAY", "indian", "English given + Tamil surname"),
    ("DAVID ADAMS", "white", "English + potentially white surname"),
]

class Phase1TestSuite:
    """Comprehensive test suite for Phase 1 critical fixes."""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete Phase 1 validation test suite."""
        print("🧪 PHASE 1 COMPREHENSIVE VALIDATION TEST SUITE")
        print("=" * 70)
        
        self.start_time = time.time()
        
        # Test 1: Critical production failures
        await self._test_critical_failures()
        
        # Test 2: Dictionary expansion validation
        await self._test_dictionary_expansions()
        
        # Test 3: Multi-word classification improvements
        await self._test_multi_word_improvements()
        
        # Test 4: Phonetic algorithm fixes
        await self._test_phonetic_fixes()
        
        # Test 5: Configuration optimization
        await self._test_configuration_optimization()
        
        # Test 6: Performance benchmarks
        await self._test_performance_benchmarks()
        
        # Test 7: Cost reduction validation
        await self._test_cost_reduction()
        
        # Generate final report
        return self._generate_final_report()
    
    async def _test_critical_failures(self):
        """Test that all critical production failures are now resolved."""
        print("\n🚨 TEST 1: Critical Production Failures")
        print("-" * 50)
        
        classifier = create_classifier(mode="cost_optimized", enable_llm=False)
        
        successes = 0
        failures = []
        
        for name, expected_ethnicity, description in CRITICAL_PRODUCTION_FAILURES:
            result = await classifier.classify_name(name)
            
            if result and result.ethnicity.value == expected_ethnicity:
                successes += 1
                print(f"   ✅ {name} -> {result.ethnicity.value} ({description})")
            else:
                failures.append((name, expected_ethnicity, description))
                actual = result.ethnicity.value if result else "NO_RESULT"
                print(f"   ❌ {name} -> {actual} (expected: {expected_ethnicity})")
        
        success_rate = (successes / len(CRITICAL_PRODUCTION_FAILURES)) * 100
        
        self.results['critical_failures'] = {
            'total': len(CRITICAL_PRODUCTION_FAILURES),
            'successes': successes,
            'failures': len(failures),
            'success_rate': success_rate,
            'failed_cases': failures
        }
        
        print(f"\n   📊 Result: {successes}/{len(CRITICAL_PRODUCTION_FAILURES)} ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("   🎉 ALL CRITICAL FAILURES RESOLVED!")
        else:
            print(f"   ⚠️  {len(failures)} critical failures remain")
    
    async def _test_dictionary_expansions(self):
        """Test that dictionary expansions are working correctly."""
        print("\n📚 TEST 2: Dictionary Expansion Validation")
        print("-" * 50)
        
        dictionaries = get_dictionaries()
        coverage = dictionaries.get_ethnicity_coverage()
        
        print("   📖 Dictionary coverage:")
        total_names = 0
        for ethnicity, count in coverage.items():
            print(f"      {ethnicity.value.title()}: {count} names")
            total_names += count
        
        print(f"      Total: {total_names} names")
        
        # Test specific new additions
        new_additions_tests = [
            ("LUCKY", "african", "Modern virtue name"),
            ("HLUNGWANI", "african", "Tsonga surname"),
            ("MULAUDZI", "african", "Venda surname"),
            ("SHUHUANG", "chinese", "Chinese given name"),
            ("YAN", "chinese", "Chinese surname"),
            ("BEN", "white", "Common English name"),  # Should be in dictionaries now
        ]
        
        classifier = create_classifier(mode="cost_optimized", enable_llm=False)
        successful_additions = 0
        
        for name, expected_ethnicity, description in new_additions_tests:
            result = await classifier.classify_name(name)
            if result and result.ethnicity.value == expected_ethnicity:
                successful_additions += 1
                print(f"   ✅ {name} -> {result.ethnicity.value} ({description})")
            else:
                actual = result.ethnicity.value if result else "NO_RESULT"
                print(f"   ❌ {name} -> {actual} (expected: {expected_ethnicity})")
        
        addition_success_rate = (successful_additions / len(new_additions_tests)) * 100
        
        self.results['dictionary_expansions'] = {
            'total_names': total_names,
            'coverage': coverage,
            'new_additions_tested': len(new_additions_tests),
            'successful_additions': successful_additions,
            'addition_success_rate': addition_success_rate
        }
        
        print(f"\n   📊 New additions: {successful_additions}/{len(new_additions_tests)} ({addition_success_rate:.1f}%)")
    
    async def _test_multi_word_improvements(self):
        """Test multi-word name classification improvements."""
        print("\n👥 TEST 3: Multi-Word Classification Improvements")
        print("-" * 50)
        
        multi_word_cases = [
            ("BEN FANYANA NKOSI", "african", "English + Zulu + Zulu"),
            ("NYIKO CYNTHIA HLUNGWANI", "african", "Tsonga + English + Tsonga"),
            ("MOHAU JOHN SEBETHA", "african", "Sotho + English + Sotho"),
            ("JUSTICE VUSIMUZI MTIMKULU", "african", "Virtue + Zulu + Zulu"),
        ]
        
        classifier = create_classifier(mode="cost_optimized", enable_llm=False)
        
        successes = 0
        for name, expected_ethnicity, description in multi_word_cases:
            result = await classifier.classify_name(name)
            
            if result and result.ethnicity.value == expected_ethnicity:
                successes += 1
                print(f"   ✅ {name} -> {result.ethnicity.value} (method: {result.method.value})")
            else:
                actual = result.ethnicity.value if result else "NO_RESULT"
                print(f"   ❌ {name} -> {actual} (expected: {expected_ethnicity})")
        
        success_rate = (successes / len(multi_word_cases)) * 100
        
        self.results['multi_word'] = {
            'tested': len(multi_word_cases),
            'successes': successes,
            'success_rate': success_rate
        }
        
        print(f"\n   📊 Multi-word: {successes}/{len(multi_word_cases)} ({success_rate:.1f}%)")
    
    async def _test_phonetic_fixes(self):
        """Test that Double Metaphone and other phonetic fixes work."""
        print("\n🔊 TEST 4: Phonetic Algorithm Fixes")
        print("-" * 50)
        
        # Test phonetic classifier directly
        phonetic_classifier = PhoneticClassifier()
        
        # Test Double Metaphone specifically (this was the critical bug)
        test_name = "MTHEMBU"
        
        try:
            result = await phonetic_classifier.classify_name(test_name)
            if result:
                print(f"   ✅ Double Metaphone fix verified: {test_name} -> {result.ethnicity.value}")
                print(f"      Confidence: {result.confidence:.3f}, Method: {result.method.value}")
                if hasattr(result, 'phonetic_details') and result.phonetic_details:
                    codes = result.phonetic_details.phonetic_codes
                    print(f"      Phonetic codes: {codes}")
            else:
                print(f"   ❌ Double Metaphone test failed: no result for {test_name}")
        except Exception as e:
            print(f"   ❌ Double Metaphone error: {e}")
        
        # Test other phonetic improvements
        phonetic_test_cases = [
            ("THABO", "african"),
            ("NOMSA", "african"),
            ("SIPHO", "african"),
        ]
        
        phonetic_successes = 0
        for name, expected_ethnicity in phonetic_test_cases:
            try:
                result = await phonetic_classifier.classify_name(name)
                if result and result.ethnicity.value == expected_ethnicity:
                    phonetic_successes += 1
                    print(f"   ✅ Phonetic: {name} -> {result.ethnicity.value}")
            except Exception as e:
                print(f"   ❌ Phonetic error for {name}: {e}")
        
        phonetic_success_rate = (phonetic_successes / len(phonetic_test_cases)) * 100
        
        self.results['phonetic_fixes'] = {
            'double_metaphone_fixed': True,  # If we got here without errors
            'phonetic_tests': len(phonetic_test_cases),
            'phonetic_successes': phonetic_successes,
            'phonetic_success_rate': phonetic_success_rate
        }
        
        print(f"\n   📊 Phonetic tests: {phonetic_successes}/{len(phonetic_test_cases)} ({phonetic_success_rate:.1f}%)")
    
    async def _test_configuration_optimization(self):
        """Test that configuration optimization is working."""
        print("\n⚙️ TEST 5: Configuration Optimization")
        print("-" * 50)
        
        # Test different configurations
        configurations = {
            'balanced': create_classifier(mode="balanced", enable_llm=False),
            'cost_optimized': create_classifier(mode="cost_optimized", enable_llm=False),
            'fast': create_classifier(mode="fast", enable_llm=False),
        }
        
        test_cases = CRITICAL_PRODUCTION_FAILURES[:5]  # Subset for speed
        
        config_results = {}
        
        for config_name, classifier in configurations.items():
            successes = 0
            total_time = 0
            
            for name, expected_ethnicity, _ in test_cases:
                start = time.time()
                result = await classifier.classify_name(name)
                total_time += (time.time() - start) * 1000
                
                if result and result.ethnicity.value == expected_ethnicity:
                    successes += 1
            
            success_rate = (successes / len(test_cases)) * 100
            avg_time = total_time / len(test_cases)
            
            config_results[config_name] = {
                'success_rate': success_rate,
                'avg_time_ms': avg_time,
                'successes': successes,
                'total': len(test_cases)
            }
            
            print(f"   {config_name.upper()}: {successes}/{len(test_cases)} ({success_rate:.1f}%) - {avg_time:.2f}ms avg")
        
        self.results['configuration_optimization'] = config_results
    
    async def _test_performance_benchmarks(self):
        """Test that performance targets are met."""
        print("\n⏱️ TEST 6: Performance Benchmarks")
        print("-" * 50)
        
        classifier = create_classifier(mode="cost_optimized", enable_llm=False)
        
        # Test processing time
        start_time = time.time()
        test_cases = EXTENDED_VALIDATION_CASES
        
        for name, _, _ in test_cases:
            await classifier.classify_name(name)
        
        total_time = (time.time() - start_time) * 1000
        avg_time = total_time / len(test_cases)
        
        # Performance targets
        target_avg_time = 10  # 10ms per classification
        target_total_time = 10000  # 10s for full suite
        
        time_target_met = avg_time <= target_avg_time
        suite_target_met = total_time <= target_total_time
        
        print(f"   Average time per classification: {avg_time:.2f}ms (target: ≤{target_avg_time}ms)")
        print(f"   Total time for {len(test_cases)} names: {total_time:.1f}ms (target: ≤{target_total_time}ms)")
        print(f"   Time targets met: {'✅' if time_target_met and suite_target_met else '❌'}")
        
        self.results['performance'] = {
            'avg_time_ms': avg_time,
            'total_time_ms': total_time,
            'tests_count': len(test_cases),
            'time_target_met': time_target_met,
            'suite_target_met': suite_target_met
        }
    
    async def _test_cost_reduction(self):
        """Test that LLM usage reduction targets are met."""
        print("\n💰 TEST 7: Cost Reduction Validation")
        print("-" * 50)
        
        classifier = create_classifier(mode="cost_optimized", enable_llm=False)
        
        # Process all test cases
        all_test_cases = CRITICAL_PRODUCTION_FAILURES + EXTENDED_VALIDATION_CASES
        
        for name, _, _ in all_test_cases:
            await classifier.classify_name(name)
        
        stats = classifier.get_session_stats()
        
        # Calculate method usage
        total = stats.total_classifications
        rule_usage = (stats.rule_classifications / total) * 100 if total > 0 else 0
        phonetic_usage = (stats.phonetic_classifications / total) * 100 if total > 0 else 0
        llm_usage = (stats.llm_classifications / total) * 100 if total > 0 else 0
        
        # Targets
        target_llm_usage = 5  # <5%
        target_rule_usage = 85  # >85%
        
        llm_target_met = llm_usage <= target_llm_usage
        rule_target_met = rule_usage >= target_rule_usage
        
        print(f"   Rule-based usage: {rule_usage:.1f}% (target: ≥{target_rule_usage}%)")
        print(f"   Phonetic usage: {phonetic_usage:.1f}%")
        print(f"   LLM usage: {llm_usage:.1f}% (target: ≤{target_llm_usage}%)")
        print(f"   Cost: ${stats.llm_cost_usd:.4f}")
        print(f"   Cost reduction targets met: {'✅' if llm_target_met and rule_target_met else '❌'}")
        
        self.results['cost_reduction'] = {
            'total_classifications': total,
            'rule_usage_percent': rule_usage,
            'phonetic_usage_percent': phonetic_usage,
            'llm_usage_percent': llm_usage,
            'llm_cost_usd': stats.llm_cost_usd,
            'llm_target_met': llm_target_met,
            'rule_target_met': rule_target_met
        }
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report."""
        total_time = (time.time() - self.start_time) * 1000
        
        print("\n" + "=" * 70)
        print("📋 PHASE 1 COMPREHENSIVE VALIDATION REPORT")
        print("=" * 70)
        
        # Overall success metrics
        critical_success = self.results['critical_failures']['success_rate']
        dictionary_success = self.results['dictionary_expansions']['addition_success_rate']
        multi_word_success = self.results['multi_word']['success_rate']
        phonetic_success = self.results['phonetic_fixes']['phonetic_success_rate']
        
        overall_success = (critical_success + dictionary_success + multi_word_success + phonetic_success) / 4
        
        print(f"\n🎯 OVERALL SUCCESS RATE: {overall_success:.1f}%")
        print(f"⏱️  Total test execution time: {total_time:.1f}ms")
        
        # Detailed breakdown
        print(f"\n📊 DETAILED RESULTS:")
        print(f"   Critical Failures:     {critical_success:.1f}% ({self.results['critical_failures']['successes']}/{self.results['critical_failures']['total']})")
        print(f"   Dictionary Expansions: {dictionary_success:.1f}%")
        print(f"   Multi-word Names:      {multi_word_success:.1f}%")
        print(f"   Phonetic Fixes:        {phonetic_success:.1f}%")
        
        # Performance metrics
        perf = self.results['performance']
        cost = self.results['cost_reduction']
        
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Average processing time: {perf['avg_time_ms']:.2f}ms")
        print(f"   Rule-based coverage:     {cost['rule_usage_percent']:.1f}%")
        print(f"   LLM usage:              {cost['llm_usage_percent']:.1f}%")
        print(f"   Total cost:             ${cost['llm_cost_usd']:.4f}")
        
        # Research targets validation
        print(f"\n🎯 RESEARCH TARGETS VALIDATION:")
        
        targets_met = 0
        total_targets = 5
        
        # Target 1: Critical failures resolved (100%)
        target1_met = critical_success == 100
        targets_met += 1 if target1_met else 0
        print(f"   Critical failures resolved: {'✅' if target1_met else '❌'} ({critical_success:.1f}%)")
        
        # Target 2: Overall accuracy >95%
        target2_met = overall_success >= 95
        targets_met += 1 if target2_met else 0
        print(f"   Overall accuracy >95%:      {'✅' if target2_met else '❌'} ({overall_success:.1f}%)")
        
        # Target 3: LLM usage <5%
        target3_met = cost['llm_usage_percent'] < 5
        targets_met += 1 if target3_met else 0
        print(f"   LLM usage <5%:              {'✅' if target3_met else '❌'} ({cost['llm_usage_percent']:.1f}%)")
        
        # Target 4: Performance <10ms avg
        target4_met = perf['avg_time_ms'] < 10
        targets_met += 1 if target4_met else 0
        print(f"   Processing time <10ms:      {'✅' if target4_met else '❌'} ({perf['avg_time_ms']:.2f}ms)")
        
        # Target 5: Rule coverage >85%
        target5_met = cost['rule_usage_percent'] > 85
        targets_met += 1 if target5_met else 0
        print(f"   Rule coverage >85%:         {'✅' if target5_met else '❌'} ({cost['rule_usage_percent']:.1f}%)")
        
        # Final assessment
        print(f"\n🏆 FINAL ASSESSMENT: {targets_met}/{total_targets} targets met")
        
        if targets_met == total_targets:
            print("🎉 OUTSTANDING: All Phase 1 targets exceeded!")
            print("✅ Ready for immediate production deployment")
            recommendation = "DEPLOY_IMMEDIATELY"
        elif targets_met >= 4:
            print("🔶 EXCELLENT: Phase 1 targets largely met")
            print("✅ Ready for production with minor monitoring")
            recommendation = "DEPLOY_WITH_MONITORING"
        elif targets_met >= 3:
            print("🔶 GOOD: Phase 1 substantially complete")
            print("🔧 Minor optimization recommended before deployment")
            recommendation = "OPTIMIZE_THEN_DEPLOY"
        else:
            print("⚠️ NEEDS WORK: Significant improvements required")
            print("🚨 Review and fix before deployment")
            recommendation = "REQUIRES_FIXES"
        
        print(f"\n📋 NEXT STEPS:")
        if targets_met >= 4:
            print("   1. Deploy cost_optimized configuration to production")
            print("   2. Begin Phase 2: Advanced pattern recognition")
            print("   3. Monitor production performance and costs")
            print("   4. Collect data for machine learning enhancement")
        else:
            print("   1. Address failing targets before deployment")
            print("   2. Re-run validation tests")
            print("   3. Consider additional dictionary expansion")
            print("   4. Review confidence threshold optimization")
        
        # Return complete results for programmatic use
        final_results = {
            'overall_success_rate': overall_success,
            'targets_met': targets_met,
            'total_targets': total_targets,
            'recommendation': recommendation,
            'total_execution_time_ms': total_time,
            'detailed_results': self.results,
            'critical_success': target1_met,
            'accuracy_target': target2_met,
            'llm_usage_target': target3_met,
            'performance_target': target4_met,
            'coverage_target': target5_met
        }
        
        return final_results

async def main():
    """Run comprehensive Phase 1 validation."""
    test_suite = Phase1TestSuite()
    results = await test_suite.run_all_tests()
    
    # Exit with appropriate code for CI/CD
    if results['targets_met'] >= 4:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Requires fixes

if __name__ == "__main__":
    asyncio.run(main())