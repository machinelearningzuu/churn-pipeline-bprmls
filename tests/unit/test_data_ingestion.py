"""
Unit Tests for Data Ingestion Module

Tests the data ingestion functionality including:
- CSV loading
- Data validation
- Column verification
- Missing value handling
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_ingestion import DataIngestion


@pytest.mark.unit
class TestDataIngestion:
    """Test suite for DataIngestion class"""
    
    def test_load_csv_success(self, sample_raw_data, tmp_path):
        """Test successful CSV loading"""
        # Save sample data to temp CSV
        csv_path = tmp_path / "test_data.csv"
        sample_raw_data.to_csv(csv_path, index=False)
        
        # Load data
        ingestion = DataIngestion(str(csv_path))
        df = ingestion.load_data()
        
        assert df is not None
        assert len(df) == len(sample_raw_data)
        assert list(df.columns) == list(sample_raw_data.columns)
    
    def test_load_csv_file_not_found(self):
        """Test handling of missing file"""
        ingestion = DataIngestion("nonexistent_file.csv")
        
        with pytest.raises(FileNotFoundError):
            ingestion.load_data()
    
    def test_validate_required_columns(self, sample_raw_data):
        """Test validation of required columns"""
        ingestion = DataIngestion("dummy_path")
        ingestion.data = sample_raw_data
        
        required_columns = ['CustomerId', 'CreditScore', 'Geography', 'Age', 'Exited']
        assert ingestion.validate_columns(required_columns) is True
    
    def test_validate_missing_columns(self, sample_raw_data):
        """Test detection of missing columns"""
        # Drop a required column
        df = sample_raw_data.drop('Exited', axis=1)
        
        ingestion = DataIngestion("dummy_path")
        ingestion.data = df
        
        required_columns = ['CustomerId', 'CreditScore', 'Exited']
        assert ingestion.validate_columns(required_columns) is False
    
    def test_check_missing_values(self, sample_raw_data):
        """Test missing value detection"""
        # Add some missing values
        df = sample_raw_data.copy()
        df.loc[0:4, 'Age'] = np.nan
        df.loc[10:14, 'Balance'] = np.nan
        
        ingestion = DataIngestion("dummy_path")
        ingestion.data = df
        
        missing_info = ingestion.check_missing_values()
        
        assert missing_info is not None
        assert 'Age' in missing_info.index
        assert 'Balance' in missing_info.index
        assert missing_info['Age'] == 5
        assert missing_info['Balance'] == 5
    
    def test_get_data_summary(self, sample_raw_data):
        """Test data summary generation"""
        ingestion = DataIngestion("dummy_path")
        ingestion.data = sample_raw_data
        
        summary = ingestion.get_summary()
        
        assert 'shape' in summary
        assert 'columns' in summary
        assert 'dtypes' in summary
        assert summary['shape'] == sample_raw_data.shape
    
    def test_filter_by_column_value(self, sample_raw_data):
        """Test filtering data by column value"""
        ingestion = DataIngestion("dummy_path")
        ingestion.data = sample_raw_data
        
        # Filter for customers from France
        filtered_df = ingestion.filter_data('Geography', 'France')
        
        assert len(filtered_df) > 0
        assert all(filtered_df['Geography'] == 'France')
    
    def test_data_shape_consistency(self, sample_raw_data):
        """Test that data shape is maintained correctly"""
        ingestion = DataIngestion("dummy_path")
        ingestion.data = sample_raw_data
        
        assert ingestion.get_row_count() == len(sample_raw_data)
        assert ingestion.get_column_count() == len(sample_raw_data.columns)
    
    def test_data_types(self, sample_raw_data):
        """Test that data types are correctly identified"""
        ingestion = DataIngestion("dummy_path")
        ingestion.data = sample_raw_data
        
        dtypes = ingestion.get_dtypes()
        
        assert dtypes['Age'] == 'int64' or dtypes['Age'] == 'int32'
        assert dtypes['Balance'] == 'float64'
        assert dtypes['Geography'] == 'object'

