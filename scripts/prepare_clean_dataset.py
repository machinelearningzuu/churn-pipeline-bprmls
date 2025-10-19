"""
Script to prepare a clean dataset with imputed Gender values.
This demonstrates data quality validation - both passing and failing scenarios.

Usage:
    python scripts/prepare_clean_dataset.py
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.s3_io import write_df_csv, key_exists
from utils.config import get_s3_bucket, load_config


def impute_missing_gender(df: pd.DataFrame, strategy: str = "random") -> pd.DataFrame:
    """
    Impute missing Gender values.
    
    Args:
        df: DataFrame with potential missing Gender values
        strategy: "random" or "mode" (most frequent)
    
    Returns:
        DataFrame with imputed Gender values
    """
    df = df.copy()
    
    missing_count = df['Gender'].isnull().sum()
    print(f"\n📊 Gender Statistics:")
    print(f"   • Total rows: {len(df)}")
    print(f"   • Missing Gender values: {missing_count} ({missing_count/len(df)*100:.2f}%)")
    
    if missing_count == 0:
        print(f"   ✅ No missing values to impute")
        return df
    
    if strategy == "random":
        # Get valid gender values from existing data
        valid_genders = df['Gender'].dropna().unique()
        print(f"   • Valid genders: {list(valid_genders)}")
        
        # Randomly impute missing values
        np.random.seed(42)  # For reproducibility
        imputed_values = np.random.choice(valid_genders, size=missing_count)
        df.loc[df['Gender'].isnull(), 'Gender'] = imputed_values
        
        print(f"   ✅ Imputed {missing_count} missing Gender values randomly")
        
    elif strategy == "mode":
        # Impute with most frequent value
        mode_value = df['Gender'].mode()[0]
        df['Gender'].fillna(mode_value, inplace=True)
        print(f"   ✅ Imputed {missing_count} missing Gender values with mode: {mode_value}")
    
    # Verify no missing values remain
    remaining_missing = df['Gender'].isnull().sum()
    if remaining_missing > 0:
        print(f"   ⚠️  Warning: {remaining_missing} missing values still remain!")
    else:
        print(f"   ✅ All Gender values are now populated")
    
    return df


def main():
    """Main function to prepare clean dataset"""
    
    print("=" * 70)
    print("🧹 CLEAN DATASET PREPARATION")
    print("=" * 70)
    
    # File paths
    input_file = "data/raw/ChurnModelling_GenderImputed.csv"
    output_file = "data/raw/ChurnModelling_Clean.csv"
    
    # S3 configuration
    config = load_config()
    bucket = get_s3_bucket()
    s3_key_original = "data/raw/ChurnModelling.csv"
    s3_key_clean = "data/raw/ChurnModelling_Clean.csv"
    
    print(f"\n📂 Files:")
    print(f"   • Input:  {input_file}")
    print(f"   • Output: {output_file}")
    print(f"   • S3 Bucket: {bucket}")
    print(f"   • S3 Key: {s3_key_clean}")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"\n❌ Error: Input file not found: {input_file}")
        print(f"   Please ensure the file exists.")
        sys.exit(1)
    
    # Load data
    print(f"\n📥 Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    print(f"   ✅ Loaded {len(df)} rows × {len(df.columns)} columns")
    
    # Show initial data quality
    print(f"\n📊 Initial Data Quality:")
    for col in ['Gender', 'Age']:
        if col in df.columns:
            missing = df[col].isnull().sum()
            missing_pct = (missing / len(df)) * 100
            print(f"   • {col}: {missing} missing ({missing_pct:.2f}%)")
    
    # Impute missing Gender values
    print(f"\n🔧 Imputing missing Gender values...")
    df_clean = impute_missing_gender(df, strategy="random")
    
    # Show final data quality
    print(f"\n📊 Final Data Quality (after imputation):")
    for col in ['Gender', 'Age']:
        if col in df_clean.columns:
            missing = df_clean[col].isnull().sum()
            missing_pct = (missing / len(df_clean)) * 100
            print(f"   • {col}: {missing} missing ({missing_pct:.2f}%)")
    
    # Show Gender distribution
    print(f"\n📊 Gender Distribution:")
    gender_counts = df_clean['Gender'].value_counts()
    for gender, count in gender_counts.items():
        pct = (count / len(df_clean)) * 100
        print(f"   • {gender}: {count} ({pct:.2f}%)")
    
    # Save locally
    print(f"\n💾 Saving clean dataset locally...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_clean.to_csv(output_file, index=False)
    print(f"   ✅ Saved to {output_file}")
    
    # Upload to S3
    print(f"\n☁️  Uploading to S3...")
    try:
        write_df_csv(df_clean, key=s3_key_clean)
        print(f"   ✅ Uploaded to s3://{bucket}/{s3_key_clean}")
        
        # Check if original file exists in S3
        if key_exists(s3_key_original):
            print(f"   ℹ️  Original file also exists: s3://{bucket}/{s3_key_original}")
        
    except Exception as e:
        print(f"   ⚠️  Warning: Failed to upload to S3: {str(e)}")
        print(f"   The file is saved locally at: {output_file}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ DATASET PREPARATION COMPLETE")
    print("=" * 70)
    print(f"\n📚 Usage:")
    print(f"   To use the CLEAN dataset (validation will PASS):")
    print(f"   1. Update config.yaml:")
    print(f"      data:")
    print(f"        raw_data_file: 'ChurnModelling_Clean.csv'")
    print(f"")
    print(f"   To use the ORIGINAL dataset (validation will FAIL):")
    print(f"   1. Update config.yaml:")
    print(f"      data:")
    print(f"        raw_data_file: 'ChurnModelling.csv'")
    print(f"")
    print(f"   Then run validation:")
    print(f"   pytest tests/validate_data.py -v")
    print("=" * 70)


if __name__ == "__main__":
    main()

