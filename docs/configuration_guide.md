# Configuration Guide

This guide explains how to configure the ML pipeline system using `config.yaml` for AWS S3 and MLflow settings.

## 📄 Configuration File: `config.yaml`

The main configuration file contains all settings for the ML pipeline, including AWS S3 and MLflow configurations.

### 🌐 **AWS S3 Configuration**

Add the following section to your `config.yaml`:

```yaml
# AWS S3 Configuration
aws:
  region: "ap-south-1"                    # AWS region for S3 bucket
  s3_bucket: "zuucrew-mlflow-artifacts-prod"  # S3 bucket name
  s3_kms_key_arn: "arn:aws:kms:ap-south-1:899013845787:key/e89689e5-326c-486f-846d-63061b1af579"  # KMS key for encryption
  force_s3_io: true                       # Force S3-only operations
```

### 🤖 **MLflow Configuration**

```yaml
# MLflow Configuration  
mlflow:
  tracking_uri: "http://localhost:5001"   # MLflow tracking server
  artifact_root: "s3://zuucrew-mlflow-artifacts-prod/mlflow-artifacts"  # S3 backend for MLflow
  experiment_name: "Zuu Crew Churn Analysis"  # Default experiment name
```

## 🔧 **Configuration Options**

### **AWS Settings**
- **`region`**: AWS region where your S3 bucket is located
- **`s3_bucket`**: Name of the S3 bucket for storing artifacts
- **`s3_kms_key_arn`**: KMS key ARN for server-side encryption (optional)
- **`force_s3_io`**: When `true`, forces all I/O operations to use S3

### **MLflow Settings**
- **`tracking_uri`**: MLflow tracking server URL (local or remote)
- **`artifact_root`**: S3 location for MLflow artifacts
- **`experiment_name`**: Default experiment name for runs

## 🔄 **Fallback to Environment Variables**

If settings are not found in `config.yaml`, the system falls back to environment variables:

```bash
# AWS environment variables (fallback)
export AWS_REGION=ap-south-1
export S3_BUCKET=zuucrew-mlflow-artifacts-prod
export S3_KMS_KEY_ARN=arn:aws:kms:ap-south-1:899013845787:key/...
export FORCE_S3_IO=true

# MLflow environment variables (fallback)
export MLFLOW_TRACKING_URI=http://localhost:5001
export MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://zuucrew-mlflow-artifacts-prod/mlflow-artifacts
```

## 🎯 **Configuration Validation**

Test your configuration with:

```bash
# Check S3 configuration
make status

# Test S3 connectivity
make s3-smoke

# Verify MLflow settings
make mlflow-ui
```

## 📋 **Complete Example Configuration**

Here's a complete `config.yaml` with all S3 and MLflow settings:

```yaml
# AWS S3 Configuration
aws:
  region: "ap-south-1"
  s3_bucket: "zuucrew-mlflow-artifacts-prod"
  s3_kms_key_arn: "arn:aws:kms:ap-south-1:899013845787:key/e89689e5-326c-486f-846d-63061b1af579"
  force_s3_io: true

# MLflow Configuration
mlflow:
  tracking_uri: "http://localhost:5001"
  artifact_root: "s3://zuucrew-mlflow-artifacts-prod/mlflow-artifacts"
  experiment_name: "Zuu Crew Churn Analysis"

# Data paths (existing configuration)
data_paths:
  raw_data: "data/raw/ChurnModelling.csv"
  processed_data: "data/processed/ChurnModelling_Missing_Values_Handled.csv"
  # ... rest of existing config
```

## 🌟 **Benefits of config.yaml Configuration**

### ✅ **Centralized Management**
- **Single file**: All configuration in one place
- **Version controlled**: Configuration changes tracked in git
- **Environment agnostic**: Same config file across environments

### ✅ **Better Organization**  
- **Structured**: YAML hierarchy for related settings
- **Readable**: Clear, human-readable format
- **Maintainable**: Easy to update and modify

### ✅ **Flexible Deployment**
- **Environment override**: Can still use environment variables
- **Docker friendly**: Easy to mount different config files
- **CI/CD ready**: Configuration as code approach

This approach is much cleaner than using multiple `.env` files! 🚀
