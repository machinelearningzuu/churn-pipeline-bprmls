# Project Structure

This document provides a comprehensive overview of the project's folder structure and organization for the **S3-native ML pipeline**.

## 📁 Root Directory Structure

```
Week 10/
├── 📄 config.yaml                 # Main configuration file (AWS S3 & MLflow settings)
├── 📄 Makefile                    # Build automation and task management
├── 📄 requirements.txt            # Python dependencies
├── 📄 setup.py                    # Package setup configuration
├── 📁 data/                       # Input data storage (raw data only)
├── 📁 docs/                       # Project documentation
├── 📁 pipelines/                  # ML pipeline implementations
├── 📁 runtime/                    # Runtime files and logs
├── 📁 scripts/                    # Utility scripts
├── 📁 src/                        # Core source code modules
├── 📁 tests/                      # Test files
└── 📁 utils/                      # Utility functions and helpers
```

## 🔧 Core Directories

### 📁 `src/` - Source Code Modules
Contains the core machine learning components and data processing modules:

```
src/
├── __init__.py                    # Package initialization
├── data_ingestion.py              # Data loading and ingestion (S3-enabled)
├── data_splitter.py               # Train/test data splitting
├── feature_binning.py             # Feature discretization
├── feature_encoding.py            # Categorical feature encoding (S3 storage)
├── feature_scaling.py             # Feature normalization/scaling
├── handle_missing_values.py       # Missing data imputation
├── model_building.py              # Model architecture definition
├── model_evaluation.py            # Model performance evaluation
├── model_inference.py             # Prediction and inference (S3 + MLflow)
├── model_training.py              # Model training logic (S3 + MLflow)
└── outlier_detection.py           # Anomaly detection
```

### 📁 `pipelines/` - ML Pipeline Orchestration
High-level pipeline implementations for different stages:

```
pipelines/
├── data_pipeline.py               # Data preprocessing pipeline (→ S3)
├── inference_pipeline.py          # Model inference pipeline (S3 → S3)
└── training_pipeline.py           # Model training pipeline (S3 → MLflow + S3)
```

### 📁 `utils/` - Utility Functions
Helper modules for configuration, S3 I/O, and infrastructure:

```
utils/
├── config.py                      # Configuration management (config.yaml)
├── mlflow_utils.py                # MLflow integration utilities (S3 backend)
├── s3_artifact_manager.py         # S3 artifact organization and versioning
├── s3_io.py                       # S3 I/O operations (boto3 wrapper)
├── spark_session.py               # Spark session management (S3A configuration)
└── spark_utils.py                 # Spark-specific utilities
```

### 📁 `scripts/` - Utility Scripts
One-time setup and utility scripts:

```
scripts/
└── upload_data_to_s3.py           # One-time data upload to S3
```

## 📊 Local Data Structure (Minimal)

### 📁 `data/` - Input Data Only
Only contains raw input data - all processed data stored in S3:

```
data/
└── raw/
    └── ChurnModelling.csv          # Original raw dataset (10,000 samples)
```

**Note**: No `data/processed/` or local artifacts - everything processed goes to S3!

## ☁️ **AWS S3 Bucket Structure** - Complete Cloud-Native Storage

All ML artifacts are stored in AWS S3 with organized folder structure and timestamp-based versioning:

