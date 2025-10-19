#!/usr/bin/env python3
"""
Data Drift & Validation Script for CI/CD

Checks:
1. Dataset has all required columns
2. Data types are correct
3. Value ranges are valid
4. Data distribution drift (statistical tests)
5. No data quality issues

Configuration:
- All thresholds are loaded from config.yaml
- Only checks critical columns (model features) for missing values
- Configurable min rows, outlier %, missing value %, etc.

Exit codes:
- 0: All checks passed
- 1: Critical issues found (blocks deployment)
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import json
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ==========================================
# Load Configuration from config.yaml
# ==========================================

def load_config():
    """Load validation configuration from config.yaml"""
    config_path = project_root / 'config.yaml'
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"⚠️  Warning: Could not load config.yaml: {e}")
        print("   Using default values...")
        return None

# Load config
CONFIG = load_config()

# Extract validation config (with defaults if config not loaded)
if CONFIG and 'validation' in CONFIG:
    VAL_CONFIG = CONFIG['validation']
    
    # Required columns (from critical columns for missing values check)
    REQUIRED_COLUMNS = VAL_CONFIG.get('critical_columns_for_missing', [
        'CreditScore', 'Geography', 'Gender', 'Age', 'Tenure',
        'Balance', 'NumOfProducts', 'HasCrCard', 'IsActiveMember',
        'EstimatedSalary', 'Exited'
    ])
    
    # Critical columns to check for missing values (only model features!)
    CRITICAL_COLUMNS_FOR_MISSING = VAL_CONFIG.get('critical_columns_for_missing', REQUIRED_COLUMNS)
    
    # Categorical validation
    cat_vals = VAL_CONFIG.get('categorical_values', {})
    CATEGORICAL_COLUMNS = {
        'Geography': set(cat_vals.get('Geography', ['France', 'Germany', 'Spain'])),
        'Gender': set(cat_vals.get('Gender', ['Male', 'Female']))
    }
    
    # Value ranges
    value_ranges = VAL_CONFIG.get('value_ranges', {})
    NUMERIC_RANGES = {}
    for col, range_config in value_ranges.items():
        if 'values' in range_config:
            # Binary column
            NUMERIC_RANGES[col] = (min(range_config['values']), max(range_config['values']))
        else:
            # Numeric range
            min_val = range_config.get('min', 0)
            max_val = range_config.get('max', 1000000)  # Large default if null
            NUMERIC_RANGES[col] = (min_val, max_val if max_val is not None else 1000000)
    
    # Data quality thresholds
    data_quality = VAL_CONFIG.get('data_quality', {})
    MIN_ROWS = data_quality.get('min_rows', 5000)
    MIN_COLUMNS = data_quality.get('min_columns', 12)
    MAX_MISSING_PCT = data_quality.get('max_missing_percentage', 5.0)
    MAX_DUPLICATE_PCT = data_quality.get('max_duplicate_percentage', 1.0)
    
    # Drift detection
    drift_config = VAL_CONFIG.get('drift_detection', {})
    DRIFT_THRESHOLD = drift_config.get('significance_level', 0.05)
    DRIFT_COLUMNS = drift_config.get('columns_to_check', [])
    
    # Outlier thresholds
    outlier_config = VAL_CONFIG.get('outlier_thresholds', {})
    MAX_OUTLIER_PCT = outlier_config.get('max_outlier_percentage', 10.0)
    
    # Class balance
    class_balance = VAL_CONFIG.get('class_balance', {})
    MIN_MINORITY_PCT = class_balance.get('min_minority_percentage', 20.0)
    MAX_MAJORITY_PCT = class_balance.get('max_majority_percentage', 80.0)
    
else:
    # Fallback defaults if config not available
    REQUIRED_COLUMNS = [
        'CreditScore', 'Geography', 'Gender', 'Age', 'Tenure',
        'Balance', 'NumOfProducts', 'HasCrCard', 'IsActiveMember',
        'EstimatedSalary', 'Exited'
    ]
    CRITICAL_COLUMNS_FOR_MISSING = REQUIRED_COLUMNS
    CATEGORICAL_COLUMNS = {
        'Geography': {'France', 'Germany', 'Spain'},
        'Gender': {'Male', 'Female'}
    }
    NUMERIC_RANGES = {
        'CreditScore': (300, 900),
        'Age': (18, 100),
        'Tenure': (0, 10),
        'Balance': (0, 1000000),
        'NumOfProducts': (1, 4),
        'EstimatedSalary': (0, 1000000),
        'Exited': (0, 1)
    }
    MIN_ROWS = 5000
    MIN_COLUMNS = 12
    MAX_MISSING_PCT = 5.0
    MAX_DUPLICATE_PCT = 1.0
    DRIFT_THRESHOLD = 0.05
    DRIFT_COLUMNS = ['CreditScore', 'Age', 'Tenure', 'Balance', 'NumOfProducts', 'EstimatedSalary']
    MAX_OUTLIER_PCT = 10.0
    MIN_MINORITY_PCT = 20.0
    MAX_MAJORITY_PCT = 80.0

print(f"📋 Loaded configuration:")
print(f"   • Min rows: {MIN_ROWS}")
print(f"   • Max missing %: {MAX_MISSING_PCT}%")
print(f"   • Max duplicate %: {MAX_DUPLICATE_PCT}%")
print(f"   • Critical columns for missing check: {len(CRITICAL_COLUMNS_FOR_MISSING)}")
print(f"   • Drift threshold: {DRIFT_THRESHOLD}")
print(f"   • Max outlier %: {MAX_OUTLIER_PCT}%")
print()


# ==========================================
# Validation Functions
# ==========================================

def load_data(data_path):
    """Load dataset"""
    try:
        df = pd.read_csv(data_path)
        print(f"✅ Loaded dataset: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        sys.exit(1)


def check_required_columns(df):
    """Check if all required columns exist"""
    print("\n🔍 Checking required columns...")
    
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    
    if missing_columns:
        print(f"❌ Missing required columns: {missing_columns}")
        return False
    
    print(f"✅ All {len(REQUIRED_COLUMNS)} required columns present")
    return True


def check_data_types(df):
    """Validate data types"""
    print("\n🔍 Checking data types...")
    
    issues = []
    
    # Numeric columns
    numeric_cols = ['CreditScore', 'Age', 'Tenure', 'Balance', 'NumOfProducts', 
                   'HasCrCard', 'IsActiveMember', 'EstimatedSalary', 'Exited']
    
    for col in numeric_cols:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                issues.append(f"{col} should be numeric, got {df[col].dtype}")
    
    # Categorical columns
    for col in ['Geography', 'Gender']:
        if col in df.columns:
            if df[col].dtype != 'object':
                issues.append(f"{col} should be string/object, got {df[col].dtype}")
    
    if issues:
        print(f"❌ Data type issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ All data types correct")
    return True


def check_value_ranges(df):
    """Check if values are within expected ranges"""
    print("\n🔍 Checking value ranges...")
    
    issues = []
    
    for col, (min_val, max_val) in NUMERIC_RANGES.items():
        if col in df.columns:
            actual_min = df[col].min()
            actual_max = df[col].max()
            
            if actual_min < min_val or actual_max > max_val:
                issues.append(
                    f"{col}: range [{actual_min}, {actual_max}] "
                    f"outside expected [{min_val}, {max_val}]"
                )
    
    if issues:
        print(f"❌ Value range issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ All values within expected ranges")
    return True


def check_categorical_values(df):
    """Check categorical column values"""
    print("\n🔍 Checking categorical values...")
    
    issues = []
    
    for col, valid_values in CATEGORICAL_COLUMNS.items():
        if col in df.columns:
            actual_values = set(df[col].unique())
            invalid_values = actual_values - valid_values
            
            if invalid_values:
                issues.append(f"{col}: invalid values {invalid_values}")
    
    if issues:
        print(f"❌ Categorical value issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ All categorical values valid")
    return True


def check_missing_values(df):
    """
    Check for missing values in CRITICAL columns only
    
    Only checks columns used for model training (feature_columns + target).
    Other columns (like CustomerId, RowNumber, Surname) are ignored.
    Uses configurable threshold from config.yaml
    """
    print("\n🔍 Checking missing values in critical columns...")
    print(f"   ℹ️  Only checking {len(CRITICAL_COLUMNS_FOR_MISSING)} model-critical columns")
    print(f"   ℹ️  Threshold: {MAX_MISSING_PCT}% max missing per column")
    
    issues = []
    
    # Only check critical columns (those used for model training)
    for col in CRITICAL_COLUMNS_FOR_MISSING:
        if col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                missing_pct = (missing_count / len(df)) * 100
                print(f"   ⚠️  {col}: {missing_count} missing ({missing_pct:.2f}%)")
                
                # Check against configurable threshold
                if missing_pct > MAX_MISSING_PCT:
                    issues.append(
                        f"{col}: {missing_pct:.2f}% missing (threshold: {MAX_MISSING_PCT}%)"
                    )
    
    if issues:
        print(f"\n❌ MISSING VALUES CHECK FAILED")
        print(f"   Columns exceeding {MAX_MISSING_PCT}% threshold:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print(f"✅ All critical columns have < {MAX_MISSING_PCT}% missing values")
    return True


def check_duplicates(df):
    """Check for duplicate rows using configurable threshold"""
    print("\n🔍 Checking duplicates...")
    print(f"   ℹ️  Threshold: {MAX_DUPLICATE_PCT}% max duplicates")
    
    # Check for duplicate CustomerIds if present
    if 'CustomerId' in df.columns:
        dup_count = df['CustomerId'].duplicated().sum()
        dup_pct = (dup_count / len(df)) * 100
        if dup_count > 0:
            print(f"   ⚠️  Found {dup_count} duplicate customer IDs ({dup_pct:.2f}%)")
            if dup_pct > MAX_DUPLICATE_PCT:
                print(f"❌ Duplicate CustomerIds: {dup_pct:.2f}% > {MAX_DUPLICATE_PCT}%")
                return False
    
    # Check for duplicate rows (entire row duplicated)
    dup_rows = df.duplicated().sum()
    dup_rows_pct = (dup_rows / len(df)) * 100
    if dup_rows > 0:
        print(f"   ⚠️  Found {dup_rows} duplicate rows ({dup_rows_pct:.2f}%)")
        if dup_rows_pct > MAX_DUPLICATE_PCT:
            print(f"❌ Duplicate rows: {dup_rows_pct:.2f}% > {MAX_DUPLICATE_PCT}%")
            return False
    
    print(f"✅ Duplicates < {MAX_DUPLICATE_PCT}% threshold")
    return True


def check_data_drift(df, reference_path=None):
    """
    Check for data drift using statistical tests (from config.yaml)
    
    Compares current data against reference data (if available)
    Uses Kolmogorov-Smirnov test for numerical features
    Only checks columns configured in config.yaml
    """
    print("\n🔍 Checking data drift...")
    print(f"   ℹ️  Checking {len(DRIFT_COLUMNS)} numerical columns")
    print(f"   ℹ️  Significance level: {DRIFT_THRESHOLD}")
    
    if reference_path is None or not Path(reference_path).exists():
        print("ℹ️  No reference data found, skipping drift detection")
        return True
    
    try:
        df_reference = pd.read_csv(reference_path)
        print(f"   Reference dataset: {len(df_reference)} rows")
    except Exception as e:
        print(f"⚠️  Could not load reference data: {e}")
        return True
    
    drift_detected = []
    
    # Use columns from config
    for col in DRIFT_COLUMNS:
        if col in df.columns and col in df_reference.columns:
            # Kolmogorov-Smirnov test
            statistic, p_value = stats.ks_2samp(
                df_reference[col].dropna(),
                df[col].dropna()
            )
            
            if p_value < DRIFT_THRESHOLD:
                drift_detected.append({
                    'feature': col,
                    'p_value': p_value,
                    'statistic': statistic,
                    'severity': 'HIGH' if p_value < 0.01 else 'MEDIUM'
                })
    
    if drift_detected:
        print(f"⚠️  Data drift detected in {len(drift_detected)} features:")
        for drift in drift_detected:
            emoji = "🔴" if drift['severity'] == 'HIGH' else "🟡"
            print(f"   {emoji} {drift['feature']}: p-value = {drift['p_value']:.4f} (KS={drift['statistic']:.4f})")
        
        # Only fail on HIGH severity drift
        high_severity = [d for d in drift_detected if d['severity'] == 'HIGH']
        if high_severity:
            print(f"❌ Critical drift detected in {len(high_severity)} features")
            return False
        else:
            print("✅ Drift severity acceptable (MEDIUM level)")
    else:
        print("✅ No significant drift detected")
    
    return True


def check_class_balance(df):
    """Check class distribution using configurable thresholds"""
    print("\n🔍 Checking class balance...")
    print(f"   ℹ️  Min minority class: {MIN_MINORITY_PCT}%")
    print(f"   ℹ️  Max majority class: {MAX_MAJORITY_PCT}%")
    
    if 'Exited' not in df.columns:
        print("⚠️  Target column 'Exited' not found")
        return True
    
    class_counts = df['Exited'].value_counts()
    total = len(df)
    
    # Calculate percentages
    class_0_pct = (class_counts.get(0, 0) / total) * 100
    class_1_pct = (class_counts.get(1, 0) / total) * 100
    
    print(f"   Class 0 (No Churn): {class_counts.get(0, 0)} ({class_0_pct:.2f}%)")
    print(f"   Class 1 (Churn):    {class_counts.get(1, 0)} ({class_1_pct:.2f}%)")
    
    # Identify minority and majority classes
    minority_pct = min(class_0_pct, class_1_pct)
    majority_pct = max(class_0_pct, class_1_pct)
    
    # Check against configurable thresholds
    if minority_pct < MIN_MINORITY_PCT:
        print(f"❌ Minority class ({minority_pct:.2f}%) < threshold ({MIN_MINORITY_PCT}%)")
        return False
    
    if majority_pct > MAX_MAJORITY_PCT:
        print(f"❌ Majority class ({majority_pct:.2f}%) > threshold ({MAX_MAJORITY_PCT}%)")
        return False
    
    # Calculate imbalance ratio
    ratio = majority_pct / minority_pct
    print(f"✅ Class balance acceptable (ratio: {ratio:.2f}:1)")
    return True


def generate_report(results, output_path='reports/data_validation_report.json'):
    """Generate validation report"""
    report_dir = Path(output_path).parent
    report_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Report saved: {output_path}")


# ==========================================
# Main Execution
# ==========================================

def main():
    """Main validation function"""
    print("=" * 70)
    print("📊 DATA VALIDATION & DRIFT DETECTION")
    print("=" * 70)
    
    # Get data path from command line or use default
    data_path = sys.argv[1] if len(sys.argv) > 1 else 'data/raw/ChurnModelling.csv'
    reference_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Try S3 first, then local
    try:
        from utils.s3_io import read_df_csv, key_exists
        from utils.config import get_s3_bucket
        
        s3_key = data_path.replace('data/raw/', '')
        if not s3_key.startswith('data/'):
            s3_key = f"data/raw/{s3_key}"
        
        bucket = get_s3_bucket()
        
        if key_exists(s3_key):
            print(f"\n📦 Loading data from S3: s3://{bucket}/{s3_key}")
            df = read_df_csv(key=s3_key)
        elif Path(data_path).exists():
            print(f"\n📁 Loading data from local: {data_path}")
            df = pd.read_csv(data_path)
        else:
            print(f"❌ Data file not found in S3 or locally: {data_path}")
            sys.exit(1)
    except Exception as e:
        # S3 not configured, use local
        if not Path(data_path).exists():
            print(f"❌ Data file not found: {data_path}")
            sys.exit(1)
        print(f"\n📁 Loading data from local: {data_path}")
        df = pd.read_csv(data_path)
    
    # Check minimum data requirements FIRST
    print(f"\n🔍 Checking data shape requirements...")
    print(f"   • Dataset shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"   • Minimum required: {MIN_ROWS} rows × {MIN_COLUMNS} columns")
    
    if df.shape[0] < MIN_ROWS:
        print(f"\n❌ INSUFFICIENT DATA")
        print(f"   Dataset has {df.shape[0]} rows, need at least {MIN_ROWS} rows")
        print("=" * 70)
        sys.exit(1)
    
    if df.shape[1] < MIN_COLUMNS:
        print(f"\n❌ INSUFFICIENT COLUMNS")
        print(f"   Dataset has {df.shape[1]} columns, need at least {MIN_COLUMNS} columns")
        print("=" * 70)
        sys.exit(1)
    
    print(f"✅ Dataset meets minimum size requirements")
    
    # Run all checks
    results = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'data_path': str(data_path),
        'num_rows': len(df),
        'num_columns': len(df.columns),
        'checks': {}
    }
    
    checks = [
        ('required_columns', check_required_columns),
        ('data_types', check_data_types),
        ('value_ranges', check_value_ranges),
        ('categorical_values', check_categorical_values),
        ('missing_values', check_missing_values),
        ('duplicates', check_duplicates),
        ('data_drift', lambda df: check_data_drift(df, reference_path)),
        ('class_balance', check_class_balance)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        passed = check_func(df)
        results['checks'][check_name] = 'PASS' if passed else 'FAIL'
        
        if not passed:
            all_passed = False
    
    # Generate report
    generate_report(results)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    
    passed_checks = sum(1 for v in results['checks'].values() if v == 'PASS')
    total_checks = len(results['checks'])
    
    print(f"\n✅ Passed: {passed_checks}/{total_checks}")
    print(f"❌ Failed: {total_checks - passed_checks}/{total_checks}")
    
    for check_name, status in results['checks'].items():
        emoji = "✅" if status == "PASS" else "❌"
        print(f"   {emoji} {check_name}: {status}")
    
    if all_passed:
        print("\n🎉 All validation checks passed!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n❌ Some validation checks failed!")
        print("=" * 70)
        sys.exit(1)


def test_data_validation():
    """
    Pytest-compatible test wrapper for data validation.
    Validates data from S3 or local fallback using configurable file from config.yaml.
    """
    import pytest
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from utils.s3_io import read_df_csv, key_exists
        from utils.config import get_s3_bucket, get_data_config, get_local_raw_data_path
        
        # Get configurable data file from config.yaml
        data_config = get_data_config()
        raw_data_file = data_config.get('raw_data_file', 'ChurnModelling.csv')
        s3_prefix = data_config.get('s3_prefix', 'data/raw')
        
        # Try S3 first (production)
        s3_key = f"{s3_prefix}/{raw_data_file}"
        bucket = get_s3_bucket()
        
        print(f"📋 Using data file from config: {raw_data_file}")
        
        if key_exists(s3_key):
            print(f"📦 Loading data from S3: s3://{bucket}/{s3_key}")
            df = read_df_csv(key=s3_key)
        else:
            # Fallback to local
            local_path = get_local_raw_data_path()
            if not os.path.exists(local_path):
                pytest.skip(f"Data file not found in S3 ({s3_key}) or locally ({local_path})")
            print(f"📁 Loading data from local: {local_path}")
            df = pd.read_csv(local_path)
            
    except Exception as e:
        # S3 not configured, use local
        from utils.config import get_local_raw_data_path
        local_path = get_local_raw_data_path()
        if not os.path.exists(local_path):
            pytest.skip(f"Data file not found locally and S3 not configured: {local_path}")
        print(f"📁 Loading data from local: {local_path}")
        df = pd.read_csv(local_path)
    
    # Check minimum data requirements FIRST
    print(f"\n🔍 Checking data shape requirements...")
    print(f"   • Dataset shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"   • Minimum required: {MIN_ROWS} rows × {MIN_COLUMNS} columns")
    
    if df.shape[0] < MIN_ROWS:
        pytest.fail(f"Insufficient data: {df.shape[0]} rows < {MIN_ROWS} rows required")
    
    if df.shape[1] < MIN_COLUMNS:
        pytest.fail(f"Insufficient columns: {df.shape[1]} columns < {MIN_COLUMNS} columns required")
    
    print(f"✅ Dataset meets minimum size requirements")
    
    # Run all checks
    checks = [
        ('required_columns', check_required_columns),
        ('data_types', check_data_types),
        ('value_ranges', check_value_ranges),
        ('categorical_values', check_categorical_values),
        ('missing_values', check_missing_values),
        ('duplicates', check_duplicates),
        ('data_drift', lambda df: check_data_drift(df, None)),
        ('class_balance', check_class_balance)
    ]
    
    failed_checks = []
    for check_name, check_func in checks:
        passed = check_func(df)
        if not passed:
            failed_checks.append(check_name)
    
    # Assert all checks passed
    if failed_checks:
        error_msg = f"Data validation failed for the following checks:\n"
        for check in failed_checks:
            error_msg += f"  - {check}\n"
        pytest.fail(error_msg)


if __name__ == "__main__":
    main()

