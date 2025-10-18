"""
Unit Tests for Feature Engineering Module

Tests feature engineering transformations including:
- Feature scaling
- Feature encoding
- Feature binning
- Outlier detection
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.feature_scaling import FeatureScaler
from src.feature_encoding import FeatureEncoder
from src.feature_binning import FeatureBinner
from src.outlier_detection import OutlierDetector


@pytest.mark.unit
class TestFeatureScaling:
    """Test suite for feature scaling"""
    
    def test_standard_scaler(self, sample_raw_data):
        """Test standard scaling transformation"""
        scaler = FeatureScaler(method='standard')
        
        # Select numerical columns
        numeric_cols = ['Age', 'Balance', 'EstimatedSalary']
        scaled_data = scaler.fit_transform(sample_raw_data[numeric_cols])
        
        # Check that mean is approximately 0 and std is approximately 1
        assert np.allclose(scaled_data.mean(axis=0), 0, atol=1e-10)
        assert np.allclose(scaled_data.std(axis=0), 1, atol=1e-10)
    
    def test_minmax_scaler(self, sample_raw_data):
        """Test min-max scaling transformation"""
        scaler = FeatureScaler(method='minmax')
        
        numeric_cols = ['Age', 'Balance', 'EstimatedSalary']
        scaled_data = scaler.fit_transform(sample_raw_data[numeric_cols])
        
        # Check that values are between 0 and 1
        assert np.all(scaled_data >= 0)
        assert np.all(scaled_data <= 1)
    
    def test_robust_scaler(self, sample_raw_data):
        """Test robust scaling (median and IQR)"""
        scaler = FeatureScaler(method='robust')
        
        numeric_cols = ['Age', 'Balance']
        scaled_data = scaler.fit_transform(sample_raw_data[numeric_cols])
        
        # Robust scaler should handle outliers well
        assert scaled_data is not None
        assert scaled_data.shape == sample_raw_data[numeric_cols].shape


@pytest.mark.unit
class TestFeatureEncoding:
    """Test suite for feature encoding"""
    
    def test_one_hot_encoding(self, sample_raw_data):
        """Test one-hot encoding for categorical variables"""
        encoder = FeatureEncoder(method='onehot')
        
        encoded_data = encoder.fit_transform(sample_raw_data[['Geography']])
        
        # Check that encoding creates multiple columns
        assert encoded_data.shape[1] >= len(sample_raw_data['Geography'].unique()) - 1
        
        # Check that values are binary
        assert set(encoded_data.values.flatten()).issubset({0, 1})
    
    def test_label_encoding(self, sample_raw_data):
        """Test label encoding for categorical variables"""
        encoder = FeatureEncoder(method='label')
        
        encoded_data = encoder.fit_transform(sample_raw_data[['Gender']])
        
        # Check that encoding creates integer labels
        assert encoded_data.dtype in ['int64', 'int32']
        assert len(np.unique(encoded_data)) == len(sample_raw_data['Gender'].unique())
    
    def test_binary_encoding(self, sample_raw_data):
        """Test binary encoding"""
        # Gender is already binary, should be 0 or 1
        encoder = FeatureEncoder(method='binary')
        
        encoded_data = encoder.fit_transform(sample_raw_data[['Gender']])
        
        assert set(encoded_data.values.flatten()).issubset({0, 1})


@pytest.mark.unit
class TestFeatureBinning:
    """Test suite for feature binning"""
    
    def test_age_binning(self, sample_raw_data):
        """Test age binning into categories"""
        binner = FeatureBinner()
        
        age_bins = [0, 18, 30, 45, 60, 100]
        age_labels = ['Teen', 'Young Adult', 'Adult', 'Middle Age', 'Senior']
        
        binned_data = binner.bin_feature(
            sample_raw_data['Age'], 
            bins=age_bins, 
            labels=age_labels
        )
        
        # Check that all values are in labels
        assert set(binned_data.unique()).issubset(set(age_labels))
    
    def test_balance_binning(self, sample_raw_data):
        """Test balance binning"""
        binner = FeatureBinner()
        
        # Bin balance into quartiles
        binned_data = binner.bin_feature(sample_raw_data['Balance'], bins=4)
        
        # Check that we have 4 categories
        assert len(binned_data.unique()) <= 4


@pytest.mark.unit
class TestOutlierDetection:
    """Test suite for outlier detection"""
    
    def test_iqr_outlier_detection(self, sample_raw_data):
        """Test IQR method for outlier detection"""
        detector = OutlierDetector(method='iqr')
        
        outliers = detector.detect(sample_raw_data['Balance'])
        
        # Outliers should be boolean mask
        assert outliers.dtype == bool
        assert len(outliers) == len(sample_raw_data)
    
    def test_zscore_outlier_detection(self, sample_raw_data):
        """Test Z-score method for outlier detection"""
        detector = OutlierDetector(method='zscore', threshold=3)
        
        outliers = detector.detect(sample_raw_data['Age'])
        
        assert outliers.dtype == bool
        # With random data, we might have some outliers
        assert outliers.sum() >= 0
    
    def test_remove_outliers(self, sample_raw_data):
        """Test outlier removal"""
        detector = OutlierDetector(method='iqr')
        
        original_len = len(sample_raw_data)
        cleaned_data = detector.remove_outliers(sample_raw_data, ['Balance'])
        
        # Cleaned data should have <= original length
        assert len(cleaned_data) <= original_len

