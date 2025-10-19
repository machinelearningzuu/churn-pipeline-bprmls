# 🚀 Production-Ready ML Pipeline: Customer Churn Prediction

A complete, production-grade machine learning system for predicting customer churn with real-time streaming, automated training, and comprehensive CI/CD validation.

[![CI Status](https://img.shields.io/badge/CI-passing-brightgreen)]()
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

---

## 🎓 Comprehensive Documentation

**NEW! 📚 Detailed end-to-end guides for the complete system:**

| Guide | Description | Read Time |
|-------|-------------|-----------|
| [📖 Kafka Integration](docs-capstone/01_KAFKA_INTEGRATION.md) | Real-time streaming with Kafka, Docker setup, producer/consumer services | 30 min |
| [🔄 CI/CD Configuration](docs-capstone/02_CICD_CONFIGURATION.md) | GitHub Actions, data/model validation, automated testing | 25 min |
| [📊 Analytics & QuickSight](docs-capstone/03_ANALYTICS_QUICKSIGHT.md) | RDS setup, SQL views, QuickSight dashboards, visualizations | 35 min |

**📂 [Browse all capstone documentation →](docs-capstone/)**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Key Features](#key-features)
4. [Prerequisites](#prerequisites)
5. [Quick Start](#quick-start)
6. [Project Structure](#project-structure)
7. [Detailed Setup](#detailed-setup)
8. [Running the Pipeline](#running-the-pipeline)
9. [CI/CD Validation](#cicd-validation)
10. [Monitoring & Analytics](#monitoring--analytics)
11. [Configuration](#configuration)
12. [Troubleshooting](#troubleshooting)
13. [Contributing](#contributing)

---

## 🎯 Overview

This project implements a **complete ML pipeline** for predicting customer churn in a banking context. It demonstrates production-level MLOps practices including:

- 🔄 **Real-time streaming** with Kafka
- 🤖 **Automated training** with Airflow
- 📊 **Model tracking** with MLflow
- 🔍 **Data validation** and drift detection
- 🎯 **Model validation** (F1 >= 75% threshold)
- 📈 **Analytics dashboard** with RDS PostgreSQL
- 🐳 **Containerized** deployment with Docker
- ✅ **CI/CD** with GitHub Actions

### Business Problem

Predict whether a bank customer will churn (leave the bank) based on their profile and behavior. This helps the bank:
- 📞 Proactively reach out to at-risk customers
- 💰 Reduce customer acquisition costs
- 📈 Improve customer retention strategies

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Raw Data   │───▶│  Processed   │───▶│   Features   │          │
│  │   (CSV)      │    │    Data      │    │   (S3)       │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      TRAINING LAYER                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Airflow    │───▶│   Training   │───▶│   MLflow     │          │
│  │ (Scheduler)  │    │   Pipeline   │    │  (Tracking)  │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STREAMING LAYER                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │    Kafka     │───▶│   Consumer   │───▶│  Analytics   │          │
│  │  (Producer)  │    │ (Inference)  │    │     (RDS)    │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CI/CD LAYER                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │    Data      │───▶│    Model     │───▶│   Deploy     │          │
│  │ Validation   │    │ Validation   │    │   (if pass)  │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🔄 Complete ML Pipeline

- **Data Ingestion**: Load and validate raw banking customer data
- **Feature Engineering**: Automated feature transformation and scaling
- **Model Training**: XGBoost, Random Forest, and ensemble models
- **Model Evaluation**: Comprehensive metrics (Accuracy, Precision, Recall, F1, ROC-AUC)
- **Model Deployment**: Automated deployment to S3 and inference service

### 📡 Real-Time Streaming

- **Kafka Producer**: Streams customer events (10 events/second)
- **Kafka Consumer**: Real-time churn predictions
- **Analytics Service**: Stores predictions in PostgreSQL for analysis

### 🤖 Automated Orchestration

- **Airflow DAGs**: Scheduled data processing and model training
- **Weekly Retraining**: Automatic model updates every Sunday
- **Model Registry**: Version control with MLflow

### 🔍 Quality Validation

- **Data Validation**: Schema, types, ranges, drift detection
- **Model Validation**: F1 Score >= 75% (automatic revert if fails)
- **CI/CD Pipeline**: Automated testing on every push

### 📊 Monitoring & Analytics

- **Jupyter Dashboard**: Interactive analytics notebook
- **RDS PostgreSQL**: Real-time prediction storage
- **Model Performance**: Continuous monitoring and alerting

---

## 📦 Prerequisites

### Required Software

- **Python**: 3.9, 3.10, or 3.11
- **Docker**: 20.10+ and Docker Compose 2.0+
- **AWS Account**: For S3 and RDS (optional but recommended)
- **Git**: For version control

### System Requirements

- **OS**: macOS, Linux, or Windows (WSL2)
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk**: 10GB free space
- **CPU**: Multi-core processor recommended

### Python Libraries

All dependencies are in `requirements.txt`:
```bash
pandas >= 2.0.0
numpy >= 1.24.0
scikit-learn >= 1.3.0
xgboost >= 1.7.0
mlflow >= 2.8.0
kafka-python >= 2.0.0
psycopg2-binary >= 2.9.0
boto3 >= 1.28.0
pyspark >= 3.5.0  # Optional
```

---

## 🚀 Quick Start

Get the system running in **5 minutes**!

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Capstone-Project
```

### 2. Set Up Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure AWS & Database

Create `.env` file in the project root:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET=your-bucket-name

# RDS PostgreSQL (optional for local testing)
RDS_HOST=your-rds-endpoint
RDS_PORT=5432
RDS_DB_NAME=analytics
RDS_USERNAME=your-username
RDS_PASSWORD=your-password

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
```

### 4. Run the Complete Pipeline

```bash
# Start all services (Kafka, MLflow, Airflow)
./run_local.sh

# This will:
# ✅ Build Docker images
# ✅ Start MLflow tracking server
# ✅ Run data pipeline
# ✅ Train model
# ✅ Start Airflow
# ✅ Start Kafka streaming
# ✅ Setup analytics tables
```

### 5. Access the Services

| Service | URL | Description |
|---------|-----|-------------|
| **MLflow UI** | http://localhost:5000 | Model tracking & registry |
| **Airflow UI** | http://localhost:8080 | Pipeline orchestration |
| **Kafka UI** | http://localhost:9021 | Kafka monitoring |

**Default Airflow credentials**: `admin` / `admin`

---

## 📁 Project Structure

```
Capstone-Project/
│
├── 📂 .github/workflows/          # CI/CD pipelines
│   └── ci-simplified.yml          # Data + Model validation
│
├── 📂 airflow/                    # Orchestration
│   └── dags/                      # Airflow DAGs
│       ├── data_pipeline_dag.py
│       ├── model_training_dag.py
│       └── inference_pipeline_dag.py
│
├── 📂 config/                     # Configuration
│   └── environments/              # Environment configs
│       ├── staging.yaml
│       └── production.yaml
│
├── 📂 docker/                     # Docker images
│   ├── Dockerfile.base            # Base Python image
│   ├── Dockerfile.airflow         # Airflow image
│   ├── Dockerfile.mlflow          # MLflow image
│   ├── Dockerfile.kafka-producer  # Producer image
│   ├── Dockerfile.kafka-consumer  # Consumer image
│   └── Dockerfile.kafka-analytics # Analytics image
│
├── 📂 docs/                       # Documentation
│   ├── README.md
│   ├── STARTUP_GUIDE.md           # Detailed setup guide
│   ├── KAFKA_QUICKSTART.md        # Kafka guide
│   ├── CI_CD_SIMPLIFIED_SUMMARY.md # CI/CD documentation
│   └── project_structure.md
│
├── 📂 kafka/                      # Streaming services
│   ├── producer_service.py        # Event generation
│   ├── consumer_service.py        # Real-time inference
│   └── analytics_service.py       # Store to RDS
│
├── 📂 pipelines/                  # ML pipelines
│   ├── data_pipeline.py           # Data processing
│   ├── training_pipeline.py       # Model training
│   └── inference_pipeline.py      # Batch inference
│
├── 📂 scripts/                    # Utilities
│   ├── analytics_visualization.ipynb  # Jupyter dashboard
│   └── monitoring/
│       └── check_model_accuracy.py    # Model monitoring
│
├── 📂 sql/                        # Database schemas
│   └── create_analytics_tables.sql    # RDS tables
│
├── 📂 src/                        # Source code
│   ├── data_ingestion.py          # Load data
│   ├── feature_*.py               # Feature engineering
│   ├── model_*.py                 # Model code
│   └── outlier_detection.py       # Outlier handling
│
├── 📂 tests/                      # Testing
│   ├── validate_data.py           # Data validation (CI/CD)
│   ├── validate_model.py          # Model validation (CI/CD)
│   ├── conftest.py                # Test fixtures
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   ├── data_validation/           # Data quality tests
│   └── model_validation/          # Model performance tests
│
├── 📂 utils/                      # Utilities
│   ├── artifact_manager.py        # Artifact handling
│   ├── config.py                  # Configuration
│   ├── kafka_utils.py             # Kafka utilities
│   ├── mlflow_utils.py            # MLflow utilities
│   ├── s3_io.py                   # S3 operations
│   └── spark_utils.py             # Spark utilities
│
├── 📄 .gitignore                  # Git exclusions
├── 📄 config.yaml                 # Main configuration
├── 📄 docker-compose.yml          # Main services
├── 📄 docker-compose.airflow.yml  # Airflow services
├── 📄 docker-compose.kafka.yml    # Kafka services
├── 📄 Makefile                    # Build automation
├── 📄 README.md                   # This file
├── 📄 requirements.txt            # Python dependencies
├── 📄 run_local.sh                # Local deployment script
└── 📄 setup.py                    # Package setup
```

---

## 🔧 Detailed Setup

### Step 1: Install Python Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-mlflow.txt  # For MLflow

# Verify installation
python -c "import pandas, sklearn, xgboost, mlflow; print('✅ All packages installed!')"
```

### Step 2: Set Up AWS (S3 & RDS)

#### Create S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://churn-pipeline-artifacts --region ap-south-1

# Create folder structure
aws s3api put-object --bucket churn-pipeline-artifacts --key data/raw/
aws s3api put-object --bucket churn-pipeline-artifacts --key data/processed/
aws s3api put-object --bucket churn-pipeline-artifacts --key models/
```

#### Create RDS PostgreSQL Instance

1. Go to AWS RDS Console
2. Create PostgreSQL database (Free Tier eligible)
3. Note down endpoint, username, and password
4. Update `.env` file with RDS credentials

#### Create Analytics Database

```bash
# Connect to RDS
psql "host=your-rds-endpoint port=5432 dbname=postgres user=your-username"

# Create database
CREATE DATABASE analytics;

# Create tables
\c analytics
\i sql/create_analytics_tables.sql
```

### Step 3: Configure Environment Variables

Create `.env` file (copy from `.env.example` if provided):

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET=churn-pipeline-artifacts

# RDS Configuration
RDS_HOST=churn-db.xxxx.ap-south-1.rds.amazonaws.com
RDS_PORT=5432
RDS_DB_NAME=analytics
RDS_USERNAME=admin
RDS_PASSWORD=your-secure-password

# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=churn-prediction

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### Step 4: Build Docker Images

```bash
# Build all images
make docker-build

# Or build individually
docker build -f docker/Dockerfile.base -t churn-pipeline/base .
docker build -f docker/Dockerfile.airflow -t churn-pipeline/airflow .
docker build -f docker/Dockerfile.mlflow -t churn-pipeline/mlflow .
```

---

## 🏃 Running the Pipeline

### Option 1: Full Automated Deployment

```bash
# Run everything with one command
./run_local.sh

# With force rebuild of Docker images
./run_local.sh --force-rebuild
```

This script will:
1. ✅ Build/check Docker images
2. ✅ Start MLflow tracking server
3. ✅ Run data processing pipeline
4. ✅ Train the ML model
5. ✅ Start Airflow services
6. ✅ Start Kafka streaming
7. ✅ Setup RDS analytics tables

### Option 2: Step-by-Step Execution

#### Step 1: Start MLflow

```bash
# Start MLflow tracking server
make mlflow-up

# Access at http://localhost:5000
```

#### Step 2: Run Data Pipeline

```bash
# Using pandas (faster)
make data-pipeline

# Using Spark (for large datasets)
make data-pipeline-spark
```

This will:
- Load raw data from `data/raw/ChurnModelling.csv`
- Clean and process data
- Engineer features
- Split into train/validation/test sets
- Save processed data to S3

#### Step 3: Train Model

```bash
# Train model
make train-pipeline

# Train with Docker (isolated environment)
make train-pipeline-docker
```

This will:
- Load processed data from S3
- Train multiple models (XGBoost, Random Forest)
- Log experiments to MLflow
- Evaluate models on test set
- Save best model to S3

#### Step 4: Start Airflow

```bash
# Start Airflow services
make airflow-up

# Access at http://localhost:8080
# Username: admin, Password: admin
```

#### Step 5: Start Kafka Streaming

```bash
# Start Kafka services
make kafka-up

# Monitor logs
make kafka-logs-producer   # Producer logs
make kafka-logs-consumer   # Consumer logs
make kafka-logs-analytics  # Analytics logs
```

---

## ✅ CI/CD Validation

Our CI/CD pipeline ensures **quality** before deployment with 2 critical checks:

### 1. Data Validation & Drift Detection

**Script**: `tests/validate_data.py`

**Checks**:
- ✅ All required columns present
- ✅ Data types correct
- ✅ Value ranges valid (Age 18-100, CreditScore 300-850, etc.)
- ✅ No critical missing values
- ✅ No duplicate customer IDs
- ✅ Data distribution drift (statistical tests)
- ✅ Class balance acceptable (5%-40% churn rate)

**Run locally**:
```bash
python tests/validate_data.py data/raw/ChurnModelling.csv
```

### 2. Model Performance Validation

**Script**: `tests/validate_model.py`

**Critical Rule**: **F1 Score MUST BE >= 75%**

**Checks**:
- 🎯 F1 Score >= 75% (HARD REQUIREMENT)
- Accuracy >= 75%
- Precision >= 70%
- Recall >= 70%
- ROC-AUC >= 75%

**Run locally**:
```bash
python tests/validate_model.py \
    artifacts/models/best_model.pkl \
    artifacts/data/test_data.pkl
```

**What happens if model fails?**
```
❌ F1 Score: 72.34% < 75.00%
🔄 REVERTING TO PREVIOUS MODEL
   Deployment blocked to maintain system quality
```

### GitHub Actions Workflow

**File**: `.github/workflows/ci-simplified.yml`

**Triggers**:
- Every push to `main`, `develop`, or `feature/**`
- Every pull request

**Pipeline**:
```
Push Code → Data Validation → Model Validation → Deploy (if passed)
```

---

## 📊 Monitoring & Analytics

### Real-Time Dashboard

Open the Jupyter notebook:

```bash
cd scripts/
jupyter notebook analytics_visualization.ipynb
```

**Features**:
- 📈 Real-time prediction metrics
- 🌍 Geography-wise churn analysis
- 🚨 High-risk customer alerts
- 📊 Model performance tracking
- 🔄 Churn trends over time

### Model Performance Monitoring

Automated script runs every 6 hours (in production):

```bash
python scripts/monitoring/check_model_accuracy.py
```

**Checks**:
- Model accuracy vs baseline
- Prediction confidence scores
- High/low confidence prediction distribution
- Alerts if accuracy drops

### Kafka Monitoring

```bash
# Check producer status
docker logs kafka-producer --follow

# Check consumer status
docker logs kafka-consumer --follow

# Check analytics service
docker logs kafka-analytics --follow

# Check Kafka topics
make kafka-topics-list

# Check consumer lag
make kafka-consumer-lag
```

---

## ⚙️ Configuration

### Main Configuration (`config.yaml`)

```yaml
# S3 Storage
s3:
  bucket: churn-pipeline-artifacts
  region: ap-south-1
  paths:
    raw_data: data/raw/
    processed_data: data/processed/
    models: models/

# Model Training
model:
  type: xgboost
  test_size: 0.2
  validation_size: 0.2
  random_state: 42
  
# Kafka Streaming
kafka:
  topics:
    customer_events: customer-events
    predictions: churn-predictions
  consumer_group: churn-consumer
```

### Environment-Specific Configs

Located in `config/environments/`:

- `staging.yaml` - Staging environment
- `production.yaml` - Production environment

### Makefile Commands

```bash
# Data Pipeline
make data-pipeline         # Run data processing
make data-pipeline-spark   # Run with Spark

# Model Training
make train-pipeline        # Train model
make train-pipeline-docker # Train in Docker

# Inference
make inference-pipeline    # Batch inference

# MLflow
make mlflow-up            # Start MLflow server
make mlflow-down          # Stop MLflow server
make mlflow-ui            # Open MLflow UI

# Airflow
make airflow-up           # Start Airflow
make airflow-down         # Stop Airflow
make airflow-restart      # Restart Airflow

# Kafka
make kafka-up             # Start Kafka services
make kafka-down           # Stop Kafka services
make kafka-logs-producer  # View producer logs
make kafka-logs-consumer  # View consumer logs

# CI/CD
make validate-data        # Run data validation
make validate-model       # Run model validation

# Cleanup
make clean                # Clean artifacts
make clean-all            # Clean everything
make docker-clean         # Clean Docker resources
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Docker Build Fails

```bash
# Error: COPY failed
Solution:
- Check .dockerignore file
- Ensure files exist in build context
- Try: docker build --no-cache
```

#### 2. Kafka Connection Error

```bash
# Error: Cannot connect to Kafka
Solution:
- Check Kafka is running: docker ps | grep kafka
- Verify port 9092 is not blocked
- Check KAFKA_BOOTSTRAP_SERVERS in .env
```

#### 3. MLflow Tracking Error

```bash
# Error: Cannot connect to MLflow
Solution:
- Start MLflow: make mlflow-up
- Check http://localhost:5000 is accessible
- Verify MLFLOW_TRACKING_URI in .env
```

#### 4. RDS Connection Timeout

```bash
# Error: Connection timeout
Solution:
- Check RDS security group allows your IP
- Verify RDS_HOST and credentials in .env
- Test: psql "host=$RDS_HOST port=5432 dbname=analytics"
```

#### 5. Model Validation Fails

```bash
# Error: F1 Score < 75%
Solution:
- Retrain model with more data
- Try different hyperparameters
- Check for data quality issues
- Consider adjusting threshold in validate_model.py
```

### Logs & Debugging

```bash
# View all Docker logs
docker-compose logs -f

# View specific service logs
docker logs <container-name> --follow

# Check Airflow logs
tail -f airflow/logs/scheduler/latest/*.log

# Check Kafka logs
make kafka-logs-producer
make kafka-logs-consumer

# Python debugging
export PYTHONPATH=$PWD
python -m pdb pipelines/training_pipeline.py
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

### 1. Fork the Repository

```bash
git clone <your-fork-url>
cd Capstone-Project
git remote add upstream <original-repo-url>
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation

### 4. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run data validation
python tests/validate_data.py data/raw/ChurnModelling.csv

# Run model validation
python tests/validate_model.py artifacts/models/best_model.pkl artifacts/data/test_data.pkl
```

### 5. Submit Pull Request

```bash
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

---

## 📚 Additional Resources

### 🎓 Comprehensive Capstone Documentation

**Complete end-to-end guides (recommended for students):**

- 📖 **[Kafka Integration Guide](docs-capstone/01_KAFKA_INTEGRATION.md)** - Full Kafka setup, Docker, producer/consumer, troubleshooting
- 🔄 **[CI/CD Configuration Guide](docs-capstone/02_CICD_CONFIGURATION.md)** - Complete GitHub Actions, validation pipelines, testing
- 📊 **[Analytics & QuickSight Guide](docs-capstone/03_ANALYTICS_QUICKSIGHT.md)** - RDS, SQL views, dashboards, visualizations
- 📂 **[All Capstone Docs](docs-capstone/)** - Browse complete documentation folder

### Quick Reference Documentation

- 📖 [Startup Guide](docs/STARTUP_GUIDE.md) - Detailed setup instructions
- 📖 [Kafka Quick Start](docs/KAFKA_QUICKSTART.md) - Kafka streaming guide
- 📖 [CI/CD Guide](docs/CI_CD_SIMPLIFIED_SUMMARY.md) - CI/CD documentation
- 📖 [AWS QuickSight Dashboards](docs/AWS_QUICKSIGHT_GUIDE.md) - Build interactive BI dashboards
- 📊 [QuickSight Calculated Fields](docs/QUICKSIGHT_CALCULATED_FIELDS.md) - SQL formulas & functions reference
- 📖 [Project Structure](docs/project_structure.md) - Architecture details

### External Links

- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [Apache Airflow](https://airflow.apache.org/)
- [Apache Kafka](https://kafka.apache.org/)
- [XGBoost](https://xgboost.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👥 Authors

**Your Name/Team**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- Banking dataset from [Kaggle](https://www.kaggle.com/)
- MLOps best practices from [Made With ML](https://madewithml.com/)
- Architecture inspired by production systems at leading tech companies

---

## 📊 Project Stats

- **Lines of Code**: ~15,000+
- **Docker Images**: 6 specialized images
- **CI/CD Checks**: 2 critical validation scripts
- **Test Coverage**: 80%+ (unit + integration)
- **Documentation**: Comprehensive guides

---

## 🎯 Learning Outcomes

By working with this project, you'll learn:

✅ **ML Engineering**: Data pipelines, feature engineering, model training  
✅ **MLOps**: MLflow tracking, model versioning, automated training  
✅ **Streaming**: Real-time inference with Kafka  
✅ **Orchestration**: Workflow automation with Airflow  
✅ **DevOps**: Docker containerization, CI/CD pipelines  
✅ **Cloud**: AWS S3, RDS integration  
✅ **Testing**: Data validation, model validation, unit tests  
✅ **Monitoring**: Performance tracking, analytics dashboards  

---

## 🚀 Next Steps

1. ✅ **Set up** the environment following [Quick Start](#quick-start)
2. ✅ **Run** the complete pipeline with `./run_local.sh`
3. ✅ **Explore** MLflow UI to see experiments
4. ✅ **Monitor** Kafka streaming in real-time
5. ✅ **Analyze** results in Jupyter notebook
6. ✅ **Deploy** to production (AWS/Cloud)
7. ✅ **Customize** for your own ML problem

---

## 📧 Support

Need help? Have questions?

- 📖 Check the [documentation](docs/)
- 🐛 [Open an issue](../../issues)
- 💬 [Start a discussion](../../discussions)
- 📧 Email: support@yourproject.com

---

<div align="center">

**⭐ Star this repository if you found it helpful!**

Made with ❤️ for students learning production ML systems

</div>
