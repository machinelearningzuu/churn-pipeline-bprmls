# Production-Ready ML Pipeline with S3 Integration

A complete machine learning pipeline system with AWS S3-based artifact storage, timestamp versioning, and cloud-native architecture.

## 🚀 Quick Start

### Prerequisites
- **Python 3.9-3.13** 
- **AWS credentials** (IAM role, AWS CLI, or environment variables)
- **S3 bucket** with appropriate permissions

### Installation
```bash
# 1. Clone and install
make install

# 2. Configure AWS (copy and edit)
cp env.example .env
# Edit .env with your S3_BUCKET, AWS_REGION, etc.

# 3. Test S3 connectivity
make s3-smoke

# 4. Run the ML pipeline
make data-pipeline
make train-pipeline
make inference-pipeline
```

## 🌟 Key Features

### ☁️ **Cloud-Native Architecture**
- **S3-First Design**: All artifacts stored in AWS S3
- **Zero Local Dependencies**: No local artifact storage
- **KMS Encryption**: Customer-managed key encryption for all data
- **IAM Integration**: Production-ready security model

### 📅 **Intelligent Versioning**
- **Timestamp Folders**: `data/artifacts/csv/20251004205151/`
- **Clean Filenames**: `X_train.csv` (no timestamp clutter)
- **Automatic Latest**: Always uses most recent artifacts
- **Smart Cleanup**: Keeps 5 recent versions automatically

### 🔄 **Complete ML Workflow**
- **Data Pipeline**: Preprocessing with S3 timestamp storage
- **Training Pipeline**: Model training with S3 artifact loading
- **Inference Pipeline**: 1000-sample predictions with S3 results
- **MLflow Integration**: Experiment tracking with S3 backend

## 📁 Project Structure

```
Week 10/
├── 📄 env.example              # AWS configuration template
├── 📄 Makefile                 # Build automation with S3 utilities
├── 📄 requirements.txt         # Dependencies (including boto3, moto)
├── 📁 data/
│   └── raw/                    # Input data (only local directory)
├── 📁 docs/                    # Comprehensive documentation
│   ├── project_structure.md    # Project overview
│   ├── s3_migration.md         # S3 implementation guide
│   ├── timestamp_artifacts.md  # Versioning system guide
│   └── installation_guide.md   # Setup and troubleshooting
├── 📁 pipelines/               # ML pipeline implementations
│   ├── data_pipeline.py        # Data preprocessing → S3
│   ├── training_pipeline.py    # Model training ← S3 → S3
│   └── inference_pipeline.py   # Batch inference ← S3 → S3
├── 📁 src/                     # Core ML modules
├── 📁 utils/                   # Utilities and infrastructure
│   ├── s3_io.py               # S3 I/O with boto3
│   ├── s3_artifact_manager.py  # S3 timestamp management
│   ├── spark_session.py        # Spark with S3A configuration
│   └── config.py               # Configuration with AWS support
└── 📁 tests/
    └── test_s3_io.py           # Comprehensive S3 testing with moto
```

## 🌐 S3 Bucket Structure

```
s3://zuucrew-mlflow-artifacts-prod/
├── data/artifacts/
│   ├── csv/20251004205151/     # Latest timestamp folder
│   │   ├── X_train.csv         # Clean filenames
│   │   ├── X_test.csv
│   │   ├── Y_train.csv
│   │   └── Y_test.csv
│   └── parquet/20251004205151/
│       ├── X_train.parquet/
│       ├── X_test.parquet/
│       ├── Y_train.parquet/
│       └── Y_test.parquet/
├── artifacts/
│   ├── models/
│   ├── encode/
│   └── inference_batches/
└── mlflow-artifacts/
```

## 🔧 Configuration

