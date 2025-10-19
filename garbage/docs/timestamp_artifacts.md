# Timestamp-Based Artifact Management

This document explains the new timestamp-based artifact management system implemented in the ML pipeline.

## 🎯 Overview

The artifact management system now uses timestamps to version all generated artifacts, preventing overwrites and enabling better experiment tracking.

## 📅 Timestamp Format

**Format**: `YYYYMMDDHHMMSS` (14 digits)
**Example**: `20251004193645` = October 4th, 2025 at 19:36:45

## 📁 Artifact Naming Convention

### Before (Static Names)
```
artifacts/data/
├── X_train.csv
├── X_test.csv  
├── Y_train.csv
└── Y_test.csv
```

### After (Clean Timestamp Folder Structure)
```
data/artifacts/
├── csv/                          # CSV format artifacts
│   ├── 20251004200927/           # First run - Oct 4, 2025 20:09:27
│   │   ├── X_train.csv
│   │   ├── X_test.csv
│   │   ├── Y_train.csv
│   │   └── Y_test.csv
│   ├── 20251004201006/           # Second run - Oct 4, 2025 20:10:06
│   │   ├── X_train.csv
│   │   ├── X_test.csv
│   │   ├── Y_train.csv
│   │   └── Y_test.csv
│   └── 20251004201117/           # Latest run - Oct 4, 2025 20:11:17 ← Latest
│       ├── X_train.csv
│       ├── X_test.csv
│       ├── Y_train.csv
│       └── Y_test.csv
└── parquet/                      # Parquet format artifacts
    ├── 20251004200927/
    │   ├── X_train.parquet/
    │   ├── X_test.parquet/
    │   ├── Y_train.parquet/
    │   └── Y_test.parquet/
    ├── 20251004201006/
    │   ├── X_train.parquet/
    │   ├── X_test.parquet/
    │   ├── Y_train.parquet/
    │   └── Y_test.parquet/
    └── 20251004201117/           # Latest run ← Latest
        ├── X_train.parquet/
        ├── X_test.parquet/
        ├── Y_train.parquet/
        └── Y_test.parquet/
```

## 🔧 How It Works

### 1. **Artifact Creation** (Data Pipeline)
When you run `make data-pipeline`:

```python
# Automatic timestamp generation
artifact_manager = ArtifactManager()
timestamp = artifact_manager.generate_timestamp()  # e.g., "20251004201117"

# Timestamped folder creation
csv_paths = artifact_manager.create_timestamped_paths(
    ['X_train', 'X_test', 'Y_train', 'Y_test'], 
    timestamp=timestamp, 
    format_ext='csv'
)
# Results in: data/artifacts/csv/20251004201117/X_train.csv, etc.
```

**Output Log:**
```
💾 Saving artifacts with timestamp: 20251004201117
✓ CSV files saved:
   X_train: data/artifacts/csv/20251004201117/X_train.csv
   X_test: data/artifacts/csv/20251004201117/X_test.csv
   Y_train: data/artifacts/csv/20251004201117/Y_train.csv
   Y_test: data/artifacts/csv/20251004201117/Y_test.csv
✓ Parquet files saved:
   X_train: data/artifacts/parquet/20251004201117/X_train.parquet
   X_test: data/artifacts/parquet/20251004201117/X_test.parquet
   Y_train: data/artifacts/parquet/20251004201117/Y_train.parquet
   Y_test: data/artifacts/parquet/20251004201117/Y_test.parquet
```

### 2. **Artifact Loading** (Training & Inference)
When you run `make train-pipeline` or `make inference-pipeline`:

```python
# Automatic latest artifact detection
artifact_manager = ArtifactManager()
latest_paths = artifact_manager.get_latest_artifacts(
    ['X_train', 'X_test', 'Y_train', 'Y_test'], 
    format_ext='csv'
)
# Automatically picks the most recent timestamp
```

**Output Log:**
```
Using latest timestamp directory: data/artifacts/csv/20251004201117
Latest artifact for X_train: data/artifacts/csv/20251004201117/X_train.csv
Latest artifact for X_test: data/artifacts/csv/20251004201117/X_test.csv
Latest artifact for Y_train: data/artifacts/csv/20251004201117/Y_train.csv
Latest artifact for Y_test: data/artifacts/csv/20251004201117/Y_test.csv
```

### 3. **Automatic Cleanup**
The system automatically keeps only the 5 most recent versions:

```python
# Cleanup old artifacts (keep last 5 versions)
artifact_manager.cleanup_old_artifacts(base_names, keep_count=5, format_ext='csv')
```

## 🚀 Key Benefits

### ✅ **Clean Organization**
- **Readable filenames**: `X_train.csv` instead of `X_train_20251004195220.csv`
- **Logical grouping**: All artifacts from one run in one timestamp folder
- **Format separation**: CSV and Parquet in separate directory trees
- **Easy navigation**: Simple folder structure for file explorers