```
s3://zuucrew-mlflow-artifacts-prod/
├── data/                           # Raw and processed data (one-time upload)
│   ├── raw/
│   │   └── ChurnModelling.csv      # Original dataset (729KB, uploaded once)
│   ├── processed/
│   │   └── imputed.csv             # Legacy processed data (if exists)
│   └── upload_metadata_20251005002314.json # Upload tracking metadata
│
├── artifacts/                      # ML Pipeline Artifacts (timestamp-organized)
│   ├── data_artifacts/             # Data processing artifacts
│   │   ├── 20251005002314/         # Data pipeline run (Oct 5, 2025 00:23:14)
│   │   │   ├── X_train.csv         # Training features (454KB)
│   │   │   ├── X_test.csv          # Test features (113KB)
│   │   │   ├── Y_train.csv         # Training labels (16KB)
│   │   │   ├── Y_test.csv          # Test labels (4KB)
│   │   │   ├── Geography_encoder.json # Geography feature encoder (47 bytes)
│   │   │   ├── Gender_encoder.json    # Gender feature encoder (46 bytes)
│   │   │   └── preprocessing_metadata.json # Pipeline metadata (791 bytes)
│   │   ├── 20251005000431/         # Previous data pipeline run
│   │   │   ├── X_train.csv
│   │   │   ├── X_test.csv
│   │   │   ├── Y_train.csv
│   │   │   ├── Y_test.csv
│   │   │   ├── Geography_encoder.json
│   │   │   ├── Gender_encoder.json
│   │   │   └── preprocessing_metadata.json
│   │   └── 20251004235755/         # Earlier data pipeline run
│   │       └── ... (similar structure)
│   │
│   ├── model_artifacts/            # Model training artifacts
│   │   ├── 20251005002314/         # Training pipeline run
│   │   │   └── spark_random_forest_model_metadata.json # Model metadata (284 bytes)
│   │   ├── 20251004235755/         # Previous training run
│   │   │   └── spark_random_forest_model_metadata.json
│   │   └── 20251004233546/         # Earlier training run
│   │       └── spark_random_forest_model_metadata.json
│   │
│   └── inference_artifacts/        # Inference results
│       ├── 20251005001516/         # Inference pipeline run (Oct 5, 2025 00:15:16)
│       │   ├── inference_results.json  # Prediction results (1000 samples)
│       │   └── inference_summary.json  # Run summary and statistics
│       ├── 20251005000620/         # Previous inference run
│       │   ├── inference_results.json
│       │   └── inference_summary.json
│       └── 20251004235020/         # Earlier inference run
│           ├── inference_results.json
│           └── inference_summary.json
│
└── mlflow-artifacts/               # MLflow Automatic Artifacts (S3 Backend)
    ├── experiments/                # Experiment tracking data
    │   └── {experiment_id}/
    │       └── {run_id}/
    │           ├── artifacts/      # Model artifacts
    │           ├── metrics/        # Training metrics (accuracy, F1, etc.)
    │           ├── params/         # Model parameters
    │           └── tags/           # Run tags and metadata
    └── models/                     # MLflow Model Registry (S3 Storage)
        ├── spark_random_forest_20251005000431/ # Registered model
        │   └── version_1/
        │       ├── MLmodel         # Model metadata
        │       ├── conda.yaml      # Environment specification
        │       ├── requirements.txt # Dependencies
        │       └── sparkml/        # Spark model files
        ├── spark_random_forest_20251005002101/ # Another model version
        │   └── version_1/
        │       └── ... (similar structure)
        └── test_s3_model/          # Test model
            └── version_1/
                └── ... (similar structure)
```

## 🎯 S3 Organization Features

### **🕐 Timestamp-based Versioning**
- Each pipeline run creates a new timestamp folder (`YYYYMMDDHHMMSS`)
- Single timestamp used throughout entire pipeline run
- Easy to trace all artifacts from a specific run

### **📁 Organized by Artifact Type**
- **`data_artifacts/`**: Preprocessed data, encoders, metadata
- **`model_artifacts/`**: Model metadata and training artifacts
- **`inference_artifacts/`**: Prediction results and summaries
- **`mlflow-artifacts/`**: MLflow experiment tracking and model registry

### **🔐 Security & Compliance**
- **KMS Encryption**: All uploads use customer-managed encryption keys (SSE-KMS)
- **IAM Access Control**: Fine-grained permissions for S3 operations
- **Audit Trail**: Complete logging of all S3 operations with timestamps

### **⚡ Performance & Efficiency**
- **S3A Integration**: Direct Spark-to-S3 operations for large datasets
- **boto3 Integration**: Python-native S3 operations for small files
- **Parallel Processing**: Concurrent uploads/downloads where possible
- **Smart Caching**: Local temporary files only during processing

### **🧹 Lifecycle Management**
- **Automatic Organization**: All artifacts automatically organized by type and timestamp
- **Manual Cleanup**: `make s3-clean` for project-specific artifact cleanup
- **Version Control**: Easy to identify and access specific pipeline runs
- **Storage Optimization**: Efficient organization reduces S3 costs

## 🏃‍♂️ Runtime and Operations

### 📁 `runtime/` - Runtime Files
Operational files generated during execution:

```
runtime/
├── kafka-logs/                    # Kafka streaming logs (if used)
└── pids/                          # Process ID files
```

### 📁 `docs/` - Documentation
Project documentation and guides:

```
docs/
├── project_structure.md           # This file - project structure documentation
├── configuration_guide.md         # Configuration setup guide
├── installation_guide.md          # Installation and setup instructions
├── README.md                      # Project overview and quick start
└── s3_implementation_summary.md   # S3 migration implementation details
```

## 🔧 Configuration Files

- **`config.yaml`**: Main configuration file containing:
  - AWS S3 settings (region, bucket, KMS key, force_s3_io)
  - MLflow settings (tracking URI, artifact root, experiment name)
  - Data paths and pipeline parameters

- **`Makefile`**: Build automation with targets for:
  - Pipeline execution (`data-pipeline`, `train-pipeline`, `inference-pipeline`)
  - S3 operations (`s3-list`, `s3-clean`, `s3-smoke`, `s3-upload-data`)
  - Development (`install`, `clean`, `clean-local-artifacts`)

- **`requirements.txt`**: Python package dependencies for the project

## 🚀 Usage

The project follows a cloud-native ML workflow with complete S3 integration:

### **S3-Native Pipeline Workflow:**

1. **Setup** (One-time):
   ```bash
   make install                     # Install dependencies
   make s3-upload-data             # Upload raw data to S3
   make s3-smoke                   # Test S3 connectivity
   ```

