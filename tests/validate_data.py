#!/usr/bin/env python3
"""
Data Drift & Validation Script for CI/CD

Checks:
1. Dataset has all required columns
2. Data types are correct
3. Value ranges are valid
4. Data distribution drift (statistical tests)
5. No data quality issues

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

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ==========================================
# Configuration
# ==========================================

REQUIRED_COLUMNS = [
    'CreditScore', 'Geography', 'Gender', 'Age', 'Tenure',
    'Balance', 'NumOfProducts', 'HasCrCard', 'IsActiveMember',
    'EstimatedSalary', 'Exited'
]

CATEGORICAL_COLUMNS = {
    'Geography': {'France', 'Germany', 'Spain'},
    'Gender': {'Male', 'Female'}
}

NUMERIC_RANGES = {
    'CreditScore': (300, 850),
    'Age': (18, 100),
    'Tenure': (0, 10),
    'Balance': (0, 300000),
    'NumOfProducts': (1, 4),
    'HasCrCard': (0, 1),
    'IsActiveMember': (0, 1),
    'EstimatedSalary': (0, 300000),
    'Exited': (0, 1)
}

DRIFT_THRESHOLD = 0.05  # 5% significance level for statistical tests


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
    """Check for missing values"""
    print("\n🔍 Checking missing values...")
    
    missing = df.isnull().sum()
    critical_missing = missing[missing > 0]
    
    if len(critical_missing) > 0:
        print(f"⚠️  Found missing values:")
        for col, count in critical_missing.items():
            pct = (count / len(df)) * 100
            print(f"   - {col}: {count} ({pct:.2f}%)")
        
        # Allow up to 5% missing in non-critical columns
        critical_cols = ['Exited', 'Age', 'Geography']
        for col in critical_cols:
            if col in critical_missing.index:
                print(f"❌ Critical column {col} has missing values")
                return False
        
        print("✅ Missing values acceptable (non-critical columns only)")
    else:
        print("✅ No missing values")
    
    return True


def check_duplicates(df):
    """Check for duplicate rows"""
    print("\n🔍 Checking duplicates...")
    
    # Check for duplicate CustomerIds if present
    if 'CustomerId' in df.columns:
        dup_count = df['CustomerId'].duplicated().sum()
        if dup_count > 0:
            print(f"❌ Found {dup_count} duplicate customer IDs")
            return False
    
    # Check for duplicate rows
    dup_rows = df.duplicated().sum()
    if dup_rows > 0:
        print(f"⚠️  Found {dup_rows} duplicate rows ({(dup_rows/len(df)*100):.2f}%)")
    
    print("✅ No critical duplicates")
    return True


def check_data_drift(df, reference_path=None):
    """
    Check for data drift using statistical tests
    
    Compares current data against reference data (if available)
    Uses Kolmogorov-Smirnov test for numerical features
    """
    print("\n🔍 Checking data drift...")
    
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
    numerical_cols = ['CreditScore', 'Age', 'Tenure', 'Balance', 
                     'NumOfProducts', 'EstimatedSalary']
    
    for col in numerical_cols:
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
                    'severity': 'HIGH' if p_value < 0.01 else 'MEDIUM'
                })
    
    if drift_detected:
        print(f"⚠️  Data drift detected in {len(drift_detected)} features:")
        for drift in drift_detected:
            emoji = "🔴" if drift['severity'] == 'HIGH' else "🟡"
            print(f"   {emoji} {drift['feature']}: p-value = {drift['p_value']:.4f}")
        
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
    """Check class distribution"""
    print("\n🔍 Checking class balance...")
    
    if 'Exited' not in df.columns:
        print("⚠️  Target column 'Exited' not found")
        return True
    
    class_counts = df['Exited'].value_counts()
    churn_rate = df['Exited'].mean()
    
    print(f"   Class 0 (No Churn): {class_counts.get(0, 0)} ({(1-churn_rate)*100:.2f}%)")
    print(f"   Class 1 (Churn):    {class_counts.get(1, 0)} ({churn_rate*100:.2f}%)")
    
    # Check if churn rate is realistic (5% - 40%)
    if not (0.05 <= churn_rate <= 0.40):
        print(f"❌ Churn rate {churn_rate:.2%} outside realistic range (5%-40%)")
        return False
    
    # Check if imbalance is too extreme (max 10:1 ratio)
    majority = class_counts.max()
    minority = class_counts.min()
    ratio = majority / minority
    
    if ratio > 10:
        print(f"❌ Class imbalance ratio {ratio:.2f} too high (max 10:1)")
        return False
    
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
    
    if not Path(data_path).exists():
        print(f"❌ Data file not found: {data_path}")
        sys.exit(1)
    
    print(f"\n📁 Data file: {data_path}")
    if reference_path:
        print(f"📁 Reference file: {reference_path}")
    
    # Load data
    df = load_data(data_path)
    
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


if __name__ == "__main__":
    main()

