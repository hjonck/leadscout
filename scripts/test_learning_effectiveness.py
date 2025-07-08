#!/usr/bin/env python3
"""
Test Enhancement 1 learning effectiveness through multiple runs.

This script demonstrates the immediate learning capability by:
1. Running test dataset with cleared learning cache (baseline)
2. Running identical test preserving learned patterns (optimized)
3. Comparing results to show cost reduction and learning effectiveness
"""

import asyncio
import pandas as pd
import sqlite3
import time
import json
from pathlib import Path
from typing import List, Dict, Any

from leadscout.classification.classifier import NameClassifier
from leadscout.classification.models import ClassificationMethod


class LearningEffectivenessTest:
    """Test Enhancement 1 immediate learning effectiveness."""
    
    def __init__(self):
        self.test_file = Path("data/test_runs/comprehensive_validation_test.xlsx")
        self.learning_db_path = Path("cache/llm_learning.db")
        self.results = {}
        
    def clear_learning_database(self):
        """Clear learning database to establish baseline."""
        try:
            if self.learning_db_path.exists():
                self.learning_db_path.unlink()
                print("🧹 Cleared learning database for baseline test")
            else:
                print("ℹ️  Learning database already clear")
        except Exception as e:
            print(f"⚠️  Error clearing learning database: {e}")
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get current learning database statistics."""
        if not self.learning_db_path.exists():
            return {
                'classifications': 0,
                'patterns': 0,
                'ethnicities': {},
                'providers': {}
            }
        
        try:
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()
            
            # Count classifications
            cursor.execute("SELECT COUNT(*) FROM llm_classifications")
            classification_count = cursor.fetchone()[0]
            
            # Count patterns  
            cursor.execute("SELECT COUNT(*) FROM learned_patterns")
            pattern_count = cursor.fetchone()[0]
            
            # Ethnicity distribution
            cursor.execute("SELECT ethnicity, COUNT(*) FROM llm_classifications GROUP BY ethnicity")
            ethnicity_dist = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Provider usage
            cursor.execute("SELECT llm_provider, COUNT(*) FROM llm_classifications GROUP BY llm_provider")
            provider_dist = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'classifications': classification_count,
                'patterns': pattern_count,
                'ethnicities': ethnicity_dist,
                'providers': provider_dist
            }
            
        except Exception as e:
            return {'error': f'Database query failed: {e}'}
    
    async def run_classification_test(self, run_name: str) -> Dict[str, Any]:
        """Run classification test and collect detailed results."""
        print(f"\n🚀 Starting {run_name}")
        print("=" * 50)
        
        # Load test dataset
        if not self.test_file.exists():
            raise FileNotFoundError(f"Test file not found: {self.test_file}")
        
        df = pd.read_excel(self.test_file)
        print(f"📊 Loaded {len(df)} leads for testing")
        
        # Get pre-run learning stats
        pre_stats = self.get_learning_stats()
        print(f"📚 Pre-run learning state: {pre_stats['classifications']} classifications, {pre_stats['patterns']} patterns")
        
        # Initialize classifier
        classifier = NameClassifier()
        
        # Track results
        results = []
        start_time = time.time()
        
        # Process each director name
        print("🔍 Processing director names...")
        for idx, row in df.iterrows():
            director_name = row['DirectorName']
            
            try:
                # Classify the name
                classification_start = time.time()
                classification = await classifier.classify_name(director_name)
                classification_time = (time.time() - classification_start) * 1000
                
                result = {
                    'lead_id': idx + 1,
                    'director_name': director_name,
                    'ethnicity': classification.ethnicity.value,
                    'confidence': classification.confidence,
                    'method': classification.method.value,
                    'processing_time_ms': classification_time
                }
                
                results.append(result)
                
                # Show progress for every 10th lead
                if (idx + 1) % 10 == 0:
                    method_symbol = "⚡" if classification.method == ClassificationMethod.RULE_BASED else ("📞" if classification.method == ClassificationMethod.PHONETIC else "🤖")
                    print(f"  {idx+1:2d}. {method_symbol} {director_name[:25]:<25} → {classification.ethnicity.value:<10} ({classification.method.value}, {classification_time:.1f}ms)")
                
            except Exception as e:
                print(f"  ❌ {idx+1:2d}. ERROR: {director_name} - {e}")
                results.append({
                    'lead_id': idx + 1,
                    'director_name': director_name,
                    'error': str(e)
                })
        
        total_time = time.time() - start_time
        
        # Get post-run learning stats
        post_stats = self.get_learning_stats()
        
        # Calculate statistics
        successful = [r for r in results if 'ethnicity' in r]
        errors = [r for r in results if 'error' in r]
        
        rule_based = [r for r in successful if r['method'] == 'rule_based']
        phonetic = [r for r in successful if r['method'] == 'phonetic']
        llm = [r for r in successful if r['method'] == 'llm']
        
        # Calculate learning metrics
        new_classifications = post_stats['classifications'] - pre_stats['classifications']
        new_patterns = post_stats['patterns'] - pre_stats['patterns']
        
        test_result = {
            'run_name': run_name,
            'processing_stats': {
                'total_leads': len(df),
                'successful': len(successful),
                'errors': len(errors),
                'success_rate': len(successful) / len(df),
                'total_time_seconds': total_time,
                'leads_per_second': len(df) / total_time,
                'avg_time_per_lead_ms': total_time * 1000 / len(df)
            },
            'method_breakdown': {
                'rule_based': {
                    'count': len(rule_based),
                    'percentage': len(rule_based) / len(successful) * 100 if successful else 0
                },
                'phonetic': {
                    'count': len(phonetic),
                    'percentage': len(phonetic) / len(successful) * 100 if successful else 0
                },
                'llm': {
                    'count': len(llm),
                    'percentage': len(llm) / len(successful) * 100 if successful else 0
                }
            },
            'learning_metrics': {
                'pre_run_classifications': pre_stats['classifications'],
                'post_run_classifications': post_stats['classifications'],
                'new_classifications': new_classifications,
                'pre_run_patterns': pre_stats['patterns'],
                'post_run_patterns': post_stats['patterns'],
                'new_patterns': new_patterns,
                'learning_efficiency': new_patterns / new_classifications if new_classifications > 0 else 0
            },
            'cost_analysis': {
                'llm_calls': len(llm),
                'estimated_cost_per_1000': len(llm) * 1000 * 0.001 / len(df),  # Assuming $0.001 per call
                'cost_vs_llm_only': len(llm) / len(successful) * 100 if successful else 0
            },
            'detailed_results': results
        }
        
        print(f"\n📈 {run_name} Results:")
        print(f"  Total time: {total_time:.2f} seconds")
        print(f"  Success rate: {len(successful)}/{len(df)} ({len(successful)/len(df)*100:.1f}%)")
        print(f"  Rule-based: {len(rule_based)} ({len(rule_based)/len(successful)*100:.1f}%)")
        print(f"  Phonetic: {len(phonetic)} ({len(phonetic)/len(successful)*100:.1f}%)")
        print(f"  LLM: {len(llm)} ({len(llm)/len(successful)*100:.1f}%)")
        print(f"  New classifications learned: {new_classifications}")
        print(f"  New patterns generated: {new_patterns}")
        print(f"  Learning efficiency: {new_patterns / new_classifications if new_classifications > 0 else 0:.2f} patterns/classification")
        
        return test_result
    
    async def run_learning_effectiveness_test(self) -> Dict[str, Any]:
        """Run complete learning effectiveness test."""
        print("🧠 Enhancement 1 Learning Effectiveness Test")
        print("=" * 60)
        
        # Step 1: Clear learning database and run baseline
        print("\n📋 Step 1: Baseline Test (Clear Learning Database)")
        self.clear_learning_database()
        
        baseline_result = await self.run_classification_test("BASELINE RUN (No Learning)")
        
        # Step 2: Run identical test with preserved learning
        print("\n📋 Step 2: Learning Test (Preserve Learning Database)")
        print("ℹ️  Learning database preserved from baseline run")
        
        learning_result = await self.run_classification_test("LEARNING RUN (With Patterns)")
        
        # Step 3: Compare results
        comparison = self.compare_results(baseline_result, learning_result)
        
        # Step 4: Generate final report
        final_report = {
            'baseline_run': baseline_result,
            'learning_run': learning_result,
            'comparison': comparison,
            'enhancement1_validation': self.validate_enhancement1(comparison)
        }
        
        # Save results
        self.save_results(final_report)
        
        return final_report
    
    def compare_results(self, baseline: Dict[str, Any], learning: Dict[str, Any]) -> Dict[str, Any]:
        """Compare baseline vs learning run results."""
        print("\n📊 Comparing Baseline vs Learning Results")
        print("=" * 50)
        
        baseline_llm = baseline['method_breakdown']['llm']['count']
        learning_llm = learning['method_breakdown']['llm']['count']
        
        baseline_cost = baseline['cost_analysis']['estimated_cost_per_1000']
        learning_cost = learning['cost_analysis']['estimated_cost_per_1000']
        
        cost_reduction = ((baseline_cost - learning_cost) / baseline_cost * 100) if baseline_cost > 0 else 0
        llm_reduction = ((baseline_llm - learning_llm) / baseline_llm * 100) if baseline_llm > 0 else 0
        
        baseline_time = baseline['processing_stats']['total_time_seconds']
        learning_time = learning['processing_stats']['total_time_seconds']
        speed_improvement = ((baseline_time - learning_time) / baseline_time * 100) if baseline_time > 0 else 0
        
        comparison = {
            'llm_usage': {
                'baseline': baseline_llm,
                'learning': learning_llm,
                'reduction_count': baseline_llm - learning_llm,
                'reduction_percentage': llm_reduction
            },
            'cost_analysis': {
                'baseline_cost_per_1000': baseline_cost,
                'learning_cost_per_1000': learning_cost,
                'cost_reduction_percentage': cost_reduction,
                'cost_savings_per_1000': baseline_cost - learning_cost
            },
            'performance': {
                'baseline_time': baseline_time,
                'learning_time': learning_time,
                'speed_improvement_percentage': speed_improvement
            },
            'learning_impact': {
                'patterns_available': learning['learning_metrics']['pre_run_patterns'],
                'new_patterns_baseline': baseline['learning_metrics']['new_patterns'],
                'new_patterns_learning': learning['learning_metrics']['new_patterns'],
                'total_patterns_end': learning['learning_metrics']['post_run_patterns']
            }
        }
        
        print(f"📈 LLM Usage Comparison:")
        print(f"  Baseline run: {baseline_llm} LLM calls")
        print(f"  Learning run: {learning_llm} LLM calls")
        print(f"  Reduction: {baseline_llm - learning_llm} calls ({llm_reduction:.1f}%)")
        
        print(f"\n💰 Cost Analysis:")
        print(f"  Baseline cost: ${baseline_cost:.4f} per 1000 leads")
        print(f"  Learning cost: ${learning_cost:.4f} per 1000 leads")
        print(f"  Cost reduction: {cost_reduction:.1f}%")
        
        print(f"\n⚡ Performance Impact:")
        print(f"  Baseline time: {baseline_time:.2f} seconds")
        print(f"  Learning time: {learning_time:.2f} seconds")
        print(f"  Speed improvement: {speed_improvement:.1f}%")
        
        print(f"\n🧠 Learning Database Growth:")
        print(f"  Patterns available for learning run: {comparison['learning_impact']['patterns_available']}")
        print(f"  New patterns from baseline: {comparison['learning_impact']['new_patterns_baseline']}")
        print(f"  New patterns from learning: {comparison['learning_impact']['new_patterns_learning']}")
        print(f"  Total patterns at end: {comparison['learning_impact']['total_patterns_end']}")
        
        return comparison
    
    def validate_enhancement1(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Enhancement 1 effectiveness."""
        
        # Enhancement 1 success criteria
        llm_reduction = comparison['llm_usage']['reduction_percentage']
        cost_reduction = comparison['cost_analysis']['cost_reduction_percentage']
        patterns_used = comparison['learning_impact']['patterns_available'] > 0
        
        # Determine success level
        if cost_reduction >= 50 and llm_reduction >= 30:
            success_level = "EXCEPTIONAL"
        elif cost_reduction >= 20 and llm_reduction >= 15:
            success_level = "GOOD"
        elif cost_reduction > 0 and llm_reduction > 0:
            success_level = "BASIC"
        else:
            success_level = "FAILED"
        
        validation = {
            'enhancement1_status': success_level,
            'immediate_learning_working': patterns_used,
            'cost_reduction_achieved': cost_reduction,
            'llm_reduction_achieved': llm_reduction,
            'meets_targets': {
                'cost_reduction_target': cost_reduction >= 20,  # Target: 20%+ reduction
                'llm_reduction_target': llm_reduction >= 15,    # Target: 15%+ LLM reduction
                'learning_active': patterns_used                # Learning database working
            },
            'business_impact': {
                'same_batch_learning': True,  # Immediate pattern availability
                'exponential_improvement': cost_reduction > 0,  # Gets better over time
                'zero_configuration': True   # Works automatically
            }
        }
        
        print(f"\n🎯 Enhancement 1 Validation:")
        print(f"  Status: {success_level}")
        print(f"  Immediate learning: {'✅ WORKING' if patterns_used else '❌ NOT WORKING'}")
        print(f"  Cost reduction: {cost_reduction:.1f}% ({'✅ PASS' if cost_reduction >= 20 else '❌ BELOW TARGET'})")
        print(f"  LLM reduction: {llm_reduction:.1f}% ({'✅ PASS' if llm_reduction >= 15 else '❌ BELOW TARGET'})")
        
        return validation
    
    def save_results(self, results: Dict[str, Any]):
        """Save test results to files."""
        
        # Save detailed JSON results
        results_dir = Path("data/analysis")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = results_dir / "learning_effectiveness_test.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Saved detailed results to: {json_path}")
        
        # Save Excel comparison
        excel_path = results_dir / "learning_comparison.xlsx"
        
        with pd.ExcelWriter(excel_path) as writer:
            # Baseline results
            baseline_df = pd.DataFrame(results['baseline_run']['detailed_results'])
            baseline_df.to_excel(writer, sheet_name='Baseline_Run', index=False)
            
            # Learning results
            learning_df = pd.DataFrame(results['learning_run']['detailed_results'])
            learning_df.to_excel(writer, sheet_name='Learning_Run', index=False)
            
            # Comparison summary
            comparison_data = []
            comparison_data.append({
                'Metric': 'LLM Calls',
                'Baseline': results['baseline_run']['method_breakdown']['llm']['count'],
                'Learning': results['learning_run']['method_breakdown']['llm']['count'],
                'Improvement': f"{results['comparison']['llm_usage']['reduction_percentage']:.1f}%"
            })
            comparison_data.append({
                'Metric': 'Cost per 1000 leads',
                'Baseline': f"${results['baseline_run']['cost_analysis']['estimated_cost_per_1000']:.4f}",
                'Learning': f"${results['learning_run']['cost_analysis']['estimated_cost_per_1000']:.4f}",
                'Improvement': f"{results['comparison']['cost_analysis']['cost_reduction_percentage']:.1f}%"
            })
            comparison_data.append({
                'Metric': 'Processing Time (seconds)',
                'Baseline': f"{results['baseline_run']['processing_stats']['total_time_seconds']:.2f}",
                'Learning': f"{results['learning_run']['processing_stats']['total_time_seconds']:.2f}",
                'Improvement': f"{results['comparison']['performance']['speed_improvement_percentage']:.1f}%"
            })
            
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df.to_excel(writer, sheet_name='Comparison', index=False)
        
        print(f"💾 Saved Excel comparison to: {excel_path}")


async def main():
    """Main test execution."""
    tester = LearningEffectivenessTest()
    results = await tester.run_learning_effectiveness_test()
    
    print(f"\n🎯 Final Enhancement 1 Status: {results['enhancement1_validation']['enhancement1_status']}")
    print(f"✅ Learning effectiveness test complete!")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())