2. **Data Pipeline** (`pipelines/data_pipeline.py`): 
   - **Input**: Loads raw data from `s3://bucket/data/raw/ChurnModelling.csv`
   - **Processing**: Feature engineering, encoding, splitting (single timestamp)
   - **Output**: `s3://bucket/artifacts/data_artifacts/{timestamp}/`
   ```bash
   make data-pipeline              # → s3://bucket/artifacts/data_artifacts/20251005002314/
   ```

3. **Training Pipeline** (`pipelines/training_pipeline.py`):
   - **Input**: Loads latest data artifacts from S3
   - **Training**: PySpark MLlib model training with MLflow tracking
   - **Output**: MLflow registry + `s3://bucket/artifacts/model_artifacts/{timestamp}/`
   ```bash
   make train-pipeline             # → MLflow + s3://bucket/artifacts/model_artifacts/20251005002314/
   ```

4. **Inference Pipeline** (`pipelines/inference_pipeline.py`):
   - **Model**: Loads from MLflow registry (`spark_random_forest_{timestamp}`)
   - **Encoders**: Loads from `s3://bucket/artifacts/data_artifacts/{timestamp}/`
   - **Data**: Loads latest test data from S3, samples 1000 records
   - **Output**: `s3://bucket/artifacts/inference_artifacts/{timestamp}/`
   ```bash
   make inference-pipeline         # → s3://bucket/artifacts/inference_artifacts/20251005002314/
   ```

### **🎯 S3 Management Commands:**
```bash
# S3 operations
make s3-list PREFIX=artifacts/      # List all S3 artifacts
make s3-list PREFIX=data/          # List S3 data files
make s3-clean                      # Clean project S3 artifacts (safe)
make s3-smoke                      # Test S3 connectivity
make status                        # Show project and S3 status

# Local cleanup
make clean                         # Clean local cache only
make clean-local-artifacts         # Remove legacy local artifact folders
```

### **🔍 Monitoring and Debugging:**
```bash
# Check S3 contents
make s3-list PREFIX=artifacts/data_artifacts/    # View data artifacts
make s3-list PREFIX=artifacts/model_artifacts/   # View model artifacts
make s3-list PREFIX=mlflow-artifacts/           # View MLflow artifacts

# Pipeline status
make status                        # Show configuration and S3 status
```

## 🌟 S3 Migration Benefits

### **☁️ Cloud-Native Architecture**
- **Zero local dependencies**: No local artifact storage required
- **Scalable storage**: Unlimited S3 storage capacity
- **Global accessibility**: Access artifacts from any environment with AWS credentials
- **Cost-effective**: Pay only for storage used, with intelligent tiering

### **🔐 Security & Compliance**
- **KMS encryption**: All artifacts encrypted with customer-managed keys
- **IAM integration**: Fine-grained access control
- **Audit logging**: Complete trail of all S3 operations
- **Secure by default**: No sensitive data stored locally

### **🕐 Version Management**
- **Timestamp versioning**: Each pipeline run creates clean timestamp folder
- **Artifact traceability**: Easy to trace all artifacts from specific runs
- **Rollback capability**: Access any previous pipeline version
- **Clean organization**: No artifact naming conflicts

### **⚡ Performance & Reliability**
- **Spark S3A integration**: Direct distributed processing with S3
- **Parallel I/O**: Concurrent uploads/downloads for large datasets
- **Fault tolerance**: S3's 99.999999999% durability
- **High availability**: Multi-AZ replication built-in

### **🛠️ Development Experience**
- **Consistent environments**: Same artifacts across dev/staging/prod
- **Easy collaboration**: Shared artifact access across team
- **Simplified deployment**: No local file management required
- **Automated cleanup**: Built-in S3 lifecycle management

## 📝 Important Notes

### **Migration Status**
- **✅ Complete S3 migration**: All local artifact dependencies removed
- **✅ S3-only storage**: All pipeline artifacts stored in organized S3 structure  
- **✅ MLflow S3 backend**: Configured with `MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://bucket/mlflow-artifacts`
- **✅ Model registry**: Models in MLflow registry (S3) + metadata in organized structure
- **✅ Raw data**: One-time upload to S3, then loaded from S3 for all pipeline runs

### **Configuration Requirements**
- **AWS credentials**: Required for S3 operations (IAM user or role)
- **S3 bucket**: Must exist with proper permissions
- **KMS key**: Customer-managed key for encryption (optional but recommended)
- **MLflow**: Can run locally or on server, artifacts automatically go to S3

### **Local vs S3 Storage**
- **Local**: Only `data/raw/` for input data and temporary processing files
- **S3**: All processed data, models, encoders, inference results, and MLflow artifacts
- **No local artifacts**: `artifacts/`, `data/processed/`, `mlruns/` folders no longer created
- **Cleanup commands**: `make clean-local-artifacts` removes any legacy local folders

Each pipeline can be executed independently and all artifacts are automatically organized in S3 with timestamp-based versioning! 🚀