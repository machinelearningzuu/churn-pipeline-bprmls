# Installation & Troubleshooting Guide

This guide provides comprehensive instructions for setting up the ML pipeline project and resolving common issues.

## 🚀 Quick Start

### Prerequisites
- **Python 3.9-3.13** (Python 3.13 recommended for latest features)
- **Git** for version control
- **Java 11+** (for PySpark and Kafka)

### Installation Steps

1. **Clone and Navigate to Project**
   ```bash
   cd "/Users/machinelearningzuu/Dropbox/Zuu Crew/Courses/Building Production-Ready Machine Learning Systems/Codes/Week 10"
   ```

2. **Install Core Dependencies**
   ```bash
   make install
   ```

3. **Set Up Project Structure**
   ```bash
   make setup-dirs
   ```

4. **Verify Installation**
   ```bash
   # Activate virtual environment
   source .venv/bin/activate
   
   # Test Python path resolution
   python -c "import sys; print('\\n'.join(sys.path))"
   
   # Test core imports
   python -c "from utils.config import load_config; print('✅ Utils import successful')"
   ```

## 🔧 Dependency Management

### Core Requirements (requirements.txt)
The project uses a streamlined dependency list for maximum compatibility:

```txt
# Core ML and Data Science Libraries
pandas>=1.5.0
numpy>=1.21.0
scikit-learn>=1.1.0
scipy>=1.9.0

# PySpark and MLlib
pyspark>=3.4.0

# Model Libraries
xgboost>=2.1.0
lightgbm>=3.3.0

# Visualization Libraries
matplotlib>=3.5.0
seaborn>=0.11.0
plotly>=5.10.0

# Configuration and Utilities
pyyaml>=6.0
python-dotenv>=0.19.0

# Data Processing
openpyxl>=3.0.0
xlrd>=2.0.0

# API and Web
fastapi>=0.95.0
uvicorn>=0.20.0
pydantic>=2.0.0,<2.11.2

# Monitoring and Logging
mlflow>=1.30.0
wandb>=0.15.0

# Testing
pytest>=7.0.0
pytest-cov>=4.0.0

# Development Tools
jupyter>=1.0.0
ipykernel>=6.0.0
black>=22.0.0
flake8>=5.0.0

# Optional: OpenAI for advanced imputation
groq>=0.11.0
```

### Optional Dependencies (setup.py)
For advanced features, install optional dependencies:

```bash
# For Airflow orchestration (if needed)
pip install -e ".[airflow]"

# For Kafka streaming (if needed)  
pip install -e ".[kafka]"

# For development tools
pip install -e ".[dev]"
```

## 🐛 Troubleshooting Common Issues

### Issue 1: ModuleNotFoundError: No module named 'utils'

**Problem**: Python can't find the project modules.

**Solution**: The Makefile has been updated to automatically set `PYTHONPATH`. Use make commands:
```bash
# ✅ Correct way
make data-pipeline

# ❌ Don't run directly
python pipelines/data_pipeline.py
```

**Manual Solution** (if needed):
```bash
# Set PYTHONPATH manually
export PYTHONPATH=.
python pipelines/data_pipeline.py
```

### Issue 2: Apache Airflow Compatibility Issues

**Problem**: Airflow 2.10.0+ doesn't support Python 3.13.

**Solution**: We've removed Airflow from core requirements. Install separately if needed:
```bash
# For Python 3.13, use compatible version
pip install "apache-airflow>=2.7.0,<2.8.0"
pip install "apache-airflow-providers-apache-spark>=3.0.0"
```

### Issue 3: XGBoost Version Conflicts

**Problem**: XGBoost 1.6.0 has compatibility issues with Python 3.13.

**Solution**: Updated to XGBoost 2.1.0+ which supports Python 3.13:
```bash
pip install "xgboost>=2.1.0"
```

### Issue 4: Virtual Environment Issues

**Problem**: Virtual environment not activating or packages not found.

