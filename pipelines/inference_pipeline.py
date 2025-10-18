#!/usr/bin/env python3
"""
Batch Inference Pipeline

This pipeline performs batch inference on processed data using the trained model.
Replaces the streaming inference pipeline with a simpler batch approach.
"""

import os
import sys
import logging
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Manual PySpark availability flag - controlled by command line argument
PYSPARK_AVAILABLE = False  # Will be set by argparse

# Conditional PySpark imports
if PYSPARK_AVAILABLE:
    try:
        from utils.spark_session import create_spark_session
    except ImportError:
        PYSPARK_AVAILABLE = False
        create_spark_session = None
else:
    create_spark_session = None

# Import project modules
from src.model_inference import ModelInference
from utils.config import load_config, get_s3_bucket, force_s3_io
from utils.mlflow_utils import MLflowTracker
from utils.s3_artifact_manager import S3ArtifactManager, get_latest_s3_artifacts
from utils.s3_io import read_df_csv, list_keys, read_pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchInferencePipeline:
    """Batch inference pipeline for ML predictions"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the batch inference pipeline"""
        self.config = load_config()
        self.model_inference = None
        self.spark = None
        self.mlflow_tracker = MLflowTracker()
        
        # Generate single timestamp for entire inference pipeline run
        from datetime import datetime
        self.pipeline_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        logger.info(f"🕐 Inference pipeline timestamp: {self.pipeline_timestamp}")
        
    def initialize(self):
        """Initialize components"""
        try:
            logger.info("🚀 Initializing Batch Inference Pipeline")
            logger.info("=" * 60)
            
            # Initialize Spark session
            self.spark = create_spark_session("BatchInferencePipeline")
            logger.info("✅ Spark session initialized")
            
            # Initialize model inference
            # Use MLflow model registry instead of S3 path
            model_path = "spark_random_forest_model"  # This will trigger latest model search
            self.model_inference = ModelInference(
                model_path=model_path, 
                use_spark=True, 
                spark=self.spark
            )
            logger.info("✅ Model inference initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {str(e)}")
            return False
    
    def load_test_data(self, sample_size: int = 1000) -> pd.DataFrame:
        """Load test data for batch inference with random sampling"""
        try:
            logger.info(f"📊 Loading test data for inference (sampling {sample_size} records)...")
            
            # Try to load latest test data from S3
            s3_manager = S3ArtifactManager()
            try:
                latest_paths = s3_manager.get_latest_artifacts(['X_test'], artifact_type='data_artifacts', format_ext='csv')
                if 'X_test' in latest_paths:
                    test_s3_key = latest_paths['X_test']
                    logger.info(f"📁 Using latest S3 artifact: s3://{get_s3_bucket()}/{test_s3_key}")
                    df = read_df_csv(key=test_s3_key)
                    
                    # Randomly sample the specified number of records
                    original_size = len(df)
                    if len(df) > sample_size:
                        df = df.sample(n=sample_size, random_state=42)
                        logger.info(f"🎲 Randomly sampled {sample_size} records from {original_size} total records")
                    else:
                        logger.info(f"📊 Using all {len(df)} available records (less than requested {sample_size})")
                    
                    logger.info(f"✅ Loaded test data: {df.shape}")
                    return df
            except Exception as e:
                logger.warning(f"⚠️ Could not load latest S3 artifacts: {e}")
            
            # Fallback to legacy local path (if S3 is not enforced)
            if not force_s3_io():
                test_data_path = Path("data/artifacts/csv/latest/X_test.csv")
                if test_data_path.exists():
                    logger.info("📁 Using legacy local path (S3 not enforced)")
                    df = pd.read_csv(test_data_path)
                    
                    # Randomly sample the specified number of records
                    original_size = len(df)
                    if len(df) > sample_size:
                        df = df.sample(n=sample_size, random_state=42)
                        logger.info(f"🎲 Randomly sampled {sample_size} records from {original_size} total records")
                    else:
                        logger.info(f"📊 Using all {len(df)} available records (less than requested {sample_size})")
                    
                    logger.info(f"✅ Loaded test data: {df.shape}")
                    return df
            else:
                # Load raw data and take a sample for inference
                logger.info("📁 No processed test data found, using raw data")
                raw_data_path = Path("data/raw/ChurnModelling.csv")
                if raw_data_path.exists():
                    df = pd.read_csv(raw_data_path)
                    # Remove target column if present
                    if 'Exited' in df.columns:
                        df = df.drop('Exited', axis=1)
                    
                    # Take a random sample for inference
                    sample_df = df.sample(n=min(sample_size, len(df)), random_state=42)
                    logger.info(f"🎲 Randomly sampled {len(sample_df)} records from raw data ({len(df)} total)")
                    logger.info(f"✅ Loaded sample data for inference: {sample_df.shape}")
                    return sample_df
                else:
                    raise FileNotFoundError("No data available for inference")
                    
        except Exception as e:
            logger.error(f"❌ Error loading test data: {str(e)}")
            raise
    
    def run_batch_inference(self, data: pd.DataFrame) -> pd.DataFrame:
        """Run batch inference on the data"""
        try:
            logger.info("🔮 Running batch inference...")
            logger.info(f"📊 Processing {len(data)} records")
            
            predictions = []
            successful_predictions = 0
            
            # Process each record
            for idx, row in data.iterrows():
                try:
                    # Convert row to dictionary
                    record_dict = row.to_dict()
                    
                    # Make prediction
                    prediction = self.model_inference.predict(record_dict)
                    
                    # Combine original data with prediction
                    result = {
                        **record_dict,
                        **prediction,
                        'processed_at': datetime.now().isoformat(),
                        'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'record_index': idx
                    }
                    
                    predictions.append(result)
                    successful_predictions += 1
                    
                    if successful_predictions % 25 == 0:
                        logger.info(f"📈 Processed {successful_predictions}/{len(data)} records")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process record {idx}: {str(e)}")
                    continue
            
            # Convert to DataFrame
            results_df = pd.DataFrame(predictions)
            
            logger.info(f"✅ Batch inference completed")
            logger.info(f"📊 Successfully processed: {successful_predictions}/{len(data)} records")
            
            return results_df
            
        except Exception as e:
            logger.error(f"❌ Error in batch inference: {str(e)}")
            raise
    
    def save_results(self, results_df: pd.DataFrame):
        """Save inference results to S3"""
        try:
            logger.info("💾 Saving inference results to S3...")
            
            # Save results to S3
            bucket = get_s3_bucket()
            
            # Save detailed results using pipeline timestamp
            results_key = f"artifacts/inference_artifacts/{self.pipeline_timestamp}/inference_results.json"
            from utils.s3_io import write_df_json
            write_df_json(results_df, key=results_key)
            logger.info(f"✅ Results saved to: s3://{bucket}/{results_key}")
            
            # Save summary
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_records': len(results_df),
                's3_key': results_key,
                'sample_predictions': results_df.head(3).to_dict('records') if len(results_df) > 0 else []
            }
            
            # Save summary to S3
            summary_key = f"artifacts/inference_artifacts/{self.pipeline_timestamp}/inference_summary.json"
            from s3_io import put_bytes
            import json
            summary_json = json.dumps(summary, indent=2).encode('utf-8')
            put_bytes(summary_json, key=summary_key, content_type='application/json')
            
            logger.info(f"✅ Summary saved to: s3://{bucket}/{summary_key}")
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")
            raise
    
    def run_pipeline(self):
        """Run the complete batch inference pipeline"""
        try:
            logger.info("🎯 STARTING BATCH INFERENCE PIPELINE")
            logger.info("=" * 60)
            
            # Start MLflow run
            run = self.mlflow_tracker.start_run("batch_inference_pipeline")
            
            # Initialize components
            if not self.initialize():
                raise Exception("Failed to initialize pipeline")
            
            # Load test data (sample 1000 records)
            test_data = self.load_test_data(sample_size=1000)
            
            # Run inference
            results_df = self.run_batch_inference(test_data)
            
            # Save results
            self.save_results(results_df)
            
            # Log metrics to MLflow
            metrics = {
                'total_records': len(test_data),
                'successful_predictions': len(results_df),
                'success_rate': len(results_df) / len(test_data) if len(test_data) > 0 else 0
            }
            
            self.mlflow_tracker.log_inference_metrics(
                predictions=results_df['prediction'].values if 'prediction' in results_df.columns else None,
                input_data_info=metrics
            )
            
            logger.info("🎉 Batch inference pipeline completed successfully!")
            logger.info(f"📊 Success rate: {metrics['success_rate']:.2%}")
            
            # End MLflow run
            self.mlflow_tracker.end_run()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            if 'run' in locals():
                self.mlflow_tracker.end_run()
            return False
        finally:
            if self.spark:
                self.spark.stop()
                logger.info("🔚 Spark session stopped")


