# LeadScout Utility Scripts Reference

**Purpose**: Documentation of utility scripts developed for data management, analysis, and system operations.

These scripts provide essential functionality for dataset creation, job analysis, and system maintenance. Future sessions can use this documentation to enhance or modify these tools.

## 📁 **Script Inventory**

### **1. export_job_results.py**
**Location**: `/Users/hjonck/Development/gitprojects/AgileWorksZA/leadscout/export_job_results.py`  
**Purpose**: Export processed job results from SQLite database to Excel format

#### **Functionality**
- Connects to `cache/jobs.db` to retrieve job processing results
- Parses JSON classification results into structured Excel columns
- Generates comprehensive export with enrichment data
- Provides detailed statistics and breakdowns

#### **Usage**
```bash
# Export specific job
python export_job_results.py <job-id> [output_path]

# Examples
python export_job_results.py 30cffb88-6446-4412-ab2c-e03c6102bb27 "data/output/western_cape_final.xlsx"
python export_job_results.py abc123  # Auto-generates filename
```

#### **Output Columns**
- `row_index` - Original row position in input file
- `batch_number` - Processing batch identifier
- `entity_name` - Company name
- `director_name` - Director name that was classified
- `ethnicity_classification` - Classified ethnicity
- `classification_confidence` - Confidence score (0.0-1.0)
- `classification_method` - Method used (rule_based, llm, phonetic, cache)
- `processing_status` - Success/failure status
- `processing_time_ms` - Time taken to process
- `api_provider` - Which provider was used
- `api_cost` - Cost of API call
- `processed_at` - Timestamp of processing

#### **Statistics Provided**
- Total records processed
- Ethnicity distribution breakdown
- Method breakdown (rule-based, LLM, phonetic, cache percentages)
- Total API costs
- Success/failure rates

#### **Error Handling**
- Graceful handling of JSON parsing errors
- Missing database/job handling
- Automatic output directory creation

---

### **2. analyze_job_statistics.py**
**Location**: `/Users/hjonck/Development/gitprojects/AgileWorksZA/leadscout/analyze_job_statistics.py`  
**Purpose**: Comprehensive statistical analysis of job performance and learning effectiveness

#### **Functionality**
- **Single Job Analysis**: Detailed breakdown of specific job performance
- **All Jobs Analysis**: Summary statistics across all jobs in database
- **Learning Database Analysis**: Pattern generation and learning effectiveness
- **Performance Target Validation**: Checks against optimization targets

#### **Usage**
```bash
# Analyze specific job
python analyze_job_statistics.py <job-id>

# Analyze all jobs
python analyze_job_statistics.py

# Examples
python analyze_job_statistics.py 30cffb88-6446-4412-ab2c-e03c6102bb27
python analyze_job_statistics.py  # Shows all jobs summary
```

#### **Analysis Categories**

**Job Performance Metrics**:
- Processing speed (leads/second)
- Method breakdown with percentages
- Ethnicity distribution analysis
- Provider usage statistics
- API cost tracking and per-lead costs

**Learning System Analytics**:
- Learning database pattern counts
- Learning efficiency (patterns per LLM call)
- Cache hit rates and effectiveness
- Cost optimization through learning

**Performance Target Validation**:
- ✅/❌ LLM Usage < 5% target
- ✅/❌ Cost Efficiency > 80% target  
- ✅/❌ Processing < 100ms target

#### **Sample Output**
```
📊 Job Analysis: 30cffb88-6446-4412-ab2c-e03c6102bb27
============================================================
   Input File: data/test_runs/transport_logistics_western_cape_test.xlsx
   Status: completed
   Total Leads: 539
   Processing Time: 0.00 seconds
   Total API Cost: $0.0000

🎯 Classification Methods:
   Rule_Based: 204 (37.8%)
   Llm: 169 (31.4%)
   Phonetic: 115 (21.3%)
   Cache: 51 (9.5%)

🧠 Learning Effectiveness:
   Non-LLM Classifications: 370 (68.6%)
   LLM Usage: 169 (31.4%)
   Cost Efficiency: 68.6%

🎯 Performance Targets:
   ❌ LLM Usage < 5%: 31.4%
   ❌ Cost Efficiency > 80%: 68.6%
   ✅ Zero Cost Operation: $0.0000
```

---

### **3. Data Subset Creation (Historical Reference)**
**Purpose**: Document the process used to create the Western Cape transport dataset

#### **Original Dataset Source**
- **File**: `data/growfin/CIPC Data PostDMA 20250702.xlsx`
- **Size**: Large CIPC dataset with companies across South Africa
- **Columns**: EntityName, TradingAsName, DirectorName, Province, Keywords, etc.

#### **Filtering Criteria Applied**
The Western Cape transport dataset was created using these criteria:

**Geographic Filter**:
- `RegisteredAddressProvince == "WESTERN CAPE"`

