# Docker Microservices Setup

This document provides comprehensive instructions for running the ML Pipeline as Dockerized microservices with step-by-step execution guidance.

## ⚡ Quick Reference

### Essential Commands (Copy & Paste)
```bash
# Complete setup (first time)
cp .env.example .env && make s3-upload-data && make docker-build && make docker-up && make docker-run-all

# Daily workflow
make docker-up && make docker-model-pipeline && open http://localhost:5001

# Check results
make docker-status && make s3-list PREFIX=artifacts/

# Cleanup
make docker-down
```

### Service URLs
- **MLflow UI**: http://localhost:5001 (experiments, models, metrics)
- **S3 Console**: https://s3.console.aws.amazon.com/s3/buckets/zuucrew-mlflow-artifacts-prod

## 🐳 Architecture Overview

The project is containerized into four independent microservices:

1. **mlflow-tracking** - MLflow Tracking Server with S3 artifact storage (Port 5001)
2. **data-pipeline** - PySpark data preprocessing pipeline (S3 → S3)
3. **model-pipeline** - PySpark model training with MLflow integration (S3 → MLflow + S3)
4. **inference-pipeline** - Batch inference with S3 I/O (MLflow + S3 → S3)

## 🚀 Complete Setup Guide

### Prerequisites Checklist

- ✅ Docker and Docker Compose installed
- ✅ AWS credentials configured in `~/.aws/credentials` with S3 permissions
- ✅ S3 bucket `zuucrew-mlflow-artifacts-prod` exists with proper permissions
- ✅ Raw data uploaded to S3 (see Data Setup below)

### Step 1: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings (optional - defaults work)
# Key variables:
# AWS_REGION=ap-south-1
# S3_BUCKET=zuucrew-mlflow-artifacts-prod
# MLFLOW_TRACKING_URI=http://mlflow-tracking:5001
```

### Step 2: Data Setup (One-Time)

```bash
# Upload raw data to S3 (run this once)
make s3-upload-data

# Verify data upload
make s3-list PREFIX=data/raw/
# Should show: data/raw/ChurnModelling.csv
```

### Step 3: Build Docker Images

```bash
# Build all Docker images (takes 10-15 minutes first time)
make docker-build

# Check built images
docker images | grep week10
# Should show:
# week10-mlflow-tracking
# week10-data-pipeline  
# week10-model-pipeline
# week10-inference-pipeline
```

### Step 4: Start MLflow Service

```bash
# Start MLflow tracking server
make docker-up

# Verify MLflow is running
make docker-status
# Should show: mlflow-tracking Up (healthy)

# Test MLflow UI
open http://localhost:5001
# MLflow UI should load
```

### Step 5: Execute ML Pipelines

#### Option A: Run All Pipelines in Sequence (Recommended)
```bash
# Run complete ML workflow
make docker-run-all

# This executes:
# 1. Data pipeline (preprocessing)
# 2. Model pipeline (training) 
# 3. Inference pipeline (predictions)
```

#### Option B: Run Individual Pipelines
```bash
# 1. Data preprocessing pipeline
make docker-data-pipeline
# Expected: ✅ Data pipeline completed!

# 2. Model training pipeline  
make docker-model-pipeline
# Expected: ✅ Model pipeline completed!
# Check MLflow UI: http://localhost:5001

# 3. Batch inference pipeline
make docker-inference-pipeline  
# Expected: ✅ Inference pipeline completed!
```

### Step 6: Verify Results

```bash
# Check MLflow experiments
open http://localhost:5001

# Check S3 artifacts
make s3-list PREFIX=artifacts/
# Should show:
# artifacts/data_artifacts/YYYYMMDDHHMMSS/
# artifacts/model_artifacts/YYYYMMDDHHMMSS/
# artifacts/inference_artifacts/YYYYMMDDHHMMSS/

# View service logs
make docker-logs
```

## 📝 Command Execution Order

### Proper Make Command Sequence

#### First-Time Complete Setup
```bash
# 1. Prerequisites check
docker --version                    # Verify Docker installed
aws sts get-caller-identity         # Verify AWS credentials

