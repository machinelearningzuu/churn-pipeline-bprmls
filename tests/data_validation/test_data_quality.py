"""
Data Quality Validation Tests

Tests data quality and integrity:
- Schema validation
- Data type validation
- Range validation
- Business rule validation
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.data
class TestDataQuality:
    """Test suite for data quality validation"""
    
    def test_no_missing_values_in_critical_columns(self, sample_raw_data):
        """Test that critical columns have no missing values"""
        critical_columns = ['CustomerId', 'Geography', 'Age', 'Exited']
        
        for col in critical_columns:
            missing_count = sample_raw_data[col].isnull().sum()
            assert missing_count == 0, f"Column {col} has {missing_count} missing values"
    
    def test_age_range_validation(self, sample_raw_data):
        """Test that age values are within realistic range"""
        ages = sample_raw_data['Age']
        
        assert ages.min() >= 18, f"Minimum age {ages.min()} below 18"
        assert ages.max() <= 100, f"Maximum age {ages.max()} above 100"
        assert ages.dtype in ['int64', 'int32'], "Age should be integer"
    
    def test_credit_score_range(self, sample_raw_data):
        """Test credit score is within valid range"""
        credit_scores = sample_raw_data['CreditScore']
        
        assert credit_scores.min() >= 300, f"Min credit score {credit_scores.min()} too low"
        assert credit_scores.max() <= 850, f"Max credit score {credit_scores.max()} too high"
    
    def test_balance_non_negative(self, sample_raw_data):
        """Test that balance values are non-negative"""
        balances = sample_raw_data['Balance']
        
        assert (balances >= 0).all(), "Negative balance values found"
    
    def test_tenure_range(self, sample_raw_data):
        """Test that tenure is within reasonable range"""
        tenure = sample_raw_data['Tenure']
        
        assert tenure.min() >= 0, "Negative tenure found"
        assert tenure.max() <= 10, f"Tenure {tenure.max()} exceeds maximum"
    
    def test_binary_columns(self, sample_raw_data):
        """Test that binary columns only contain 0 or 1"""
        binary_columns = ['HasCrCard', 'IsActiveMember', 'Exited']
        
        for col in binary_columns:
            unique_values = set(sample_raw_data[col].unique())
            assert unique_values.issubset({0, 1}), f"{col} contains non-binary values: {unique_values}"
    
    def test_categorical_values(self, sample_raw_data):
        """Test that categorical columns have expected values"""
        # Geography should be one of three countries
        valid_geographies = {'France', 'Germany', 'Spain'}
        actual_geographies = set(sample_raw_data['Geography'].unique())
        assert actual_geographies.issubset(valid_geographies), \
            f"Invalid geographies: {actual_geographies - valid_geographies}"
        
        # Gender should be Male or Female
        valid_genders = {'Male', 'Female'}
        actual_genders = set(sample_raw_data['Gender'].unique())
        assert actual_genders.issubset(valid_genders), \
            f"Invalid genders: {actual_genders - valid_genders}"
    
    def test_num_of_products_range(self, sample_raw_data):
        """Test number of products is within reasonable range"""
        num_products = sample_raw_data['NumOfProducts']
        
        assert num_products.min() >= 1, "Customer with 0 products found"
        assert num_products.max() <= 4, f"Customer with {num_products.max()} products (max is 4)"
    
    def test_no_duplicate_customers(self, sample_raw_data):
        """Test that there are no duplicate customer IDs"""
        duplicate_count = sample_raw_data['CustomerId'].duplicated().sum()
        assert duplicate_count == 0, f"Found {duplicate_count} duplicate customer IDs"
    
    def test_data_types(self, sample_raw_data):
        """Test that columns have correct data types"""
        expected_types = {
            'RowNumber': ['int64', 'int32'],
            'CustomerId': ['int64', 'int32'],
            'CreditScore': ['int64', 'int32'],
            'Age': ['int64', 'int32'],
            'Tenure': ['int64', 'int32'],
            'Balance': ['float64', 'float32'],
            'NumOfProducts': ['int64', 'int32'],
            'HasCrCard': ['int64', 'int32'],
            'IsActiveMember': ['int64', 'int32'],
            'EstimatedSalary': ['float64', 'float32'],
            'Exited': ['int64', 'int32'],
            'Geography': ['object'],
            'Gender': ['object'],
            'Surname': ['object']
        }
        
        for col, valid_types in expected_types.items():
            if col in sample_raw_data.columns:
                actual_type = str(sample_raw_data[col].dtype)
                assert actual_type in valid_types, \
                    f"Column {col} has type {actual_type}, expected one of {valid_types}"
    
    def test_churn_rate_realistic(self, sample_raw_data):
        """Test that churn rate is within realistic bounds"""
        churn_rate = sample_raw_data['Exited'].mean()
        
        # Typical churn rates are between 5% and 40%
        assert 0.05 <= churn_rate <= 0.40, \
            f"Churn rate {churn_rate:.2%} outside realistic range (5%-40%)"
    
    def test_class_imbalance_acceptable(self, sample_raw_data):
        """Test that class imbalance is not too extreme"""
        class_counts = sample_raw_data['Exited'].value_counts()
        majority_class = class_counts.max()
        minority_class = class_counts.min()
        
        imbalance_ratio = majority_class / minority_class
        
        # Ratio should not be more than 5:1
        assert imbalance_ratio <= 5, \
            f"Class imbalance ratio {imbalance_ratio:.2f} too high"

