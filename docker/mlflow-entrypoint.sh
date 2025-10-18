#!/bin/bash
set -e

echo "🚀 Starting MLflow Tracking Server..."
echo "📍 Backend Store URI: ${MLFLOW_BACKEND_STORE_URI}"
echo "☁️ Default Artifact Root: ${MLFLOW_DEFAULT_ARTIFACT_ROOT}"
echo "🌐 Host: 0.0.0.0:5001"

# Create MLflow directory
mkdir -p /tmp/mlruns
echo "✅ MLflow directory created"

# Start MLflow server with proper signal handling
exec mlflow server \
    --host 0.0.0.0 \
    --port 5001 \
    --backend-store-uri "${MLFLOW_BACKEND_STORE_URI}" \
    --default-artifact-root "${MLFLOW_DEFAULT_ARTIFACT_ROOT}" \
    --serve-artifacts