### ✅ **Version Control**
- **No overwrites**: Each run creates new timestamp folder
- **Historical tracking**: Keep multiple versions for comparison
- **Rollback capability**: Can revert to previous data versions
- **Atomic operations**: Each run is completely self-contained

### ✅ **Automatic Management**
- **Latest selection**: Always picks the most recent timestamp folder
- **Fallback support**: Falls back to legacy paths if needed
- **Auto-cleanup**: Removes old timestamp directories (keeps 5 recent)
- **Efficient cleanup**: Remove entire folders instead of individual files

### ✅ **Better Debugging**
- **Traceability**: Folder name = exact run timestamp
- **Experiment tracking**: Link artifacts to specific runs
- **Reproducibility**: Can recreate exact conditions
- **Complete snapshots**: All run artifacts grouped together

## 🔄 Workflow Examples

### Example 1: Multiple Data Pipeline Runs
```bash
# First run
make data-pipeline
# Creates: data/artifacts/csv/20251004200927/

# Second run (later)  
make data-pipeline
# Creates: data/artifacts/csv/20251004201006/

# Third run (latest)
make data-pipeline  
# Creates: data/artifacts/csv/20251004201117/ ← Latest
```

### Example 2: Training with Latest Data
```bash
make train-pipeline
# Output: "Using latest timestamp directory: data/artifacts/csv/20251004201117"
# Automatically uses artifacts from latest timestamp folder
```

### Example 3: Inference with Sampling
```bash
make inference-pipeline
# Loads: data/artifacts/csv/20251004201117/X_test.csv (latest)
# Samples: 1000 random records from 1920 total
# Output: "🎲 Randomly sampled 1000 records from 1920 total records"
```

## 📊 Current Implementation Status

### ✅ **Completed Features**
- **Data Pipeline**: ✅ Creates timestamped artifacts  
- **Training Pipeline**: ✅ Uses latest timestamped artifacts
- **Inference Pipeline**: ✅ Uses latest artifacts + 1000 sample limit
- **Automatic Cleanup**: ✅ Keeps 5 most recent versions
- **Fallback Support**: ✅ Falls back to legacy paths if needed

### 🎯 **Sample Size Configuration**
The inference pipeline now supports configurable sampling:

```python
# Default: 1000 samples
test_data = self.load_test_data(sample_size=1000)

# Custom sample size
test_data = self.load_test_data(sample_size=500)  # 500 samples
test_data = self.load_test_data(sample_size=2000) # 2000 samples (if available)
```

## 📈 **Performance Impact**

### **Disk Usage**
- **Before**: 1 version = ~1MB total
- **After**: 5 versions = ~5MB total (auto-cleanup prevents bloat)

### **Loading Speed**
- **Minimal impact**: Latest artifact detection is fast (glob + regex)
- **Fallback safety**: Never breaks existing workflows

### **Development Efficiency**
- **Faster iteration**: No need to backup/restore artifacts manually
- **Better experimentation**: Can compare results across runs
- **Safer development**: No accidental data loss

## 🔧 **Advanced Usage**

### Manual Artifact Management
```python
from utils.artifact_manager import ArtifactManager

# Create manager
manager = ArtifactManager()

# Get artifact information
info = manager.get_artifact_info()
print(info)
# Output: {'X_train': [('20251004193645', 'path1'), ('20251004193549', 'path2')]}

# Custom cleanup (keep only 3 versions)
manager.cleanup_old_artifacts(['X_train'], keep_count=3)

# Get specific timestamp artifacts
paths = manager.create_timestamped_paths(['X_train'], timestamp='20251004120000')
```

### Artifact Status Checking
```bash
# Check current artifacts
make status
# Shows latest artifact timestamps and counts
```

## 🎉 **Success Indicators**

You'll know the system is working when you see:

1. **Data Pipeline Logs:**
   ```
   💾 Saving artifacts with timestamp: 20251004193645
   ✓ CSV files saved:
      X_train: artifacts/data/X_train_20251004193645.csv
   ```

2. **Training Pipeline Logs:**
   ```
   ✅ Found latest csv artifacts:
      X_train: artifacts/data/X_train_20251004193645.csv
   ```

3. **Inference Pipeline Logs:**
   ```
   📊 Loading test data for inference (sampling 1000 records)...
   Using latest timestamp directory: data/artifacts/csv/20251004201117
   📁 Using latest timestamped artifact: data/artifacts/csv/20251004201117/X_test.csv
   🎲 Randomly sampled 1000 records from 1920 total records
   ```

4. **Directory Structure:**
   ```bash
   ls data/artifacts/csv/
   # Shows: 20251004200927  20251004201006  20251004201117
   
   ls data/artifacts/csv/20251004201117/
   # Shows: X_train.csv  X_test.csv  Y_train.csv  Y_test.csv
   
   ls data/artifacts/parquet/  
   # Shows: 20251004200927  20251004201006  20251004201117
   ```

This system ensures that every pipeline run is reproducible, traceable, and safe! 🚀
