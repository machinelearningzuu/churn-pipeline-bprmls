# 🧪 Simplified CI/CD Testing Guide

This project uses **2 focused validation scripts** in CI/CD to ensure quality before deployment.

---

## 🎯 The Two Critical Checks

### 1. **Data Validation & Drift Detection** (`validate_data.py`)

**What it checks**:
- ✅ All required columns present
- ✅ Data types are correct
- ✅ Value ranges are valid (Age 18-100, CreditScore 300-850, etc.)
- ✅ Categorical values valid (Geography, Gender)
- ✅ No critical missing values
- ✅ No duplicate customer IDs
- ✅ Data distribution drift (statistical tests)
- ✅ Class balance is reasonable

**Exit behavior**:
- `Exit 0`: All checks passed ✅
- `Exit 1`: Critical issues found ❌ (blocks deployment)

**Usage**:
```bash
# Basic usage
python tests/validate_data.py data/raw/ChurnModelling.csv

# With drift detection (compare against reference data)
python tests/validate_data.py data/raw/ChurnModelling.csv data/reference/baseline.csv
```

---

### 2. **Model Performance Validation** (`validate_model.py`)

**What it checks**:
- 🎯 **F1 Score >= 75%** (HARD REQUIREMENT)
- ✅ Accuracy >= 75%
- ✅ Precision >= 70%
- ✅ Recall >= 70%
- ✅ ROC-AUC >= 75%

**Critical Rule**: If F1 score < 75%, **deployment is BLOCKED** and system reverts to previous model.

**Exit behavior**:
- `Exit 0`: Model meets all thresholds ✅ (deploy)
- `Exit 1`: Model fails thresholds ❌ (block + revert)

**Usage**:
```bash
# Basic validation
python tests/validate_model.py artifacts/models/best_model.pkl artifacts/data/test_data.pkl

# With comparison to previous model
python tests/validate_model.py \
    artifacts/models/new_model.pkl \
    artifacts/data/test_data.pkl \
    artifacts/models/previous_model.pkl
```

---

## 🔄 CI/CD Workflow

### When It Runs
- Every **push** to `main`, `develop`, or `feature/**` branches
- Every **pull request** to `main` or `develop`

### Workflow Steps

```
1. Data Validation & Drift Check
   ├── Load dataset
   ├── Check schema (columns, types, ranges)
   ├── Check data quality (missing, duplicates)
   ├── Detect drift (vs reference data)
   └── Generate report
   
   ✅ PASS → Continue
   ❌ FAIL → BLOCK DEPLOYMENT

2. Model Performance Validation
   ├── Download latest model from S3
   ├── Load test data
   ├── Evaluate model (F1, Accuracy, etc.)
   ├── Check F1 >= 75% threshold
   └── Generate report
   
   ✅ F1 >= 75% → APPROVE DEPLOYMENT
   ❌ F1 < 75%  → BLOCK & REVERT

3. Validation Summary
   └── Display results & make final decision
```

---

## 📊 Performance Thresholds

| Metric | Minimum Threshold | Severity |
|--------|------------------|----------|
| **F1 Score** | **75%** | 🔴 **CRITICAL** |
| Accuracy | 75% | 🟡 High |
| Precision | 70% | 🟡 High |
| Recall | 70% | 🟡 High |
| ROC-AUC | 75% | 🟡 High |

**Why F1 Score is critical?**
- Balances precision and recall
- Best metric for imbalanced classes (churn prediction)
- If F1 < 75%, model quality is insufficient for production

---

## 🚀 Running Locally

### 1. Test Data Validation

```bash
# Install dependencies
pip install pandas numpy scipy scikit-learn

# Run validation
python tests/validate_data.py data/raw/ChurnModelling.csv

# Expected output:
# ✅ All required columns present
# ✅ Data types correct
# ✅ Value ranges valid
# ✅ No critical issues
# 🎉 All validation checks passed!
```

### 2. Test Model Validation

```bash
# Train a model first
make train-pipeline

# Run validation
python tests/validate_model.py \
    artifacts/models/best_model.pkl \
    artifacts/data/test_data.pkl

# Expected output:
# 📊 Performance Metrics:
#    F1 Score: 0.7823 (78.23%)
# ✅ MODEL APPROVED FOR DEPLOYMENT
# 🚀 Proceeding with deployment...
```