# 2. Environment setup  
cp .env.example .env                # Copy environment template

# 3. Data preparation (one-time)
make s3-upload-data                 # Upload raw data to S3
make s3-list PREFIX=data/           # Verify upload success

# 4. Docker setup
make docker-build                   # Build all images (10-15 min)
make docker-up                      # Start MLflow service
sleep 30                           # Wait for MLflow startup

# 5. Pipeline execution
make docker-run-all                # Complete ML workflow

# 6. Verification
make docker-status                  # Check service health
open http://localhost:5001         # View MLflow UI
make s3-list PREFIX=artifacts/     # View S3 artifacts
```

#### Development Workflow (Daily)
```bash
# Start services
make docker-up                     # Start MLflow (if not running)

# Run pipelines individually (as needed)
make docker-data-pipeline          # Reprocess data
make docker-model-pipeline         # Retrain model  
make docker-inference-pipeline     # Generate predictions

# Monitor results
make docker-logs                   # View logs
open http://localhost:5001         # MLflow UI

# Stop when done
make docker-down                   # Stop services
```

#### Debugging Workflow
```bash
# Check service status
make docker-status                 # Service health check

# View logs
make docker-logs                   # All service logs
docker-compose logs mlflow-tracking # Specific service

# Interactive debugging
docker-compose run --rm data-pipeline bash     # Access container
docker-compose run --rm model-pipeline python3 -c "import mlflow; print(mlflow.__version__)"

# Test components
curl http://localhost:5001/health  # MLflow health
make s3-smoke                      # S3 connectivity
```

#### Cleanup Workflow
```bash
# Stop services
make docker-down                   # Stop all containers

# Clean Docker resources
make docker-clean                  # Remove containers, networks, volumes

# Clean S3 artifacts (optional)
make s3-clean                      # Remove project S3 artifacts

# Clean local artifacts (if any)
make clean                         # Remove local cache
```

## 📋 Available Commands

### Service Management
```bash
# Build and Setup
make docker-build              # Build all Docker images (10-15 min first time)
make docker-up                 # Start MLflow tracking server on port 5001
make docker-down               # Stop all Docker services
make docker-clean              # Stop services + clean Docker resources

# Status and Monitoring  
make docker-status             # Show running services and health status
make docker-logs              # View real-time logs from all services
```

### Pipeline Execution
```bash
# Complete Workflow (Recommended)
make docker-run-all           # Run all pipelines: data → model → inference

# Individual Pipelines (for development/debugging)
make docker-data-pipeline      # Data preprocessing: S3 → processed data → S3
make docker-model-pipeline     # Model training: S3 data → MLflow model + S3 metadata  
make docker-inference-pipeline # Batch inference: MLflow model → predictions → S3
```

### S3 Operations (Works with Docker)
```bash
# Data Management
make s3-upload-data            # One-time: upload raw data to S3
make s3-list PREFIX=data/      # List S3 data files
make s3-list PREFIX=artifacts/ # List all ML artifacts

# Cleanup
make s3-clean                  # Clean project S3 artifacts (safe)
make clean                     # Clean local cache only
```

## 🌐 Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| MLflow UI | http://localhost:5001 | Experiment tracking and model registry |

## 🎯 Detailed Execution Workflow

### First-Time Setup (Complete)
```bash
# 1. Check prerequisites
docker --version && docker-compose --version
aws sts get-caller-identity  # Verify AWS credentials

# 2. Setup environment
cp .env.example .env         # Use defaults or customize

# 3. Upload data to S3 (one-time)
make s3-upload-data          # Upload data/raw/ChurnModelling.csv
make s3-list PREFIX=data/    # Verify: should show data/raw/ChurnModelling.csv

# 4. Build Docker images (10-15 minutes)
make docker-build           # Build all 4 microservices

# 5. Start MLflow service
make docker-up              # Start MLflow on port 5001
sleep 30                    # Wait for MLflow to be ready
curl http://localhost:5001  # Should return 200

# 6. Run complete ML workflow
make docker-run-all         # Data → Model → Inference
```

### Daily Development Workflow
```bash
# Start MLflow (if not running)
make docker-up