**Solution**:
```bash
# Remove existing virtual environment
rm -rf .venv

# Recreate and install
make install

# Verify activation
source .venv/bin/activate
which python  # Should point to .venv/bin/python
```

### Issue 5: PySpark Java Issues

**Problem**: PySpark can't find Java or wrong Java version.

**Solution**:
```bash
# Check Java version
java -version  # Should be Java 11+

# Set JAVA_HOME if needed (macOS example)
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-11.jdk/Contents/Home

# Add to your shell profile
echo 'export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-11.jdk/Contents/Home' >> ~/.zshrc
```

## 🔍 Verification Commands

### Test Core Functionality
```bash
# Test configuration loading
python -c "from utils.config import load_config; print('Config loaded successfully')"

# Test Spark session
python -c "from utils.spark_session import create_spark_session; spark = create_spark_session('test'); print('Spark session created'); spark.stop()"

# Test data pipeline imports
python -c "from src.data_ingestion import DataIngestion; print('Data ingestion module loaded')"
```

### Test Pipeline Execution
```bash
# Test data pipeline (should work now)
make data-pipeline

# Test training pipeline
make train-pipeline

# Test inference pipeline
make batch-inference
```

## 📦 Package Structure

The project is now properly structured as a Python package:

```
Week 10/
├── setup.py                  # Package configuration
├── requirements.txt          # Core dependencies
├── Makefile                  # Build automation (with PYTHONPATH fixes)
├── src/                      # Source modules (importable)
├── utils/                    # Utility modules (importable)
├── pipelines/                # Pipeline scripts
└── docs/                     # Documentation
```

## 🚀 Development Workflow

### Recommended Development Setup
```bash
# 1. Install in development mode
pip install -e .

# 2. Install development dependencies
pip install -e ".[dev]"

# 3. Set up pre-commit hooks (optional)
pre-commit install

# 4. Run tests
pytest

# 5. Format code
black .
flake8 .
```

### IDE Configuration
For VS Code/Cursor, ensure the Python interpreter points to `.venv/bin/python`:
1. Open Command Palette (`Cmd+Shift+P`)
2. Select "Python: Select Interpreter"
3. Choose `.venv/bin/python`

## 🔧 Environment Variables

Create a `.env` file for environment-specific settings:
```bash
# .env
SPARK_HOME=/path/to/spark
JAVA_HOME=/path/to/java
MLFLOW_TRACKING_URI=http://localhost:5000
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

## 📊 Performance Optimization

### For Apple Silicon (M1/M2/M3/M4)
```bash
# Use optimized NumPy/SciPy
pip install --upgrade numpy scipy

# Enable MPS acceleration for PyTorch (if using)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### For CUDA GPUs
```bash
# Install CUDA-enabled versions
pip install cudf cuml cupy-cuda11x  # For RAPIDS
```

## 📞 Getting Help

If you encounter issues:

1. **Check this guide first** - Most common issues are covered
2. **Verify Python version**: `python --version` (should be 3.9+)
3. **Check virtual environment**: `which python` (should point to `.venv`)
4. **Review error messages carefully** - They often contain the solution
5. **Use make commands** - They handle PYTHONPATH automatically

## 📋 Quick Commands Reference

```bash
# Setup
make install             # Install dependencies
make setup-dirs          # Create directories
make clean              # Clean artifacts

# Pipelines
make data-pipeline      # Run data processing
make train-pipeline     # Run model training
make inference-pipeline # Run inference
make run-all           # Run all pipelines in sequence

# MLflow
make mlflow-ui         # Start MLflow UI
make stop-mlflow       # Stop MLflow servers

# Development
make status            # Show project status
make dev-install       # Install with dev dependencies
```

## ✅ Success Indicators

You'll know everything is working when:
- ✅ `make install` completes without errors
- ✅ `make data-pipeline` runs successfully
- ✅ No "ModuleNotFoundError" messages
- ✅ MLflow UI accessible at http://localhost:5001
- ✅ Artifacts generated in `artifacts/` directory
