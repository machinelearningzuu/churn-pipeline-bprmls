"""
Data processing pipeline for customer churn prediction.
Prioritizes pandas/scikit-learn with PySpark as fallback for large datasets.
Supports both CSV and Parquet output formats with comprehensive preprocessing.
"""

import os
import sys
import logging
import json
import argparse
from typing import Dict, Optional, List, Tuple, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Global PySpark availability flag - controlled by command line argument
PYSPARK_AVAILABLE = False  # Will be set by argparse

# Conditional PySpark imports
if PYSPARK_AVAILABLE:
    try:
        from pyspark.sql import DataFrame as SparkDataFrame, SparkSession
        from pyspark.sql import functions as F
        from pyspark.ml import Pipeline, PipelineModel
    except ImportError:
        PYSPARK_AVAILABLE = False
        SparkDataFrame = None
        SparkSession = None
else:
    SparkDataFrame = None
    SparkSession = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils.spark_session import create_spark_session, stop_spark_session
from utils.spark_utils import save_dataframe, spark_to_pandas, get_dataframe_info, check_missing_values
from data_ingestion import DataIngestorCSV
# Temporarily comment out broken imports - use direct pandas/sklearn in pandas pipeline
# from handle_missing_values import DropMissingValuesStrategy, FillMissingValuesStrategy
# from outlier_detection import OutlierDetector, IQROutlierDetection
# from feature_binning import CustomBinningStrategy
# from feature_encoding import OrdinalEncodingStrategy, NominalEncodingStrategy
# from feature_scaling import MinMaxScalingStrategy
# from data_splitter import SimpleTrainTestSplitStrategy
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from config import get_data_paths, get_columns, get_missing_values_config, get_outlier_config, get_binning_config, get_encoding_config, get_scaling_config, get_splitting_config, get_s3_bucket, force_s3_io
from mlflow_utils import MLflowTracker, setup_mlflow_autolog, create_mlflow_run_tags
from s3_artifact_manager import S3ArtifactManager, get_s3_artifact_paths
from s3_io import write_df_csv, write_pickle
import mlflow


# Visualization functions removed for Week 07 - focus on core PySpark processing


def log_stage_metrics(df: Union[pd.DataFrame, object], stage: str, additional_metrics: Dict = None, spark: object = None):
    """Log key metrics for each processing stage."""
    try:
        # Calculate missing values count efficiently
        missing_counts = []
        for col in df.columns:
            missing_counts.append(df.filter(F.col(col).isNull()).count())
        total_missing = sum(missing_counts)
        
        metrics = {
            f'{stage}_rows': df.count(),
            f'{stage}_columns': len(df.columns),
            f'{stage}_missing_values': total_missing,
            f'{stage}_partitions': df.rdd.getNumPartitions()
        }
        
        if additional_metrics:
            metrics.update({f'{stage}_{k}': v for k, v in additional_metrics.items()})
        
        mlflow.log_metrics(metrics)
        logger.info(f"✓ Metrics logged for {stage}: ({metrics[f'{stage}_rows']}, {metrics[f'{stage}_columns']})")
        
    except Exception as e:
        logger.error(f"✗ Failed to log metrics for {stage}: {str(e)}")


def save_processed_data(
    X_train: Union[pd.DataFrame, object], 
    X_test: Union[pd.DataFrame, object], 
    Y_train: Union[pd.DataFrame, object], 
    Y_test: Union[pd.DataFrame, object],
    pipeline_timestamp: str,
    output_format: str = "both"
) -> Dict[str, str]:
    """
    Save processed data to S3 in specified format(s) with timestamp-based naming.
    
    Args:
        X_train, X_test, Y_train, Y_test: PySpark DataFrames
        pipeline_timestamp: Timestamp for this pipeline run
        output_format: "csv", "parquet", or "both"
        
    Returns:
        Dictionary of S3 key paths with timestamp
    """
    paths = {}
    s3_manager = S3ArtifactManager()
    bucket = get_s3_bucket()
    
    logger.info(f"💾 Saving artifacts to S3 with timestamp: {pipeline_timestamp}")
    
    if output_format in ["csv", "both"]:
        # Save as CSV to S3
        logger.info("Saving data in CSV format to S3...")
        
        # Convert to pandas for CSV upload
        X_train_pd = spark_to_pandas(X_train)
        X_test_pd = spark_to_pandas(X_test)
        Y_train_pd = spark_to_pandas(Y_train)
        Y_test_pd = spark_to_pandas(Y_test)
        
        # Create S3 CSV paths for data artifacts
        csv_paths = s3_manager.create_s3_paths(
            ['X_train', 'X_test', 'Y_train', 'Y_test'], 
            timestamp=pipeline_timestamp,
            artifact_type='data_artifacts',
            format_ext='csv'
        )
        
        # Try to upload CSV files to S3, fallback to local if needed
        try:
            write_df_csv(X_train_pd, key=csv_paths['X_train'])
            write_df_csv(X_test_pd, key=csv_paths['X_test'])
            write_df_csv(Y_train_pd, key=csv_paths['Y_train'])
            write_df_csv(Y_test_pd, key=csv_paths['Y_test'])
            
            paths.update({f"{k}_csv": v for k, v in csv_paths.items()})
            logger.info("✓ CSV files saved to S3")
            
        except Exception as s3_error:
            logger.error(f"❌ S3 save failed: {s3_error}")
            logger.error("💡 Please check your AWS credentials and S3 bucket configuration")
            raise s3_error
    
    # Clean up old artifacts in S3 (keep last 5 versions) - optional
    try:
        s3_manager.cleanup_old_artifacts(artifact_type='data_artifacts', keep_count=5)
    except Exception as cleanup_error:
        logger.warning(f"S3 cleanup failed: {cleanup_error}")
    
    paths['timestamp'] = pipeline_timestamp
    return paths