# Run individual pipelines as needed
make docker-data-pipeline      # Reprocess data
make docker-model-pipeline     # Retrain model
make docker-inference-pipeline # Run inference

# View results
open http://localhost:5001     # MLflow UI
make s3-list PREFIX=artifacts/ # S3 artifacts

# Stop services when done
make docker-down
```

### Expected Output Examples

#### Successful Data Pipeline
```
🔄 Starting Data Pipeline Service...
✅ MLflow service is ready!
✅ SparkSession created/retrieved: ChurnPredictionDataPipeline  
✅ Spark Version: 4.0.1
✅ Downloaded 454,219 bytes from S3 (X_train.csv)
✅ Data pipeline completed!
```

#### Successful Model Pipeline  
```
🎯 Starting Model Pipeline Service...
✅ PySpark model training completed in 7.62 seconds
✅ Training samples: 8,001
✅ Successfully registered model 'spark_random_forest_YYYYMMDDHHMMSS'
✅ AUC: 0.8599, Accuracy: 0.8586
✅ Model pipeline completed!
```

#### Successful Inference Pipeline
```
🔮 Starting Inference Pipeline Service...
✅ Model loaded from MLflow: spark_random_forest_YYYYMMDDHHMMSS
✅ Loaded 2 feature encoders from S3
✅ Successfully processed: 1000/1000 records
✅ Inference pipeline completed!
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# AWS Configuration
AWS_REGION=ap-south-1
S3_BUCKET=zuucrew-mlflow-artifacts-prod
AWS_PROFILE=zuucrew-root

# MLflow Configuration
MLFLOW_TRACKING_URI=http://mlflow-tracking:5000
MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://zuucrew-mlflow-artifacts-prod/mlflow-artifacts

# Docker Configuration
COMPOSE_PROJECT_NAME=ml-pipeline
DOCKER_BUILDKIT=1
```

### AWS Credentials
Mount your AWS credentials as read-only volumes:
```yaml
volumes:
  - ~/.aws:/aws:ro
environment:
  - AWS_SHARED_CREDENTIALS_FILE=/aws/credentials
  - AWS_CONFIG_FILE=/aws/config
```

## 🏗️ Service Architecture

### MLflow Tracking Server
- **Base Image**: `python:3.11-slim`
- **Port**: 5000
- **Storage**: SQLite backend + S3 artifacts
- **Health Check**: HTTP endpoint monitoring

### Pipeline Services (Data/Model/Inference)
- **Base Image**: `openjdk:11-jre-slim` + Python 3
- **Spark**: PySpark with S3A integration
- **Dependencies**: Hadoop AWS JARs for S3 connectivity
- **Networking**: Communicate via `ml-pipeline-network`

## 🔐 Security Features

### Non-Root Execution
All containers run as non-root user `appuser`:
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

### Credential Management
- No credentials baked into images
- AWS credentials mounted as read-only volumes
- Uses boto3's default credential chain

### Network Isolation
- Custom bridge network `ml-pipeline-network`
- Internal service communication only
- Only MLflow exposed to host

## 🔍 Monitoring and Debugging

### View Service Status
```bash
make docker-status
```

### View Logs
```bash
# All services
make docker-logs

# Specific service
docker-compose logs -f mlflow-tracking
docker-compose logs -f data-pipeline
```

### Health Checks
All services include health checks:
- **MLflow**: HTTP endpoint check
- **Pipeline services**: S3 connectivity check

### Debugging Failed Services
```bash
# Run service interactively
docker-compose run --rm data-pipeline bash

# Check container logs
docker logs ml-pipeline_data-pipeline_1

