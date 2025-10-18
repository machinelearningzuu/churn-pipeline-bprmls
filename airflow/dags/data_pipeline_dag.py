"""
Data Pipeline DAG - Every 20 minutes
Uses DockerOperator to run churn-pipeline/data:latest container
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
    dag_id="data_pipeline_every_20m",
    default_args=default_args,
    schedule="*/20 * * * *",  # Every 20 minutes
    max_active_runs=1,  # Allow 2 concurrent runs for better throughput
    dagrun_timeout=timedelta(minutes=30),  # Increased from 18 to 30 mins
    description="Run data preprocessing pipeline every 20 minutes via DockerOperator",
    tags=["ml_pipeline", "data_preprocessing", "pandas", "docker"]
) as dag:

    run_data_pipeline = DockerOperator(
        task_id="run_data_pipeline",
        image="churn-pipeline/data:latest",
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
        execution_timeout=timedelta(minutes=30),  # Increased from 18 to 30 mins
    )
