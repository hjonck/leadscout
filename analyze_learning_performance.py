"""
Analyze learning database performance and patterns.

Shows what the system has learned and cost optimization achieved.
Provides detailed insights into the auto-improvement system performance.

Developer B - Classification & Enrichment Specialist
"""

from src.leadscout.classification.learning_database import LLMLearningDatabase
import sqlite3
import json
from datetime import datetime, timedelta

def analyze_learning_performance():
    """Analyze learning database performance."""
    
    print("🧠 LEARNING DATABASE PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    learning_db = LLMLearningDatabase()
    stats = learning_db.get_learning_statistics()
    
    print(f"📊 Overall Statistics:")
    print(f"  Total LLM Classifications Stored: {stats.get('total_llm_classifications', 0)}")
    print(f"  Active Learned Patterns: {stats.get('active_learned_patterns', 0)}")
    print(f"  Phonetic Families: {stats.get('phonetic_families', 0)}")
    print(f"  Learning Efficiency: {stats.get('learning_efficiency', 0):.3f} patterns/LLM call")
    
    if 'recent_30_days' in stats:
        recent = stats['recent_30_days']
        print(f"\n📈 Recent Performance (30 days):")
        print(f"  Classifications: {recent.get('total_classifications', 0)}")
        print(f"  Average Confidence: {recent.get('average_confidence', 0):.2f}")
        print(f"  Total Cost: ${recent.get('total_cost_usd', 0):.4f}")
    
    # Detailed database analysis
    try:
        with sqlite3.connect(learning_db.db_path) as conn:
            # Get ethnicity distribution
            ethnicity_dist = conn.execute('''
                SELECT ethnicity, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM llm_classifications 
                GROUP BY ethnicity 
                ORDER BY count DESC
            ''').fetchall()
            
            if ethnicity_dist:
                print(f"\n🏷️ Ethnicity Distribution in Learning Database:")
                for ethnicity, count, avg_conf in ethnicity_dist:
                    print(f"  {ethnicity}: {count} classifications (avg confidence: {avg_conf:.2f})")
            
            # Get linguistic pattern breakdown
            pattern_breakdown = conn.execute('''
                SELECT pattern_type, pattern_value, target_ethnicity, confidence_score, evidence_count
                FROM learned_patterns 
                WHERE is_active = true 
                ORDER BY evidence_count DESC, confidence_score DESC
                LIMIT 10
            ''').fetchall()
            
            if pattern_breakdown:
                print(f"\n🔍 Top Learned Patterns:")
                for pattern_type, pattern_value, ethnicity, confidence, evidence in pattern_breakdown:
                    print(f"  {pattern_type}: '{pattern_value}' → {ethnicity} "
                          f"(confidence: {confidence:.2f}, evidence: {evidence})")
            
            # Get phonetic families analysis
            phonetic_families = conn.execute('''
                SELECT ethnicity, COUNT(*) as family_count, 
                       AVG(confidence) as avg_confidence,
                       AVG(member_count) as avg_size
                FROM phonetic_families 
                GROUP BY ethnicity 
                ORDER BY family_count DESC
            ''').fetchall()
            
            if phonetic_families:
                print(f"\n🔊 Phonetic Families by Ethnicity:")
                for ethnicity, family_count, avg_conf, avg_size in phonetic_families:
                    print(f"  {ethnicity}: {family_count} families "
                          f"(avg confidence: {avg_conf:.2f}, avg size: {avg_size:.1f})")
            
            # Get recent learning trends
            recent_learning = conn.execute('''
                SELECT DATE(classification_timestamp) as date, 
                       COUNT(*) as daily_count,
                       AVG(confidence) as avg_confidence,
                       SUM(cost_usd) as daily_cost
                FROM llm_classifications 
                WHERE classification_timestamp > datetime('now', '-7 days')
                GROUP BY DATE(classification_timestamp)
                ORDER BY date DESC
            ''').fetchall()
            
            if recent_learning:
                print(f"\n📅 Recent Learning Activity (Last 7 Days):")
                for date, count, avg_conf, cost in recent_learning:
                    print(f"  {date}: {count} classifications "
                          f"(avg confidence: {avg_conf:.2f}, cost: ${cost:.4f})")
            
            # Sample learned names for each ethnicity
            sample_names = conn.execute('''
                SELECT ethnicity, name, confidence, llm_provider
                FROM llm_classifications 
                WHERE confidence > 0.8
                GROUP BY ethnicity
                HAVING COUNT(*) > 0
                ORDER BY confidence DESC
            ''').fetchall()
            
            if sample_names:
                print(f"\n👥 Sample High-Confidence Learned Names:")
                for ethnicity, name, confidence, provider in sample_names:
                    print(f"  {ethnicity}: '{name}' "
                          f"(confidence: {confidence:.2f}, provider: {provider})")
    
    except Exception as e:
        print(f"\n⚠️ Error accessing detailed database information: {e}")
    
    # Cost optimization potential
    total_llm = stats.get('total_llm_classifications', 0)
    patterns = stats.get('active_learned_patterns', 0)
    families = stats.get('phonetic_families', 0)
    
    if total_llm > 0:
        avg_llm_cost = 0.002  # Estimated average LLM cost per classification
        potential_savings = total_llm * avg_llm_cost
        learning_investment = total_llm * avg_llm_cost  # One-time learning cost
        
        print(f"\n💰 Cost Optimization Analysis:")
        print(f"  Learning Investment (one-time): ${learning_investment:.4f}")
        print(f"  Potential Future Savings per 1000 classifications:")
        
        # Calculate savings based on pattern coverage
        if patterns > 0:
            coverage_rate = min(0.8, patterns / 100)  # Max 80% coverage
            savings_per_1000 = 1000 * avg_llm_cost * coverage_rate
            print(f"    Pattern-based savings: ${savings_per_1000:.2f} ({coverage_rate:.1%} coverage)")
        
        if families > 0:
            phonetic_coverage = min(0.6, families / 50)  # Max 60% phonetic coverage
            phonetic_savings = 1000 * avg_llm_cost * phonetic_coverage
            print(f"    Phonetic family savings: ${phonetic_savings:.2f} ({phonetic_coverage:.1%} coverage)")
        
        total_coverage = min(0.9, (patterns + families) / 150)  # Max 90% total coverage
        total_savings = 1000 * avg_llm_cost * total_coverage
        print(f"    Total estimated savings: ${total_savings:.2f} ({total_coverage:.1%} coverage)")
        
        # ROI calculation
        if total_savings > 0:
            classifications_to_break_even = learning_investment / (avg_llm_cost * total_coverage)
            print(f"  Break-even point: {classifications_to_break_even:.0f} future classifications")
    
    # Learning system health assessment
    print(f"\n🏥 Learning System Health Assessment:")
    health_score = 0
    max_score = 5
    
    # 1. Learning volume
    if total_llm >= 10:
        print(f"  ✅ Learning Volume: Sufficient ({total_llm} classifications)")
        health_score += 1
    else:
        print(f"  ⚠️ Learning Volume: Needs more data ({total_llm} classifications)")
    
    # 2. Pattern diversity
    if patterns >= 5:
        print(f"  ✅ Pattern Diversity: Good ({patterns} patterns)")
        health_score += 1
    else:
        print(f"  ⚠️ Pattern Diversity: Limited ({patterns} patterns)")
    
    # 3. Phonetic coverage
    if families >= 3:
        print(f"  ✅ Phonetic Coverage: Good ({families} families)")
        health_score += 1
    else:
        print(f"  ⚠️ Phonetic Coverage: Limited ({families} families)")
    
    # 4. Learning efficiency
    efficiency = stats.get('learning_efficiency', 0)
    if efficiency >= 0.5:
        print(f"  ✅ Learning Efficiency: Excellent ({efficiency:.3f})")
        health_score += 1
    elif efficiency >= 0.2:
        print(f"  ⚠️ Learning Efficiency: Moderate ({efficiency:.3f})")
        health_score += 0.5
    else:
        print(f"  ❌ Learning Efficiency: Poor ({efficiency:.3f})")
    
    # 5. Data freshness
    if 'recent_30_days' in stats and stats['recent_30_days']['total_classifications'] > 0:
        print(f"  ✅ Data Freshness: Active learning")
        health_score += 1
    else:
        print(f"  ⚠️ Data Freshness: No recent learning activity")
    
    health_percentage = (health_score / max_score) * 100
    health_status = "🟢 Excellent" if health_percentage >= 80 else "🟡 Good" if health_percentage >= 60 else "🔴 Needs Attention"
    
    print(f"\n  Overall Health Score: {health_score:.1f}/{max_score} ({health_percentage:.0f}%) - {health_status}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if total_llm < 20:
        print(f"  • Process more diverse names to build learning database")
    if patterns < 10:
        print(f"  • Focus on names with clear linguistic patterns")
    if families < 5:
        print(f"  • Process more phonetically similar names")
    if efficiency < 0.3:
        print(f"  • Review pattern extraction algorithms for better efficiency")
    
    return {
        'total_llm_classifications': total_llm,
        'active_patterns': patterns,
        'phonetic_families': families,
        'learning_efficiency': efficiency,
        'health_score': health_score,
        'health_percentage': health_percentage
    }

if __name__ == "__main__":
    analyze_learning_performance()