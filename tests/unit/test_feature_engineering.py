"""
Unit Tests for Feature Engineering
Tests scaling, encoding, and transformations using sklearn (not PySpark wrappers)
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Use sklearn directly (production uses this, not PySpark wrappers)
from sklearn.preprocessing import StandardScaler, MinMaxScaler
# For encoding, use pandas' get_dummies (production uses this)


@pytest.mark.unit
class TestFeatureScaling:
    """Test suite for feature scaling"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample numeric data for testing"""
        return pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': [10, 20, 30, 40, 50],
            'feature3': [100, 200, 300, 400, 500]
        })
    
    def test_standard_scaler_normalizes_mean_to_zero(self, sample_data):
        """Test that StandardScaler normalizes mean to approximately 0"""
        scaler = StandardScaler()
        df = sample_data.copy()
        df[['feature1', 'feature2']] = scaler.fit_transform(df[['feature1', 'feature2']])
        
        # Check mean is close to 0
        assert abs(df['feature1'].mean()) < 1e-9, "Mean should be close to 0"
        assert abs(df['feature2'].mean()) < 1e-9, "Mean should be close to 0"
    
    def test_standard_scaler_std_to_one(self, sample_data):
        """Test that StandardScaler normalizes std to approximately 1"""
        scaler = StandardScaler()
        df = sample_data.copy()
        df[['feature1', 'feature2']] = scaler.fit_transform(df[['feature1', 'feature2']])
        
        # Check std is close to 1 (use ddof=0 for population std, matching sklearn)
        assert abs(df['feature1'].std(ddof=0) - 1.0) < 1e-9, "Std should be close to 1"
        assert abs(df['feature2'].std(ddof=0) - 1.0) < 1e-9, "Std should be close to 1"
    
    def test_minmax_scaler_scales_to_zero_one(self, sample_data):
        """Test that MinMaxScaler scales values to [0, 1]"""
        scaler = MinMaxScaler()
        df = sample_data.copy()
        df[['feature1', 'feature2']] = scaler.fit_transform(df[['feature1', 'feature2']])
        
        # Check values are in [0, 1]
        assert abs(df['feature1'].min() - 0.0) < 1e-9, "Min should be 0"
        assert abs(df['feature1'].max() - 1.0) < 1e-9, "Max should be 1"
        assert abs(df['feature2'].min() - 0.0) < 1e-9, "Min should be 0"
        assert abs(df['feature2'].max() - 1.0) < 1e-9, "Max should be 1"
    
    def test_scaler_preserves_unscaled_columns(self, sample_data):
        """Test that scaler doesn't modify unscaled columns"""
        scaler = StandardScaler()
        df = sample_data.copy()
        original_feature3 = df['feature3'].copy()
        
        df[['feature1', 'feature2']] = scaler.fit_transform(df[['feature1', 'feature2']])
        
        # feature3 should remain unchanged
        pd.testing.assert_series_equal(df['feature3'], original_feature3)
    
    def test_scaler_handles_single_column(self, sample_data):
        """Test that scaler works with single column"""
        scaler = StandardScaler()
        df = sample_data.copy()
        df[['feature1']] = scaler.fit_transform(df[['feature1']])
        
        assert abs(df['feature1'].mean()) < 1e-9, "Single column should scale correctly"


@pytest.mark.unit
class TestFeatureEncoding:
    """Test suite for feature encoding"""
    
    @pytest.fixture
    def categorical_data(self):
        """Create sample categorical data"""
        return pd.DataFrame({
            'Geography': ['France', 'Spain', 'Germany', 'France', 'Spain'],
            'Gender': ['Male', 'Female', 'Male', 'Female', 'Male'],
            'numeric_col': [1, 2, 3, 4, 5]
        })
    
    def test_one_hot_encoding_creates_binary_columns(self, categorical_data):
        """Test that one-hot encoding creates binary columns"""
        df = categorical_data.copy()
        encoded_data = pd.get_dummies(df, columns=['Geography'], drop_first=False)
        
        # Check that Geography columns are created
        geography_cols = [col for col in encoded_data.columns if col.startswith('Geography_')]
        assert len(geography_cols) == 3, "Should create 3 Geography columns (France, Spain, Germany)"
        
        # Check values are binary (0 or 1)
        for col in geography_cols:
            assert encoded_data[col].isin([0, 1]).all(), f"{col} should be binary"
    
    def test_encoding_preserves_numeric_columns(self, categorical_data):
        """Test that encoding doesn't affect numeric columns"""
        df = categorical_data.copy()
        original_numeric = df['numeric_col'].copy()
        
        encoded_data = pd.get_dummies(df, columns=['Geography'], drop_first=False)
        
        pd.testing.assert_series_equal(encoded_data['numeric_col'], original_numeric)
    
    def test_encoding_removes_original_categorical_column(self, categorical_data):
        """Test that original categorical column is removed after encoding"""
        df = categorical_data.copy()
        encoded_data = pd.get_dummies(df, columns=['Geography'], drop_first=False)
        
        # Original Geography column should not exist
        assert 'Geography' not in encoded_data.columns, \
               "Original categorical column should be removed"
    
    def test_encoding_handles_multiple_columns(self, categorical_data):
        """Test encoding multiple categorical columns at once"""
        df = categorical_data.copy()
        encoded_data = pd.get_dummies(df, columns=['Geography', 'Gender'], drop_first=False)
        
        # Should have columns for both Geography and Gender
        geography_cols = [col for col in encoded_data.columns if col.startswith('Geography_')]
        gender_cols = [col for col in encoded_data.columns if col.startswith('Gender_')]
        
        assert len(geography_cols) == 3, "Should create 3 Geography columns"
        assert len(gender_cols) == 2, "Should create 2 Gender columns"

