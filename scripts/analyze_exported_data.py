#!/usr/bin/env python3
"""
Comprehensive analysis of exported Excel data and system performance.

This script analyzes all exported Excel files, databases, and logs to provide
detailed insights into system performance and data quality.
"""

import pandas as pd
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List
import numpy as np


def analyze_excel_output(file_path: Path) -> Dict[str, Any]:
    """Comprehensive analysis of exported Excel data."""
    if not file_path.exists():
        return {'error': f'File not found: {file_path}'}
    
    try:
        df = pd.read_excel(file_path)
        
        analysis = {
            'file_info': {
                'path': str(file_path),
                'size_mb': file_path.stat().st_size / (1024 * 1024),
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns)
            },
            'data_quality': {
                'completeness': check_data_completeness(df),
                'null_values': count_null_values(df),
                'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()}
            },
            'classification_analysis': analyze_classifications(df),
            'enhancement_validation': validate_enhancements(df)
        }
        
        return analysis
        
    except Exception as e:
        return {'error': f'Analysis failed: {e}'}


def check_data_completeness(df: pd.DataFrame) -> Dict[str, Any]:
    """Check completeness of critical data fields."""
    required_fields = ['DirectorName', 'EntityName', 'EmailAddress']
    
    completeness = {}
    for field in required_fields:
        if field in df.columns:
            non_null = df[field].notna().sum()
            completeness[field] = {
                'non_null_count': int(non_null),
                'completeness_rate': float(non_null / len(df)),
                'status': 'GOOD' if non_null / len(df) > 0.95 else 'NEEDS_ATTENTION'
            }
        else:
            completeness[field] = {'status': 'MISSING'}
    
    return completeness


def count_null_values(df: pd.DataFrame) -> Dict[str, int]:
    """Count null values in each column."""
    return {col: int(df[col].isna().sum()) for col in df.columns}


