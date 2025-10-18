"""
Model Training DAG - Every 60 minutes (Hourly)
Uses DockerOperator to run churn-pipeline/model:latest container
"""

import os
import platform
from airflow import DAG
from datetime import datetime, timedelta
from airflow.providers.docker.operators.docker import DockerOperator

# Cross-platform Docker socket configuration
def get_docker_url():
    """
    Returns the appropriate Docker socket URL based on the platform.
    
    Returns:
        str: Docker socket URL
            - Linux/macOS: unix://var/run/docker.sock
            - Windows: npipe:////./pipe/docker_engine
    """
    system = platform.system()
    if system == "Windows":
        return "npipe:////./pipe/docker_engine"
    else:
        # Linux, macOS, WSL
        return "unix://var/run/docker.sock"

DOCKER_URL = get_docker_url()

default_args = {
    "owner": "ml_engineering_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "start_date": datetime(2025, 10, 12),
    "catchup": False
}

with DAG(
    dag_id="train_pipeline_every_60m",
    default_args=default_args,
    schedule="0 * * * *",  # Every 60 minutes (hourly)
    max_active_runs=1,  # Prevent overlap
    dagrun_timeout=timedelta(minutes=55),
    description="Run model training every 60 minutes via DockerOperator",
    tags=["ml_pipeline", "model_training", "sklearn", "mlflow", "docker"]
) as dag:

    run_training_pipeline = DockerOperator(
        task_id="run_training_pipeline",
        image="churn-pipeline/model:latest",
        api_version="auto",
        auto_remove=True,
        docker_url=DOCKER_URL,  # Cross-platform compatible
        network_mode="churn-pipeline-network",
        mount_tmp_dir=False,  # Disable tmp mount for macOS Docker Desktop compatibility
        environment={
            "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
            "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            "AWS_REGION": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            "AWS_DEFAULT_REGION": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            "S3_BUCKET": "zuucrew-mlflow-artifacts-prod",
            "MLFLOW_TRACKING_URI": "http://mlflow-tracking:5001",
            "CONTAINERIZED": "true"
        },
        # Container uses entrypoint, so no command needed
        execution_timeout=timedelta(minutes=55),
    )