**Industry Filter**:
- Keywords containing: "TRANSPORT", "LOGISTICS", "FREIGHT", "DELIVERY", "COURIER"
- Case-insensitive matching
- Partial word matching (e.g., "TRANSPORT" matches "TRANSPORTATION")

**Data Quality Filter**:
- Required non-empty `DirectorName` field
- Required non-empty `EntityName` field
- Excluded rows with missing contact information

#### **Creation Process**
```python
# Pseudo-code for dataset creation
import pandas as pd

# Load source data
df = pd.read_excel('data/growfin/CIPC Data PostDMA 20250702.xlsx')

# Apply geographic filter
western_cape = df[df['RegisteredAddressProvince'] == 'WESTERN CAPE']

# Apply industry keywords filter
transport_keywords = ['TRANSPORT', 'LOGISTICS', 'FREIGHT', 'DELIVERY', 'COURIER']
mask = western_cape['Keyword'].str.contains('|'.join(transport_keywords), case=False, na=False)
transport_companies = western_cape[mask]

# Apply data quality filters
quality_filtered = transport_companies[
    (transport_companies['DirectorName'].notna()) & 
    (transport_companies['DirectorName'] != '') &
    (transport_companies['EntityName'].notna()) &
    (transport_companies['EntityName'] != '')
]

# Save subset
quality_filtered.to_excel('data/test_runs/transport_logistics_western_cape_test.xlsx', index=False)
```

#### **Resulting Dataset**
- **Final size**: 539 companies
- **Geographic scope**: Western Cape Province only
- **Industry focus**: Transport and logistics companies
- **Data quality**: 100% complete for required fields

---

## 🔧 **Script Enhancement Guidelines**

### **For Future Development Sessions**

#### **1. Extending export_job_results.py**

**Add New Export Formats**:
```python
# Add to export_job_results.py
def export_to_csv(data, output_path):
    """Export to CSV format."""
    pass

def export_to_json(data, output_path):
    """Export to JSON format."""
    pass

# Usage: python export_job_results.py job-id output.csv --format csv
```

**Add Filtering Options**:
```python
# Add command-line arguments
parser.add_argument('--status', choices=['success', 'failed', 'all'], default='all')
parser.add_argument('--method', choices=['rule_based', 'llm', 'phonetic', 'cache'])
parser.add_argument('--ethnicity', help='Filter by ethnicity')

# Usage: python export_job_results.py job-id --status success --method rule_based
```

#### **2. Extending analyze_job_statistics.py**

**Add Trend Analysis**:
```python
def analyze_trends_over_time():
    """Analyze learning improvement over time."""
    # Compare LLM usage rates across jobs chronologically
    # Show learning effectiveness trends
    # Identify optimal batch sizes
    pass
```

**Add Comparative Analysis**:
```python
def compare_jobs(job_ids):
    """Compare performance between multiple jobs."""
    # Side-by-side comparison
    # Identify best performing configurations
    # Highlight differences in approach
    pass
```

#### **3. Creating New Dataset Subsets**

**Generic Dataset Filtering Script**:
```python
#!/usr/bin/env python3
"""
create_dataset_subset.py - Generic dataset filtering tool

Usage:
    python create_dataset_subset.py input.xlsx output.xlsx \
        --province "WESTERN CAPE" \
        --keywords "TRANSPORT,LOGISTICS" \
        --min-employees 10 \
        --exclude-keywords "SCRAP,WASTE"
"""

import pandas as pd
import argparse

def create_subset(input_file, output_file, filters):
    """Create filtered subset based on criteria."""
    df = pd.read_excel(input_file)
    
    # Apply filters
    if filters.get('province'):
        df = df[df['RegisteredAddressProvince'] == filters['province']]
    
    if filters.get('keywords'):
        keywords = filters['keywords'].split(',')
        mask = df['Keyword'].str.contains('|'.join(keywords), case=False, na=False)
        df = df[mask]
    
    if filters.get('exclude_keywords'):
        exclude = filters['exclude_keywords'].split(',')
        mask = ~df['Keyword'].str.contains('|'.join(exclude), case=False, na=False)
        df = df[mask]
    
    # Data quality filters
    df = df[
        (df['DirectorName'].notna()) & 
        (df['DirectorName'] != '') &
        (df['EntityName'].notna()) &
        (df['EntityName'] != '')
    ]
    
    # Save result
    df.to_excel(output_file, index=False)
    print(f"Created subset: {len(df)} companies saved to {output_file}")

if __name__ == "__main__":
    # Command-line interface implementation
    pass
```

### **4. Common Dataset Filtering Scenarios**