# Inspect service configuration
docker-compose config
```

## 📊 Validation Checklist

After `make docker-up`, verify:

| Component | Check | Expected Result |
|-----------|-------|-----------------|
| MLflow UI | http://localhost:5000 | MLflow interface loads |
| Data Pipeline | `docker-compose logs data-pipeline` | Data uploaded to S3 |
| Model Pipeline | MLflow UI experiments | Model artifacts in MLflow |
| Inference Pipeline | S3 console | Prediction results in S3 |
| S3 Integration | AWS S3 console | Artifacts in `zuucrew-mlflow-artifacts-prod` |

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. **Port 5000 Already in Use (macOS)**
**Error**: `bind: address already in use`
**Solution**: We use port 5001 instead (fixed in our setup)
```bash
# Check if port is free
lsof -i :5001
# MLflow UI: http://localhost:5001 (not 5000)
```

#### 2. **AWS Credentials Not Found**
**Error**: `Unable to locate credentials`
**Solution**: 
```bash
# Check AWS credentials exist
ls -la ~/.aws/credentials

# Verify credentials work
aws sts get-caller-identity

# Test in container
docker-compose run --rm data-pipeline aws sts get-caller-identity
```

#### 3. **MLflow Service Not Ready**
**Error**: `MLflow not ready, waiting...`
**Solution**:
```bash
# Check MLflow status
make docker-status

# View MLflow logs
docker-compose logs mlflow-tracking

# Test MLflow health
curl http://localhost:5001/health
```

#### 4. **Docker Build Fails (Java/Python Issues)**
**Error**: `UnsupportedClassVersionError` or `externally-managed-environment`
**Solution**: Our Dockerfiles handle this with:
- Java 17 (`eclipse-temurin:17-jre`)
- Python with `--break-system-packages`
```bash
# Clean rebuild if issues
make docker-clean
make docker-build
```

#### 5. **S3 Permission Errors**  
**Error**: `AccessDenied` when uploading to S3
**Solution**: Add S3 bucket policy for root user:
```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"AWS": "arn:aws:iam::899013845787:root"},
        "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
        "Resource": [
            "arn:aws:s3:::zuucrew-mlflow-artifacts-prod",
            "arn:aws:s3:::zuucrew-mlflow-artifacts-prod/*"
        ]
    }]
}
```

#### 6. **Model Not Found in Inference**
**Error**: `No MLflow models found with base name`
**Solution**: Models are saved with timestamps
```bash
# Check what models exist in MLflow
open http://localhost:5001  # Go to "Models" tab

# Check S3 model artifacts
make s3-list PREFIX=artifacts/model_artifacts/

# Model names: spark_random_forest_20251005025511 (with timestamp)
```

#### 7. **Pipeline Container Exits Immediately**
**Error**: Container stops right after starting
**Solution**: 
```bash
# Check container logs
docker-compose logs data-pipeline

# Run interactively for debugging
docker-compose run --rm data-pipeline bash

# Check environment variables
docker-compose run --rm data-pipeline env | grep MLFLOW
```

### Debug Commands
```bash
# Interactive container access
docker-compose run --rm data-pipeline bash
docker-compose run --rm model-pipeline bash

# Check specific service logs
docker-compose logs -f mlflow-tracking
docker-compose logs -f data-pipeline

# Test individual components
docker-compose run --rm data-pipeline python3 -c "import boto3; print('S3 OK')"
docker-compose run --rm model-pipeline curl http://mlflow-tracking:5001/health
```

### Performance Optimization

1. **Build Caching**
   ```bash
   # Enable Docker BuildKit
   export DOCKER_BUILDKIT=1
   
   # Use build cache
   make docker-build
   ```

2. **Resource Limits**
   Add to docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G
         cpus: '2.0'
   ```

3. **Parallel Execution**
   ```bash
   # Run pipelines in parallel (advanced)
   docker-compose up -d mlflow-tracking
   docker-compose run -d --name data-pipeline data-pipeline
   docker-compose run -d --name model-pipeline model-pipeline
   ```

## 🎯 Production Considerations

### For AWS ECS Deployment
1. Replace volume mounts with IAM roles
2. Use AWS Secrets Manager for sensitive data
3. Configure ALB for MLflow UI access
4. Set up CloudWatch logging

### Scaling Considerations
1. Use external database for MLflow backend
2. Configure Spark cluster mode
3. Implement pipeline orchestration (Airflow/Prefect)
4. Add monitoring and alerting

## 📝 Development Workflow