def analyze_classifications(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze classification results in the dataset."""
    classification_cols = [col for col in df.columns if 'classification' in col.lower() or 'ethnicity' in col.lower()]
    
    if not classification_cols:
        return {'status': 'NO_CLASSIFICATION_DATA'}
    
    analysis = {
        'total_names_classified': 0,
        'classification_methods': {},
        'ethnicity_distribution': {},
        'confidence_scores': {}
    }
    
    # Look for classification results
    ethnicity_col = None
    method_col = None
    confidence_col = None
    
    for col in df.columns:
        if 'ethnicity' in col.lower():
            ethnicity_col = col
        elif 'method' in col.lower():
            method_col = col
        elif 'confidence' in col.lower():
            confidence_col = col
    
    if ethnicity_col:
        # Count classifications
        classified = df[ethnicity_col].notna()
        analysis['total_names_classified'] = int(classified.sum())
        
        # Ethnicity distribution
        ethnicity_counts = df[ethnicity_col].value_counts()
        analysis['ethnicity_distribution'] = {
            str(k): int(v) for k, v in ethnicity_counts.items()
        }
    
    if method_col:
        # Method breakdown
        method_counts = df[method_col].value_counts()
        analysis['classification_methods'] = {
            str(k): int(v) for k, v in method_counts.items()
        }
    
    if confidence_col:
        # Confidence analysis
        confidences = df[confidence_col].dropna()
        if len(confidences) > 0:
            analysis['confidence_scores'] = {
                'mean': float(confidences.mean()),
                'median': float(confidences.median()),
                'min': float(confidences.min()),
                'max': float(confidences.max()),
                'std': float(confidences.std())
            }
    
    return analysis


def validate_enhancements(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate Enhancement 1 & 2 performance."""
    validation = {
        'rule_hit_rate': 0.0,
        'llm_usage_percentage': 0.0,
        'cost_per_1000_leads': 0.0,
        'enhancement2_cases': {}
    }
    
    # Enhancement 2 test cases
    enhancement2_names = [
        'ANDREAS PETRUS VAN DER MERWE',
        'HEINRICH ADRIAN TIMMIE', 
        'NOMVUYISEKO EUNICE MSINDO',
        'ALLISTER PIETERSEN',
        'MNCEDI NICHOLAS MAJIBANE'
    ]
    
    method_col = None
    for col in df.columns:
        if 'method' in col.lower():
            method_col = col
            break
    
    if method_col:
        # Calculate rule hit rate
        total_classifications = df[method_col].notna().sum()
        rule_based_count = (df[method_col] == 'rule_based').sum()
        
        if total_classifications > 0:
            validation['rule_hit_rate'] = float(rule_based_count / total_classifications)
        
        # Calculate LLM usage
        llm_count = (df[method_col] == 'llm').sum()
        if total_classifications > 0:
            validation['llm_usage_percentage'] = float(llm_count / total_classifications)
        
        # Estimate cost (assuming $0.001 per LLM call)
        validation['cost_per_1000_leads'] = float(llm_count * 1000 * 0.001 / len(df))
        
        # Check Enhancement 2 cases
        for name in enhancement2_names:
            name_rows = df[df['DirectorName'] == name]
            if len(name_rows) > 0:
                method = name_rows[method_col].iloc[0]
                validation['enhancement2_cases'][name] = {
                    'method': str(method),
                    'rule_based': method == 'rule_based'
                }
    
    return validation


def analyze_databases() -> Dict[str, Any]:
    """Analyze all system databases."""
    db_analysis = {}
    
    # Analyze learning database
    learning_db_path = Path("cache/llm_learning.db")
    if learning_db_path.exists():
        db_analysis['learning_database'] = analyze_learning_database(learning_db_path)
    
    # Analyze job database
    job_db_path = Path("cache/job_database.db")
    if job_db_path.exists():
        db_analysis['job_database'] = analyze_job_database(job_db_path)
    
    return db_analysis


def analyze_learning_database(db_path: Path) -> Dict[str, Any]:
    """Analyze learning database contents."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        analysis = {}
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        analysis['tables'] = tables
        
        if 'llm_classifications' in tables:
            # Classification statistics
            cursor.execute("SELECT COUNT(*), AVG(confidence), MIN(confidence), MAX(confidence) FROM llm_classifications")
            count, avg_conf, min_conf, max_conf = cursor.fetchone()
            
            analysis['llm_classifications'] = {
                'total_count': count,
                'avg_confidence': float(avg_conf) if avg_conf else 0,
                'min_confidence': float(min_conf) if min_conf else 0,
                'max_confidence': float(max_conf) if max_conf else 0
            }
            
            # Ethnicity distribution
            cursor.execute("SELECT ethnicity, COUNT(*) FROM llm_classifications GROUP BY ethnicity")
            ethnicity_dist = {row[0]: row[1] for row in cursor.fetchall()}
            analysis['ethnicity_distribution'] = ethnicity_dist
            
            # Provider usage
            cursor.execute("SELECT llm_provider, COUNT(*) FROM llm_classifications GROUP BY llm_provider")
            provider_dist = {row[0]: row[1] for row in cursor.fetchall()}
            analysis['provider_usage'] = provider_dist
        
        if 'learned_patterns' in tables:
            # Pattern statistics
            cursor.execute("SELECT COUNT(*), AVG(confidence_score) FROM learned_patterns")
            pattern_count, avg_pattern_conf = cursor.fetchone()
            
            analysis['learned_patterns'] = {
                'total_count': pattern_count,
                'avg_confidence': float(avg_pattern_conf) if avg_pattern_conf else 0
            }
            
            # Pattern types
            cursor.execute("SELECT pattern_type, COUNT(*) FROM learned_patterns GROUP BY pattern_type")
            pattern_types = {row[0]: row[1] for row in cursor.fetchall()}
            analysis['pattern_types'] = pattern_types
        
        conn.close()
        return analysis
        
    except Exception as e:
        return {'error': f'Learning database analysis failed: {e}'}


def analyze_job_database(db_path: Path) -> Dict[str, Any]:
    """Analyze job database contents."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        analysis = {}
        
        # Job execution statistics
        cursor.execute("SELECT COUNT(*), AVG(processed_leads_count), AVG(processing_time_total_ms) FROM job_executions")
        job_count, avg_leads, avg_time = cursor.fetchone()
        
        analysis['job_executions'] = {
            'total_jobs': job_count,
            'avg_leads_processed': float(avg_leads) if avg_leads else 0,
            'avg_processing_time_ms': float(avg_time) if avg_time else 0
        }
        
        # Job status distribution
        cursor.execute("SELECT status, COUNT(*) FROM job_executions GROUP BY status")
        status_dist = {row[0]: row[1] for row in cursor.fetchall()}
        analysis['job_status_distribution'] = status_dist
        
        conn.close()
        return analysis
        
    except Exception as e:
        return {'error': f'Job database analysis failed: {e}'}


def generate_analysis_report() -> Dict[str, Any]:
    """Generate comprehensive analysis report."""
    print("🔍 Starting Comprehensive Data Analysis")
    print("=" * 50)
    
    report = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'excel_files': {},
        'databases': {},
        'summary': {}
    }
    
    # Analyze Excel outputs
    excel_files = [
        "data/test_runs/core_enrichment_output.xlsx",
        "data/test_runs/baseline_output.xlsx"
    ]
    
    for file_path in excel_files:
        path = Path(file_path)
        if path.exists():
            print(f"📊 Analyzing {path.name}...")
            report['excel_files'][path.name] = analyze_excel_output(path)
        else:
            print(f"⚠️  File not found: {path}")
            report['excel_files'][path.name] = {'status': 'NOT_FOUND'}
    
    # Analyze databases
    print("💾 Analyzing databases...")
    report['databases'] = analyze_databases()
    
    # Generate summary
    report['summary'] = generate_summary(report)
    
    # Save report
    analysis_dir = Path("data/analysis")
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = analysis_dir / "comprehensive_data_analysis.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"💾 Saved analysis report to: {report_path}")
    
    return report


