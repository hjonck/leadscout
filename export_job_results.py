#!/usr/bin/env python3
"""
Quick job results exporter.

Export processed lead data from the job database to Excel format.
Provides standalone job data export when CLI interface is not preferred.

Key Features:
- Direct SQLite database access
- JSON classification parsing  
- Excel format output with statistics
- Comprehensive error handling

Usage:
    python export_job_results.py <job_id> [output_path]
    
When to use:
- Quick manual exports outside of CLI workflow
- Custom export processing or formatting
- Integration with external tools
- Direct database access needs

Alternative: Use `poetry run leadscout jobs export <job-id>` for CLI interface
"""

import sqlite3
import pandas as pd
import json
import sys
from pathlib import Path

def export_job_results(job_id: str, output_path: str = None):
    """Export job results to Excel file."""
    
    if not output_path:
        output_path = f"data/output/job_{job_id[:8]}_results.xlsx"
    
    # Connect to job database
    db_path = Path("cache/jobs.db")
    if not db_path.exists():
        print(f"❌ Job database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Get job info
        job_query = """
        SELECT job_id, input_file_path, total_rows, processed_leads_count, 
               status, start_time, completion_time, processing_time_total_ms
        FROM job_executions 
        WHERE job_id = ?
        """
        job_info = pd.read_sql_query(job_query, conn, params=(job_id,))
        
        if job_info.empty:
            print(f"❌ Job not found: {job_id}")
            return False
        
        print(f"📊 Exporting job: {job_id}")
        print(f"   Input file: {job_info.iloc[0]['input_file_path']}")
        print(f"   Status: {job_info.iloc[0]['status']}")
        print(f"   Processed: {job_info.iloc[0]['processed_leads_count']} leads")
        
        # Get lead processing results
        results_query = """
        SELECT row_index, batch_number, entity_name, director_name,
               classification_result, processing_status, processing_time_ms,
               api_provider, api_cost, created_at
        FROM lead_processing_results 
        WHERE job_id = ?
        ORDER BY row_index
        """
        results_df = pd.read_sql_query(results_query, conn, params=(job_id,))
        
        print(f"   Retrieved: {len(results_df)} result records")
        
        # Parse classification results and expand columns
        enriched_data = []
        
        for _, row in results_df.iterrows():
            try:
                # Parse classification JSON
                classification_data = json.loads(row['classification_result']) if row['classification_result'] else {}
                
                # Create enriched row
                enriched_row = {
                    'row_index': row['row_index'],
                    'batch_number': row['batch_number'],
                    'entity_name': row['entity_name'],
                    'director_name': row['director_name'],
                    'ethnicity_classification': classification_data.get('ethnicity', 'unknown'),
                    'classification_confidence': classification_data.get('confidence', 0.0),
                    'classification_method': classification_data.get('method', 'unknown'),
                    'processing_status': row['processing_status'],
                    'processing_time_ms': row['processing_time_ms'],
                    'api_provider': row['api_provider'],
                    'api_cost': row['api_cost'] or 0.0,
                    'processed_at': row['created_at']
                }
                
                # Add any additional fields from classification
                for key, value in classification_data.items():
                    if key not in ['ethnicity', 'confidence', 'method']:
                        enriched_row[f'classification_{key}'] = value
                
                enriched_data.append(enriched_row)
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: Failed to parse classification for row {row['row_index']}: {e}")
                # Add basic row without classification details
                enriched_data.append({
                    'row_index': row['row_index'],
                    'entity_name': row['entity_name'],
                    'director_name': row['director_name'],
                    'processing_status': 'parse_error',
                    'error': str(e)
                })
        
        # Create DataFrame and save
        export_df = pd.DataFrame(enriched_data)
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to Excel
        export_df.to_excel(output_path, index=False)
        
        print(f"💾 Exported to: {output_path}")
        
        # Show summary statistics
        print(f"\n📈 Export Summary:")
        print(f"   Total records: {len(export_df)}")
        
        if 'ethnicity_classification' in export_df.columns:
            print(f"   Ethnicity breakdown:")
            ethnicity_counts = export_df['ethnicity_classification'].value_counts()
            for ethnicity, count in ethnicity_counts.items():
                print(f"     {ethnicity}: {count}")
        
        if 'classification_method' in export_df.columns:
            print(f"   Method breakdown:")
            method_counts = export_df['classification_method'].value_counts()
            for method, count in method_counts.items():
                print(f"     {method}: {count}")
        
        if 'api_cost' in export_df.columns:
            total_cost = export_df['api_cost'].sum()
            print(f"   Total API cost: ${total_cost:.4f}")
        
        print(f"✅ Export completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_job_results.py <job_id> [output_path]")
        sys.exit(1)
    
    job_id = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    export_job_results(job_id, output_path)