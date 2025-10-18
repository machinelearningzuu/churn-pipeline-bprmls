#!/usr/bin/env bash
set -euo pipefail

# ================================
# Embedded Spark ML Pipeline Entrypoint
# ================================
# This template handles all common setup for ML pipeline services with embedded Spark
# Service-specific behavior is controlled via environment variables:
# - PIPELINE_TYPE: data|model|inference
# - PIPELINE_SCRIPT: path to pipeline script
# - PIPELINE_NAME: human-readable pipeline name
# - PIPELINE_EMOJI: emoji for logging

echo "${PIPELINE_EMOJI:-🚀} Starting ${PIPELINE_NAME:-ML Pipeline} Service (Embedded Spark)..."
echo "whoami: $(whoami)"
echo "HOME: $HOME"
mkdir -p "$HOME/.cache" "$HOME/.ivy2" "$HOME/.config" "$SPARK_LOCAL_DIRS" /tmp/hadoop

# Set containerized environment variable for MLflow URL detection
export CONTAINERIZED=true
echo "🐳 Environment: Containerized (CONTAINERIZED=true)"

# ================================
# AWS Credentials Setup
# ================================
setup_aws_credentials() {
    if [ -f "/aws/credentials" ]; then
        echo "🔑 Setting up AWS credentials for Spark S3A..."
        export AWS_ACCESS_KEY_ID=$(grep -A 10 "^\[default\]" /aws/credentials | grep "aws_access_key_id" | cut -d'=' -f2 | tr -d ' ')
        export AWS_SECRET_ACCESS_KEY=$(grep -A 10 "^\[default\]" /aws/credentials | grep "aws_secret_access_key" | cut -d'=' -f2 | tr -d ' ')
        echo "✅ AWS credentials extracted for Spark"
    else
        echo "⚠️ AWS credentials file not found at /aws/credentials"
    fi
}

# ================================
# MLflow Health Check
# ================================
wait_for_mlflow() {
    echo "⏳ Waiting for MLflow service..."
    until curl -f "${MLFLOW_TRACKING_URI}/health" > /dev/null 2>&1; do
        echo "   MLflow not ready, waiting 5 seconds..."
        sleep 5
    done
    echo "✅ MLflow service is ready!"
}

# ================================
# Embedded Spark Configuration
# ================================
configure_spark() {
    export SPARK_CONF_DIR=/tmp/spark-conf
    mkdir -p $SPARK_CONF_DIR

    cat > $SPARK_CONF_DIR/spark-defaults.conf << EOF
# Embedded Spark configuration
spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.aws.credentials.provider=com.amazonaws.auth.DefaultAWSCredentialsProviderChain
spark.hadoop.fs.s3a.endpoint=s3.${AWS_REGION}.amazonaws.com
spark.hadoop.fs.s3a.path.style.access=false
spark.hadoop.fs.s3a.connection.ssl.enabled=true
spark.hadoop.fs.s3a.fast.upload=true
spark.hadoop.fs.s3a.multipart.size=67108864
spark.hadoop.fs.s3a.connection.timeout=60000
spark.hadoop.fs.s3a.socket.timeout=60000
# JARs are downloaded by PySpark automatically via spark.jars.packages
# No need to specify spark.jars path
EOF

    echo "🔧 Embedded Spark S3A configuration completed"
}

# ================================
# Pipeline-Specific Setup
# ================================
setup_pipeline_specific() {
    case "${PIPELINE_TYPE}" in
        "data")
            echo "📊 Pipeline: Data Preprocessing (Embedded Spark)"
            ;;
        "model")
            echo "🎯 Pipeline: Model Training (Embedded Spark)"
            setup_ivy_cache
            check_data_artifacts
            ;;
        "inference")
            echo "🔮 Pipeline: Batch Inference (Embedded Spark)"
            setup_ivy_cache
            check_model_and_data_artifacts
            ;;
        *)
            echo "⚠️ Unknown pipeline type: ${PIPELINE_TYPE}"
            ;;
    esac
}

# ================================
# Ivy Cache Setup (for model/inference)
# ================================
setup_ivy_cache() {
    export HOME=/tmp/home
    export SPARK_LOCAL_DIRS=/tmp/spark
    export IVY_CACHE_DIR=/tmp/ivy-cache
    mkdir -p /tmp/home /tmp/ivy-cache /tmp/spark
    chmod 777 /tmp/home /tmp/ivy-cache /tmp/spark
}

# ================================
# S3 Artifact Checks
# ================================
check_data_artifacts() {
    echo "⏳ Checking for data artifacts in S3..."
    python3 -c "
import boto3
import sys
from botocore.exceptions import NoCredentialsError, ClientError

try:
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket='${S3_BUCKET}', Prefix='artifacts/data_artifacts/', MaxKeys=1)
    if 'Contents' in response:
        print('✅ Data artifacts found in S3')
    else:
        print('⚠️ No data artifacts found - will use fallback data loading')
except Exception as e:
    print(f'⚠️ Could not check S3 data artifacts: {e}')
    print('   Continuing with pipeline...')
"
}

check_model_and_data_artifacts() {
    echo "⏳ Checking for model and data artifacts in S3..."
    python3 -c "
import boto3
import sys
from botocore.exceptions import NoCredentialsError, ClientError

try:
    s3 = boto3.client('s3')
    
    # Check for model artifacts
    model_response = s3.list_objects_v2(Bucket='${S3_BUCKET}', Prefix='artifacts/train_artifacts/', MaxKeys=1)
    if 'Contents' in model_response:
        print('✅ Model artifacts found in S3')
    else:
        print('⚠️ No model artifacts found in S3')
    
    # Check for data artifacts
    data_response = s3.list_objects_v2(Bucket='${S3_BUCKET}', Prefix='artifacts/data_artifacts/', MaxKeys=1)
    if 'Contents' in data_response:
        print('✅ Data artifacts found in S3')
    else:
        print('⚠️ No data artifacts found in S3')
        
except Exception as e:
    print(f'⚠️ Could not check S3 artifacts: {e}')
    print('   Continuing with inference pipeline...')
"
}

# ================================
# Main Execution Flow
# ================================
main() {
    # Common setup
    setup_aws_credentials
    
    echo "☁️ S3 Bucket: ${S3_BUCKET}"
    echo "📍 MLflow Tracking: ${MLFLOW_TRACKING_URI}"
    
    wait_for_mlflow
    configure_spark
    setup_pipeline_specific
    
    # Run the specific pipeline
    echo "🚀 Starting ${PIPELINE_NAME} pipeline with embedded Spark..."
    exec python3 "${PIPELINE_SCRIPT}"
}

# Execute main function
main "$@"
