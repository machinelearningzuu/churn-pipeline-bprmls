import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=logging.INFO, format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
    'config.yaml')


def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f'Error loading configuration: {e}')
        return {}


def get_data_paths():
    config = load_config()
    return config.get('data_paths', {})


def get_columns():
    config = load_config()
    return config.get('columns', {})


def get_missing_values_config():
    config = load_config()
    return config.get('missing_values', {})


def get_outlier_config():
    config = load_config()
    return config.get('outlier_detection', {})


def get_binning_config():
    config = load_config()
    return config.get('feature_binning', {})


def get_encoding_config():
    config = load_config()
    return config.get('feature_encoding', {})


def get_scaling_config():
    config = load_config()
    return config.get('feature_scaling', {})


def get_splitting_config():
    config = load_config()
    return config.get('data_splitting', {})


def get_training_config():
    config = load_config()
    return config.get('training', {})


def get_model_config():
    config = load_config()
    return config.get('model', {})


def get_evaluation_config():
    config = load_config()
    return config.get('evaluation', {})


def get_deployment_config():
    config = load_config()
    return config.get('deployment', {})


def get_logging_config():
    config = load_config()
    return config.get('logging', {})


def get_environment_config():
    config = load_config()
    return config.get('environment', {})


def get_pipeline_config():
    config = load_config()
    return config.get('pipeline', {})


def get_inference_config():
    config = load_config()
    return config.get('inference', {})

def get_mlflow_config():
    config = load_config()
    return config.get('mlflow', {})

def get_config() ->Dict[str, Any]:
    return load_config()


def get_data_config() ->Dict[str, Any]:
    config = get_config()
    return config.get('data', {})


def get_preprocessing_config() ->Dict[str, Any]:
    config = get_config()
    return config.get('preprocessing', {})


def get_selected_model_config() ->Dict[str, Any]:
    training_config = get_training_config()
    selected_model = training_config.get('selected_model', 'random_forest')
    model_types = training_config.get('model_types', {})
    return {'model_type': selected_model, 'model_config': model_types.get(
        selected_model, {}), 'training_strategy': training_config.get(
        'training_strategy', 'cv'), 'cv_folds': training_config.get(
        'cv_folds', 5), 'random_state': training_config.get('random_state', 42)
        }


def get_available_models() ->List[str]:
    training_config = get_training_config()
    return list(training_config.get('model_types', {}).keys())


def update_config(updates: Dict[str, Any]) ->None:
    config_path = CONFIG_FILE
    config = get_config()
    for key, value in updates.items():
        keys = key.split('.')
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)


def create_default_config() ->None:
    config_path = CONFIG_FILE
    if not os.path.exists(config_path):
        default_config = {'data': {'file_path':
            'data/raw/ChurnModelling.csv', 'target_column': 'Exited',
            'test_size': 0.2, 'random_state': 42}, 'preprocessing': {
            'handle_missing_values': True, 'handle_outliers': True,
            'feature_binning': True, 'feature_encoding': True,
            'feature_scaling': True}, 'training': {'selected_model':
            'random_forest', 'training_strategy': 'cv', 'cv_folds': 5,
            'random_state': 42}}
        with open(config_path, 'w') as file:
            yaml.dump(default_config, file, default_flow_style=False)
        logger.info(f'Created default configuration file: {config_path}')


# AWS S3 Configuration Functions
def get_aws_config() -> Dict[str, Any]:
    """Get AWS configuration from config.yaml"""
    config = load_config()
    aws_config = config.get('aws', {})
    
    # Fallback to environment variables if not in config.yaml
    return {
        'region': aws_config.get('region', os.getenv('AWS_REGION', 'ap-south-1')),
        'bucket': aws_config.get('s3_bucket', os.getenv('S3_BUCKET')),
        'kms_key_arn': aws_config.get('s3_kms_key_arn', os.getenv('S3_KMS_KEY_ARN')),
        'force_s3_io': aws_config.get('force_s3_io', os.getenv('FORCE_S3_IO', 'true').lower() in ('true', '1', 'yes'))
    }


def get_aws_region() -> str:
    """Get AWS region from config.yaml or environment variables"""
    aws_config = get_aws_config()
    return aws_config['region']


def get_s3_bucket() -> str:
    """Get S3 bucket name from config.yaml or environment variables (required)"""
    aws_config = get_aws_config()
    bucket = aws_config['bucket']
    if not bucket:
        raise ValueError(
            "S3 bucket is required. Please set 'aws.s3_bucket' in config.yaml "
            "or S3_BUCKET environment variable."
        )
    return bucket


def get_s3_kms_arn() -> Optional[str]:
    """Get S3 KMS key ARN from config.yaml or environment variables"""
    aws_config = get_aws_config()
    return aws_config['kms_key_arn']


def force_s3_io() -> bool:
    """Check if S3-only I/O is enforced from config.yaml or environment variables"""
    aws_config = get_aws_config()
    return aws_config['force_s3_io']


def get_mlflow_config() -> Dict[str, Any]:
    """Get MLflow configuration from config.yaml"""
    config = load_config()
    mlflow_config = config.get('mlflow', {})
    
    # Environment variables take priority over config.yaml
    return {
        'tracking_uri': os.getenv('MLFLOW_TRACKING_URI') or mlflow_config.get('tracking_uri', 'http://localhost:5001'),
        'artifact_root': os.getenv('MLFLOW_DEFAULT_ARTIFACT_ROOT') or mlflow_config.get('artifact_root'),
        'experiment_name': mlflow_config.get('experiment_name', 'Zuu Crew Churn Analysis')
    }


def get_s3_config() -> Dict[str, Any]:
    """Get complete S3 configuration (legacy function for compatibility)"""
    config = load_config()
    return config.get('aws', {})

def get_aws_region():
    """Get AWS region from environment variables or config"""
    # Try environment variables first
    region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION')
    if region:
        return region
    
    # Fallback to config file
    config = load_config()
    return config.get('aws', {}).get('region', 'ap-south-1')

def get_s3_kms_arn():
    """Get S3 KMS key ARN from config"""
    config = load_config()
    return config.get('aws', {}).get('s3_kms_key_arn')

def get_mlflow_tracking_uri():
    """Get MLflow tracking URI based on CONTAINERIZED environment variable"""
    import os
    
    config = load_config()
    mlflow_config = config.get('mlflow', {})
    
    # Check if running in containerized environment
    containerized = os.environ.get('CONTAINERIZED', 'false').lower() == 'true'
    
    if containerized:
        tracking_uri = mlflow_config.get('docker_tracking_uri', 'http://mlflow-tracking:5001')
        environment = 'Docker'
    else:
        tracking_uri = mlflow_config.get('local_tracking_uri', 'http://localhost:5001')
        environment = 'Local'
    
    return tracking_uri, environment

def is_containerized():
    """Check if running in containerized environment"""
    import os
    return os.environ.get('CONTAINERIZED', 'false').lower() == 'true'


create_default_config()
