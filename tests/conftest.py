"""
Pytest Configuration and Shared Fixtures

This file contains pytest configuration and reusable fixtures
for all test modules.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ==========================================
# Test Data Fixtures
# ==========================================

@pytest.fixture
def sample_raw_data():
    """Generate sample raw customer data"""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'RowNumber': range(1, n_samples + 1),
        'CustomerId': range(15000000, 15000000 + n_samples),
        'Surname': [f'Customer_{i}' for i in range(n_samples)],
        'CreditScore': np.random.randint(350, 850, n_samples),
        'Geography': np.random.choice(['France', 'Germany', 'Spain'], n_samples),
        'Gender': np.random.choice(['Male', 'Female'], n_samples),
        'Age': np.random.randint(18, 92, n_samples),
        'Tenure': np.random.randint(0, 11, n_samples),
        'Balance': np.random.uniform(0, 250000, n_samples),
        'NumOfProducts': np.random.randint(1, 5, n_samples),
        'HasCrCard': np.random.choice([0, 1], n_samples),
        'IsActiveMember': np.random.choice([0, 1], n_samples),
        'EstimatedSalary': np.random.uniform(10, 200000, n_samples),
        'Exited': np.random.choice([0, 1], n_samples, p=[0.8, 0.2])
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_processed_data(sample_raw_data):
    """Generate sample processed data"""
    df = sample_raw_data.copy()
    
    # Drop unnecessary columns
    df = df.drop(['RowNumber', 'CustomerId', 'Surname'], axis=1)
    
    # Encode categorical variables
    df = pd.get_dummies(df, columns=['Geography', 'Gender'], drop_first=True)
    
    return df


@pytest.fixture
def sample_features_labels(sample_processed_data):
    """Generate sample feature matrix and labels"""
    X = sample_processed_data.drop('Exited', axis=1)
    y = sample_processed_data['Exited']
    return X, y


@pytest.fixture
def sample_model_predictions():
    """Generate sample model predictions"""
    np.random.seed(42)
    n_samples = 100
    
    return {
        'predictions': np.random.choice([0, 1], n_samples),
        'probabilities': np.random.uniform(0, 1, n_samples),
        'true_labels': np.random.choice([0, 1], n_samples)
    }


# ==========================================
# Configuration Fixtures
# ==========================================

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        's3': {
            'bucket': 'test-bucket',
            'region': 'us-east-1'
        },
        'rds': {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_pass'
        },
        'kafka': {
            'bootstrap_servers': 'localhost:9092',
            'topics': {
                'customer_events': 'test-events',
                'predictions': 'test-predictions'
            }
        },
        'model': {
            'name': 'churn_model',
            'version': 'test_v1'
        }
    }


@pytest.fixture
def temp_artifacts_dir(tmp_path):
    """Create temporary artifacts directory"""
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    
    # Create subdirectories
    (artifacts_dir / "data").mkdir()
    (artifacts_dir / "models").mkdir()
    (artifacts_dir / "evaluation").mkdir()
    
    return artifacts_dir


# ==========================================
# Environment Fixtures
# ==========================================

@pytest.fixture
def mock_aws_credentials(monkeypatch):
    """Mock AWS credentials for testing"""
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'test_access_key')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'test_secret_key')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')


@pytest.fixture
def mock_rds_credentials(monkeypatch):
    """Mock RDS credentials for testing"""
    monkeypatch.setenv('RDS_HOST', 'localhost')
    monkeypatch.setenv('RDS_PORT', '5432')
    monkeypatch.setenv('RDS_DB_NAME', 'test_analytics')
    monkeypatch.setenv('RDS_USERNAME', 'test_user')
    monkeypatch.setenv('RDS_PASSWORD', 'test_password')


@pytest.fixture
def mock_kafka_config(monkeypatch):
    """Mock Kafka configuration for testing"""
    monkeypatch.setenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    monkeypatch.setenv('RUNNING_IN_DOCKER', 'false')


# ==========================================
# Pytest Configuration
# ==========================================

def pytest_configure(config):
    """Pytest configuration hook"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interactions"
    )
    config.addinivalue_line(
        "markers", "data: Data validation and quality tests"
    )
    config.addinivalue_line(
        "markers", "model: Model validation and performance tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end pipeline tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )


# ==========================================
# Pytest Command Line Options
# ==========================================

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options"""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

