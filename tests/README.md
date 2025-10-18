# 🧪 Test Suite Documentation

Comprehensive testing guide for the Churn Prediction ML Pipeline.

---

## 📋 Table of Contents

1. [Test Structure](#test-structure)
2. [Test Categories](#test-categories)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [CI/CD Integration](#cicd-integration)
6. [Coverage Reports](#coverage-reports)

---

## 🗂️ Test Structure

```
tests/
├── __init__.py                          # Test package initialization
├── conftest.py                          # Shared fixtures and configuration
├── README.md                            # This file
│
├── unit/                                # Unit tests (fast, isolated)
│   ├── test_data_ingestion.py         # Data loading tests
│   ├── test_feature_engineering.py    # Feature transformation tests
│   ├── test_model_training.py         # Model training tests
│   └── test_model_inference.py        # Inference tests
│
├── integration/                         # Integration tests (slower)
│   ├── test_data_pipeline.py          # End-to-end data processing
│   ├── test_training_pipeline.py      # Complete training workflow
│   ├── test_kafka_integration.py      # Kafka streaming tests
│   └── test_rds_integration.py        # Database integration tests
│
├── data_validation/                     # Data quality tests
│   ├── test_data_schema.py            # Schema validation
│   └── test_data_quality.py           # Data integrity checks
│
├── model_validation/                    # Model quality tests
│   ├── test_model_performance.py      # Performance metrics
│   └── test_model_behavior.py         # Edge cases & robustness
│
└── e2e/                                 # End-to-end tests
    └── test_complete_pipeline.py      # Full system tests
```

---

## 🎯 Test Categories

### 1. Unit Tests 🔬
**Purpose**: Test individual functions and classes in isolation

**Characteristics**:
- Fast execution (< 100ms per test)
- No external dependencies
- Mocked data and services
- High code coverage

**Examples**:
```python
# Test data loading
def test_load_csv_success()
def test_validate_required_columns()

# Test feature engineering
def test_standard_scaler()
def test_one_hot_encoding()

# Test model training
def test_model_initialization()
def test_train_random_forest()
```

**Run**:
```bash
pytest tests/unit/ -v
```

### 2. Integration Tests 🔗
**Purpose**: Test how components work together

**Characteristics**:
- Slower execution (seconds)
- May use test databases/Kafka
- Tests real interactions
- Validates workflows

**Examples**:
```python
# Test data pipeline
def test_end_to_end_data_pipeline()

# Test Kafka
def test_producer_consumer_flow()

# Test database
def test_rds_write_and_read()
```

**Run**:
```bash
pytest tests/integration/ --run-integration -v
```

### 3. Data Validation Tests 📊
**Purpose**: Ensure data quality and schema compliance

**Characteristics**:
- Validates data integrity
- Checks business rules
- Detects anomalies
- Range validation

**Examples**:
```python
# Schema validation
def test_required_columns_exist()
def test_data_types_correct()

# Quality validation
def test_age_range_validation()
def test_no_duplicate_customers()
def test_churn_rate_realistic()
```

**Run**:
```bash
pytest tests/data_validation/ -v
```

### 4. Model Validation Tests 🎯
**Purpose**: Validate model performance and behavior

**Characteristics**:
- Checks accuracy thresholds
- Tests prediction quality
- Validates model robustness
- Edge case handling

**Examples**:
```python
# Performance validation
def test_accuracy_threshold()
def test_precision_recall_balance()
def test_roc_auc_score()

# Behavior validation
def test_prediction_distribution()
def test_model_consistency()
def test_model_robustness()
```

**Run**:
```bash
pytest tests/model_validation/ -m model -v
```

### 5. End-to-End Tests 🚀
**Purpose**: Test complete system workflows

**Characteristics**:
- Slowest execution (minutes)
- Tests full pipelines
- Real or near-real environments
- Critical path validation

**Examples**:
```python
# Complete pipeline
def test_data_to_prediction_pipeline()
def test_model_training_deployment()
def test_kafka_streaming_to_rds()
```

**Run**:
```bash
pytest tests/e2e/ --run-slow -v
```

---

## 🚀 Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_data_ingestion.py

# Run specific test function
pytest tests/unit/test_data_ingestion.py::test_load_csv_success

# Run tests matching pattern
pytest -k "test_model"
```

### Using Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only data validation tests
pytest -m data

# Run only model validation tests
pytest -m model

# Run slow tests
pytest -m slow
```

### With Coverage

```bash
# Run with coverage report
pytest --cov=src --cov=pipelines

# Generate HTML coverage report
pytest --cov=src --cov=pipelines --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Parallel Execution

```bash
# Run tests in parallel (faster)
pytest -n auto

# Run with 4 workers
pytest -n 4
```

### Filtering and Selection

```bash
# Run tests that match pattern
pytest -k "data_ingestion or feature"

# Run tests excluding pattern
pytest -k "not slow"

# Run last failed tests
pytest --lf

# Run failed tests first
pytest --ff
```

---

## ✍️ Writing Tests

### Test Naming Convention

```python
# Format: test_<what>_<condition>
def test_load_csv_success()           # Happy path
def test_load_csv_file_not_found()    # Error case
def test_validate_missing_columns()   # Edge case
```

### Using Fixtures

```python
import pytest

@pytest.fixture
def sample_data():
    """Create sample data for testing"""
    return pd.DataFrame({
        'age': [25, 30, 35],
        'balance': [1000, 2000, 3000]
    })

def test_process_data(sample_data):
    """Test using fixture"""
    result = process_data(sample_data)
    assert len(result) == len(sample_data)
```

### Assertions

```python
# Basic assertions
assert value == expected
assert value > threshold
assert isinstance(result, pd.DataFrame)

# Pandas assertions
pd.testing.assert_frame_equal(df1, df2)
pd.testing.assert_series_equal(s1, s2)

# NumPy assertions
np.testing.assert_array_equal(arr1, arr2)
np.testing.assert_allclose(arr1, arr2, rtol=1e-5)

# Pytest helpers
assert result == pytest.approx(3.14, abs=0.01)
```

### Testing Exceptions

```python
import pytest

def test_invalid_input_raises_error():
    """Test that invalid input raises ValueError"""
    with pytest.raises(ValueError):
        process_invalid_data(None)
    
def test_error_message():
    """Test specific error message"""
    with pytest.raises(ValueError, match="Invalid data"):
        process_invalid_data(None)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    (10, 20),
    (5, 10),
    (0, 0)
])
def test_double_value(input, expected):
    """Test function with multiple inputs"""
    assert double(input) == expected
```

---

## 🔄 CI/CD Integration

### GitHub Actions Workflow

Tests run automatically on:
- Every push
- Every pull request
- Before deployment

```yaml
# .github/workflows/ci.yml
- name: Run Unit Tests
  run: pytest tests/unit/ -v
  
- name: Run Integration Tests
  run: pytest tests/integration/ --run-integration -v
  
- name: Generate Coverage
  run: pytest --cov=src --cov-report=xml
```

### Test Reports

- **Coverage**: Uploaded to Codecov
- **Test Results**: Available in Actions artifacts
- **Security Scans**: Bandit + Safety reports

---

## 📊 Coverage Reports

### Viewing Coverage

```bash
# Terminal report
pytest --cov=src --cov-report=term-missing

# HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# XML report (for CI)
pytest --cov=src --cov-report=xml
```

### Coverage Goals

- **Overall**: > 80%
- **Critical paths**: > 90%
- **Unit tests**: > 85%
- **Integration tests**: > 70%

---

## 🎓 Best Practices

### 1. Test Independence
```python
# ✅ Good: Independent test
def test_function_a():
    result = function_a()
    assert result == expected

# ❌ Bad: Depends on previous test
def test_function_b():
    # Assumes test_function_a ran first
    assert global_state == something
```

### 2. Clear Assertions
```python
# ✅ Good: Clear error message
assert len(result) > 0, f"Expected non-empty result, got {len(result)} items"

# ❌ Bad: No context
assert len(result) > 0
```

### 3. Test One Thing
```python
# ✅ Good: Single responsibility
def test_data_loading():
    df = load_data("test.csv")
    assert df is not None

def test_data_validation():
    df = load_data("test.csv")
    assert validate_schema(df) is True

# ❌ Bad: Multiple concerns
def test_data_loading_and_validation():
    df = load_data("test.csv")
    assert df is not None
    assert validate_schema(df) is True
    assert len(df) > 0
```

### 4. Use Fixtures
```python
# ✅ Good: Reusable fixture
@pytest.fixture
def sample_data():
    return create_test_data()

def test_a(sample_data):
    assert process(sample_data) is not None

def test_b(sample_data):
    assert validate(sample_data) is True

# ❌ Bad: Duplicate setup
def test_a():
    data = create_test_data()
    assert process(data) is not None

def test_b():
    data = create_test_data()
    assert validate(data) is True
```

---

## 🐛 Debugging Tests

```bash
# Run with print statements visible
pytest -s

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Verbose output with timings
pytest -vv --durations=10
```

---

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing ML Systems](https://madewithml.com/courses/mlops/testing/)
- [Test-Driven Development](https://www.obeythetestinggoat.com/)

---

## ✅ Checklist: Adding New Tests

- [ ] Test file created in appropriate directory
- [ ] Tests follow naming convention
- [ ] Fixtures used for common setup
- [ ] Both happy path and error cases tested
- [ ] Assertions have clear messages
- [ ] Tests are independent
- [ ] Documentation added
- [ ] Tests pass locally
- [ ] Coverage maintained or improved

---

**Last Updated**: 2024-01-19
**Maintained by**: ML Platform Team

