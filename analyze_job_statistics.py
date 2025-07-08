#!/usr/bin/env python3
"""
Job Statistics Analyzer.

Comprehensive analysis of job processing results with learning analytics.
"""

import sqlite3
import json
import pandas as pd
import sys
from pathlib import Path
from collections import defaultdict

def analyze_job_statistics(job_id: str = None):
    """Analyze job statistics and learning effectiveness."""
    
    db_path = Path("cache/jobs.db")
    if not db_path.exists():
        print(f"❌ Job database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    
    try:
        if job_id:
            # Analyze specific job
            analyze_specific_job(conn, job_id)
        else:
            # Analyze all jobs
            analyze_all_jobs(conn)
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
    finally:
        conn.close()
    
    return True

def analyze_specific_job(conn, job_id: str):
    """Analyze a specific job in detail."""
    
    # Get job info
    job_query = """
    SELECT job_id, input_file_path, total_rows, processed_leads_count, 
           status, start_time, completion_time, processing_time_total_ms,
           api_costs_total
    FROM job_executions 
    WHERE job_id = ?
    """
    job_info = pd.read_sql_query(job_query, conn, params=(job_id,))
    
    if job_info.empty:
        print(f"❌ Job not found: {job_id}")
        return
    
    job = job_info.iloc[0]
    
    print(f"📊 Job Analysis: {job_id}")
    print("=" * 60)
    print(f"   Input File: {job['input_file_path']}")
    print(f"   Status: {job['status']}")
    print(f"   Total Leads: {job['total_rows']}")
    print(f"   Processed: {job['processed_leads_count']}")
    print(f"   Processing Time: {job['processing_time_total_ms']/1000:.2f} seconds")
    print(f"   Total API Cost: ${job['api_costs_total']:.4f}")
    
    # Get lead processing results
    results_query = """
    SELECT classification_result, processing_status, processing_time_ms,
           api_provider, api_cost, batch_number
    FROM lead_processing_results 
    WHERE job_id = ?
    """
    results_df = pd.read_sql_query(results_query, conn, params=(job_id,))
    
    if results_df.empty:
        print("❌ No processing results found")
        return
    
    # Parse classification results
    methods = []
    ethnicities = []
    confidences = []
    providers = []
    
    for _, row in results_df.iterrows():
        try:
            if row['classification_result']:
                classification = json.loads(row['classification_result'])
                methods.append(classification.get('method', 'unknown'))
                ethnicities.append(classification.get('ethnicity', 'unknown'))
                confidences.append(classification.get('confidence', 0.0))
            providers.append(row['api_provider'] or 'none')
        except:
            methods.append('error')
            ethnicities.append('error')
            confidences.append(0.0)
    
    # Calculate statistics
    print(f"\n🎯 Classification Methods:")
    method_counts = pd.Series(methods).value_counts()
    total_classifications = len(methods)
    
    for method, count in method_counts.items():
        percentage = count / total_classifications * 100
        print(f"   {method.title()}: {count} ({percentage:.1f}%)")
    
    print(f"\n🌍 Ethnicity Distribution:")
    ethnicity_counts = pd.Series(ethnicities).value_counts()
    for ethnicity, count in ethnicity_counts.items():
        percentage = count / total_classifications * 100
        print(f"   {ethnicity.title()}: {count} ({percentage:.1f}%)")
    
    print(f"\n🔍 Provider Usage:")
    provider_counts = pd.Series(providers).value_counts()
    for provider, count in provider_counts.items():
        percentage = count / len(providers) * 100
        print(f"   {provider.title()}: {count} ({percentage:.1f}%)")
    
    # Performance metrics
    avg_processing_time = results_df['processing_time_ms'].mean()
    total_api_cost = results_df['api_cost'].sum()
    
    print(f"\n⚡ Performance Metrics:")
    print(f"   Average Processing Time: {avg_processing_time:.2f}ms")
    print(f"   Processing Rate: {1000/avg_processing_time:.1f} leads/second")
    print(f"   Total API Cost: ${total_api_cost:.4f}")
    print(f"   Cost per Lead: ${total_api_cost/total_classifications:.6f}")
    
    # Learning effectiveness
    rule_based_count = method_counts.get('rule_based', 0)
    phonetic_count = method_counts.get('phonetic', 0)
    cache_count = method_counts.get('cache', 0)
    llm_count = method_counts.get('llm', 0)
    
    non_llm_count = rule_based_count + phonetic_count + cache_count
    llm_percentage = llm_count / total_classifications * 100
    cost_efficiency = non_llm_count / total_classifications * 100
    
    print(f"\n🧠 Learning Effectiveness:")
    print(f"   Non-LLM Classifications: {non_llm_count} ({cost_efficiency:.1f}%)")
    print(f"   LLM Usage: {llm_count} ({llm_percentage:.1f}%)")
    print(f"   Cost Efficiency: {cost_efficiency:.1f}%")
    
    # Performance targets
    print(f"\n🎯 Performance Targets:")
    print(f"   {'✅' if llm_percentage < 5 else '❌'} LLM Usage < 5%: {llm_percentage:.1f}%")
    print(f"   {'✅' if cost_efficiency > 80 else '❌'} Cost Efficiency > 80%: {cost_efficiency:.1f}%")
    print(f"   {'✅' if avg_processing_time < 100 else '❌'} Processing < 100ms: {avg_processing_time:.1f}ms")

def analyze_all_jobs(conn):
    """Analyze all jobs in the database."""
    
    # Get all jobs
    jobs_query = """
    SELECT job_id, input_file_path, total_rows, processed_leads_count, 
           status, start_time, completion_time, processing_time_total_ms,
           api_costs_total
    FROM job_executions 
    ORDER BY start_time DESC
    """
    jobs_df = pd.read_sql_query(jobs_query, conn)
    
    if jobs_df.empty:
        print("❌ No jobs found in database")
        return
    
    print(f"📊 All Jobs Analysis")
    print("=" * 60)
    print(f"   Total Jobs: {len(jobs_df)}")
    
    # Job status breakdown
    status_counts = jobs_df['status'].value_counts()
    print(f"\n📋 Job Status:")
    for status, count in status_counts.items():
        print(f"   {status.title()}: {count}")
    
    # Completed jobs analysis
    completed_jobs = jobs_df[jobs_df['status'] == 'completed']
    
    if not completed_jobs.empty:
        total_leads = completed_jobs['processed_leads_count'].sum()
        total_time = completed_jobs['processing_time_total_ms'].sum() / 1000
        total_cost = completed_jobs['api_costs_total'].sum()
        
        print(f"\n📈 Completed Jobs Summary:")
        print(f"   Total Leads Processed: {total_leads:,}")
        print(f"   Total Processing Time: {total_time:.2f} seconds")
        print(f"   Average Processing Rate: {total_leads/total_time:.1f} leads/second")
        print(f"   Total API Costs: ${total_cost:.4f}")
        print(f"   Average Cost per Lead: ${total_cost/total_leads:.6f}")
        
        # Show recent jobs
        print(f"\n📝 Recent Jobs:")
        for _, job in completed_jobs.head(5).iterrows():
            processing_time = job['processing_time_total_ms'] / 1000
            rate = job['processed_leads_count'] / processing_time if processing_time > 0 else 0
            print(f"   {job['job_id'][:8]}... | {job['processed_leads_count']:4d} leads | "
                  f"{rate:6.1f} leads/sec | ${job['api_costs_total']:.4f}")

def analyze_learning_database():
    """Analyze the learning database patterns."""
    
    learning_db_path = Path("cache/llm_learning.db")
    if not learning_db_path.exists():
        print(f"❌ Learning database not found: {learning_db_path}")
        return
    
    conn = sqlite3.connect(learning_db_path)
    
    try:
        print(f"\n🧠 Learning Database Analysis")
        print("=" * 60)
        
        # Classification counts
        classifications_query = "SELECT COUNT(*) as count FROM llm_classifications"
        classifications_count = pd.read_sql_query(classifications_query, conn).iloc[0]['count']
        
        # Pattern counts
        patterns_query = "SELECT COUNT(*) as count FROM learned_patterns"
        patterns_count = pd.read_sql_query(patterns_query, conn).iloc[0]['count']
        
        print(f"   Total LLM Classifications: {classifications_count}")
        print(f"   Generated Patterns: {patterns_count}")
        
        if classifications_count > 0:
            learning_efficiency = patterns_count / classifications_count
            print(f"   Learning Efficiency: {learning_efficiency:.2f} patterns per LLM call")
        
        # Ethnicity distribution in learning database
        ethnicity_query = "SELECT ethnicity, COUNT(*) as count FROM llm_classifications GROUP BY ethnicity"
        ethnicity_df = pd.read_sql_query(ethnicity_query, conn)
        
        if not ethnicity_df.empty:
            print(f"\n🌍 Learning Database Ethnicities:")
            for _, row in ethnicity_df.iterrows():
                print(f"   {row['ethnicity'].title()}: {row['count']}")
        
        # Pattern types
        pattern_types_query = "SELECT pattern_type, COUNT(*) as count FROM learned_patterns GROUP BY pattern_type"
        pattern_types_df = pd.read_sql_query(pattern_types_query, conn)
        
        if not pattern_types_df.empty:
            print(f"\n🔍 Pattern Types:")
            for _, row in pattern_types_df.iterrows():
                print(f"   {row['pattern_type'].title()}: {row['count']}")
                
    except Exception as e:
        print(f"❌ Learning analysis failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
        print(f"Analyzing specific job: {job_id}")
        analyze_job_statistics(job_id)
    else:
        print("Analyzing all jobs...")
        analyze_job_statistics()
    
    # Also analyze learning database
    analyze_learning_database()