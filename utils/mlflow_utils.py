import os
import logging
import mlflow
import mlflow.sklearn
from typing import Dict, Any, Optional, Union
from datetime import datetime
import pandas as pd
import numpy as np
from pathlib import Path

from config import get_mlflow_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MLflowTracker:
    """MLflow tracking utilities for experiment management and model versioning"""
    
    def __init__(self):
        self.config = get_mlflow_config()
        self.setup_mlflow()
        
    def setup_mlflow(self):
        """Initialize MLflow tracking with dynamic URL based on CONTAINERIZED environment"""
        from config import get_mlflow_tracking_uri, is_containerized
        
        # Get dynamic MLflow URL based on environment
        tracking_uri, environment = get_mlflow_tracking_uri()
        artifact_root = self.config.get('artifact_root')
        
        logger.info(f"🎯 Environment detected: {environment}")
        logger.info(f"🔗 MLflow URL: {tracking_uri}")
        logger.info(f"📦 Containerized: {is_containerized()}")
        
        # Try to connect to the configured tracking URI
        try:
            mlflow.set_tracking_uri(tracking_uri)
            logger.info(f"MLflow tracking URI set to: {tracking_uri}")
            
            # Test connection by trying to get experiments
            if tracking_uri.startswith('http'):
                import requests
                health_url = tracking_uri.replace('/api', '').rstrip('/') + '/health'
                response = requests.get(health_url, timeout=5)
                if response.status_code != 200:
                    raise ConnectionError(f"MLflow server not responding: {health_url}")
                logger.info(f"✅ MLflow server connection verified: {tracking_uri}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to MLflow server at {tracking_uri}: {e}")
            logger.info("🔄 Falling back to local file-based MLflow tracking...")
            
            # Fallback to local file-based tracking
            fallback_uri = 'file:./mlruns'
            mlflow.set_tracking_uri(fallback_uri)
            logger.info(f"MLflow fallback URI set to: {fallback_uri}")
            artifact_root = None  # Don't use S3 for local fallback
        
        # Set artifact root if configured for S3 and connection successful
        if artifact_root:
            import os
            os.environ['MLFLOW_DEFAULT_ARTIFACT_ROOT'] = artifact_root
            logger.info(f"MLflow artifact root set to: {artifact_root}")
        
        experiment_name = self.config.get('experiment_name', 'churn_prediction_experiment')
        
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                # Create experiment with S3 artifact location if configured
                if artifact_root:
                    experiment_id = mlflow.create_experiment(
                        name=experiment_name,
                        artifact_location=artifact_root
                    )
                    logger.info(f"Created new MLflow experiment with S3 backend: {experiment_name} (ID: {experiment_id})")
                    logger.info(f"Artifact location: {artifact_root}")
                else:
                    experiment_id = mlflow.create_experiment(experiment_name)
                    logger.info(f"Created new MLflow experiment: {experiment_name} (ID: {experiment_id})")
            else:
                experiment_id = experiment.experiment_id
                logger.info(f"Using existing MLflow experiment: {experiment_name} (ID: {experiment_id})")
                
            mlflow.set_experiment(experiment_name)
            
        except Exception as e:
            logger.error(f"Error setting up MLflow experiment: {e}")
            # Don't raise - continue without MLflow tracking
            logger.warning("⚠️ Continuing without MLflow experiment tracking")
    
    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> Optional[mlflow.ActiveRun]:
        """Start a new MLflow run with error handling"""
        try:
            # Format timestamp for run name
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if run_name is None:
                run_name_prefix = self.config.get('run_name_prefix', 'run')
                # Remove underscores and format with timestamp
                run_name_prefix = run_name_prefix.replace('_', ' ')
                run_name = f"{run_name_prefix} | {timestamp}"
            else:
                # Remove underscores from provided run name and append timestamp
                run_name = run_name.replace('_', ' ')
                run_name = f"{run_name} | {timestamp}"
            
            # Merge default tags with provided tags
            default_tags = self.config.get('tags', {})
            if tags:
                default_tags.update(tags)
                
            run = mlflow.start_run(run_name=run_name, tags=default_tags)
            logger.info(f"Started MLflow run: {run_name} (ID: {run.info.run_id})")
            print(f"🎯 MLflow Run Name: {run_name}")
            return run
        except Exception as e:
            logger.warning(f"⚠️ Failed to start MLflow run: {e}")
            logger.info("Continuing without MLflow run tracking...")
            return None
    
    def log_data_pipeline_metrics(self, dataset_info: Dict[str, Any]):
        """Log data pipeline metrics and artifacts"""
        try:
            # Check if MLflow run is active
            if not mlflow.active_run():
                logger.debug("No active MLflow run, skipping data pipeline metrics logging")
                return
                
            # Log dataset metrics
            mlflow.log_metrics({
                'dataset_rows': dataset_info.get('total_rows', 0),
                'training_rows': dataset_info.get('train_rows', 0),
                'test_rows': dataset_info.get('test_rows', 0),
                'num_features': dataset_info.get('num_features', 0),
                'missing_values_count': dataset_info.get('missing_values', 0),
                'outliers_removed': dataset_info.get('outliers_removed', 0)
            })
            
            # Log dataset parameters
            mlflow.log_params({
                'test_size': dataset_info.get('test_size', 0.2),
                'random_state': dataset_info.get('random_state', 42),
                'missing_value_strategy': dataset_info.get('missing_strategy', 'unknown'),
                'outlier_detection_method': dataset_info.get('outlier_method', 'unknown'),
                'feature_encoding_applied': dataset_info.get('encoding_applied', False),
                'feature_scaling_applied': dataset_info.get('scaling_applied', False)
            })
            
            # Log feature names
            if 'feature_names' in dataset_info:
                mlflow.log_param('feature_names', str(dataset_info['feature_names']))
            
            logger.info("Logged data pipeline metrics to MLflow")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to log data pipeline metrics to MLflow: {e}")
            logger.debug("Continuing without MLflow data pipeline logging...")
    
    def log_training_metrics(self, model, training_metrics: Dict[str, Any], model_params: Dict[str, Any]):
        """Log training metrics, parameters, and model artifacts"""
        try:
            # Log model parameters
            mlflow.log_params(model_params)
            
            # Log training metrics
            mlflow.log_metrics(training_metrics)
            
            # Log the model
            artifact_path = self.config.get('artifact_path', 'model')
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path=artifact_path,
                registered_model_name=self.config.get('model_registry_name', 'churn_prediction_model')
            )
            
            logger.info("Logged training metrics and model to MLflow")
            
        except Exception as e:
            logger.error(f"Error logging training metrics: {e}")
    
    def log_evaluation_metrics(self, evaluation_metrics: Dict[str, Any], confusion_matrix_path: Optional[str] = None):
        """Log evaluation metrics and artifacts"""
        try:
            # Log evaluation metrics
            if 'metrics' in evaluation_metrics:
                mlflow.log_metrics(evaluation_metrics['metrics'])
            
            # Log confusion matrix if provided
            if confusion_matrix_path and os.path.exists(confusion_matrix_path):
                mlflow.log_artifact(confusion_matrix_path, "evaluation")
            
            logger.info("Logged evaluation metrics to MLflow")
            
        except Exception as e:
            logger.error(f"Error logging evaluation metrics: {e}")
    
    def log_inference_metrics(self, predictions: np.ndarray, probabilities: Optional[np.ndarray] = None, 
                            input_data_info: Optional[Dict[str, Any]] = None):
        """Log inference metrics and results"""
        try:
            # Log inference metrics
            inference_metrics = {
                'num_predictions': len(predictions),
                'avg_prediction': float(np.mean(predictions)),
                'prediction_distribution_churn': int(np.sum(predictions)),
                'prediction_distribution_retain': int(len(predictions) - np.sum(predictions))
            }
            
            if probabilities is not None:
                inference_metrics.update({
                    'avg_churn_probability': float(np.mean(probabilities)),
                    'high_risk_predictions': int(np.sum(probabilities > 0.7)),
                    'medium_risk_predictions': int(np.sum((probabilities > 0.5) & (probabilities <= 0.7))),
                    'low_risk_predictions': int(np.sum(probabilities <= 0.5))
                })
            
            mlflow.log_metrics(inference_metrics)
            
            # Log input data info if provided
            if input_data_info:
                mlflow.log_params(input_data_info)
            
            logger.info("Logged inference metrics to MLflow")
            
        except Exception as e:
            logger.error(f"Error logging inference metrics: {e}")
    
    def load_model_from_registry(self, model_name: Optional[str] = None, 
                               version: Optional[Union[int, str]] = None, 
                               stage: Optional[str] = None):
        """Load model from MLflow Model Registry"""
        try:
            if model_name is None:
                model_name = self.config.get('model_registry_name', 'churn_prediction_model')
            
            if stage:
                model_uri = f"models:/{model_name}/{stage}"
            elif version:
                model_uri = f"models:/{model_name}/{version}"
            else:
                model_uri = f"models:/{model_name}/latest"
            
            model = mlflow.sklearn.load_model(model_uri)
            logger.info(f"Loaded model from MLflow registry: {model_uri}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model from MLflow registry: {e}")
            return None
    
    def get_latest_model_version(self, model_name: Optional[str] = None) -> Optional[str]:
        """Get the latest version of a registered model"""
        try:
            if model_name is None:
                model_name = self.config.get('model_registry_name', 'churn_prediction_model')
            
            client = mlflow.tracking.MlflowClient()
            latest_version = client.get_latest_versions(model_name, stages=["None", "Staging", "Production"])
            
            if latest_version:
                return latest_version[0].version
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest model version: {e}")
            return None
    
    def transition_model_stage(self, model_name: Optional[str] = None, 
                             version: Optional[str] = None, 
                             stage: str = "Staging"):
        """Transition model to a specific stage"""
        try:
            if model_name is None:
                model_name = self.config.get('model_registry_name', 'churn_prediction_model')
            
            if version is None:
                version = self.get_latest_model_version(model_name)
            
            if version:
                client = mlflow.tracking.MlflowClient()
                client.transition_model_version_stage(
                    name=model_name,
                    version=version,
                    stage=stage
                )
                logger.info(f"Transitioned model {model_name} version {version} to {stage}")
            
        except Exception as e:
            logger.error(f"Error transitioning model stage: {e}")
    
    def end_run(self):
        """End the current MLflow run"""
        try:
            if mlflow.active_run():
                mlflow.end_run()
                logger.info("Ended MLflow run")
            else:
                logger.debug("No active MLflow run to end")
        except Exception as e:
            logger.warning(f"⚠️ Failed to end MLflow run: {e}")


def setup_mlflow_autolog():
    """Setup MLflow autologging for supported frameworks"""
    mlflow_config = get_mlflow_config()
    if mlflow_config.get('autolog', True):
        mlflow.sklearn.autolog()
        logger.info("MLflow autologging enabled for scikit-learn")


def create_mlflow_run_tags(pipeline_type: str, additional_tags: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Create standardized tags for MLflow runs"""
    tags = {
        'pipeline_type': pipeline_type,
        'timestamp': datetime.now().isoformat(),
    }
    
    if additional_tags:
        tags.update(additional_tags)
    
    return tags