### Environment Variables (`.env`)
```env
# Required
AWS_REGION=ap-south-1
S3_BUCKET=your-ml-bucket
S3_KMS_KEY_ARN=arn:aws:kms:region:account:key/key-id

# Optional
FORCE_S3_IO=true
MLFLOW_TRACKING_URI=http://localhost:5001
```

### AWS Credentials
Choose one method:
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Option 3: IAM Role (for EC2/ECS)
# Automatically provided
```

## 📋 Available Commands

### **Core Pipeline**
```bash
make data-pipeline      # Data preprocessing → S3
make train-pipeline     # Model training ← S3 → S3  
make inference-pipeline # Batch inference ← S3 → S3
make run-all           # Execute all pipelines
```

### **S3 Operations**
```bash
make s3-smoke                    # Test S3 connectivity
make s3-list PREFIX=data/        # List S3 artifacts
make s3-delete-prefix PREFIX=test/ # Bulk delete (with confirmation)
make status                      # Show S3 config and artifacts
```

### **Development**
```bash
make install            # Install dependencies
make dev-install        # Install with dev dependencies
make clean             # Clean cache (preserves S3)
make mlflow-ui         # Launch experiment tracking
```

## 🎯 Workflow Examples

### **Standard ML Pipeline**
```bash
# 1. Setup
make install
cp env.example .env     # Configure your AWS settings
make s3-smoke          # Verify S3 connectivity

# 2. Run pipeline
make data-pipeline     # Creates: s3://bucket/data/artifacts/csv/20251004205151/
make train-pipeline    # Loads latest artifacts, trains model
make inference-pipeline # 1000-sample predictions → S3 results

# 3. Monitor
make status           # Check S3 artifacts
make mlflow-ui       # View experiments
```

### **Development Workflow**
```bash
# List recent artifacts
make s3-list PREFIX=data/artifacts/csv/

# Multiple data pipeline runs (versioning)
make data-pipeline    # Creates timestamp folder 1
make data-pipeline    # Creates timestamp folder 2 (latest)
make train-pipeline   # Automatically uses latest

# Clean up test artifacts
make s3-delete-prefix PREFIX=test/
```

## 🧪 Testing

```bash
# Run S3 I/O tests
pytest tests/test_s3_io.py -v

# Test coverage
pytest --cov=utils --cov=src --cov-report=html

# S3 smoke test
make s3-smoke
```

## 📊 Key Benefits

### **🌐 Cloud-Native**
- **Scalable**: No local disk limitations
- **Durable**: 99.999999999% S3 durability
- **Secure**: KMS encryption, IAM access control

### **🧹 Clean Organization**
- **Readable filenames**: `X_train.csv` vs `X_train_20251004205151.csv`
- **Logical grouping**: All run artifacts in one timestamp folder
- **Format separation**: CSV and Parquet in separate S3 prefixes

### **⚡ Production-Ready**
- **No local artifacts**: Zero local storage dependencies
- **Automatic versioning**: Timestamp-based artifact management
- **Intelligent sampling**: 1000-record inference processing
- **Comprehensive testing**: Full moto-based S3 test suite

## 🛡️ Security

- **Encryption at Rest**: SSE-KMS with customer-managed keys
- **Encryption in Transit**: HTTPS/TLS for all S3 operations
- **IAM Integration**: Role-based access control
- **No Hardcoded Credentials**: Environment-based configuration

## 📈 Monitoring & Observability

- **MLflow Integration**: S3-backed experiment tracking
- **Comprehensive Logging**: All S3 operations logged with bucket + key
- **Error Handling**: Clear messages with actionable information
- **Status Monitoring**: Real-time S3 configuration and artifact status

---

## 🎉 Success! 

The project is now a **production-ready, cloud-native ML pipeline** with:
- ✅ Complete S3 integration
- ✅ Timestamp-based versioning  
- ✅ 1000-sample inference processing
- ✅ Zero local artifact dependencies
- ✅ Comprehensive testing and documentation

Ready for deployment in any AWS environment! 🌟
