import json
import logging
import os
import joblib, sys
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
# Manual PySpark availability flag - set to False to prioritize pandas
PYSPARK_AVAILABLE = False  # Set to True to enable PySpark, False for pandas-only

# Conditional PySpark imports
if PYSPARK_AVAILABLE:
    try:
        from pyspark.sql import SparkSession, DataFrame as SparkDataFrame
        from pyspark.sql import functions as F
    except ImportError:
        PYSPARK_AVAILABLE = False
        SparkSession = None
        SparkDataFrame = None
else:
    SparkSession = None
    SparkDataFrame = None
from utils.spark_session import get_or_create_spark_session
from utils.spark_utils import spark_to_pandas

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from utils.config import get_binning_config, get_encoding_config
logging.basicConfig(level=logging.INFO, format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

""" 
{
  "RowNumber": 1,
  "CustomerId": 15634602,
  "Firstname": "Grace",
  "Lastname": "Williams",
  "CreditScore": 619,
  "Geography": "France",
  "Gender": "Female",
  "Age": 42,
  "Tenure": 2,
  "Balance": 0,
  "NumOfProducts": 1,
  "HasCrCard": 1,
  "IsActiveMember": 1,
  "EstimatedSalary": 101348.88,
}

"""
class ModelInference:
    """
    Enhanced model inference class with comprehensive logging and error handling.
    """
    
    def __init__(self, model_path: str, use_spark: bool = False, spark: Optional[SparkSession] = None):
        """
        Initialize the model inference system.
        
        Args:
            model_path: Path to the trained model file
            use_spark: Whether to use PySpark for preprocessing (default: False for single records)
            spark: Optional SparkSession instance
            
        Raises:
            ValueError: If model_path is invalid
            FileNotFoundError: If model file doesn't exist
        """
        logger.info(f"\n{'='*60}")
        logger.info("INITIALIZING MODEL INFERENCE")
        logger.info(f"{'='*60}")
        
        if not model_path or not isinstance(model_path, str):
            logger.error("✗ Invalid model path provided")
            raise ValueError("Invalid model path provided")
            
        self.model_path = model_path
        self.encoders = {}
        self.scaler = None
        self.scaler_metadata = None
        self.model = None
        self.use_spark = use_spark
        self.spark = spark if spark else (get_or_create_spark_session() if use_spark else None)
        
        logger.info(f"Model Path: {model_path}")
        logger.info(f"Processing Engine: {'PySpark' if use_spark else 'Pandas'}")
        
        try:
            # Load model and configurations
            self.load_model()
            self.binning_config = get_binning_config()
            self.encoding_config = get_encoding_config()
            
            # Load scaler metadata
            self._load_scaler_metadata()
            
            logger.info("✓ Model inference system initialized successfully")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize model inference: {str(e)}")
            raise

    def load_model(self) -> None:
        """
        Load the trained model from disk with validation.
        
        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: For any loading errors
        """
        logger.info("Loading trained model...")
        
        # Import S3 utilities for model loading
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
        from s3_io import read_pickle, key_exists
        from s3_artifact_manager import S3ArtifactManager
        from config import get_s3_bucket
        
        bucket = get_s3_bucket()
        
        # Try to load model from local artifacts first, then S3
        logger.info("Loading model from local artifacts or S3...")
        
        import time
        import glob
        import json
        start_time = time.time()
        
        # First, try to find local model metadata files
        local_model_metadata_pattern = "artifacts/train_artifacts/model_metadata_*.json"
        local_metadata_files = glob.glob(local_model_metadata_pattern)
        
        if local_metadata_files:
            # Use the latest local metadata file
            latest_local_metadata = max(local_metadata_files, key=os.path.getctime)
            logger.info(f"Found local model metadata: {latest_local_metadata}")
            
            with open(latest_local_metadata, 'r') as f:
                metadata = json.load(f)
            
            train_artifacts_dir = os.path.dirname(latest_local_metadata)
            mlflow_model_path = metadata.get('mlflow_model_path')
            
            logger.info(f"📁 Using local model artifacts from: {train_artifacts_dir}")
            logger.info(f"📊 Model metadata: {metadata}")
            
        else:
            # Fallback to S3 if no local metadata found
            logger.info("No local model metadata found, trying S3...")
            
            # Get latest timestamp folder dynamically from S3
            latest_timestamp = self._get_latest_model_timestamp_from_s3(bucket)
            if not latest_timestamp:
                logger.error(f"❌ No model timestamp folders found in S3")
                raise FileNotFoundError(f"No model artifacts found in S3")
                
            train_artifacts_dir = f"artifacts/train_artifacts/{latest_timestamp}"
            metadata_s3_key = f"{train_artifacts_dir}/model_metadata.json"
            
            logger.info(f"📁 Using latest train artifacts directory: {train_artifacts_dir}")
            logger.info(f"🔍 Looking for metadata: s3://{bucket}/{metadata_s3_key}")
            
            # Try to read the metadata (optional - we can proceed without it)
            metadata = {}
            model_name = None
            mlflow_model_path = None
            
            try:
                from utils.s3_io import get_bytes, key_exists
                if key_exists(metadata_s3_key):
                    metadata_bytes = get_bytes(metadata_s3_key)
                    metadata = json.loads(metadata_bytes.decode('utf-8'))
                    model_name = metadata.get('model_name')
                    mlflow_model_path = metadata.get('mlflow_model_path')
                    
                    logger.info(f"✅ Model metadata loaded:")
                    logger.info(f"  • Model name: {model_name}")
                    logger.info(f"  • MLflow path: {mlflow_model_path}")
                else:
                    logger.info(f"⚠️ No metadata file found, proceeding with dynamic discovery...")
            except Exception as metadata_error:
                logger.warning(f"⚠️ Failed to load metadata (proceeding anyway): {metadata_error}")
                
        # Try to load the Spark model directly from local or S3 model artifacts directory
        try:
            from pyspark.ml import PipelineModel
            
            if local_metadata_files:
                # Load from local model artifacts
                spark_model_path = metadata.get('spark_model_path', f"artifacts/train_artifacts/{metadata['timestamp']}/spark_model")
                logger.info(f"🔍 Attempting to load Spark model from local path: {spark_model_path}")
                
                if os.path.exists(spark_model_path):
                    self.model = PipelineModel.load(spark_model_path)
                    self.model_type = 'spark_s3'
                    logger.info(f"✅ Successfully loaded local Spark model from: {spark_model_path}")
                    
                    # Load encoders from local files
                    if 'encoders' in metadata:
                        for encoder_name, encoder_path in metadata['encoders'].items():
                            if os.path.exists(encoder_path):
                                logger.info(f"📋 Loading local encoder: {encoder_name} from {encoder_path}")
                                with open(encoder_path, 'r') as f:
                                    encoder_data = json.load(f)
                                    self.encoders[encoder_name] = encoder_data
                            else:
                                logger.warning(f"⚠️ Local encoder not found: {encoder_path}")
                    
                    load_time = time.time() - start_time
                    logger.info(f"✅ Local model loaded successfully in {load_time:.2f} seconds")
                    return
                else:
                    raise FileNotFoundError(f"Local Spark model not found at: {spark_model_path}")
            else:
                # Construct S3A path for the Spark model directory
                # The model should be saved as a directory in S3 model artifacts
                spark_model_s3a_path = f"s3a://{bucket}/{train_artifacts_dir}/spark_model"
                
                logger.info(f"🔍 Attempting to load Spark model from: {spark_model_s3a_path}")
                
                # Try to load the PipelineModel directly from S3A
                try:
                    self.model = PipelineModel.load(spark_model_s3a_path)
                    self.model_type = 'spark_s3'
                    
                    load_time = time.time() - start_time
                    logger.info(f"✅ Model loaded directly from S3 in {load_time:.2f} seconds")
                    logger.info(f"  • Model path: {spark_model_s3a_path}")
                    logger.info(f"  • Model stages: {len(self.model.stages)}")
                    
                    # Load encoders from S3 data_artifacts folder
                    self._load_encoders_from_s3()
                    return
                    
                except Exception as s3_load_error:
                    logger.warning(f"⚠️ Direct S3 Spark model loading failed: {s3_load_error}")
                    logger.info("🔄 Trying sklearn model fallback...")
                    
                    # Try to load sklearn model from S3 model artifacts
                    try:
                        from utils.s3_io import read_pickle
                        sklearn_model_key = f"{train_artifacts_dir}/sklearn_model.pkl"
                        
                        logger.info(f"🔍 Attempting to load sklearn model from: s3://{bucket}/{sklearn_model_key}")
                        self.model = read_pickle(key=sklearn_model_key)
                        self.model_type = 'sklearn_s3'
                        
                        load_time = time.time() - start_time
                        logger.info(f"✅ Sklearn fallback model loaded from S3 in {load_time:.2f} seconds")
                        logger.info(f"  • Model type: {type(self.model).__name__}")
                        
                        # Load encoders from S3 data_artifacts folder
                        self._load_encoders_from_s3()
                        return
                        
                    except Exception as sklearn_load_error:
                        logger.warning(f"⚠️ Sklearn model loading also failed: {sklearn_load_error}")
                        
                        # Final fallback: Try MLflow if available
                        if mlflow_model_path:
                            logger.info(f"🔄 Final fallback - trying MLflow: {mlflow_model_path}")
                            try:
                                import mlflow.spark
                                self.model = mlflow.spark.load_model(mlflow_model_path)
                                self.model_type = 'spark_mlflow'
                                
                                load_time = time.time() - start_time
                                logger.info(f"✅ Model loaded from MLflow final fallback in {load_time:.2f} seconds")
                                
                                # Load encoders from S3 data_artifacts folder
                                self._load_encoders_from_s3()
                                return
                                
                            except Exception as mlflow_fallback_error:
                                logger.error(f"❌ All model loading methods failed!")
                                logger.error(f"  • Spark S3: {s3_load_error}")
                                logger.error(f"  • Sklearn S3: {sklearn_load_error}")
                                logger.error(f"  • MLflow: {mlflow_fallback_error}")
                                raise FileNotFoundError(f"All model loading failed. Check S3 model artifacts directory.")
                        else:
                            logger.error(f"❌ Both S3 model loading methods failed!")
                            logger.error(f"  • Spark S3: {s3_load_error}")
                            logger.error(f"  • Sklearn S3: {sklearn_load_error}")
                            raise FileNotFoundError(f"No working model found in S3 model artifacts")
                            
                except Exception as model_load_error:
                    logger.error(f"❌ Model loading failed: {model_load_error}")
                    raise FileNotFoundError(f"Failed to load model from S3 artifacts: {model_load_error}")
                    
        except Exception as metadata_error:
            logger.error(f"❌ Failed to read model metadata: {metadata_error}")
            raise FileNotFoundError(f"Failed to read model metadata: {metadata_error}")
            
        logger.error(f"✗ No model metadata found for base name: {self.model_path}")
        raise FileNotFoundError(f"No model metadata found with base name: {self.model_path}")

    def _get_latest_model_timestamp_from_s3(self, bucket: str) -> Optional[str]:
        """
        Dynamically get the latest model timestamp folder from S3.
        
        Args:
            bucket: S3 bucket name
            
        Returns:
            Latest timestamp string or None if no folders found
        """
        try:
            from utils.s3_io import list_keys
            
            # List all keys in model_artifacts directory
            prefix = "artifacts/train_artifacts/"
            keys = list_keys(prefix=prefix)
            
            # Extract timestamp folders (format: YYYYMMDDHHMMSS)
            timestamps = set()
            for key in keys:
                # Remove prefix and get the first path component (timestamp)
                relative_path = key[len(prefix):]
                if '/' in relative_path:
                    timestamp_candidate = relative_path.split('/')[0]
                    # Validate it's a timestamp (14 digits)
                    if timestamp_candidate.isdigit() and len(timestamp_candidate) == 14:
                        timestamps.add(timestamp_candidate)
            
            if not timestamps:
                logger.warning(f"⚠️ No timestamp folders found in s3://{bucket}/{prefix}")
                return None
                
            # Get the latest (max) timestamp
            latest_timestamp = max(timestamps)
            logger.info(f"📅 Found {len(timestamps)} timestamp folders, using latest: {latest_timestamp}")
            return latest_timestamp
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest timestamp from S3: {e}")
            return None
    
    def _get_latest_data_timestamp_from_s3(self, bucket: str) -> Optional[str]:
        """
        Dynamically get the latest data artifacts timestamp folder from S3.
        
        Args:
            bucket: S3 bucket name
            
        Returns:
            Latest timestamp string or None if no folders found
        """
        try:
            from utils.s3_io import list_keys
            
            # List all keys in data_artifacts directory
            prefix = "artifacts/data_artifacts/"
            keys = list_keys(prefix=prefix)
            
            # Extract timestamp folders (format: YYYYMMDDHHMMSS)
            timestamps = set()
            for key in keys:
                # Remove prefix and get the first path component (timestamp)
                relative_path = key[len(prefix):]
                if '/' in relative_path:
                    timestamp_candidate = relative_path.split('/')[0]
                    # Validate it's a timestamp (14 digits)
                    if timestamp_candidate.isdigit() and len(timestamp_candidate) == 14:
                        timestamps.add(timestamp_candidate)
            
            if not timestamps:
                logger.warning(f"⚠️ No data timestamp folders found in s3://{bucket}/{prefix}")
                return None
                
            # Get the latest (max) timestamp
            latest_timestamp = max(timestamps)
            logger.info(f"📅 Found {len(timestamps)} data timestamp folders, using latest: {latest_timestamp}")
            return latest_timestamp
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest data timestamp from S3: {e}")
            return None
    
    def _load_encoders_from_s3(self) -> None:
        """Load feature encoders from S3 using dynamic timestamp discovery"""
        try:
            import json
            from utils.s3_io import get_bytes, key_exists
            from utils.config import get_s3_bucket
            
            bucket = get_s3_bucket()
            logger.info("Loading feature encoders from S3...")
            
            # Get latest data artifacts timestamp dynamically (same logic as model loading)
            latest_data_timestamp = self._get_latest_data_timestamp_from_s3(bucket)
            if not latest_data_timestamp:
                logger.warning("⚠️ No data artifacts timestamp folders found in S3")
                logger.info("Continuing without encoders - some preprocessing steps may be skipped")
                return
            
            logger.info(f"📅 Using latest data artifacts timestamp: {latest_data_timestamp}")
            
            # List of encoder files to look for (lowercase filenames)
            encoder_files = ['gender_encoder.json', 'geography_encoder.json']
            
            for encoder_file in encoder_files:
                encoder_name = encoder_file.replace('_encoder.json', '').capitalize()
                encoder_path = f"artifacts/data_artifacts/{latest_data_timestamp}/{encoder_file}"
                
                try:
                    if key_exists(encoder_path):
                        logger.info(f"🔍 Loading {encoder_name} encoder from: s3://{bucket}/{encoder_path}")
                        encoder_bytes = get_bytes(encoder_path)
                        encoder_data = json.loads(encoder_bytes.decode('utf-8'))
                        self.encoders[encoder_name] = encoder_data
                        logger.info(f"✅ {encoder_name} encoder loaded: type={encoder_data.get('encoder_type', 'unknown')}, categories={encoder_data.get('categories', [])}")
                    else:
                        logger.warning(f"⚠️ Encoder not found: {encoder_path}")
                        
                except Exception as encoder_error:
                    logger.warning(f"⚠️ Failed to load {encoder_name} encoder: {encoder_error}")
            
            logger.info(f"✓ Loaded {len(self.encoders)} feature encoders from S3")
            
        except Exception as e:
            logger.warning(f"⚠ Failed to load encoders from S3: {e}")
            logger.info("Continuing without encoders - some preprocessing steps may be skipped")
    
    def _load_scaler_metadata(self) -> None:
        """Load scaler metadata from S3 for inference"""
        try:
            import json
            from utils.s3_io import get_bytes, key_exists, read_pickle
            from utils.config import get_s3_bucket
            
            bucket = get_s3_bucket()
            logger.info("Loading scaler metadata from S3...")
            
            # Get latest data artifacts timestamp
            latest_data_timestamp = self._get_latest_data_timestamp_from_s3(bucket)
            if not latest_data_timestamp:
                logger.warning("⚠️ No scaler metadata found - scaling will be skipped")
                return
            
            # Load scaler object
            scaler_path = f"artifacts/data_artifacts/{latest_data_timestamp}/scaler.pkl"
            try:
                if key_exists(scaler_path):
                    self.scaler = read_pickle(scaler_path)
                    logger.info(f"✅ Scaler object loaded from: s3://{bucket}/{scaler_path}")
                else:
                    logger.warning(f"⚠️ Scaler not found: {scaler_path}")
                    return
            except Exception as scaler_error:
                logger.warning(f"⚠️ Failed to load scaler: {scaler_error}")
                return
            
            # Load scaler metadata
            metadata_path = f"artifacts/data_artifacts/{latest_data_timestamp}/scaler_metadata.json"
            try:
                if key_exists(metadata_path):
                    metadata_bytes = get_bytes(metadata_path)
                    self.scaler_metadata = json.loads(metadata_bytes.decode('utf-8'))
                    logger.info(f"✅ Scaler metadata loaded from: s3://{bucket}/{metadata_path}")
                    logger.info(f"  • Columns to scale: {self.scaler_metadata.get('columns_to_scale', [])}")
                    logger.info(f"  • Scaling type: {self.scaler_metadata.get('scaling_type', 'unknown')}")
                else:
                    logger.warning(f"⚠️ Scaler metadata not found: {metadata_path}")
            except Exception as metadata_error:
                logger.warning(f"⚠️ Failed to load scaler metadata: {metadata_error}")
                
        except Exception as e:
            logger.warning(f"⚠ Failed to load scaler: {e}")
            logger.info("Continuing without scaler - features will not be scaled")

    def load_encoders(self, encoders_dir: str) -> None:
        """
        Load feature encoders from directory with validation and logging.
        
        Args:
            encoders_dir: Directory containing encoder JSON files
            
        Raises:
            FileNotFoundError: If encoders directory doesn't exist
            Exception: For any loading errors
        """
        logger.info(f"\n{'='*50}")
        logger.info("LOADING FEATURE ENCODERS")
        logger.info(f"{'='*50}")
        
        if not os.path.exists(encoders_dir):
            logger.error(f"✗ Encoders directory not found: {encoders_dir}")
            raise FileNotFoundError(f"Encoders directory not found: {encoders_dir}")
        
        try:
            encoder_files = [f for f in os.listdir(encoders_dir) if f.endswith('_encoder.json')]
            
            if not encoder_files:
                logger.warning("⚠ No encoder files found in directory")
                return
            
            logger.info(f"Found {len(encoder_files)} encoder files")
            
            for file in encoder_files:
                feature_name = file.split('_encoder.json')[0]
                file_path = os.path.join(encoders_dir, file)
                
                with open(file_path, 'r') as f:
                    encoder_data = json.load(f)
                    self.encoders[feature_name] = encoder_data
                    
                logger.info(f"  ✓ Loaded encoder for '{feature_name}': {len(encoder_data)} mappings")
            
            logger.info(f"✓ All encoders loaded successfully")
            logger.info(f"{'='*50}\n")
            
        except Exception as e:
            logger.error(f"✗ Failed to load encoders: {str(e)}")
            raise

    def preprocess_input(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Preprocess input data for model prediction with ONE-HOT encoding and proper scaling.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Preprocessed DataFrame ready for prediction
            
        Raises:
            ValueError: If input data is invalid
            Exception: For any preprocessing errors
        """
        logger.info(f"\n{'='*50}")
        logger.info("PREPROCESSING INPUT DATA")
        logger.info(f"{'='*50}")
        
        if not data or not isinstance(data, dict):
            logger.error("✗ Input data must be a non-empty dictionary")
            raise ValueError("Input data must be a non-empty dictionary")
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame([data])
            logger.info(f"✓ Input data converted to DataFrame: {df.shape}")
            logger.info(f"  • Input features: {list(df.columns)}")
            
            # Drop unnecessary columns first
            drop_columns = ['RowNumber', 'CustomerId', 'Firstname', 'Lastname']
            existing_drop_columns = [col for col in drop_columns if col in df.columns]
            if existing_drop_columns:
                df = df.drop(columns=existing_drop_columns)
                logger.info(f"  ✓ Dropped columns: {existing_drop_columns}")
            
            # Apply ONE-HOT encoding for categorical variables
            if self.encoders:
                logger.info("Applying ONE-HOT encoding for categorical features...")
                for col, encoder_info in self.encoders.items():
                    if col in df.columns:
                        original_value = df[col].iloc[0]
                        encoder_type = encoder_info.get('encoder_type', 'unknown')
                        
                        if encoder_type == 'one_hot':
                            # Get categories from encoder
                            categories = encoder_info.get('categories', [])
                            logger.info(f"  • {col}: {original_value} → one-hot encoding")
                            
                            # Create binary columns for each category
                            for category in categories:
                                new_col_name = f"{col}_{category}"
                                df[new_col_name] = (df[col] == category).astype(int)
                            
                            # Drop original column
                            df = df.drop(columns=[col])
                            
                            binary_cols = [f"{col}_{cat}" for cat in categories]
                            logger.info(f"    ✓ Created binary columns: {binary_cols}")
                        else:
                            logger.warning(f"  ⚠ Unknown encoder type '{encoder_type}' for {col}")
                    else:
                        logger.warning(f"  ⚠ Column '{col}' not found in input data")
            else:
                logger.warning("No encoders available - skipping encoding step")

            # Apply feature binning (KEEP CreditScore)
            if 'CreditScore' in df.columns:
                logger.info("Applying feature binning for CreditScore...")
                original_score = df['CreditScore'].iloc[0]
                
                def bin_credit_score(score):
                    if score is None or pd.isna(score):
                        return 2  # Default to 'Good'
                    elif score <= 580:
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
                
                binned_score = df['CreditScoreBins'].iloc[0]
                bin_names = ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent']
                logger.info(f"  ✓ CreditScore: {original_score} → CreditScoreBins: {binned_score} ({bin_names[binned_score] if binned_score < len(bin_names) else 'Unknown'})")
                logger.info(f"  ✓ Kept 'CreditScore' column for model compatibility")
            else:
                logger.warning("  ⚠ CreditScore not found - skipping binning")
            
            # Apply feature scaling using loaded scaler
            if self.scaler is not None and self.scaler_metadata is not None:
                columns_to_scale = self.scaler_metadata.get('columns_to_scale', [])
                available_scale_cols = [col for col in columns_to_scale if col in df.columns]
                
                if available_scale_cols:
                    logger.info(f"Applying feature scaling to {len(available_scale_cols)} columns: {available_scale_cols}")
                    
                    # Log before scaling
                    for col in available_scale_cols:
                        logger.info(f"  • {col}: {df[col].iloc[0]:.4f} (before scaling)")
                    
                    # Apply scaling using pre-fitted scaler (NO re-fitting)
                    df[available_scale_cols] = self.scaler.transform(df[available_scale_cols])
                    
                    # Log after scaling
                    for col in available_scale_cols:
                        logger.info(f"  ✓ {col}: {df[col].iloc[0]:.4f} (after scaling)")
                else:
                    logger.warning(f"  ⚠ No scalable columns found in data")
            else:
                logger.warning("No scaler available - skipping scaling step")
            
            # CRITICAL: Enforce exact column order for model compatibility
            logger.info("\n🔧 Enforcing exact column order for model compatibility...")
            expected_column_order = [
                'CreditScore', 'Age', 'Tenure', 'Balance', 'NumOfProducts',
                'HasCrCard', 'IsActiveMember', 'EstimatedSalary', 'CreditScoreBins',
                'Geography_France', 'Geography_Germany', 'Geography_Spain',
                'Gender_Female', 'Gender_Male'
            ]
            
            # Filter to only columns that exist
            available_columns = [col for col in expected_column_order if col in df.columns]
            missing_columns = [col for col in expected_column_order if col not in df.columns]
            extra_columns = [col for col in df.columns if col not in expected_column_order]
            
            if missing_columns:
                logger.warning(f"  ⚠️ Missing expected columns: {missing_columns}")
            if extra_columns:
                logger.warning(f"  ⚠️ Extra columns (will be dropped): {extra_columns}")
            
            # Reorder columns
            df = df[available_columns]
            
            logger.info(f"  ✅ Columns reordered: {available_columns}")
            logger.info(f"  • Total columns: {len(available_columns)}")
            
            logger.info(f"✓ Preprocessing completed - Final shape: {df.shape}")
            logger.info(f"{'='*50}\n")
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Preprocessing failed: {str(e)}")
            import traceback
            logger.error(f"  Traceback: {traceback.format_exc()}")
            raise
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Make prediction on input data with comprehensive logging.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Dictionary containing prediction status and confidence
            
        Raises:
            ValueError: If input data is invalid
            Exception: For any prediction errors
        """
        logger.info(f"\n{'='*60}")
        logger.info("MAKING PREDICTION")
        logger.info(f"{'='*60}")
        
        if not data:
            logger.error("✗ Input data cannot be empty")
            raise ValueError("Input data cannot be empty")
        
        if self.model is None:
            logger.error("✗ Model not loaded")
            raise ValueError("Model not loaded")
        
        try:
            # Preprocess input data
            processed_data = self.preprocess_input(data)
            
            # Make prediction based on model type
            logger.info("Generating predictions...")
            
            if hasattr(self, 'model_type') and self.model_type in ['pyspark', 'spark_mlflow', 'spark_s3']:
                # PySpark model prediction
                spark_df = self.spark.createDataFrame(processed_data)
                predictions = self.model.transform(spark_df)
                
                # Get prediction and probability
                prediction_row = predictions.select("prediction", "probability").collect()[0]
                prediction = int(prediction_row.prediction)
                
                # Extract probability for positive class (index 1)
                probability_vector = prediction_row.probability
                probability = float(probability_vector[1])
                
            elif hasattr(self, 'model_type') and self.model_type == 'sklearn_s3':
                # Scikit-learn model prediction (from S3 fallback)
                logger.info("Using sklearn model for prediction...")
                y_pred = self.model.predict(processed_data)
                y_proba = self.model.predict_proba(processed_data)[:, 1]
                
                prediction = int(y_pred[0])
                probability = float(y_proba[0])
                
            else:
                # Default scikit-learn model prediction
                y_pred = self.model.predict(processed_data)
                y_proba = self.model.predict_proba(processed_data)[:, 1]
                
                prediction = int(y_pred[0])
                probability = float(y_proba[0])
            
            status = 'Churn' if prediction == 1 else 'Retain'
            confidence = round(probability * 100, 2)
            
            result = {
                "Status": status,
                "Confidence": f"{confidence}%"
            }
            
            logger.info("✓ Prediction completed:")
            logger.info(f"  • Raw Prediction: {prediction}")
            logger.info(f"  • Raw Probability: {probability:.4f}")
            logger.info(f"  • Final Status: {status}")
            logger.info(f"  • Confidence: {confidence}%")
            logger.info(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Prediction failed: {str(e)}")
            raise