### Local Development
```bash
# Start only MLflow for development
make docker-mlflow

# Run pipelines locally with Docker MLflow
MLFLOW_TRACKING_URI=http://localhost:5000 make data-pipeline
```

### Testing Changes
```bash
# Rebuild specific service
docker-compose build data-pipeline

# Run single pipeline
make docker-data-pipeline
```

### Cleanup
```bash
# Stop services
make docker-down

# Full cleanup
make docker-clean
```

## 🎯 Real Execution Examples

### Complete First-Time Setup (Copy & Paste)
```bash
# Step-by-step first-time setup
echo "🚀 Starting Docker ML Pipeline Setup..."

# 1. Check prerequisites
docker --version && echo "✅ Docker OK" || echo "❌ Install Docker"
aws sts get-caller-identity && echo "✅ AWS OK" || echo "❌ Configure AWS"

# 2. Setup environment
cp .env.example .env && echo "✅ Environment configured"

# 3. Upload data (one-time)
make s3-upload-data && echo "✅ Data uploaded to S3"

# 4. Build Docker images (10-15 minutes)
echo "⏳ Building Docker images (this takes 10-15 minutes)..."
make docker-build && echo "✅ Docker images built"

# 5. Start MLflow service
make docker-up && echo "✅ MLflow started on port 5001"
sleep 30 && echo "✅ MLflow ready"

# 6. Run complete workflow
make docker-run-all && echo "🎉 Complete ML workflow finished!"

# 7. View results
echo "🌐 MLflow UI: http://localhost:5001"
echo "☁️ S3 Artifacts:"
make s3-list PREFIX=artifacts/
```

### Quick Daily Usage
```bash
# Start MLflow
make docker-up

# Run model training
make docker-model-pipeline

# View results in MLflow UI
open http://localhost:5001

# Stop services
make docker-down
```

### Troubleshooting Commands
```bash
# If things go wrong, run these in order:

# 1. Check service status
make docker-status

# 2. View logs
make docker-logs | tail -20

# 3. Test MLflow connectivity
curl http://localhost:5001/health

# 4. Test S3 connectivity  
make s3-smoke

# 5. If still issues, clean rebuild
make docker-clean && make docker-build
```

## 📊 Expected Results

### After Successful Setup
- **MLflow UI**: http://localhost:5001 shows experiments and models
- **S3 Bucket**: Contains organized artifacts in timestamp folders
- **Model Performance**: ~85.86% accuracy on churn prediction
- **Processing Speed**: 8,001 training samples in ~7 seconds

### S3 Artifact Structure (After Full Run)
```
s3://zuucrew-mlflow-artifacts-prod/
├── data/raw/ChurnModelling.csv                    # Raw data (729KB)
├── artifacts/data_artifacts/20251005025511/       # Latest data run
│   ├── X_train.csv (454KB), X_test.csv (113KB)   # Features
│   ├── Y_train.csv (16KB), Y_test.csv (4KB)      # Labels  
│   ├── Geography_encoder.json, Gender_encoder.json # Encoders
│   └── preprocessing_metadata.json                # Metadata
├── artifacts/model_artifacts/20251005025511/      # Latest model run
│   └── spark_random_forest_model_metadata.json   # Model info
├── artifacts/inference_artifacts/20251005025511/  # Latest inference run
│   ├── inference_results.json                    # Predictions
│   └── inference_summary.json                    # Summary stats
└── mlflow-artifacts/                              # MLflow S3 backend
    ├── experiments/                               # Experiment data
    └── models/spark_random_forest_20251005025511/ # Registered models
```

This Docker setup provides a complete, production-ready microservices architecture for the ML pipeline with full S3 integration! 🚀

## 🎉 Success Indicators

### ✅ Everything Working When You See:
- **Docker Status**: All services show "Up (healthy)"
- **MLflow UI**: Experiments and models visible at http://localhost:5001
- **S3 Artifacts**: Organized timestamp folders in S3 bucket
- **Pipeline Logs**: "✅ Pipeline completed successfully!" messages
- **Model Metrics**: AUC ~0.86, Accuracy ~0.86 in MLflow
- **No Errors**: Clean execution logs without exceptions