def data_pipeline(
    data_path: str = None,
    target_column: str = 'Exited',
    test_size: float = 0.2,
    force_rebuild: bool = False,
    output_format: str = "both",
    processing_engine: str = None
) -> Dict[str, np.ndarray]:
    """
    Execute comprehensive data processing pipeline with pandas/scikit-learn priority.
    Falls back to PySpark for large datasets when needed.
    
    Args:
        data_path: Path to the raw data file
        target_column: Name of the target column
        test_size: Proportion of data to use for testing
        force_rebuild: Whether to force rebuild of existing artifacts
        output_format: Output format - "csv", "parquet", or "both"
        processing_engine: "pandas" or "pyspark" (default: from config)
        
    Returns:
        Dictionary containing processed train/test splits as numpy arrays
    """
    
    # Get configuration
    from utils.config import load_config
    config = load_config()
    
    # Determine processing engine (prioritize pandas)
    if processing_engine is None:
        processing_engine = config.get('processing', {}).get('data_processing_engine', 'pandas')
    
    logger.info(f"🎯 Processing Engine: {processing_engine.upper()}")
    
    # Get data path from config if not provided
    if data_path is None:
        data_path = config['data_paths']['raw_data']
        logger.info(f"📁 Using data path from config: {data_path}")
    
    # Generate single timestamp for entire pipeline run
    from datetime import datetime
    pipeline_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    logger.info(f"🕐 Pipeline timestamp: {pipeline_timestamp}")
    logger.info(f"\n{'='*80}")
    logger.info(f"STARTING {processing_engine.upper()} DATA PIPELINE")
    logger.info(f"{'='*80}")
    
    # Route to appropriate engine
    if processing_engine.lower() == 'pandas':
        return _run_pandas_pipeline(data_path, target_column, test_size, force_rebuild, output_format, pipeline_timestamp, config)
    elif processing_engine.lower() == 'pyspark':
        return _run_pyspark_pipeline(data_path, target_column, test_size, force_rebuild, output_format, pipeline_timestamp, config)
    else:
        raise ValueError(f"Unknown processing engine: {processing_engine}. Use 'pandas' or 'pyspark'.")
    