---

## 📁 Output Reports

Both scripts generate JSON reports:

### Data Validation Report
```json
{
  "timestamp": "2024-01-19T10:30:00",
  "data_path": "data/raw/ChurnModelling.csv",
  "num_rows": 10000,
  "num_columns": 14,
  "checks": {
    "required_columns": "PASS",
    "data_types": "PASS",
    "value_ranges": "PASS",
    "data_drift": "PASS",
    "class_balance": "PASS"
  }
}
```

### Model Validation Report
```json
{
  "timestamp": "2024-01-19T10:35:00",
  "metrics": {
    "f1_score": 0.7823,
    "accuracy": 0.8015,
    "precision": 0.7456,
    "recall": 0.8234
  },
  "thresholds": {
    "f1_score": {
      "value": 0.7823,
      "threshold": 0.75,
      "passed": true
    }
  },
  "deployment_approved": true
}
```

---

## 🔧 Customizing Thresholds

### Data Validation Thresholds
Edit `tests/validate_data.py`:

```python
# Adjust value ranges
NUMERIC_RANGES = {
    'Age': (18, 100),           # Change age range
    'CreditScore': (300, 850),  # Change credit score range
}

# Adjust drift sensitivity
DRIFT_THRESHOLD = 0.05  # 5% significance level (make stricter: 0.01)
```

### Model Performance Thresholds
Edit `tests/validate_model.py`:

```python
THRESHOLDS = {
    'f1_score': 0.75,    # Change to 0.80 for stricter requirement
    'accuracy': 0.75,
    'precision': 0.70,
    'recall': 0.70,
}
```

---

## ⚠️ What Happens on Failure?

### Data Validation Fails
```
❌ Some validation checks failed!
   ❌ value_ranges: FAIL
   ❌ data_drift: FAIL

CI/CD: BLOCKS DEPLOYMENT
Action: Fix data quality issues before merging
```

### Model Validation Fails (F1 < 75%)
```
❌ MODEL REJECTED - DOES NOT MEET REQUIREMENTS
   F1 Score: 72.34% < 75.00%
   Failed metrics: f1_score

🔄 REVERTING TO PREVIOUS MODEL
   Deployment blocked to maintain system quality

CI/CD: BLOCKS DEPLOYMENT + REVERTS MODEL
Action: Retrain model with better performance
```

---

## 🎯 Best Practices

### 1. **Always Run Locally First**
```bash
# Before pushing code
python tests/validate_data.py data/raw/ChurnModelling.csv
python tests/validate_model.py artifacts/models/best_model.pkl artifacts/data/test_data.pkl
```

### 2. **Monitor CI/CD Results**
- Check GitHub Actions after each push
- Review validation reports (artifacts)
- Fix issues immediately

### 3. **Maintain Reference Data**
- Keep baseline dataset for drift detection
- Update reference data periodically
- Store in `data/reference/` directory

### 4. **Track Model Performance**
- Review validation reports regularly
- Monitor F1 score trends
- Retrain if performance degrades

---

## 📚 Quick Commands

```bash
# Data validation only
python tests/validate_data.py data/raw/ChurnModelling.csv

# Model validation only
python tests/validate_model.py artifacts/models/best_model.pkl artifacts/data/test_data.pkl

# Full CI/CD simulation (both tests)
python tests/validate_data.py data/raw/ChurnModelling.csv && \
python tests/validate_model.py artifacts/models/best_model.pkl artifacts/data/test_data.pkl

# View reports
cat reports/data_validation_report.json | python -m json.tool
cat reports/model_validation_report.json | python -m json.tool
```

---

## ✅ Success Criteria

Your deployment will be **approved** if:

1. ✅ All data validation checks pass
2. ✅ No critical data drift detected
3. ✅ **Model F1 score >= 75%**
4. ✅ All model metrics meet thresholds

If ANY of these fail → **Deployment BLOCKED** ❌

---

**Last Updated**: 2024-01-19  
**Maintained by**: ML Platform Team

