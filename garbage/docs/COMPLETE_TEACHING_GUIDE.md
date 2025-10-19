# Complete Teaching Guide: Local to Cloud ML Pipeline Deployment

**Last Updated:** October 12, 2025  
**Target Audience:** Students learning production ML systems  
**Duration:** ~4 hours to complete

---

## 📚 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Part 1: Local Development Setup](#part-1-local-development-setup)
5. [Part 2: AWS RDS Configuration](#part-2-aws-rds-configuration)
6. [Part 3: Docker & Airflow Setup](#part-3-docker--airflow-setup)
7. [Part 4: AWS ECS Deployment](#part-4-aws-ecs-deployment)
8. [Part 5: Understanding the Deployment Scripts](#part-5-understanding-the-deployment-scripts)
9. [Part 6: Monitoring & Operations](#part-6-monitoring--operations)
10. [Best Practices & Tips](#best-practices--tips)

---

## Overview

### What You'll Learn

In this guide, you'll learn how to build and deploy a complete production-grade machine learning pipeline that runs in two environments:

1. **Local Development** - Docker-based setup on your laptop
2. **Cloud Production** - AWS ECS Fargate with scalable infrastructure

### The ML Pipeline

Our churn prediction pipeline consists of:
- **Data Pipeline**: Preprocesses customer data
- **Training Pipeline**: Trains machine learning models
- **Inference Pipeline**: Makes predictions on new data

### Key Technologies

- **Orchestration**: Apache Airflow (with CeleryExecutor)
- **Experiment Tracking**: MLflow
- **Containerization**: Docker
- **Cloud Platform**: AWS (ECS, RDS, ECR, ALB, CloudWatch)
- **Infrastructure as Code**: Shell scripts (not Terraform/CDK)

---

## Architecture

### Local Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Laptop (localhost)                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐  │
│  │  Airflow   │  │   MLflow   │  │  Local PostgreSQL    │  │
│  │  UI :8080  │  │  UI :5001  │  │  (Airflow metadata)  │  │
│  └────────────┘  └────────────┘  └──────────────────────┘  │
│                                                               │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐  │
│  │ Scheduler  │  │   Worker   │  │       Redis          │  │
│  └────────────┘  └────────────┘  └──────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Docker Containers (churn-pipeline-network)    │  │
│  │  - data-pipeline    - model-pipeline                  │  │
│  │  - inference-pipeline                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  Storage:                                                    │
│  • S3 (MLflow artifacts)                                    │
│  • RDS (MLflow experiments - shared with ECS)               │
└─────────────────────────────────────────────────────────────┘
```

### AWS ECS Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                         AWS Cloud (ap-south-1)                     │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────── VPC ─────────────────────────────┐     │
│  │                                                           │     │
│  │  ┌──────────────────────────────────────────────┐       │     │
│  │  │  Application Load Balancer (Public)          │       │     │
│  │  │  • :80 → Airflow UI                          │       │     │
│  │  │  • :5001 → MLflow UI                         │       │     │
│  │  └──────────────────────────────────────────────┘       │     │
│  │                          ↓                                │     │
│  │  ┌──────────────────────────────────────────────┐       │     │
│  │  │  ECS Fargate Services (Public Subnets)       │       │     │
│  │  │  ┌────────────┐  ┌────────────┐             │       │     │
│  │  │  │  Airflow   │  │   MLflow   │             │       │     │
│  │  │  │  Web/Sched │  │  Tracking  │             │       │     │
│  │  │  │  /Worker   │  │   Server   │             │       │     │
│  │  │  └────────────┘  └────────────┘             │       │     │
│  │  │                                               │       │     │
│  │  │  Pipeline Tasks (run on-demand via ECS):    │       │     │
│  │  │  • data-pipeline    • model-pipeline         │       │     │
│  │  │  • inference-pipeline                        │       │     │
│  │  └──────────────────────────────────────────────┘       │     │
│  │                                                           │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │     │
│  │  │     RDS      │  │ ElastiCache  │  │     ECR     │  │     │
│  │  │  PostgreSQL  │  │    Redis     │  │  (Images)   │  │     │
│  │  │  (Airflow +  │  │              │  │             │  │     │
│  │  │   MLflow)    │  │              │  │             │  │     │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │     │
│  │                                                           │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                     │
│  External Services:                                                │
│  • S3 Bucket (MLflow artifacts)                                   │
│  • CloudWatch Logs                                                 │
│  • Secrets Manager (credentials)                                   │
│  • IAM Roles (task execution)                                      │
└───────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Software

```bash
# 1. Docker Desktop
# Download: https://www.docker.com/products/docker-desktop

# 2. AWS CLI
brew install awscli  # macOS
# or download from: https://aws.amazon.com/cli/

# 3. Python 3.11+
python3 --version

# 4. Make
make --version
```

### Required AWS Account

1. AWS account with admin access
2. AWS credentials configured
3. RDS PostgreSQL instance (existing)
4. S3 bucket for MLflow artifacts (existing)

### Project Structure

```
Week 11/
├── run_local.sh           # Local deployment script
├── run_ecs.sh             # ECS deployment script
├── Makefile               # Make commands
├── .env                   # Environment variables
├── docker/                # Dockerfiles
│   ├── Dockerfile.base    # Base image for pipelines
│   ├── Dockerfile.mlflow  # MLflow server
│   └── Dockerfile.airflow # Custom Airflow image
├── docker-compose.yml     # ML services
├── docker-compose.airflow.yml  # Airflow services
├── airflow/               # Local Airflow DAGs
│   └── dags/
│       ├── data_pipeline_dag.py
│       ├── model_training_dag.py
│       └── inference_pipeline_dag.py
├── ecs-deploy/            # ECS deployment files
│   ├── 00_env.sh          # Environment config
│   ├── 10_bootstrap.sh    # ECR setup
│   ├── 20_networking.sh   # Security groups
│   ├── 30_iam.sh          # IAM roles
│   ├── 40_cluster_alb.sh  # ECS cluster + ALB
│   ├── 50_register_tasks.sh  # Task definitions
│   ├── 60_services.sh     # ECS services
│   ├── 70_airflow_init.sh # Airflow initialization
│   ├── 80_airflow_vars.sh # Airflow variables
│   ├── 99_cleanup_all.sh  # Cleanup script
│   ├── taskdefs/          # ECS task definitions (JSON)
│   └── airflow/dags/      # ECS-specific DAGs
├── src/                   # ML pipeline code
├── pipelines/             # Pipeline orchestration
└── docs/                  # Documentation
```

---

## Part 1: Local Development Setup

### Step 1: Configure AWS Credentials

```bash
# Run AWS configure
aws configure

# You'll be prompted for:
AWS Access Key ID: [your-access-key]
AWS Secret Access Key: [your-secret-key]
Default region name: ap-south-1
Default output format: json

# Verify it works
aws sts get-caller-identity
```

**What this does:**
- Creates `~/.aws/credentials` and `~/.aws/config`
- Stores your AWS access keys securely
- Sets default region for AWS CLI commands

### Step 2: Create .env File

Create `.env` in the project root:

```bash
# RDS Configuration (for MLflow)
RDS_HOST=your-rds-instance.amazonaws.com
RDS_USER=zuucrew
RDS_PASSWORD=your-password
RDS_MLFLOW_DB=mlflow
RDS_PORT=5432

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-south-1

# S3 Configuration
S3_BUCKET=your-mlflow-bucket

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5001
```

**Why we need this:**
- MLflow stores experiments in RDS (shared between local and ECS)
- MLflow stores artifacts in S3
- Pipelines need AWS access to read/write data

### Step 3: Understand Docker Compose Files

#### docker-compose.yml (ML Services)

```yaml
services:
  mlflow-tracking:
    image: churn-pipeline/mlflow:latest
    ports:
      - "5001:5001"
    environment:
      - RDS_HOST=${RDS_HOST}
      - RDS_USER=${RDS_USER}
      - RDS_PASSWORD=${RDS_PASSWORD}
      - S3_BUCKET=${S3_BUCKET}
    networks:
      - churn-pipeline-network

  data-pipeline:
    image: churn-pipeline/data:latest
    # ... similar config

  model-pipeline:
    image: churn-pipeline/model:latest
    # ... similar config

  inference-pipeline:
    image: churn-pipeline/inference:latest
    # ... similar config

networks:
  churn-pipeline-network:
    external: true
```

**Key points:**
- All services share `churn-pipeline-network`
- Environment variables loaded from `.env`
- MLflow uses RDS for metadata, S3 for artifacts

#### docker-compose.airflow.yml (Airflow Services)

```yaml
services:
  airflow-postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - airflow-postgres-data:/var/lib/postgresql/data

  airflow-webserver:
    image: churn-pipeline/airflow:2.8.1-amazon
    depends_on:
      - airflow-postgres
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@airflow-postgres:5432/airflow
      AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@airflow-postgres:5432/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
    ports:
      - "8080:8080"
    networks:
      - churn-pipeline-network

  airflow-scheduler:
    # ... similar to webserver

  airflow-worker:
    # ... similar to webserver

  flower:
    # ... Celery monitoring UI

  redis:
    image: redis:latest

volumes:
  airflow-postgres-data:

networks:
  churn-pipeline-network:
    external: true
```

**Key points:**
- Local Airflow uses **local PostgreSQL container** (not RDS)
- ECS Airflow will use **RDS PostgreSQL** (different database!)
- This isolation prevents conflicts between local and cloud

### Step 4: Run Local Deployment

```bash
# Option 1: Use the shell script (recommended)
./run_local.sh

# Option 2: Use Make command
make deploy-local

# Option 3: Manual step-by-step
make docker-build        # Build all images
make airflow-build       # Build Airflow image
make docker-up           # Start MLflow + pipelines
make airflow-init        # Initialize Airflow (clears history!)
make airflow-up          # Start Airflow services
```

### Step 5: Verify Local Setup

```bash
# Check running containers
docker ps

# You should see:
# - mlflow-tracking
# - airflow-webserver
# - airflow-scheduler
# - airflow-worker
# - flower
# - airflow-postgres
# - redis
# - data-pipeline (may be stopped - runs on demand)
# - model-pipeline (may be stopped)
# - inference-pipeline (may be stopped)

# Access UIs
open http://localhost:8080   # Airflow (admin/admin)
open http://localhost:5001   # MLflow
open http://localhost:5555   # Flower

# Check Airflow DAGs
# Go to Airflow UI → should see 3 DAGs:
# - data_pipeline_every_20m
# - inference_pipeline_every_10m
# - train_pipeline_every_60m
```

### Step 6: Understand Local DAGs

**Example: data_pipeline_dag.py**

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 12),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    'data_pipeline_every_20m',
    default_args=default_args,
    description='Data preprocessing pipeline',
    schedule='*/20 * * * *',  # Every 20 minutes
    catchup=False,
    max_active_runs=1,
)

run_data_pipeline = DockerOperator(
    task_id='run_data_pipeline',
    image='churn-pipeline/data:latest',
    api_version='auto',
    auto_remove=True,
    network_mode='churn-pipeline-network',  # Connect to same network
    environment={
        'MLFLOW_TRACKING_URI': 'http://mlflow-tracking:5001',
        'AWS_ACCESS_KEY_ID': '{{ var.value.AWS_ACCESS_KEY_ID }}',
        # ... other env vars
    },
    dag=dag,
)
```

**Key concepts:**
- Uses `DockerOperator` to run containers
- Containers connect to `churn-pipeline-network`
- Can access MLflow at `mlflow-tracking:5001` (Docker DNS)
- Schedule is cron format: `*/20 * * * *` = every 20 mins

---

## Part 2: AWS RDS Configuration

### Why RDS?

- **MLflow**: Stores experiment metadata (runs, parameters, metrics)
- **Airflow (ECS only)**: Stores DAG metadata, task history
- **Shared**: Local and ECS both use same RDS for MLflow (shared experiments)
- **Isolated**: Local Airflow uses local PostgreSQL, ECS Airflow uses RDS

### Step 1: Create RDS Instance (if not exists)

```bash
# Check if RDS exists
aws rds describe-db-instances \
  --db-instance-identifier churn-pipeline-metadata-db \
  --region ap-south-1

# If not exists, create it
aws rds create-db-instance \
  --db-instance-identifier churn-pipeline-metadata-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 13.7 \
  --master-username zuucrew \
  --master-user-password your-password \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --publicly-accessible \
  --region ap-south-1
```

### Step 2: Configure Security Groups

```bash
# Get your public IP
MY_IP=$(curl -s https://checkip.amazonaws.com)

# Allow access from your IP
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 5432 \
  --cidr $MY_IP/32 \
  --region ap-south-1
```

### Step 3: Create Databases

```bash
# Install PostgreSQL client if needed
brew install postgresql

# Connect to RDS
psql -h churn-pipeline-metadata-db.xxxxx.ap-south-1.rds.amazonaws.com \
     -U zuucrew \
     -d postgres

# Create databases
CREATE DATABASE mlflow;
CREATE DATABASE airflow;

# Verify
\l
```

**Database purposes:**
- `mlflow`: Stores experiment runs, metrics, parameters
- `airflow`: Stores DAG runs, task instances (ECS only)

---

## Part 3: Docker & Airflow Setup

### Understanding Docker Images

We build 5 Docker images:

#### 1. Dockerfile.base (Multi-stage for pipelines)

```dockerfile
FROM eclipse-temurin:17-jre as ml-base

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip

# Copy requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy code
COPY src/ ./src/
COPY pipelines/ ./pipelines/
COPY config.yaml .

# This is the base, then we have targets:
# - data-pipeline
# - model-pipeline  
# - inference-pipeline
```

#### 2. Dockerfile.mlflow

```dockerfile
FROM python:3.11-slim

# Install MLflow
RUN pip install mlflow psycopg2-binary boto3

# Copy entrypoint
COPY docker/mlflow-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

**mlflow-entrypoint.sh:**
```bash
#!/bin/bash
mlflow server \
  --backend-store-uri postgresql://${RDS_USER}:${RDS_PASSWORD}@${RDS_HOST}:5432/${RDS_MLFLOW_DB} \
  --default-artifact-root s3://${S3_BUCKET}/artifacts \
  --host 0.0.0.0 \
  --port 5001
```

#### 3. Dockerfile.airflow

```dockerfile
FROM apache/airflow:2.8.1-python3.11

# Install providers
RUN pip install \
    apache-airflow-providers-amazon \
    apache-airflow-providers-docker \
    psycopg2-binary

# Copy DAGs
COPY ecs-deploy/airflow/dags/*.py /opt/airflow/dags/
```

**Why copy ECS DAGs into image?**
- ECS doesn't have access to local filesystem
- DAGs must be baked into the Docker image
- Local Airflow mounts DAGs as volumes instead

### Building Images

```bash
# Build all pipeline images
docker compose -f docker-compose.yml build

# Build Airflow image
docker compose -f docker-compose.airflow.yml build airflow-init

# Verify images
docker images | grep churn-pipeline
```

### Airflow Initialization

```bash
# What airflow-init does:
# 1. Drops all volumes (clears history)
# 2. Removes logs
# 3. Clears Python cache
# 4. Creates fresh local PostgreSQL database
# 5. Runs: airflow db init (creates tables)
# 6. Runs: airflow users create (admin user)

make airflow-init

# Check if successful
docker logs airflow-init
```

### Network Configuration

```bash
# Create Docker network
docker network create churn-pipeline-network

# Why external network?
# - Allows services to communicate across compose files
# - MLflow and Airflow can talk to pipeline containers
# - Containers can resolve each other by name (DNS)

# Test connectivity
docker run --rm --network churn-pipeline-network alpine ping mlflow-tracking
```

---

## Part 4: AWS ECS Deployment

### Overview

ECS deployment involves 9 scripts that must run in order:

```
rebuild_for_amd64.sh → 10_bootstrap.sh → 20_networking.sh → 30_iam.sh 
→ 40_cluster_alb.sh → 50_register_tasks.sh → 60_services.sh 
→ 70_airflow_init.sh → 80_airflow_vars.sh
```

### Step 1: Configure Environment (00_env.sh)

**Location:** `ecs-deploy/00_env.sh`

```bash
#!/bin/bash
set -eo pipefail

# AWS Configuration
export AWS_REGION="ap-south-1"
export ACCOUNT_ID="899013845787"
export PROJECT="churn-pipeline"
export VPC_ID="vpc-xxxxxx"

# Subnets
export PUBLIC_SUBNETS='["subnet-xxx","subnet-yyy","subnet-zzz"]'
export PRIVATE_SUBNETS='["subnet-xxx","subnet-yyy","subnet-zzz"]'

# RDS
export RDS_HOST="churn-pipeline-metadata-db.xxxxx.rds.amazonaws.com"
export RDS_USER="zuucrew"
export RDS_PASSWORD="your-password"
export RDS_DB="airflow"
export RDS_MLFLOW_DB="mlflow"

# Redis
export REDIS_ENDPOINT="churn-pipeline-redis.xxxxx.cache.amazonaws.com"

# S3
export S3_BUCKET="your-mlflow-bucket"

# Computed variables
export ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
export ECS_CLUSTER="${PROJECT}-ecs"
export ALB_NAME="${PROJECT}-alb"
```

**What this does:**
- Centralizes all configuration in one place
- Other scripts source this file: `source 00_env.sh`
- Generates `.env.out` with computed values

### Step 2: Rebuild Images for AMD64

**Why needed:**
- Local Mac uses ARM64 (Apple Silicon)
- AWS Fargate requires AMD64/x86_64
- Must rebuild all images for correct architecture

**Script:** `ecs-deploy/rebuild_for_amd64.sh`

```bash
#!/bin/bash
set -e

# Use Docker Buildx for cross-platform builds
docker buildx create --name amd64-builder --use 2>/dev/null || true

# Build each image for linux/amd64
IMAGES=(
    "churn-pipeline/airflow:2.8.1-amazon"
    "churn-pipeline/mlflow:latest"
    "churn-pipeline/data:latest"
    "churn-pipeline/model:latest"
    "churn-pipeline/inference:latest"
)

for img in "${IMAGES[@]}"; do
    echo "Building $img for linux/amd64..."
    
    # Parse image name and Dockerfile
    if [[ $img == *"airflow"* ]]; then
        docker buildx build \
            --platform linux/amd64 \
            --file docker/Dockerfile.airflow \
            --tag $img \
            --load \
            .
    elif [[ $img == *"mlflow"* ]]; then
        docker buildx build \
            --platform linux/amd64 \
            --file docker/Dockerfile.mlflow \
            --tag $img \
            --load \
            .
    elif [[ $img == *"data"* ]]; then
        docker buildx build \
            --platform linux/amd64 \
            --file docker/Dockerfile.base \
            --target data-pipeline \
            --tag $img \
            --load \
            .
    # ... similar for model and inference
    fi
done

# Verify platform
for img in "${IMAGES[@]}"; do
    PLATFORM=$(docker inspect $img --format='{{.Os}}/{{.Architecture}}')
    echo "✅ $img → $PLATFORM"
done

# Clean up dangling images
docker image prune -f
```

**Run it:**
```bash
cd ecs-deploy
./rebuild_for_amd64.sh

# Takes 10-15 minutes on Apple Silicon
# Output: All images rebuilt for linux/amd64
```

### Step 3: Bootstrap ECR Repositories

**Script:** `ecs-deploy/10_bootstrap.sh`

```bash
#!/bin/bash
set -e
source 00_env.sh

# Create ECR repositories
REPOS=(
    "churn-pipeline/airflow"
    "churn-pipeline/mlflow"
    "churn-pipeline/data"
    "churn-pipeline/model"
    "churn-pipeline/inference"
)

for repo in "${REPOS[@]}"; do
    # Check if exists
    if aws ecr describe-repositories \
        --repository-names "$repo" \
        --region "$AWS_REGION" &>/dev/null; then
        echo "✅ Repository exists: $repo"
    else
        # Create repository
        aws ecr create-repository \
            --repository-name "$repo" \
            --region "$AWS_REGION" \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256
        echo "✅ Created: $repo"
    fi
done

# Login to ECR
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin \
    "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Tag and push images
LOCAL_IMAGES=(
    "churn-pipeline/airflow:2.8.1-amazon"
    "churn-pipeline/mlflow:latest"
    "churn-pipeline/data:latest"
    "churn-pipeline/model:latest"
    "churn-pipeline/inference:latest"
)

ECR_REPOS=(
    "churn-pipeline/airflow"
    "churn-pipeline/mlflow"
    "churn-pipeline/data"
    "churn-pipeline/model"
    "churn-pipeline/inference"
)

for i in "${!LOCAL_IMAGES[@]}"; do
    local_img="${LOCAL_IMAGES[$i]}"
    ecr_repo="${ECR_REPOS[$i]}"
    ecr_uri="${ECR_REGISTRY}/${ecr_repo}:latest"
    
    # Tag
    docker tag "$local_img" "$ecr_uri"
    
    # Push
    docker push "$ecr_uri"
    echo "✅ Pushed: $ecr_uri"
done

# Save ECR URIs to .env.out
cat > .env.out <<EOF
IMG_AIRFLOW_ECR=${ECR_REGISTRY}/churn-pipeline/airflow:latest
IMG_MLFLOW_ECR=${ECR_REGISTRY}/churn-pipeline/mlflow:latest
IMG_DATA_ECR=${ECR_REGISTRY}/churn-pipeline/data:latest
IMG_TRAIN_ECR=${ECR_REGISTRY}/churn-pipeline/model:latest
IMG_INFER_ECR=${ECR_REGISTRY}/churn-pipeline/inference:latest
EOF
```

**What this does:**
1. Creates ECR repositories (container registry)
2. Logs into ECR
3. Tags local images with ECR URIs
4. Pushes images to ECR
5. Saves URIs for next scripts

### Step 4: Setup Networking

**Script:** `ecs-deploy/20_networking.sh`

```bash
#!/bin/bash
set -e
source 00_env.sh

# Create ECS Tasks Security Group
SG_NAME="ecs-tasks-${PROJECT}"

SG_ECS_ID=$(aws ec2 create-security-group \
    --group-name "$SG_NAME" \
    --description "Security group for ECS tasks" \
    --vpc-id "$VPC_ID" \
    --region "$AWS_REGION" \
    --query 'GroupId' \
    --output text)

echo "✅ Created ECS security group: $SG_ECS_ID"

# Allow inbound traffic from ALB on port 8080 (Airflow)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ECS_ID" \
    --protocol tcp \
    --port 8080 \
    --source-group "$SG_ALB_ID" \
    --region "$AWS_REGION"

# Allow inbound traffic from ALB on port 5001 (MLflow)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ECS_ID" \
    --protocol tcp \
    --port 5001 \
    --source-group "$SG_ALB_ID" \
    --region "$AWS_REGION"

# Allow ECS tasks to communicate with each other (Redis)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ECS_ID" \
    --protocol tcp \
    --port 6379 \
    --source-group "$SG_ECS_ID" \
    --region "$AWS_REGION"

# Create ALB Security Group
SG_ALB_NAME="alb-${PROJECT}"

SG_ALB_ID=$(aws ec2 create-security-group \
    --group-name "$SG_ALB_NAME" \
    --description "Security group for ALB" \
    --vpc-id "$VPC_ID" \
    --region "$AWS_REGION" \
    --query 'GroupId' \
    --output text)

# Allow HTTP from anywhere
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ALB_ID" \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region "$AWS_REGION"

# Allow port 5001 from anywhere (MLflow)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ALB_ID" \
    --protocol tcp \
    --port 5001 \
    --cidr 0.0.0.0/0 \
    --region "$AWS_REGION"

# Create CloudWatch Log Group
aws logs create-log-group \
    --log-group-name "/ecs/${PROJECT}" \
    --region "$AWS_REGION"

echo "✅ Created CloudWatch log group: /ecs/${PROJECT}"

# Save to .env.out
cat >> .env.out <<EOF
SG_ECS_ID=${SG_ECS_ID}
SG_ALB_ID=${SG_ALB_ID}
EOF
```

**What this does:**
- Creates security group for ECS tasks
- Creates security group for ALB
- Configures firewall rules (who can talk to whom)
- Creates CloudWatch Logs group for container logs

### Step 5: Create IAM Roles

**Script:** `ecs-deploy/30_iam.sh`

```bash
#!/bin/bash
set -e
source 00_env.sh

# Task Execution Role (used by ECS to start containers)
EXEC_ROLE_NAME="${PROJECT}-task-execution-role"

# Create trust policy
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
    --role-name "$EXEC_ROLE_NAME" \
    --assume-role-policy-document file://trust-policy.json \
    --region "$AWS_REGION"

# Attach AWS managed policies
aws iam attach-role-policy \
    --role-name "$EXEC_ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" \
    --region "$AWS_REGION"

# Task Role (used by containers to access AWS services)
TASK_ROLE_NAME="${PROJECT}-task-role"

aws iam create-role \
    --role-name "$TASK_ROLE_NAME" \
    --assume-role-policy-document file://trust-policy.json \
    --region "$AWS_REGION"

# Create custom policy for S3 access
cat > s3-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ],
    "Resource": [
      "arn:aws:s3:::${S3_BUCKET}",
      "arn:aws:s3:::${S3_BUCKET}/*"
    ]
  }]
}
EOF

aws iam put-role-policy \
    --role-name "$TASK_ROLE_NAME" \
    --policy-name "S3Access" \
    --policy-document file://s3-policy.json

# Save ARNs
EXEC_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${EXEC_ROLE_NAME}"
TASK_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${TASK_ROLE_NAME}"

cat >> .env.out <<EOF
TASK_EXECUTION_ROLE_ARN=${EXEC_ROLE_ARN}
TASK_ROLE_ARN=${TASK_ROLE_ARN}
EOF
```

**What this does:**
- Creates **Task Execution Role** - ECS uses this to pull images, write logs
- Creates **Task Role** - Containers use this to access S3, RDS, Secrets Manager
- Sets up permissions policies

### Step 6: Create ECS Cluster and ALB

**Script:** `ecs-deploy/40_cluster_alb.sh`

```bash
#!/bin/bash
set -e
source 00_env.sh
source .env.out

# Create ECS Cluster
aws ecs create-cluster \
    --cluster-name "$ECS_CLUSTER" \
    --region "$AWS_REGION"

echo "✅ Created ECS cluster: $ECS_CLUSTER"

# Create Application Load Balancer
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name "$ALB_NAME" \
    --subnets ${PUBLIC_SUBNETS//[\[\]\"]/} \
    --security-groups "$SG_ALB_ID" \
    --scheme internet-facing \
    --region "$AWS_REGION" \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

# Get ALB DNS
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns "$ALB_ARN" \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo "✅ Created ALB: $ALB_DNS"

# Create Target Group for Airflow
TG_AIRFLOW_ARN=$(aws elbv2 create-target-group \
    --name "${PROJECT}-airflow-tg" \
    --protocol HTTP \
    --port 8080 \
    --vpc-id "$VPC_ID" \
    --target-type ip \
    --health-check-path "/health" \
    --region "$AWS_REGION" \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# Create Target Group for MLflow
TG_MLFLOW_ARN=$(aws elbv2 create-target-group \
    --name "${PROJECT}-mlflow-tg" \
    --protocol HTTP \
    --port 5001 \
    --vpc-id "$VPC_ID" \
    --target-type ip \
    --health-check-path "/" \
    --region "$AWS_REGION" \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# Create Listener on port 80 (Airflow)
aws elbv2 create-listener \
    --load-balancer-arn "$ALB_ARN" \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn="$TG_AIRFLOW_ARN" \
    --region "$AWS_REGION"

# Create Listener on port 5001 (MLflow)
aws elbv2 create-listener \
    --load-balancer-arn "$ALB_ARN" \
    --protocol HTTP \
    --port 5001 \
    --default-actions Type=forward,TargetGroupArn="$TG_MLFLOW_ARN" \
    --region "$AWS_REGION"

cat >> .env.out <<EOF
ALB_ARN=${ALB_ARN}
ALB_DNS=${ALB_DNS}
TG_AIRFLOW_ARN=${TG_AIRFLOW_ARN}
TG_MLFLOW_ARN=${TG_MLFLOW_ARN}
EOF
```

**What this does:**
- Creates ECS cluster (logical grouping of services)
- Creates Application Load Balancer (entry point for traffic)
- Creates Target Groups (routes traffic to containers)
- Creates Listeners (maps ports 80 and 5001 to target groups)

**Architecture:**
```
Internet → ALB:80 → Airflow Target Group → Airflow Tasks
Internet → ALB:5001 → MLflow Target Group → MLflow Tasks
```

### Step 7: Register Task Definitions

**Script:** `ecs-deploy/50_register_tasks.sh`

```bash
#!/bin/bash
set -e
source 00_env.sh
source .env.out

# Process each task definition template
for template in taskdefs/*.json.template; do
    output="${template%.template}"
    
    # Replace variables in template
    envsubst < "$template" > "$output"
    
    # Register with ECS
    aws ecs register-task-definition \
        --cli-input-json "file://${output}" \
        --region "$AWS_REGION"
    
    echo "✅ Registered: $(basename $output)"
done
```

**Example Task Definition:** `taskdefs/airflow-web.json.template`

```json
{
  "family": "churn-pipeline-airflow-web",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "taskRoleArn": "${TASK_ROLE_ARN}",
  "executionRoleArn": "${TASK_EXECUTION_ROLE_ARN}",
  "containerDefinitions": [{
    "name": "airflow-webserver",
    "image": "${IMG_AIRFLOW_ECR}",
    "essential": true,
    "portMappings": [{
      "containerPort": 8080,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "AIRFLOW__CORE__EXECUTOR", "value": "CeleryExecutor"},
      {"name": "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", 
       "value": "postgresql+psycopg2://${RDS_USER}:${RDS_PASSWORD}@${RDS_HOST}:5432/${RDS_DB}"},
      {"name": "AIRFLOW__CELERY__BROKER_URL", 
       "value": "redis://${REDIS_ENDPOINT}:6379/0"},
      {"name": "AWS_DEFAULT_REGION", "value": "${AWS_REGION}"}
    ],
    "command": ["webserver"],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/${PROJECT}",
        "awslogs-region": "${AWS_REGION}",
        "awslogs-stream-prefix": "airflow-web"
      }
    }
  }]
}
```

**Key points:**
- Fargate launch type (serverless containers)
- 512 CPU units = 0.5 vCPU
- 1024 MB memory = 1 GB RAM
- Environment variables for RDS, Redis, AWS
- Logs go to CloudWatch

### Step 8: Create ECS Services

**Script:** `ecs-deploy/60_services.sh`

```bash
#!/bin/bash
set -e
source 00_env.sh
source .env.out

# Create Airflow Webserver Service
aws ecs create-service \
    --cluster "$ECS_CLUSTER" \
    --service-name "airflow-webserver-svc" \
    --task-definition "churn-pipeline-airflow-web" \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={
        subnets=[${PUBLIC_SUBNETS//[\[\]\"]/}],
        securityGroups=[$SG_ECS_ID],
        assignPublicIp=ENABLED
    }" \
    --load-balancers "targetGroupArn=$TG_AIRFLOW_ARN,containerName=airflow-webserver,containerPort=8080" \
    --region "$AWS_REGION"

# Create Airflow Scheduler Service
aws ecs create-service \
    --cluster "$ECS_CLUSTER" \
    --service-name "airflow-scheduler-svc" \
    --task-definition "churn-pipeline-airflow-scheduler" \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={
        subnets=[${PUBLIC_SUBNETS//[\[\]\"]/}],
        securityGroups=[$SG_ECS_ID],
        assignPublicIp=ENABLED
    }" \
    --region "$AWS_REGION"

# Create Airflow Worker Service
aws ecs create-service \
    --cluster "$ECS_CLUSTER" \
    --service-name "airflow-worker-svc" \
    --task-definition "churn-pipeline-airflow-worker" \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={
        subnets=[${PUBLIC_SUBNETS//[\[\]\"]/}],
        securityGroups=[$SG_ECS_ID],
        assignPublicIp=ENABLED
    }" \
    --region "$AWS_REGION"

# Create MLflow Service
aws ecs create-service \
    --cluster "$ECS_CLUSTER" \
    --service-name "mlflow-tracking-svc" \
    --task-definition "churn-pipeline-mlflow" \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={
        subnets=[${PUBLIC_SUBNETS//[\[\]\"]/}],
        securityGroups=[$SG_ECS_ID],
        assignPublicIp=ENABLED
    }" \
    --load-balancers "targetGroupArn=$TG_MLFLOW_ARN,containerName=mlflow-tracking,containerPort=5001" \
    --region "$AWS_REGION"

# Wait for services to stabilize
aws ecs wait services-stable \
    --cluster "$ECS_CLUSTER" \
    --services airflow-webserver-svc airflow-scheduler-svc airflow-worker-svc mlflow-tracking-svc \
    --region "$AWS_REGION"

echo "✅ All services are running!"
```

**What this does:**
- Creates 4 ECS services (long-running containers)
- Each service runs 1 task (desired-count=1)
- Assigns public IPs (needed for internet access)
- Connects webserver/MLflow to target groups (ALB)
- Waits for services to become healthy

### Step 9: Initialize Airflow on ECS

**Script:** `ecs-deploy/70_airflow_init.sh`

```bash
#!/bin/bash
set -e
source 00_env.sh
source .env.out

# Run DB migration
echo "Running airflow db init..."
TASK_ARN=$(aws ecs run-task \
    --cluster "$ECS_CLUSTER" \
    --launch-type FARGATE \
    --task-definition "churn-pipeline-airflow-web" \
    --network-configuration "awsvpcConfiguration={
        subnets=[${PUBLIC_SUBNETS//[\[\]\"]/}],
        securityGroups=[$SG_ECS_ID],
        assignPublicIp=ENABLED
    }" \
    --overrides '{
        "containerOverrides": [{
            "name": "airflow-webserver",
            "command": ["db", "init"]
        }]
    }' \
    --query 'tasks[0].taskArn' \
    --output text \
    --region "$AWS_REGION")

# Wait for task to complete
aws ecs wait tasks-stopped \
    --cluster "$ECS_CLUSTER" \
    --tasks "$TASK_ARN" \
    --region "$AWS_REGION"

echo "✅ DB migration completed"

# Create admin user
echo "Creating admin user..."
TASK_ARN=$(aws ecs run-task \
    --cluster "$ECS_CLUSTER" \
    --launch-type FARGATE \
    --task-definition "churn-pipeline-airflow-web" \
    --network-configuration "awsvpcConfiguration={
        subnets=[${PUBLIC_SUBNETS//[\[\]\"]/}],
        securityGroups=[$SG_ECS_ID],
        assignPublicIp=ENABLED
    }" \
    --overrides '{
        "containerOverrides": [{
            "name": "airflow-webserver",
            "command": ["users", "create", 
                        "--username", "admin",
                        "--password", "admin",
                        "--firstname", "Admin",
                        "--lastname", "User",
                        "--role", "Admin",
                        "--email", "admin@example.com"]
        }]
    }' \
    --query 'tasks[0].taskArn' \
    --output text \
    --region "$AWS_REGION")

aws ecs wait tasks-stopped \
    --cluster "$ECS_CLUSTER" \
    --tasks "$TASK_ARN" \
    --region "$AWS_REGION"

echo "✅ Admin user created (admin/admin)"
```

**What this does:**
- Runs one-off tasks to initialize Airflow
- `airflow db init` - creates tables in RDS
- `airflow users create` - creates admin user
- Uses `run-task` (not `create-service`) for one-time jobs

### Step 10: Configure Airflow Variables

**Script:** `ecs-deploy/80_airflow_vars.sh`

```bash
#!/bin/bash
set -e
source 00_env.sh
source .env.out

# Create script to set variables
cat > /tmp/set_airflow_vars.sh <<'SCRIPT'
#!/bin/bash
airflow variables set ECS_CLUSTER "${ECS_CLUSTER}"
airflow variables set ECS_PRIVATE_SUBNETS "${PRIVATE_SUBNETS}"
airflow variables set ECS_SECURITY_GROUPS "[\"${SG_ECS_ID}\"]"
airflow variables set AWS_REGION "${AWS_REGION}"
airflow variables set S3_BUCKET "${S3_BUCKET}"
airflow variables set MLFLOW_URL "http://mlflow-tracking.internal:5001"
SCRIPT

# Run task with script
aws ecs run-task \
    --cluster "$ECS_CLUSTER" \
    --launch-type FARGATE \
    --task-definition "churn-pipeline-airflow-web" \
    --network-configuration "awsvpcConfiguration={...}" \
    --overrides "{
        \"containerOverrides\": [{
            \"name\": \"airflow-webserver\",
            \"command\": [\"bash\", \"-c\", \"$(cat /tmp/set_airflow_vars.sh)\"]
        }]
    }" \
    --region "$AWS_REGION"

echo "✅ Airflow variables configured"
```

**What this does:**
- Sets Airflow variables that DAGs will use
- Variables tell Airflow how to run ECS tasks
- DAGs use these to dynamically create pipeline jobs

---

## Part 5: Understanding the Deployment Scripts

### run_local.sh

**Purpose:** One-command local deployment with proper checks

**Structure:**
```bash
#!/bin/bash
set -e  # Exit on any error

# 1. Check AWS credentials
aws sts get-caller-identity || exit 1

# 2. Check Docker is running
docker info || exit 1

# 3. Ask for confirmation
read -p "Continue? (yes/no): " confirm
[ "$confirm" != "yes" ] && exit 1

# 4. Build images
make docker-build
make airflow-build

# 5. Start services
make docker-up
make airflow-init
make airflow-up

# 6. Verify
docker ps
docker exec airflow-webserver airflow db check
```

**Why this is better than Make:**
- Color-coded output (red for errors, green for success)
- Pre-flight checks prevent wasted time
- Single shell context (no Make subshell issues)
- Better error messages

### run_ecs.sh

**Purpose:** One-command ECS deployment with credential handling

**Structure:**
```bash
#!/bin/bash
set -e

# Set AWS_PROFILE explicitly
export AWS_PROFILE=${AWS_PROFILE:-default}

# 1. Check credentials
aws sts get-caller-identity || exit 1

# 2. Confirm deployment
read -p "Continue? (yes/no): " confirm

# 3. Run all scripts in order
cd ecs-deploy
./rebuild_for_amd64.sh
./10_bootstrap.sh
./20_networking.sh
./30_iam.sh
./40_cluster_alb.sh
./50_register_tasks.sh
./60_services.sh
./70_airflow_init.sh
./80_airflow_vars.sh

# 4. Show access URLs
echo "Airflow: http://$ALB_DNS"
echo "MLflow: http://$ALB_DNS:5001"
```

**Why shell script instead of Make:**
- Make has subshell issues with environment variables
- Each Make `@` line runs in different shell
- AWS_PROFILE doesn't persist between Make commands
- Shell scripts run in single bash process

### Cleanup Script

**Script:** `ecs-deploy/99_cleanup_all.sh`

```bash
#!/bin/bash
set -e
source 00_env.sh

# WARNING: This deletes everything!
read -p "Type DELETE to confirm: " confirm
[ "$confirm" != "DELETE" ] && exit 1

# 1. Delete ECS Services
for svc in airflow-webserver-svc airflow-scheduler-svc airflow-worker-svc mlflow-tracking-svc; do
    aws ecs delete-service \
        --cluster "$ECS_CLUSTER" \
        --service "$svc" \
        --force \
        --region "$AWS_REGION"
done

# 2. Stop all tasks
TASKS=$(aws ecs list-tasks --cluster "$ECS_CLUSTER" --query 'taskArns[]' --output text)
for task in $TASKS; do
    aws ecs stop-task --cluster "$ECS_CLUSTER" --task "$task" --region "$AWS_REGION"
done

# 3. Delete ECS Cluster
aws ecs delete-cluster --cluster "$ECS_CLUSTER" --region "$AWS_REGION"

# 4. Delete ALB
aws elbv2 delete-load-balancer --load-balancer-arn "$ALB_ARN" --region "$AWS_REGION"

# 5. Delete Target Groups
aws elbv2 delete-target-group --target-group-arn "$TG_AIRFLOW_ARN" --region "$AWS_REGION"
aws elbv2 delete-target-group --target-group-arn "$TG_MLFLOW_ARN" --region "$AWS_REGION"

# 6. Delete Security Groups (wait for resources to detach)
sleep 60
aws ec2 delete-security-group --group-id "$SG_ECS_ID" --region "$AWS_REGION"
aws ec2 delete-security-group --group-id "$SG_ALB_ID" --region "$AWS_REGION"

# 7. Delete IAM Roles
aws iam delete-role --role-name "${PROJECT}-task-execution-role" --region "$AWS_REGION"
aws iam delete-role --role-name "${PROJECT}-task-role" --region "$AWS_REGION"

# 8. Delete ECR Repositories
for repo in "${REPOS[@]}"; do
    aws ecr delete-repository --repository-name "$repo" --force --region "$AWS_REGION"
done

# 9. Delete CloudWatch Log Group
aws logs delete-log-group --log-group-name "/ecs/${PROJECT}" --region "$AWS_REGION"

echo "✅ All resources deleted!"
```

**Make equivalent:**
```bash
make docker-clean-all-ecs
```

---

## Part 6: Monitoring & Operations

### Viewing Logs

**Local:**
```bash
# Airflow scheduler
docker logs airflow-scheduler -f

# Airflow webserver
docker logs airflow-webserver -f

# MLflow
docker logs mlflow-tracking -f

# All Airflow logs
docker compose -f docker-compose.airflow.yml logs -f
```

**ECS:**
```bash
# View all logs
aws logs tail /ecs/churn-pipeline --follow --region ap-south-1

# Filter by container
aws logs tail /ecs/churn-pipeline --follow \
    --filter-pattern "airflow-web" \
    --region ap-south-1

# View specific log stream
aws logs get-log-events \
    --log-group-name /ecs/churn-pipeline \
    --log-stream-name airflow-web/airflow-webserver/xxxxx \
    --region ap-south-1
```

### Checking Service Status

**Local:**
```bash
# Make commands
make docker-status
make airflow-status

# Direct Docker
docker ps
docker stats

# Check networks
docker network inspect churn-pipeline-network
```

**ECS:**
```bash
# List services
aws ecs list-services --cluster churn-pipeline-ecs --region ap-south-1

# Describe service
aws ecs describe-services \
    --cluster churn-pipeline-ecs \
    --services airflow-webserver-svc \
    --region ap-south-1

# List tasks
aws ecs list-tasks --cluster churn-pipeline-ecs --region ap-south-1

# Describe task
aws ecs describe-tasks \
    --cluster churn-pipeline-ecs \
    --tasks <task-arn> \
    --region ap-south-1
```

### Testing DAGs

**Trigger manually:**
```bash
# Local
open http://localhost:8080
# Click on DAG → Trigger DAG

# ECS
open http://your-alb-dns.amazonaws.com
# Click on DAG → Trigger DAG

# Via CLI
docker exec airflow-webserver \
    airflow dags trigger data_pipeline_every_20m
```

**View DAG run:**
```bash
# Check run status
docker exec airflow-webserver \
    airflow dags list-runs -d data_pipeline_every_20m

# View task logs
docker exec airflow-webserver \
    airflow tasks logs data_pipeline_every_20m run_data_pipeline <date>
```

### Updating DAGs

**Local:**
```bash
# DAGs are mounted as volumes
# Edit: airflow/dags/data_pipeline_dag.py
# Save file
# Airflow auto-detects changes in ~30 seconds
# Refresh UI to see updated DAG
```

**ECS:**
```bash
# DAGs are baked into image
# Edit: ecs-deploy/airflow/dags/data_pipeline_ecs_dag.py
# Rebuild Airflow image
cd ecs-deploy
./rebuild_for_amd64.sh  # Only rebuild airflow

# Push to ECR
docker tag churn-pipeline/airflow:2.8.1-amazon \
    ${ECR_REGISTRY}/churn-pipeline/airflow:latest
docker push ${ECR_REGISTRY}/churn-pipeline/airflow:latest

# Force service update
aws ecs update-service \
    --cluster churn-pipeline-ecs \
    --service airflow-webserver-svc \
    --force-new-deployment \
    --region ap-south-1
```

### Scaling ECS Services

```bash
# Scale up workers
aws ecs update-service \
    --cluster churn-pipeline-ecs \
    --service airflow-worker-svc \
    --desired-count 3 \
    --region ap-south-1

# Scale down
aws ecs update-service \
    --cluster churn-pipeline-ecs \
    --service airflow-worker-svc \
    --desired-count 1 \
    --region ap-south-1
```

### Cost Monitoring

```bash
# ECS costs
aws ce get-cost-and-usage \
    --time-period Start=2025-10-01,End=2025-10-12 \
    --granularity DAILY \
    --metrics UnblendedCost \
    --filter file://filter.json

# Approximate daily costs:
# - ECS Fargate (4 tasks): ~$3.84/day
# - ALB: ~$0.60/day  
# - RDS (if new): ~$0.70/day
# - Total: ~$5/day = $150/month
```

---

## Best Practices & Tips

### 1. Development Workflow

**Always start local:**
```bash
# Develop locally
./run_local.sh

# Test DAG
# Trigger manually in Airflow UI
# Check logs
# Verify results in MLflow

# Once working, deploy to ECS
./run_ecs.sh
```

### 2. Database Management

**Local vs ECS isolation:**
- Local Airflow → Local PostgreSQL (ephemeral)
- ECS Airflow → RDS PostgreSQL (persistent)
- Both use same RDS for MLflow (shared experiments)

**Clear local history:**
```bash
make airflow-init
# This drops local PostgreSQL volume
# Doesn't affect ECS or MLflow experiments
```

### 3. Image Management

**Keep images consistent:**
```bash
# After code changes
make docker-build
make airflow-build

# For ECS, rebuild AMD64
cd ecs-deploy
./rebuild_for_amd64.sh
```

**Clean up dangling images:**
```bash
docker image prune -f
```

### 4. Network Debugging

**Test connectivity:**
```bash
# Local containers
docker exec airflow-webserver ping mlflow-tracking
docker exec airflow-webserver curl mlflow-tracking:5001

# ECS tasks (get shell)
aws ecs execute-command \
    --cluster churn-pipeline-ecs \
    --task <task-arn> \
    --container airflow-webserver \
    --interactive \
    --command "/bin/bash"
```

### 5. Secrets Management

**Never commit credentials:**
```bash
# Add to .gitignore
.env
.env.out
*.pem
*.key
credentials
```

**Use Secrets Manager for ECS:**
```bash
# Store secret
aws secretsmanager create-secret \
    --name airflow-db-password \
    --secret-string "your-password" \
    --region ap-south-1

# Reference in task definition
"secrets": [{
    "name": "DB_PASSWORD",
    "valueFrom": "arn:aws:secretsmanager:...:secret:airflow-db-password"
}]
```

### 6. Backup Strategy

**MLflow experiments:**
```bash
# Backup RDS
aws rds create-db-snapshot \
    --db-instance-identifier churn-pipeline-metadata-db \
    --db-snapshot-identifier mlflow-backup-$(date +%Y%m%d)

# Backup S3 artifacts
aws s3 sync s3://your-bucket s3://your-backup-bucket
```

**Airflow DAGs:**
```bash
# DAGs are in Git - just commit
git add airflow/dags/
git commit -m "Update DAGs"
git push
```

### 7. Troubleshooting Checklist

**If DAG doesn't appear:**
1. Check file syntax: `python airflow/dags/my_dag.py`
2. Check Airflow logs: `docker logs airflow-scheduler`
3. Clear cache: Remove `__pycache__` folders
4. Refresh UI: Wait 30 seconds or click refresh

**If container won't start:**
1. Check logs: `docker logs <container-name>`
2. Check resources: `docker stats`
3. Verify network: `docker network ls`
4. Check environment: `docker inspect <container-name>`

**If ECS task fails:**
1. Check CloudWatch logs
2. Check security group rules
3. Verify IAM permissions
4. Check RDS connectivity

### 8. DAG Best Practices

**Set reasonable schedules:**
```python
# Good
schedule='*/20 * * * *'  # Every 20 mins

# Bad (too frequent)
schedule='* * * * *'  # Every minute - wastes resources
```

**Use max_active_runs:**
```python
dag = DAG(
    max_active_runs=1,  # Prevent overlapping runs
)
```

**Set start_date correctly:**
```python
# Always use recent date
start_date=datetime(2025, 10, 12)

# Not old date (causes backfill)
start_date=datetime(2020, 1, 1)  # BAD
```

---

## Summary

You've learned how to:

1. ✅ Set up local ML pipeline with Docker and Airflow
2. ✅ Configure AWS RDS for metadata storage
3. ✅ Deploy complete infrastructure to AWS ECS Fargate
4. ✅ Use 9 deployment scripts to create 28+ AWS resources
5. ✅ Monitor and operate both environments
6. ✅ Troubleshoot common issues
7. ✅ Follow best practices for production ML systems

**Key Takeaways:**

- **Local Development**: Fast iteration with local PostgreSQL
- **Cloud Production**: Scalable with RDS and ECS Fargate
- **Isolation**: Local and ECS don't interfere (different Airflow DBs)
- **Shared**: MLflow experiments shared via RDS
- **Automation**: Shell scripts are more reliable than Make for AWS
- **Monitoring**: CloudWatch Logs for ECS, Docker logs for local

**Next Steps:**

1. Customize pipelines for your use case
2. Add more sophisticated DAGs
3. Implement CI/CD for automated deployments
4. Set up alerting with CloudWatch Alarms
5. Optimize costs with spot instances or scheduled scaling

---

**Questions? Check the debugging guide for common issues and solutions!**