def generate_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary of all analysis results."""
    summary = {
        'data_quality': 'UNKNOWN',
        'enhancement_performance': 'UNKNOWN',
        'learning_effectiveness': 'UNKNOWN',
        'overall_status': 'UNKNOWN'
    }
    
    # Check if we have successful Excel analysis
    successful_files = [
        file_data for file_data in report['excel_files'].values()
        if 'error' not in file_data and 'classification_analysis' in file_data
    ]
    
    if successful_files:
        # Data quality assessment
        file_data = successful_files[0]
        completeness = file_data.get('data_quality', {}).get('completeness', {})
        if all(field.get('status') == 'GOOD' for field in completeness.values() if isinstance(field, dict)):
            summary['data_quality'] = 'EXCELLENT'
        else:
            summary['data_quality'] = 'GOOD'
        
        # Enhancement performance
        enhancement_data = file_data.get('enhancement_validation', {})
        rule_hit_rate = enhancement_data.get('rule_hit_rate', 0)
        enhancement2_success = all(
            case.get('rule_based', False) 
            for case in enhancement_data.get('enhancement2_cases', {}).values()
        )
        
        if rule_hit_rate >= 0.9 and enhancement2_success:
            summary['enhancement_performance'] = 'EXCELLENT'
        elif rule_hit_rate >= 0.8:
            summary['enhancement_performance'] = 'GOOD'
        else:
            summary['enhancement_performance'] = 'NEEDS_IMPROVEMENT'
    
    # Learning effectiveness
    learning_data = report.get('databases', {}).get('learning_database', {})
    if 'llm_classifications' in learning_data and 'learned_patterns' in learning_data:
        classification_count = learning_data['llm_classifications'].get('total_count', 0)
        pattern_count = learning_data['learned_patterns'].get('total_count', 0)
        
        if classification_count > 50 and pattern_count > 100:
            summary['learning_effectiveness'] = 'EXCELLENT'
        elif classification_count > 10 and pattern_count > 20:
            summary['learning_effectiveness'] = 'GOOD'
        else:
            summary['learning_effectiveness'] = 'BASIC'
    
    # Overall status
    statuses = [summary['data_quality'], summary['enhancement_performance'], summary['learning_effectiveness']]
    if all(status == 'EXCELLENT' for status in statuses):
        summary['overall_status'] = 'PRODUCTION_READY'
    elif any(status in ['EXCELLENT', 'GOOD'] for status in statuses):
        summary['overall_status'] = 'STRONG_PERFORMANCE'
    else:
        summary['overall_status'] = 'NEEDS_IMPROVEMENT'
    
    return summary


def main():
    """Main analysis execution."""
    report = generate_analysis_report()
    
    print("\n📋 Analysis Summary:")
    summary = report['summary']
    print(f"  Data Quality: {summary['data_quality']}")
    print(f"  Enhancement Performance: {summary['enhancement_performance']}")
    print(f"  Learning Effectiveness: {summary['learning_effectiveness']}")
    print(f"  Overall Status: {summary['overall_status']}")
    
    return report


if __name__ == "__main__":
    main()