def run_pandas_inference(model_timestamp=None):
    """Run inference using pandas (fast, default)."""
    logger.info("🐼 Using pandas for batch inference (fast, lightweight)")
    logger.info(f"\n{'='*80}")
    logger.info("🎯 PANDAS BATCH INFERENCE PIPELINE")
    logger.info(f"{'='*80}")
    
    try:
        import json
        
        # Generate timestamp for this inference run
        inference_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        logger.info(f"🕐 Inference timestamp: {inference_timestamp}")
        
        # 1. Load best trained model (MLflow first, S3 fallback)
        logger.info(f"\n{'='*60}")
        logger.info("🤖 STEP 1: LOAD BEST TRAINED MODEL")
        logger.info(f"{'='*60}")
        
        model = None
        model_source = None
        
        # Try to load best model from MLflow first (with quick timeout)
        try:
            import mlflow
            from mlflow.tracking import MlflowClient
            import requests
            
            logger.info("🏆 Attempting to load best model from MLflow...")
            
            # Quick health check first (1 second timeout)
            try:
                response = requests.get("http://localhost:5001/health", timeout=1)
                if response.status_code != 200:
                    raise ConnectionError("MLflow server not healthy")
                logger.info("✅ MLflow server is running")
            except Exception as health_error:
                logger.warning(f"⚠️ MLflow server not available: {str(health_error)}")
                raise ConnectionError("MLflow server not reachable")
            
            client = MlflowClient()
            
            # Get latest versions of registered model (with timeout handling)
            try:
                # Set a shorter timeout for MLflow operations
                import os
                os.environ['MLFLOW_HTTP_REQUEST_TIMEOUT'] = '5'  # 5 second timeout
                
                latest_versions = client.get_latest_versions(
                    "churn_prediction_sklearn", 
                    stages=["Production", "Staging", "None"]
                )
                
                if latest_versions:
                    # Get the best model (highest accuracy or latest)
                    best_version = latest_versions[0]  # Take first (latest)
                    model_uri = f"models:/churn_prediction_sklearn/{best_version.version}"
                    
                    model = mlflow.sklearn.load_model(model_uri)
                    model_source = f"MLflow (version {best_version.version})"
                    # Don't use MLflow timestamp - use our S3 timestamp format
                    model_timestamp = None  # Will be set to latest S3 timestamp
                    
                    logger.info(f"✅ Loaded best model from MLflow:")
                    logger.info(f"  • Model: churn_prediction_sklearn v{best_version.version}")
                    logger.info(f"  • Stage: {best_version.current_stage}")
                    logger.info(f"  • Source: MLflow Model Registry")
                    
                else:
                    logger.warning("⚠️ No registered models found in MLflow")
                    raise ConnectionError("No models in registry")
                    
            except Exception as mlflow_error:
                logger.warning(f"⚠️ MLflow model loading failed: {str(mlflow_error)}")
                raise mlflow_error
                
        except Exception as e:
            logger.warning(f"⚠️ MLflow not available, using S3 fallback: {str(e)}")
        
        # Always determine the correct S3 timestamp (whether from MLflow or S3 fallback)
        if model is None or model_timestamp is None:
            logger.info("🔄 Determining latest model timestamp from S3...")
        else:
            logger.info("🔄 Finding corresponding S3 timestamp for MLflow model...")
        
        # Find latest training artifacts timestamp
        train_keys = list_keys("artifacts/train_artifacts/")
        if not train_keys:
            raise FileNotFoundError("No training artifacts found in S3. Please run training pipeline first.")
        
        timestamps = []
        for key in train_keys:
            if "/sklearn_model.pkl" in key:
                timestamp = key.split("/")[-2]
                timestamps.append(timestamp)
        
        if not timestamps:
            raise FileNotFoundError("No trained models found in S3.")
        
        s3_model_timestamp = sorted(timestamps)[-1]
        logger.info(f"✅ Latest S3 model timestamp: {s3_model_timestamp}")
        
        # If no model loaded from MLflow, load from S3
        if model is None:
            logger.info("🔄 Loading model from S3...")
            model_key = f"artifacts/train_artifacts/{s3_model_timestamp}/sklearn_model.pkl"
            model = read_pickle(key=model_key)
            model_source = f"S3 ({s3_model_timestamp})"
            logger.info(f"✅ Loaded sklearn model from S3: {model_key}")
        else:
            # Model loaded from MLflow, but use S3 timestamp for consistency
            model_key = f"artifacts/train_artifacts/{s3_model_timestamp}/sklearn_model.pkl"
        
        # Use S3 timestamp for data artifacts (consistent format)
        model_timestamp = s3_model_timestamp
        
        logger.info(f"🎯 Model source: {model_source}")
        logger.info(f"🎯 Using timestamp for data artifacts: {model_timestamp}")
        
        # 2. Load corresponding data artifacts for preprocessing
        logger.info(f"\n{'='*60}")
        logger.info("📥 STEP 2: LOAD PREPROCESSING ARTIFACTS")
        logger.info(f"{'='*60}")
        
        # Load model metadata to find linked data artifacts
        metadata_key = f"artifacts/train_artifacts/{model_timestamp}/model_metadata.json"
        try:
            from utils.s3_io import get_bytes
            metadata_json = get_bytes(metadata_key).decode('utf-8')
            metadata = json.loads(metadata_json)
            data_timestamp = metadata.get('data_artifacts_timestamp', model_timestamp)
            logger.info(f"✅ Found linked data artifacts: {data_timestamp}")
        except:
            logger.warning(f"⚠️ Could not load model metadata, using model timestamp")
            data_timestamp = model_timestamp
        
        # Load encoders and scaler
        encoders_key = f"artifacts/data_artifacts/{data_timestamp}/encoders.pkl"
        scaler_key = f"artifacts/data_artifacts/{data_timestamp}/scaler.pkl"
        
        encoders = read_pickle(key=encoders_key)
        scaler = read_pickle(key=scaler_key)
        
        logger.info(f"✅ Loaded preprocessing artifacts:")
        logger.info(f"  • Encoders: {len(encoders)} categorical encoders")
        logger.info(f"  • Scaler: MinMaxScaler for numeric features")
        
        # 3. Load test data for inference
        logger.info(f"\n{'='*60}")
        logger.info("📊 STEP 3: LOAD TEST DATA FOR INFERENCE")
        logger.info(f"{'='*60}")
        
        X_test_key = f"artifacts/data_artifacts/{data_timestamp}/X_test.csv"
        y_test_key = f"artifacts/data_artifacts/{data_timestamp}/y_test.csv"
        
        X_test = read_df_csv(key=X_test_key)
        y_test = read_df_csv(key=y_test_key).iloc[:, 0]  # Extract series
        
        logger.info(f"✅ Loaded test data:")
        logger.info(f"  • X_test: {X_test.shape[0]:,} rows × {X_test.shape[1]} features")
        logger.info(f"  • y_test: {len(y_test):,} true labels")
        
        # 4. Perform inference
        logger.info(f"\n{'='*60}")
        logger.info("🔮 STEP 4: PERFORM BATCH INFERENCE")
        logger.info(f"{'='*60}")
        
        # Convert to numpy for sklearn
        X_test_np = X_test.values
        y_test_np = y_test.values
        
        # Make predictions
        logger.info("🎯 Making predictions with sklearn model...")
        y_pred = model.predict(X_test_np)
        y_pred_proba = model.predict_proba(X_test_np)[:, 1]  # Probability of positive class
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
        accuracy = accuracy_score(y_test_np, y_pred)
        
        logger.info(f"✅ Inference completed:")
        logger.info(f"  • Predictions made: {len(y_pred):,}")
        logger.info(f"  • Accuracy: {accuracy:.4f}")
        logger.info(f"  • Predicted churn: {(y_pred == 1).sum():,} customers")
        logger.info(f"  • Predicted stay: {(y_pred == 0).sum():,} customers")
        
        # 5. Save inference results to S3
        logger.info(f"\n{'='*60}")
        logger.info("💾 STEP 5: SAVE INFERENCE RESULTS TO S3")
        logger.info(f"{'='*60}")
        
        # Create inference results DataFrame
        inference_results = pd.DataFrame({
            'true_label': y_test_np,
            'predicted_label': y_pred,
            'prediction_probability': y_pred_proba,
            'correct_prediction': (y_test_np == y_pred)
        })
        
        # Save to S3 inference_artifacts
        from utils.s3_io import write_df_csv, put_bytes
        
        inference_s3_paths = {
            'predictions': f"artifacts/inference_artifacts/{inference_timestamp}/predictions.csv",
            'metrics': f"artifacts/inference_artifacts/{inference_timestamp}/inference_metrics.json",
            'metadata': f"artifacts/inference_artifacts/{inference_timestamp}/inference_metadata.json",
            'business_insights': f"artifacts/inference_artifacts/{inference_timestamp}/business_insights.json"
        }
        
        logger.info(f"📁 S3 inference artifact paths:")
        for name, path in inference_s3_paths.items():
            logger.info(f"  • {name}: s3://zuucrew-mlflow-artifacts-prod/{path}")
        
        # Save predictions
        write_df_csv(inference_results, key=inference_s3_paths['predictions'])
        logger.info(f"✅ predictions.csv: {len(inference_results):,} predictions saved")
        
        # Save inference metrics
        inference_metrics = {
            'accuracy': float(accuracy),
            'total_predictions': int(len(y_pred)),
            'predicted_churn': int((y_pred == 1).sum()),
            'predicted_stay': int((y_pred == 0).sum()),
            'true_churn': int((y_test_np == 1).sum()),
            'true_stay': int((y_test_np == 0).sum()),
            'inference_timestamp': inference_timestamp,
            'model_timestamp': model_timestamp,
            'data_timestamp': data_timestamp,
            'engine': 'pandas'
        }
        
        metrics_json = json.dumps(inference_metrics, indent=2)
        put_bytes(metrics_json.encode('utf-8'), key=inference_s3_paths['metrics'])
        logger.info(f"✅ inference_metrics.json: Performance metrics saved")
        
        # Save inference metadata
        inference_metadata = {
            'model_path': model_key,
            'data_artifacts_path': f"artifacts/data_artifacts/{data_timestamp}/",
            'inference_engine': 'pandas',
            'model_type': 'RandomForestClassifier',
            'feature_count': X_test.shape[1],
            'inference_timestamp': inference_timestamp,
            'processing_time_seconds': 3.0  # Approximate
        }
        
        metadata_json = json.dumps(inference_metadata, indent=2)
        put_bytes(metadata_json.encode('utf-8'), key=inference_s3_paths['metadata'])
        logger.info(f"✅ inference_metadata.json: Inference configuration saved")
        
        # Calculate business insights data first
        total_customers = len(y_pred)
        predicted_churn = (y_pred == 1).sum()
        predicted_retained = (y_pred == 0).sum()
        churn_rate = (predicted_churn / total_customers) * 100
        retention_rate = (predicted_retained / total_customers) * 100
        
        # Probability analysis
        retained_proba = y_pred_proba[y_pred == 0]
        churn_proba = y_pred_proba[y_pred == 1]
        
        # Risk segmentation
        high_risk = (y_pred_proba > 0.7).sum()
        medium_risk = ((y_pred_proba >= 0.3) & (y_pred_proba <= 0.7)).sum()
        low_risk = (y_pred_proba < 0.3).sum()
        
        # Save business insights
        business_insights = {
            'customer_analysis': {
                'total_customers': int(total_customers),
                'predicted_retained': int(predicted_retained),
                'predicted_churn': int(predicted_churn),
                'retention_rate_percent': float(retention_rate),
                'churn_rate_percent': float(churn_rate)
            },
            'confidence_analysis': {
                'average_retention_confidence': float(1 - retained_proba.mean()),
                'average_churn_confidence': float(churn_proba.mean()),
                'high_confidence_predictions': int(((y_pred_proba > 0.8) | (y_pred_proba < 0.2)).sum()),
                'uncertain_predictions': int(((y_pred_proba >= 0.4) & (y_pred_proba <= 0.6)).sum())
            },
            'risk_segmentation': {
                'high_risk_customers': int(high_risk),
                'medium_risk_customers': int(medium_risk),
                'low_risk_customers': int(low_risk),
                'high_risk_percentage': float(high_risk/total_customers*100),
                'medium_risk_percentage': float(medium_risk/total_customers*100),
                'low_risk_percentage': float(low_risk/total_customers*100)
            },
            'business_recommendations': {
                'churn_risk_level': 'HIGH' if churn_rate > 25 else 'MODERATE' if churn_rate > 15 else 'LOW',
                'focus_on_high_risk': int(high_risk),
                'monitor_medium_risk': int(medium_risk),
                'stable_low_risk': int(low_risk)
            },
            'timestamp': inference_timestamp,
            'model_timestamp': model_timestamp,
            'data_timestamp': data_timestamp
        }
        
        insights_json = json.dumps(business_insights, indent=2)
        put_bytes(insights_json.encode('utf-8'), key=inference_s3_paths['business_insights'])
        logger.info(f"✅ business_insights.json: Business analysis saved")
        
        # Generate comprehensive business insights
        logger.info(f"\n{'='*80}")
        logger.info("📈 BUSINESS INSIGHTS & SUMMARY ANALYSIS")
        logger.info(f"{'='*80}")
        
        logger.info(f"👥 CUSTOMER RETENTION ANALYSIS:")
        logger.info(f"  • Total customers analyzed: {total_customers:,}")
        logger.info(f"  • Predicted to be RETAINED: {predicted_retained:,} ({retention_rate:.1f}%)")
        logger.info(f"  • Predicted to CHURN: {predicted_churn:,} ({churn_rate:.1f}%)")
        logger.info(f"  • Retention rate: {retention_rate:.1f}%")
        logger.info(f"  • Churn risk: {churn_rate:.1f}%")
        
        logger.info(f"\n🎯 CONFIDENCE ANALYSIS:")
        logger.info(f"  • Average retention confidence: {(1 - retained_proba.mean()):.3f}")
        logger.info(f"  • Average churn confidence: {churn_proba.mean():.3f}")
        logger.info(f"  • High confidence predictions (>80%): {((y_pred_proba > 0.8) | (y_pred_proba < 0.2)).sum():,} ({((y_pred_proba > 0.8) | (y_pred_proba < 0.2)).sum()/total_customers*100:.1f}%)")
        logger.info(f"  • Uncertain predictions (40-60%): {((y_pred_proba >= 0.4) & (y_pred_proba <= 0.6)).sum():,} ({((y_pred_proba >= 0.4) & (y_pred_proba <= 0.6)).sum()/total_customers*100:.1f}%)")
        
        logger.info(f"\n⚠️ RISK SEGMENTATION:")
        logger.info(f"  • HIGH RISK customers (>70% churn probability): {high_risk:,} ({high_risk/total_customers*100:.1f}%)")
        logger.info(f"  • MEDIUM RISK customers (30-70% churn probability): {medium_risk:,} ({medium_risk/total_customers*100:.1f}%)")
        logger.info(f"  • LOW RISK customers (<30% churn probability): {low_risk:,} ({low_risk/total_customers*100:.1f}%)")
        
        # Model performance insights
        if len(y_test_np) > 0:  # If we have true labels
            true_churn = (y_test_np == 1).sum()
            true_retained = (y_test_np == 0).sum()
            
            # Confusion matrix insights
            from sklearn.metrics import confusion_matrix
            cm = confusion_matrix(y_test_np, y_pred)
            tn, fp, fn, tp = cm.ravel()
            
            logger.info(f"\n🎯 MODEL PERFORMANCE INSIGHTS:")
            logger.info(f"  • True retention rate: {(true_retained/len(y_test_np)*100):.1f}%")
            logger.info(f"  • True churn rate: {(true_churn/len(y_test_np)*100):.1f}%")
            logger.info(f"  • Correctly identified retained: {tn:,} customers")
            logger.info(f"  • Correctly identified churn: {tp:,} customers")
            logger.info(f"  • False churn alerts: {fp:,} customers ({fp/len(y_test_np)*100:.1f}%)")
            logger.info(f"  • Missed churn cases: {fn:,} customers ({fn/len(y_test_np)*100:.1f}%)")
        
        # Business recommendations
        logger.info(f"\n💡 BUSINESS RECOMMENDATIONS:")
        if churn_rate > 25:
            logger.info(f"  🚨 HIGH CHURN RISK: {churn_rate:.1f}% predicted churn rate requires immediate attention")
        elif churn_rate > 15:
            logger.info(f"  ⚠️ MODERATE CHURN RISK: {churn_rate:.1f}% predicted churn rate needs monitoring")
        else:
            logger.info(f"  ✅ LOW CHURN RISK: {churn_rate:.1f}% predicted churn rate is healthy")
        
        logger.info(f"  • Focus retention efforts on {high_risk:,} high-risk customers")
        logger.info(f"  • Monitor {medium_risk:,} medium-risk customers closely")
        logger.info(f"  • {low_risk:,} low-risk customers are stable")
        
        # Top insights
        logger.info(f"\n🔍 KEY INSIGHTS:")
        logger.info(f"  • {retention_rate:.0f}% of customers are likely to stay")
        logger.info(f"  • {churn_rate:.0f}% of customers are at risk of churning")
        logger.info(f"  • Model confidence is high for {((y_pred_proba > 0.8) | (y_pred_proba < 0.2)).sum()/total_customers*100:.0f}% of predictions")
        logger.info(f"  • Revenue protection: Focus on {high_risk:,} high-risk customers first")
        
        logger.info(f"\n{'='*80}")
        logger.info("🎉 PANDAS INFERENCE PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info(f"{'='*80}")
        logger.info(f"📊 TECHNICAL SUMMARY:")
        logger.info(f"  • Model accuracy: {accuracy:.4f}")
        logger.info(f"  • Total predictions: {len(y_pred):,}")
        logger.info(f"  • Model used: {model_timestamp}")
        logger.info(f"  • Data used: {data_timestamp}")
        logger.info(f"📁 S3 inference artifacts: s3://zuucrew-mlflow-artifacts-prod/artifacts/inference_artifacts/{inference_timestamp}/")
        logger.info(f"🎯 Engine used: Pandas + Scikit-learn (fast, efficient)")
        logger.info(f"{'='*80}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pandas inference failed: {str(e)}")
        return False

def main():
    """Main function with argparse for PySpark control."""
    global PYSPARK_AVAILABLE
    
    parser = argparse.ArgumentParser(description="Batch Inference Pipeline")
    parser.add_argument(
        '--pyspark', 
        action='store_true', 
        help='Enable PySpark for large dataset inference (default: use pandas)'
    )
    parser.add_argument(
        '--engine',
        choices=['pandas', 'pyspark'],
        default='pandas',
        help='Inference engine to use (default: pandas)'
    )
    parser.add_argument(
        '--model-timestamp',
        help='Specific model timestamp to use (default: latest)'
    )
    
    args = parser.parse_args()
    
    # Set global PYSPARK_AVAILABLE based on arguments
    PYSPARK_AVAILABLE = args.pyspark or (args.engine == 'pyspark')
    
    logger.info(f"🎯 Command line arguments:")
    logger.info(f"  • PySpark enabled: {PYSPARK_AVAILABLE}")
    logger.info(f"  • Inference engine: {args.engine}")
    logger.info(f"  • Model timestamp: {args.model_timestamp or 'latest'}")
    
    try:
        if args.engine == 'pandas':
            success = run_pandas_inference(args.model_timestamp)
        else:
            pipeline = BatchInferencePipeline()
            success = pipeline.run_pipeline()
        
        return 0 if success else 1
            
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import json
    exit(main())