def _run_pandas_pipeline(data_path, target_column, test_size, force_rebuild, output_format, pipeline_timestamp, config):
    """Run data pipeline using pandas (fast, default)."""
    logger.info("🐼 Using pandas for data processing (fast, lightweight)")
    
    try:
        # Start pipeline timing
        import time
        pipeline_start = time.time()
        
        # MLflow setup
        from utils.mlflow_utils import MLflowTracker, setup_mlflow_autolog, create_mlflow_run_tags
        import mlflow
        
        mlflow_tracker = MLflowTracker()
        run_tags = create_mlflow_run_tags(pipeline_type="data_processing")
        run_tags['engine'] = 'pandas'
        run_tags['timestamp'] = pipeline_timestamp
        mlflow_tracker.start_run(run_name=f"data_pipeline_pandas_{pipeline_timestamp}", tags=run_tags)
        setup_mlflow_autolog()
        
        # 1. Data Ingestion using pandas
        import time
        step_start = time.time()
        logger.info(f"\n{'='*60}")
        logger.info("📥 STEP 1: DATA INGESTION (PANDAS)")
        logger.info(f"{'='*60}")
        logger.info(f"🔗 Data source: {data_path}")
        logger.info(f"🎯 Engine: Pandas (fast, lightweight)")
        
        from data_ingestion import DataIngestorCSV
        ingestor = DataIngestorCSV()  # No Spark session needed
        df = ingestor.ingest(data_path)
        
        step_time = time.time() - step_start
        logger.info(f"✅ DATA INGESTION COMPLETED")
        logger.info(f"📊 Dataset shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        logger.info(f"💾 Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        logger.info(f"⏱️ Processing time: {step_time:.2f} seconds")
        logger.info(f"🔍 Sample columns: {list(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
        
        # Log data quality metrics
        missing_total = df.isnull().sum().sum()
        duplicates = df.duplicated().sum()
        logger.info(f"📋 Data Quality Metrics:")
        logger.info(f"  • Missing values: {missing_total:,}")
        logger.info(f"  • Duplicate rows: {duplicates:,}")
        logger.info(f"  • Data types: {dict(df.dtypes.value_counts())}")
        
        # 2. Handle missing values using pandas
        step_start = time.time()
        logger.info(f"\n{'='*60}")
        logger.info("🔧 STEP 2: MISSING VALUE HANDLING (PANDAS)")
        logger.info(f"{'='*60}")
        
        initial_missing = df.isnull().sum().sum()
        logger.info(f"📊 Initial missing values: {initial_missing:,}")
        
        if initial_missing > 0:
            # Analyze missing values by column
            missing_by_col = df.isnull().sum()
            missing_cols = missing_by_col[missing_by_col > 0]
            logger.info(f"📋 Missing values by column:")
            for col, count in missing_cols.items():
                percentage = (count / len(df)) * 100
                logger.info(f"  • {col}: {count:,} ({percentage:.1f}%)")
            
            # Fill numeric columns with median, categorical with mode
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            
            logger.info(f"🔢 Handling {len(numeric_cols)} numeric columns with median")
            for col in numeric_cols:
                if df[col].isnull().sum() > 0:
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    logger.info(f"  • {col}: filled {missing_by_col[col]} values with {median_val:.2f}")
            
            logger.info(f"📝 Handling {len(categorical_cols)} categorical columns")
            for col in categorical_cols:
                if df[col].isnull().sum() > 0:
                    # Special handling for Gender: DROP rows with missing values
                    if col == 'Gender':
                        rows_before = len(df)
                        df = df.dropna(subset=['Gender'])
                        rows_dropped = rows_before - len(df)
                        logger.info(f"  • {col}: DROPPED {rows_dropped} rows with missing values (no Gender_Unknown)")
                    else:
                        # For other categorical columns, fill with mode
                        mode_val = df[col].mode()[0] if len(df[col].mode()) > 0 else 'Unknown'
                        df[col] = df[col].fillna(mode_val)
                        logger.info(f"  • {col}: filled {missing_by_col[col]} values with '{mode_val}'")
        
        final_missing = df.isnull().sum().sum()
        step_time = time.time() - step_start
        logger.info(f"✅ MISSING VALUE HANDLING COMPLETED")
        logger.info(f"📊 Remaining missing values: {final_missing:,}")
        logger.info(f"📈 Missing values reduced: {initial_missing:,} → {final_missing:,}")
        logger.info(f"⏱️ Processing time: {step_time:.2f} seconds")
        
        # 3. Feature encoding using pandas/sklearn (ONE-HOT ENCODING)
        step_start = time.time()
        logger.info(f"\n{'='*60}")
        logger.info("🔤 STEP 3: FEATURE ENCODING (ONE-HOT)")
        logger.info(f"{'='*60}")
        
        # Identify categorical columns
        categorical_cols = ['Geography', 'Gender']  # Known categorical columns
        available_categorical = [col for col in categorical_cols if col in df.columns]
        logger.info(f"📝 One-hot encoding {len(available_categorical)} categorical columns: {available_categorical}")
        
        encoders = {}
        for col in available_categorical:
            unique_values = sorted(df[col].dropna().unique())
            logger.info(f"🔍 {col}: {len(unique_values)} unique values {unique_values}")
            
            # Save encoder mapping for inference
            encoders[col] = {'categories': unique_values, 'encoding_type': 'one_hot'}
            
            # Create one-hot encoded columns (alphabetically sorted for consistency)
            for value in unique_values:
                new_col_name = f"{col}_{value}"
                df[new_col_name] = (df[col] == value).astype(int)
                logger.info(f"  ✅ Created binary column: {new_col_name}")
            
            # Drop original column
            df = df.drop(columns=[col])
            logger.info(f"  ✅ Dropped original column: {col}")
        
        step_time = time.time() - step_start
        logger.info(f"✅ FEATURE ENCODING COMPLETED (ONE-HOT)")
        logger.info(f"  • Geography → Geography_France, Geography_Germany, Geography_Spain")
        logger.info(f"  • Gender → Gender_Female, Gender_Male")
        logger.info(f"⏱️ Processing time: {step_time:.2f} seconds")
        
        # 3.5. Feature binning for CreditScore (KEEP original CreditScore column)
        step_start = time.time()
        logger.info(f"\n{'='*60}")
        logger.info("🔢 STEP 3.5: FEATURE BINNING (KEEP CreditScore)")
        logger.info(f"{'='*60}")
        
        if 'CreditScore' in df.columns:
            logger.info(f"📊 Creating CreditScoreBins (keeping original CreditScore for model)")
            
            def bin_credit_score(score):
                if score <= 580:
                    return 0  # Poor
                elif score <= 670:
                    return 1  # Fair
                elif score <= 740:
                    return 2  # Good
                elif score <= 800:
                    return 3  # Very Good
                else:
                    return 4  # Excellent
            
            df['CreditScoreBins'] = df['CreditScore'].apply(bin_credit_score)
            # CRITICAL: Do NOT drop CreditScore - model expects both columns
            
            # Log binning distribution
            bin_dist = df['CreditScoreBins'].value_counts().sort_index()
            bin_names = ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent']
            logger.info(f"  • CreditScore binning distribution:")
            for bin_val, count in bin_dist.items():
                bin_name = bin_names[bin_val] if bin_val < len(bin_names) else 'Unknown'
                percentage = (count / len(df)) * 100
                logger.info(f"    - {bin_name} ({bin_val}): {count} ({percentage:.1f}%)")
            
            logger.info(f"  ✅ Added 'CreditScoreBins' column (kept 'CreditScore' for model compatibility)")
        else:
            logger.warning(f"  ⚠️ CreditScore column not found - skipping binning")
        
        step_time = time.time() - step_start
        logger.info(f"✅ FEATURE BINNING COMPLETED")
        logger.info(f"⏱️ Processing time: {step_time:.2f} seconds")
        
        # 4. Feature scaling using sklearn (with Age included)
        step_start = time.time()
        logger.info(f"\n{'='*60}")
        logger.info("📏 STEP 4: FEATURE SCALING (SKLEARN)")
        logger.info(f"{'='*60}")
        
        from sklearn.preprocessing import MinMaxScaler
        
        # Get scaling columns from config (now includes Age)
        scaling_config = config.get('feature_scaling', {})
        columns_to_scale = scaling_config.get('columns_to_scale', ['Balance', 'EstimatedSalary', 'Age'])
        available_numeric = [col for col in columns_to_scale if col in df.columns]
        logger.info(f"🔢 Scaling {len(available_numeric)} numeric columns: {available_numeric}")
        
        # Log before scaling statistics
        logger.info(f"📊 Before scaling statistics:")
        for col in available_numeric:
            logger.info(f"  • {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}")
        
        scaler = MinMaxScaler()
        df[available_numeric] = scaler.fit_transform(df[available_numeric])
        
        # Log after scaling statistics
        logger.info(f"📊 After scaling statistics (should be 0-1 range):")
        for col in available_numeric:
            logger.info(f"  • {col}: min={df[col].min():.3f}, max={df[col].max():.3f}, mean={df[col].mean():.3f}")
        
        step_time = time.time() - step_start
        logger.info(f"✅ FEATURE SCALING COMPLETED")
        logger.info(f"  • Scaled features: {available_numeric}")
        logger.info(f"⏱️ Processing time: {step_time:.2f} seconds")
        
        # 5. Data splitting using sklearn
        step_start = time.time()
        logger.info(f"\n{'='*60}")
        logger.info("✂️ STEP 5: DATA SPLITTING (SKLEARN)")
        logger.info(f"{'='*60}")
        
        from sklearn.model_selection import train_test_split
        
        # Clean data before splitting (remove non-numeric columns that shouldn't be features)
        logger.info(f"🧹 Cleaning data before splitting...")
        
        # Drop columns that shouldn't be features
        columns_to_drop = ['RowNumber', 'CustomerId', 'Firstname', 'Lastname']
        existing_drop_cols = [col for col in columns_to_drop if col in df.columns]
        if existing_drop_cols:
            df = df.drop(columns=existing_drop_cols)
            logger.info(f"🗑️ Dropped non-feature columns: {existing_drop_cols}")
        
        # Prepare features and target
        logger.info(f"🎯 Target column: {target_column}")
        logger.info(f"📊 Dataset before splitting: {df.shape[0]:,} rows × {df.shape[1]} columns")
        
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        # Verify all features are numeric
        non_numeric_cols = X.select_dtypes(exclude=[np.number]).columns
        if len(non_numeric_cols) > 0:
            logger.warning(f"⚠️ Found non-numeric columns in features: {list(non_numeric_cols)}")
            logger.info(f"🔧 Converting remaining categorical columns to numeric...")
            for col in non_numeric_cols:
                if col not in encoders:  # Not already encoded
                    logger.info(f"  • Emergency encoding {col}...")
                    le = LabelEncoder()
                    X[col] = le.fit_transform(X[col].astype(str))
                    encoders[col] = le
                    logger.info(f"    ✅ {col} encoded: {len(le.classes_)} unique values")
        
        logger.info(f"✅ All features are now numeric")
        logger.info(f"📊 Final feature types: {dict(X.dtypes.value_counts())}")
        
        # Log target distribution
        target_dist = y.value_counts()
        logger.info(f"📊 Target distribution:")
        for value, count in target_dist.items():
            percentage = (count / len(y)) * 100
            logger.info(f"  • {value}: {count:,} ({percentage:.1f}%)")
        
        logger.info(f"🔀 Performing stratified train-test split (test_size={test_size})")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # CRITICAL: Enforce exact column order for model compatibility
        logger.info(f"\n🔧 Enforcing exact column order for model compatibility...")
        expected_column_order = [
            'CreditScore', 'Age', 'Tenure', 'Balance', 'NumOfProducts',
            'HasCrCard', 'IsActiveMember', 'EstimatedSalary', 'CreditScoreBins',
            'Geography_France', 'Geography_Germany', 'Geography_Spain',
            'Gender_Female', 'Gender_Male'
        ]
        
        # Filter to only columns that exist
        available_columns = [col for col in expected_column_order if col in X_train.columns]
        missing_columns = [col for col in expected_column_order if col not in X_train.columns]
        extra_columns = [col for col in X_train.columns if col not in expected_column_order]
        
        if missing_columns:
            logger.warning(f"  ⚠️ Missing expected columns: {missing_columns}")
        if extra_columns:
            logger.warning(f"  ⚠️ Extra columns not in expected order: {extra_columns}")
        
        # Reorder columns
        X_train = X_train[available_columns]
        X_test = X_test[available_columns]
        
        logger.info(f"  ✅ Columns reordered: {available_columns}")
        logger.info(f"  • Total columns: {len(available_columns)}")
        
        step_time = time.time() - step_start
        logger.info(f"✅ DATA SPLITTING COMPLETED")
        logger.info(f"📊 Training set: {len(X_train):,} samples ({len(X_train)/len(df)*100:.1f}%)")
        logger.info(f"📊 Test set: {len(X_test):,} samples ({len(X_test)/len(df)*100:.1f}%)")
        logger.info(f"📊 Feature count: {X_train.shape[1]} columns")
        logger.info(f"⏱️ Processing time: {step_time:.2f} seconds")
        
        # 6. Save processed data and encoders
        step_start = time.time()
        logger.info(f"\n{'='*60}")
        logger.info("💾 STEP 6: SAVE PROCESSED DATA & ENCODERS TO S3")
        logger.info(f"{'='*60}")
        from utils.s3_io import write_df_csv, write_pickle
        import json
        
        # Prepare S3 paths with timestamp
        s3_paths = {
            'X_train': f"artifacts/data_artifacts/{pipeline_timestamp}/X_train.csv",
            'X_test': f"artifacts/data_artifacts/{pipeline_timestamp}/X_test.csv",
            'y_train': f"artifacts/data_artifacts/{pipeline_timestamp}/y_train.csv",
            'y_test': f"artifacts/data_artifacts/{pipeline_timestamp}/y_test.csv",
            'encoders': f"artifacts/data_artifacts/{pipeline_timestamp}/encoders.pkl",
            'geography_encoder': f"artifacts/data_artifacts/{pipeline_timestamp}/geography_encoder.json",
            'gender_encoder': f"artifacts/data_artifacts/{pipeline_timestamp}/gender_encoder.json",
            'scaler': f"artifacts/data_artifacts/{pipeline_timestamp}/scaler.pkl",
            'feature_names': f"artifacts/data_artifacts/{pipeline_timestamp}/feature_names.json"
        }
        
        logger.info(f"📁 S3 artifact paths:")
        for name, path in s3_paths.items():
            logger.info(f"  • {name}: s3://zuucrew-mlflow-artifacts-prod/{path}")
        
        # Save datasets to S3
        datasets = {
            'X_train': X_train,
            'X_test': X_test, 
            'y_train': y_train.to_frame(),
            'y_test': y_test.to_frame()
        }
        
        logger.info(f"💾 Uploading {len(datasets)} datasets to S3...")
        for name, dataset in datasets.items():
            dataset_size = dataset.memory_usage(deep=True).sum() / 1024**2
            logger.info(f"📤 Uploading {name}: {dataset.shape[0]:,} rows × {dataset.shape[1]} cols ({dataset_size:.2f} MB)")
            write_df_csv(dataset, key=s3_paths[name])
            logger.info(f"  ✅ {name} uploaded successfully")
        
        # Save encoders and preprocessing artifacts
        logger.info(f"\n🔧 Uploading preprocessing artifacts...")
        
        # 1. Save encoders (LabelEncoders for Geography, Gender)
        logger.info(f"📝 Saving categorical encoders...")
        write_pickle(encoders, key=s3_paths['encoders'])
        logger.info(f"  ✅ encoders.pkl: {len(encoders)} encoders (Geography, Gender)")
        
        # 2. Save individual encoder JSON files (ONE-HOT ENCODING)
        from utils.s3_io import put_bytes
        
        for col, encoder_info in encoders.items():
            encoder_data = {
                'column_name': col,
                'encoder_type': 'one_hot',
                'categories': encoder_info['categories'],
                'binary_columns': [f"{col}_{val}" for val in encoder_info['categories']],
                'num_categories': len(encoder_info['categories']),
                'timestamp': pipeline_timestamp,
                'processing_engine': 'pandas'
            }
            
            encoder_json = json.dumps(encoder_data, indent=2)
            s3_key = s3_paths[f'{col.lower()}_encoder']
            put_bytes(encoder_json.encode('utf-8'), key=s3_key)
            
            logger.info(f"  ✅ {col.lower()}_encoder.json: {col} one-hot encoder mapping")
            logger.info(f"    • Categories: {encoder_data['categories']}")
            logger.info(f"    • Binary columns: {encoder_data['binary_columns']}")
            logger.info(f"    • File: s3://zuucrew-mlflow-artifacts-prod/{s3_key}")
        
        # 3. Save scaler with metadata
        logger.info(f"📏 Saving feature scaler with metadata...")
        write_pickle(scaler, key=s3_paths['scaler'])
        
        # Save scaler metadata for inference
        scaler_metadata = {
            'columns_to_scale': available_numeric,
            'data_min': scaler.data_min_.tolist(),
            'data_max': scaler.data_max_.tolist(),
            'n_features': len(available_numeric),
            'scaling_type': 'minmax',
            'framework': 'sklearn',
            'timestamp': pipeline_timestamp
        }
        scaler_metadata_key = f"artifacts/data_artifacts/{pipeline_timestamp}/scaler_metadata.json"
        scaler_metadata_json = json.dumps(scaler_metadata, indent=2)
        put_bytes(scaler_metadata_json.encode('utf-8'), key=scaler_metadata_key)
        
        logger.info(f"  ✅ scaler.pkl: MinMaxScaler for {len(available_numeric)} numeric features")
        logger.info(f"    • Scaled features: {available_numeric}")
        logger.info(f"  ✅ scaler_metadata.json: Scaler parameters for inference")
        logger.info(f"    • Min values: {[f'{v:.2f}' for v in scaler.data_min_]}")
        logger.info(f"    • Max values: {[f'{v:.2f}' for v in scaler.data_max_]}")
        
        # 4. Save feature names and metadata
        feature_metadata = {
            'feature_columns': X_train.columns.tolist(),
            'target_column': target_column,
            'categorical_columns': available_categorical,
            'numeric_columns': available_numeric,
            'original_shape': [int(df.shape[0]), int(df.shape[1])],
            'processed_shape': [int(X_train.shape[0]), int(X_train.shape[1])],
            'test_size': test_size,
            'processing_engine': 'pandas',
            'timestamp': pipeline_timestamp
        }
        
        feature_json = json.dumps(feature_metadata, indent=2)
        put_bytes(feature_json.encode('utf-8'), key=s3_paths['feature_names'])
        logger.info(f"  ✅ feature_names.json: Dataset metadata and feature information")
        logger.info(f"    • Features: {len(feature_metadata['feature_columns'])} columns")
        logger.info(f"    • Categorical: {feature_metadata['categorical_columns']}")
        logger.info(f"    • Numeric: {feature_metadata['numeric_columns']}")
        
        step_time = time.time() - step_start
        logger.info(f"✅ DATA & PREPROCESSING ARTIFACTS SAVED")
        logger.info(f"📊 Total artifacts saved: {len(s3_paths)}")
        logger.info(f"  • Datasets: 4 files (X_train, X_test, y_train, y_test)")
        logger.info(f"  • Encoders: 3 files (encoders.pkl, geography_encoder.json, gender_encoder.json)")
        logger.info(f"  • Scaler: 1 file (scaler.pkl)")
        logger.info(f"  • Metadata: 1 file (feature_names.json)")
        logger.info(f"⏱️ Upload time: {step_time:.2f} seconds")
        
        # Pipeline completion summary
        total_pipeline_time = time.time() - pipeline_start
        logger.info(f"\n{'='*80}")
        logger.info("🎉 PANDAS DATA PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info(f"{'='*80}")
        logger.info(f"📊 FINAL RESULTS:")
        logger.info(f"  • Total processing time: {total_pipeline_time:.2f} seconds")
        logger.info(f"  • Original dataset: {df.shape[0]:,} rows × {df.shape[1]} columns")
        logger.info(f"  • Training set: {len(X_train):,} samples")
        logger.info(f"  • Test set: {len(X_test):,} samples")
        logger.info(f"  • Features: {X_train.shape[1]} columns")
        logger.info(f"  • Target: {target_column}")
        logger.info(f"📁 S3 artifacts: s3://zuucrew-mlflow-artifacts-prod/artifacts/data_artifacts/{pipeline_timestamp}/")
        logger.info(f"🔧 Preprocessing artifacts:")
        logger.info(f"  • geography_encoder.json: {len(encoders.get('Geography', {}).get('categories', []))} categories (one-hot)")
        logger.info(f"  • gender_encoder.json: {len(encoders.get('Gender', {}).get('categories', []))} categories (one-hot)") 
        logger.info(f"  • scaler.pkl: MinMax scaling for {len(available_numeric)} numeric features")
        logger.info(f"  • encoders.pkl: Combined pickle file for programmatic use")
        logger.info(f"  • feature_names.json: Complete dataset metadata")
        logger.info(f"🎯 Engine used: Pandas + Scikit-learn (fast, efficient)")
        logger.info(f"{'='*80}")
        
        # End MLflow run
        mlflow_tracker.end_run()
        
        # Return numpy arrays for compatibility
        return {
            'X_train': X_train.values,
            'X_test': X_test.values,
            'Y_train': y_train.values,
            'Y_test': y_test.values
        }
        
    except Exception as e:
        logger.error(f"❌ Pandas pipeline failed: {str(e)}")
        if 'mlflow_tracker' in locals():
            mlflow_tracker.end_run()
        raise

def _run_pyspark_pipeline(data_path, target_column, test_size, force_rebuild, output_format, pipeline_timestamp, config):
    """Run data pipeline using PySpark (for large datasets)."""
    logger.info("⚡ Using PySpark for data processing (large dataset support)")
    
    if not PYSPARK_AVAILABLE:
        raise ImportError("PySpark not available. Install PySpark or use pandas engine.")
    
    # Input validation for local files (skip for S3 paths)
    if not data_path.startswith('s3://') and not os.path.exists(data_path):
        logger.error(f"✗ Data file not found: {data_path}")
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    if not 0 < test_size < 1:
        logger.error(f"✗ Invalid test_size: {test_size}")
        raise ValueError(f"Invalid test_size: {test_size}")
    
    # Initialize Spark session
    spark = create_spark_session("ChurnPredictionDataPipeline")
    
    try:
        # Load configurations
        data_paths = get_data_paths()
        columns = get_columns()
        outlier_config = get_outlier_config()
        binning_config = get_binning_config()
        encoding_config = get_encoding_config()
        scaling_config = get_scaling_config()
        splitting_config = get_splitting_config()
        
        # Initialize MLflow tracking
        mlflow_tracker = MLflowTracker()
        run_tags = create_mlflow_run_tags('data_pipeline_pyspark', {
            'data_source': data_path,
            'force_rebuild': str(force_rebuild),
            'target_column': target_column,
            'output_format': output_format,
            'processing_engine': 'pyspark'
        })
        run = mlflow_tracker.start_run(run_name='data_pipeline_pyspark', tags=run_tags)
        
        # MLflow artifacts are now handled by S3 backend, no local directory needed
        
        # Check for existing artifacts in S3
        s3_manager = S3ArtifactManager()
        try:
            latest_paths = s3_manager.get_latest_artifacts(['X_train', 'X_test', 'Y_train', 'Y_test'], artifact_type='data_artifacts', format_ext='csv')
            artifacts_exist = len(latest_paths) == 4
        except Exception as e:
            logger.info(f"Could not check S3 artifacts: {e}")
            artifacts_exist = False
        
        if artifacts_exist and not force_rebuild:
            logger.info("✓ Loading existing processed data artifacts from S3")
            from s3_io import read_df_csv
            X_train = read_df_csv(key=latest_paths['X_train'])
            X_test = read_df_csv(key=latest_paths['X_test'])
            Y_train = read_df_csv(key=latest_paths['Y_train'])
            Y_test = read_df_csv(key=latest_paths['Y_test'])
            
            mlflow_tracker.log_data_pipeline_metrics({
                'total_samples': len(X_train) + len(X_test),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'processing_engine': 'existing_artifacts'
            })
            mlflow_tracker.end_run()
            
            logger.info("✓ Data pipeline completed using existing artifacts")
            return {
                'X_train': X_train.values,
                'X_test': X_test.values,
                'Y_train': Y_train.values.ravel(),
                'Y_test': Y_test.values.ravel()
            }
        
        # Process data from scratch with PySpark
        logger.info("Processing data from scratch with PySpark...")
        
        # Data ingestion
        logger.info(f"\n{'='*80}")
        logger.info(f"DATA INGESTION STEP")
        logger.info(f"{'='*80}")
        
        # Check if we should load from S3 or local
        if force_s3_io():
            # Try to load from S3 first using boto3 (more reliable than S3A)
            from s3_io import key_exists, read_df_csv
            s3_key = data_path  # Use local path as S3 key (data/raw/ChurnModelling.csv)
            bucket = get_s3_bucket()
            
            if key_exists(s3_key):
                logger.info(f"📁 Loading raw data from S3 using boto3: s3://{bucket}/{s3_key}")
                # Use boto3 to load CSV instead of S3A (more reliable)
                df_pandas = read_df_csv(key=s3_key)
                # Convert to Spark DataFrame
                df = spark.createDataFrame(df_pandas)
                logger.info(f"✅ Successfully loaded CSV data from S3 - Shape: ({df.count()}, {len(df.columns)})")
            else:
                logger.warning(f"⚠️ Raw data not found in S3: {s3_key}, using local file")
                logger.info(f"💡 Run 'make s3-upload-data' to upload raw data to S3")
                ingestor = DataIngestorCSV(spark)
                df = ingestor.ingest(data_path)
        else:
            # Use local file
            logger.info(f"📁 Loading from local file: {data_path}")
            ingestor = DataIngestorCSV(spark)
            df = ingestor.ingest(data_path)
        logger.info(f"✓ Raw data loaded: {get_dataframe_info(df)}")
        
        # Log raw data metrics
        log_stage_metrics(df, 'raw', spark=spark)
        
        # Validate target column
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found")
        
        # Handle missing values
        logger.info(f"\n{'='*80}")
        logger.info(f"HANDLING MISSING VALUES STEP")
        logger.info(f"{'='*80}")
        initial_count = df.count()
        
        # Drop critical missing values
        drop_handler = DropMissingValuesStrategy(critical_columns=columns['critical_columns'], spark=spark)
        df = drop_handler.handle(df)
        
        # Fill Age column
        age_handler = FillMissingValuesStrategy(method='mean', relevant_column='Age', spark=spark)
        df = age_handler.handle(df)
        
        # Fill Gender column (skip API-based imputation for now, use simple fill)
        df = df.fillna({'Gender': 'Unknown'})
        
        rows_removed = initial_count - df.count()
        log_stage_metrics(df, 'missing_handled', {'rows_removed': rows_removed}, spark)
        logger.info(f"✓ Missing values handled: {initial_count} → {df.count()}")
        
        # Outlier detection
        logger.info(f"\n{'='*80}")
        logger.info(f"OUTLIER DETECTION STEP")
        logger.info(f"{'='*80}")
        initial_count = df.count()
        outlier_detector = OutlierDetector(strategy=IQROutlierDetection(spark=spark))
        df = outlier_detector.handle_outliers(df, columns['outlier_columns'], method='remove')
        
        outliers_removed = initial_count - df.count()
        log_stage_metrics(df, 'outliers_removed', {'outliers_removed': outliers_removed}, spark)
        logger.info(f"✓ Outliers removed: {initial_count} → {df.count()}")
        
        # Feature binning
        logger.info(f"\n{'='*80}")
        logger.info(f"FEATURE BINNING STEP")
        logger.info(f"{'='*80}")
        binning = CustomBinningStrategy(binning_config['credit_score_bins'], spark=spark)
        df = binning.bin_feature(df, 'CreditScore')
        
        # Log binning distribution
        if 'CreditScoreBins' in df.columns:
            bin_dist = df.groupBy('CreditScoreBins').count().collect()
            bin_metrics = {f'credit_score_bin_{row["CreditScoreBins"]}': row['count'] for row in bin_dist}
            mlflow.log_metrics(bin_metrics)
        
        logger.info("✓ Feature binning completed")
        
        # Feature encoding
        logger.info(f"\n{'='*80}")
        logger.info(f"FEATURE ENCODING STEP")
        logger.info(f"{'='*80}")
        nominal_strategy = NominalEncodingStrategy(encoding_config['nominal_columns'], spark=spark)
        ordinal_strategy = OrdinalEncodingStrategy(encoding_config['ordinal_mappings'], spark=spark)
        
        df = nominal_strategy.encode(df)
        df = ordinal_strategy.encode(df)
        
        log_stage_metrics(df, 'encoded', spark=spark)
        logger.info("✓ Feature encoding completed")
        
        # Feature scaling
        logger.info(f"\n{'='*80}")
        logger.info(f"FEATURE SCALING STEP")
        logger.info(f"{'='*80}")
        minmax_strategy = MinMaxScalingStrategy(spark=spark)
        df = minmax_strategy.scale(df, scaling_config['columns_to_scale'])
        logger.info("✓ Feature scaling completed")
        
        # Post-processing - drop unnecessary columns
        drop_columns = ['RowNumber', 'CustomerId', 'Firstname', 'Lastname']
        existing_drop_columns = [col for col in drop_columns if col in df.columns]
        if existing_drop_columns:
            df = df.drop(*existing_drop_columns)
            logger.info(f"✓ Dropped columns: {existing_drop_columns}")
        
        # Data splitting
        logger.info(f"\n{'='*80}")
        logger.info(f"DATA SPLITTING STEP")
        logger.info(f"{'='*80}")
        splitting_strategy = SimpleTrainTestSplitStrategy(test_size=splitting_config['test_size'], spark=spark)
        X_train, X_test, Y_train, Y_test = splitting_strategy.split_data(df, target_column)
        
        # Save processed data
        output_paths = save_processed_data(X_train, X_test, Y_train, Y_test, pipeline_timestamp, output_format)
        
        logger.info("✓ Data splitting completed")
        logger.info(f"\nDataset shapes after splitting:")
        logger.info(f"  • X_train: {X_train.count()} rows, {len(X_train.columns)} columns")
        logger.info(f"  • X_test:  {X_test.count()} rows, {len(X_test.columns)} columns")
        logger.info(f"  • Y_train: {Y_train.count()} rows, 1 column")
        logger.info(f"  • Y_test:  {Y_test.count()} rows, 1 column")
        logger.info(f"  • Feature columns: {X_train.columns}")
        
        # Save preprocessing pipeline metadata to S3
        if hasattr(minmax_strategy, 'scaler_models'):
            # Save metadata about the preprocessing to S3
            preprocessing_metadata = {
                'scaling_columns': scaling_config['columns_to_scale'],
                'encoding_columns': encoding_config['nominal_columns'],
                'ordinal_mappings': encoding_config['ordinal_mappings'],
                'binning_config': binning_config,
                'spark_version': spark.version,
                'timestamp': pipeline_timestamp
            }
            
            # Try to save to S3, fallback to local if needed
            try:
                metadata_s3_key = f"artifacts/data_artifacts/{pipeline_timestamp}/preprocessing_metadata.json"
                from s3_io import put_bytes
                metadata_json = json.dumps(preprocessing_metadata, indent=2).encode('utf-8')
                put_bytes(metadata_json, key=metadata_s3_key, content_type='application/json')
                
                logger.info(f"✓ Saved preprocessing metadata to s3://{get_s3_bucket()}/{metadata_s3_key}")
                
            except Exception as s3_error:
                # Fallback to local save
                logger.warning(f"S3 metadata save failed ({s3_error}), saving locally")
                local_metadata_path = f'artifacts/encode/preprocessing_metadata_{pipeline_timestamp}.json'
                with open(local_metadata_path, 'w') as f:
                    json.dump(preprocessing_metadata, f, indent=2)
                logger.info(f"✓ Saved preprocessing metadata locally: {local_metadata_path}")
        
        # Final metrics and visualizations
        log_stage_metrics(X_train, 'final_train', spark=spark)
        log_stage_metrics(X_test, 'final_test', spark=spark)
        
        # Log comprehensive pipeline metrics
        comprehensive_metrics = {
            'total_samples': X_train.count() + X_test.count(),
            'train_samples': X_train.count(),
            'test_samples': X_test.count(),
            'final_features': len(X_train.columns),
            'processing_engine': 'pyspark',
            'output_format': output_format
        }
        
        # Get class distribution
        train_dist = Y_train.groupBy(target_column).count().collect()
        test_dist = Y_test.groupBy(target_column).count().collect()
        
        for row in train_dist:
            comprehensive_metrics[f'train_class_{row[target_column]}'] = row['count']
        for row in test_dist:
            comprehensive_metrics[f'test_class_{row[target_column]}'] = row['count']
        
        mlflow_tracker.log_data_pipeline_metrics(comprehensive_metrics)
        
        # Log parameters
        mlflow.log_params({
            'final_feature_names': X_train.columns,
            'preprocessing_steps': ['missing_values', 'outlier_detection', 'feature_binning', 
                                  'feature_encoding', 'feature_scaling'],
            'data_pipeline_version': '3.0_pyspark'
        })
        
        # Log artifacts
        for path_key, path_value in output_paths.items():
            if os.path.exists(path_value):
                mlflow.log_artifact(path_value, "processed_datasets")
        
        mlflow_tracker.end_run()
        
        # Convert to numpy arrays for return
        X_train_np = spark_to_pandas(X_train).values
        X_test_np = spark_to_pandas(X_test).values
        Y_train_np = spark_to_pandas(Y_train).values.ravel()
        Y_test_np = spark_to_pandas(Y_test).values.ravel()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"FINAL DATASET SHAPES")
        logger.info(f"{'='*80}")
        logger.info(f"✓ Final dataset shapes:")
        logger.info(f"  • X_train shape: {X_train_np.shape} (rows: {X_train_np.shape[0]}, features: {X_train_np.shape[1]})")
        logger.info(f"  • X_test shape:  {X_test_np.shape} (rows: {X_test_np.shape[0]}, features: {X_test_np.shape[1]})")
        logger.info(f"  • Y_train shape: {Y_train_np.shape} (rows: {Y_train_np.shape[0]})")
        logger.info(f"  • Y_test shape:  {Y_test_np.shape} (rows: {Y_test_np.shape[0]})")
        logger.info(f"  • Total samples: {X_train_np.shape[0] + X_test_np.shape[0]}")
        logger.info(f"  • Train/Test ratio: {X_train_np.shape[0]/(X_train_np.shape[0] + X_test_np.shape[0]):.1%} / {X_test_np.shape[0]/(X_train_np.shape[0] + X_test_np.shape[0]):.1%}")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"{'='*80}")
        logger.info("✓ PySpark data pipeline completed successfully!")
        
        return {
            'X_train': X_train_np,
            'X_test': X_test_np,
            'Y_train': Y_train_np,
            'Y_test': Y_test_np
        }
        
    except Exception as e:
        logger.error(f"✗ Data pipeline failed: {str(e)}")
        if 'mlflow_tracker' in locals():
            mlflow_tracker.end_run()
        raise
    finally:
        # Stop Spark session
        stop_spark_session(spark)


def main():
    """Main function with argparse for PySpark control."""
    global PYSPARK_AVAILABLE
    
    parser = argparse.ArgumentParser(description="Data Processing Pipeline")
    parser.add_argument(
        '--pyspark', 
        action='store_true', 
        help='Enable PySpark for large dataset processing (default: use pandas)'
    )
    parser.add_argument(
        '--engine',
        choices=['pandas', 'pyspark'],
        default='pandas',
        help='Processing engine to use (default: pandas)'
    )
    parser.add_argument(
        '--output-format',
        choices=['csv', 'parquet', 'both'],
        default='csv',
        help='Output format for processed data (default: csv)'
    )
    
    args = parser.parse_args()
    
    # Set global PYSPARK_AVAILABLE based on arguments
    PYSPARK_AVAILABLE = args.pyspark or (args.engine == 'pyspark')
    
    # Re-import modules with updated PYSPARK_AVAILABLE if needed
    if PYSPARK_AVAILABLE:
        logger.info("🔄 PySpark mode enabled - reimporting modules...")
        # Note: In practice, you'd restart the process for clean imports
        
    logger.info(f"🎯 Command line arguments:")
    logger.info(f"  • PySpark enabled: {PYSPARK_AVAILABLE}")
    logger.info(f"  • Processing engine: {args.engine}")
    logger.info(f"  • Output format: {args.output_format}")
    
    # Run the pipeline with specified engine
    processed_data = data_pipeline(
        processing_engine=args.engine,
        output_format=args.output_format
    )
    
    if processed_data and 'X_train' in processed_data:
        logger.info(f"🎉 Pipeline completed successfully!")
        if hasattr(processed_data['X_train'], 'shape'):
            logger.info(f"📊 Train samples: {processed_data['X_train'].shape[0]}")
        else:
            logger.info(f"📊 Train samples: {len(processed_data['X_train'])}")

if __name__ == "__main__":
    main()