#### **Industry-Specific Subsets**
```bash
# Manufacturing companies in Gauteng
python create_dataset_subset.py cipc_data.xlsx manufacturing_gauteng.xlsx \
    --province "GAUTENG" \
    --keywords "MANUFACTURING,PRODUCTION,FACTORY"

# IT companies in Cape Town
python create_dataset_subset.py cipc_data.xlsx it_cape_town.xlsx \
    --province "WESTERN CAPE" \
    --keywords "IT,SOFTWARE,TECHNOLOGY,DEVELOPMENT" \
    --city "CAPE TOWN"

# Retail companies nationally
python create_dataset_subset.py cipc_data.xlsx retail_national.xlsx \
    --keywords "RETAIL,SHOP,STORE,SALES"
```

#### **Size-Based Subsets**
```bash
# Small businesses (assuming employee count field exists)
python create_dataset_subset.py cipc_data.xlsx small_business.xlsx \
    --max-employees 50

# Large enterprises
python create_dataset_subset.py cipc_data.xlsx large_enterprise.xlsx \
    --min-employees 500
```

#### **Geographic Subsets**
```bash
# All companies in specific provinces
python create_dataset_subset.py cipc_data.xlsx eastern_cape.xlsx \
    --province "EASTERN CAPE"

# Companies in major cities
python create_dataset_subset.py cipc_data.xlsx major_cities.xlsx \
    --cities "JOHANNESBURG,CAPE TOWN,DURBAN,PRETORIA"
```

---

## 📊 **Database Schema Reference**

### **Jobs Database (cache/jobs.db)**

#### **job_executions Table**
- `job_id` - Unique job identifier
- `input_file_path` - Source Excel file path
- `total_rows` - Total leads in input
- `processed_leads_count` - Successfully processed leads
- `status` - Job status (running, completed, failed)
- `start_time` - Job start timestamp
- `completion_time` - Job completion timestamp
- `processing_time_total_ms` - Total processing time
- `api_costs_total` - Total API costs incurred

#### **lead_processing_results Table**
- `job_id` - Foreign key to job_executions
- `row_index` - Row position in input file
- `batch_number` - Processing batch identifier
- `entity_name` - Company name
- `director_name` - Director name processed
- `classification_result` - JSON with classification details
- `processing_status` - success/failed status
- `processing_time_ms` - Individual processing time
- `api_provider` - Provider used for classification
- `api_cost` - Cost of individual API call
- `created_at` - Processing timestamp

### **Learning Database (cache/llm_learning.db)**

#### **llm_classifications Table**
- `id` - Unique classification ID
- `name` - Full name that was classified
- `ethnicity` - Classified ethnicity
- `confidence` - Classification confidence
- `llm_provider` - Provider used
- `created_at` - Classification timestamp

#### **learned_patterns Table**
- `id` - Unique pattern ID
- `pattern_type` - Type of pattern (structural_prefix_2, etc.)
- `pattern_value` - The actual pattern string
- `ethnicity` - Associated ethnicity
- `confidence_score` - Pattern confidence
- `created_at` - Pattern creation timestamp

---

## 🚀 **Integration Roadmap**

### **Phase 1: CLI Integration** (Developer A Task)
- Integrate `export_job_results.py` as `leadscout jobs export`
- Integrate `analyze_job_statistics.py` as `leadscout jobs analyze`
- Add `leadscout data filter` command for dataset creation

### **Phase 2: Enhanced Analytics**
- Add trend analysis across multiple jobs
- Implement comparative job analysis
- Create learning effectiveness dashboards

### **Phase 3: Advanced Data Management**
- Generic dataset filtering with complex criteria
- Data validation and quality checking
- Automated dataset recommendations based on industry patterns

### **Phase 4: Monitoring & Optimization**
- Real-time performance monitoring
- Automated optimization suggestions
- Cost tracking and budgeting tools

---

## 📝 **Usage Examples**

### **Complete Workflow Example**
```bash
# 1. Create custom dataset subset
python create_dataset_subset.py cipc_data.xlsx healthcare_gauteng.xlsx \
    --province "GAUTENG" \
    --keywords "MEDICAL,HEALTH,CLINIC,HOSPITAL"

# 2. Process the dataset
poetry run leadscout jobs process healthcare_gauteng.xlsx --batch-size 100

# 3. Export results
python export_job_results.py <job-id> healthcare_enriched.xlsx

# 4. Analyze performance
python analyze_job_statistics.py <job-id>

# 5. Compare with previous runs
python analyze_job_statistics.py  # All jobs comparison
```

### **Research & Development Workflow**
```bash
# Test different batch sizes
poetry run leadscout jobs process test_data.xlsx --batch-size 50
poetry run leadscout jobs process test_data.xlsx --batch-size 100
poetry run leadscout jobs process test_data.xlsx --batch-size 200

# Compare performance
python analyze_job_statistics.py job-id-1
python analyze_job_statistics.py job-id-2  
python analyze_job_statistics.py job-id-3

# Export comparison data
python export_job_results.py job-id-1 results_batch50.xlsx
python export_job_results.py job-id-2 results_batch100.xlsx
python export_job_results.py job-id-3 results_batch200.xlsx
```

This documentation provides the foundation for future development and enhancement of LeadScout's utility scripts and data management capabilities.