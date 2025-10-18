import os
import time
import joblib
import logging
import numpy as np
import pandas as pd
from typing import Any, Tuple, Union
from sklearn.base import BaseEstimator

# Manual PySpark availability flag - set to False to prioritize scikit-learn
PYSPARK_AVAILABLE = False  # Set to True to enable PySpark, False for sklearn-only

# Conditional PySpark imports
if PYSPARK_AVAILABLE:
    try:
        from pyspark.sql import DataFrame as SparkDataFrame, SparkSession
        from pyspark.ml import Pipeline, PipelineModel
        from pyspark.ml.feature import VectorAssembler
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


class ModelTrainer:
    """
    Original ModelTrainer for scikit-learn models.
    """
    
    def __init__(self):
        """Initialize the model trainer."""
        logger.info("ModelTrainer initialized")
    
    def train(
            self,
            model: BaseEstimator,
            X_train: Union[pd.DataFrame, np.ndarray],
            Y_train: Union[pd.Series, np.ndarray]
            ) -> Tuple[BaseEstimator, float]:
        """
        Train a machine learning model.
        
        Args:
            model: The machine learning model to train
            X_train: Training features
            Y_train: Training targets
            
        Returns:
            Tuple of (trained_model, training_score)
        """
        logger.info("Starting model training...")
        start_time = time.time()
        
        model.fit(X_train, Y_train)
        
        training_time = time.time() - start_time
        train_score = model.score(X_train, Y_train)
        
        logger.info(f"✓ Model training completed in {training_time:.2f} seconds")
        logger.info(f"✓ Training Score: {train_score:.4f}")
        
        return model, train_score
    
    def save_model(self, model: BaseEstimator, filepath: str) -> None:
        """Save a trained model to disk."""
        if model is None:
            raise ValueError("Cannot save None model")
        
        joblib.dump(model, filepath)
        logger.info(f"✓ Model saved to: {filepath}")

    def load_model(self, filepath: str) -> BaseEstimator:
        """Load a trained model from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model = joblib.load(filepath)
        logger.info(f"✓ Model loaded from: {filepath}")
        return model

class SparkModelTrainer:
    """
    PySpark MLlib model trainer - simplified to match original ModelTrainer structure.
    """
    
    def __init__(self, spark_session: SparkSession = None):
        """Initialize the PySpark model trainer."""
        self.spark = spark_session or SparkSession.getActiveSession()
        if self.spark is None:
            raise ValueError("No active SparkSession found.")
        logger.info("SparkModelTrainer initialized")
    
    def train(
            self,
            model,
            train_data: Union[pd.DataFrame, object],
            feature_columns: list
            ) -> Tuple[object, dict]:
        """
        Train a PySpark MLlib model.
        
        Args:
            model: PySpark MLlib model (e.g., RandomForestClassifier)
            train_data: Training DataFrame with features and label columns
            feature_columns: List of feature column names
            
        Returns:
            Tuple of (trained_pipeline, training_metrics)
        """
        logger.info("Starting PySpark model training...")
        start_time = time.time()
        
        # Create feature vector assembler with null handling
        assembler = VectorAssembler(
            inputCols=feature_columns,
            outputCol="features",
            handleInvalid="skip"  # Skip rows with null/NaN values
        )
        
        # Create pipeline
        pipeline = Pipeline(stages=[assembler, model])
        
        # Fit the pipeline
        trained_pipeline = pipeline.fit(train_data)
        
        training_time = time.time() - start_time
        
        # Calculate training metrics
        train_predictions = trained_pipeline.transform(train_data)
        train_count = train_data.count()
        
        metrics = {
            'training_time': training_time,
            'training_samples': train_count
        }
        
        logger.info(f"✓ PySpark model training completed in {training_time:.2f} seconds")
        logger.info(f"✓ Training samples: {train_count:,}")
        
        return trained_pipeline, metrics
    
    def save_model(self, model: object, filepath: str) -> None:
        """Save a trained PySpark model using MLflow model registry."""
        if model is None:
            raise ValueError("Cannot save None model")
        
        # Use MLflow to save Spark models (proper way)
        import mlflow
        import mlflow.spark
        
        # Extract timestamp from filepath for model name
        import re
        timestamp_match = re.search(r'(\d{14})', filepath)
        timestamp = timestamp_match.group(1) if timestamp_match else 'unknown'
        
        # Save model using MLflow (which handles S3 automatically)
        model_name = f"spark_random_forest_{timestamp}"
        
        try:
            # Log the model to MLflow (automatically goes to S3)
            mlflow.spark.log_model(
                spark_model=model,
                artifact_path="model",
                registered_model_name=model_name
            )
            logger.info(f"✓ PySpark model saved to MLflow registry: {model_name}")
            
            # Also save model metadata to our organized S3 structure
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
            from config import get_s3_bucket
            from s3_io import put_bytes
            import json
            
            model_metadata = {
                'model_name': model_name,
                'model_type': 'spark_random_forest',
                'timestamp': timestamp,
                'mlflow_model_path': f"models:/{model_name}/latest",
                'stages': [stage.__class__.__name__ for stage in model.stages] if hasattr(model, 'stages') else []
            }
            
            # Save metadata to our organized structure
            bucket = get_s3_bucket()
            metadata_key = f"artifacts/train_artifacts/{timestamp}/model_metadata.json"
            metadata_json = json.dumps(model_metadata, indent=2).encode('utf-8')
            put_bytes(metadata_json, key=metadata_key, content_type='application/json')
            
            logger.info(f"✓ Model metadata saved to: s3://{bucket}/{metadata_key}")
            
            # Also save the actual Spark model to S3 model artifacts directory for direct loading
            try:
                spark_model_s3a_path = f"s3a://{bucket}/artifacts/train_artifacts/{timestamp}/spark_model"
                logger.info(f"💾 Saving Spark model to S3 model artifacts: {spark_model_s3a_path}")
                
                # Save the PipelineModel directly to S3A
                model.write().overwrite().save(spark_model_s3a_path)
                logger.info(f"✅ Spark model saved to S3 model artifacts: {spark_model_s3a_path}")
                
            except Exception as s3_model_save_error:
                logger.warning(f"⚠️ Failed to save Spark model to S3 model artifacts: {s3_model_save_error}")
                logger.info("💡 Model is still available via MLflow registry")
            
        except Exception as e:
            logger.error(f"❌ MLflow model save failed: {e}")
            logger.error("💡 Please check your AWS credentials and S3 bucket configuration")
            logger.error("💡 Ensure MLflow server is running and accessible")
            raise e

    def load_model(self, filepath: str) -> object:
        """Load a trained PySpark model from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model directory not found: {filepath}")
        
        from pyspark.ml import PipelineModel
        model = PipelineModel.load(filepath)
        logger.info(f"✓ PySpark model loaded from: {filepath}")
        return model
    
    def train_sklearn_fallback(self, X_train, y_train, X_test, y_test, timestamp: str) -> None:
        """Train sklearn model as fallback and save to S3"""
        logger.info("🔄 Training sklearn model as fallback...")
        
        # Check if data is already pandas or needs conversion from Spark
        if hasattr(X_train, 'toPandas'):
            # Data is Spark DataFrame, convert to pandas
            from utils.spark_utils import spark_to_pandas
            X_train_pd = spark_to_pandas(X_train)
            y_train_pd = spark_to_pandas(y_train)
            X_test_pd = spark_to_pandas(X_test)
            y_test_pd = spark_to_pandas(y_test)
        else:
            # Data is already pandas DataFrame
            X_train_pd = X_train
            y_train_pd = y_train
            X_test_pd = X_test
            y_test_pd = y_test
        
        # Remove RowNumber if present
        if 'RowNumber' in X_train_pd.columns:
            X_train_pd = X_train_pd.drop('RowNumber', axis=1)
        if 'RowNumber' in X_test_pd.columns:
            X_test_pd = X_test_pd.drop('RowNumber', axis=1)
            
        # Train sklearn Random Forest
        from sklearn.ensemble import RandomForestClassifier
        
        sklearn_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        start_time = time.time()
        sklearn_model.fit(X_train_pd, y_train_pd.values.ravel())
        training_time = time.time() - start_time
        
        logger.info(f"✓ Sklearn model training completed in {training_time:.2f} seconds")
        
        # Save sklearn model to S3
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
            from s3_io import write_pickle
            
            sklearn_model_key = f"artifacts/train_artifacts/{timestamp}/sklearn_model.pkl"
            write_pickle(sklearn_model, key=sklearn_model_key)
            logger.info(f"✅ Sklearn model saved to S3: {sklearn_model_key}")
            
        except Exception as sklearn_save_error:
            logger.warning(f"⚠️ Failed to save sklearn model to S3: {sklearn_save_error}")
            
        return sklearn_model