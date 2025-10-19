"""
Unit Tests for Data Ingestion Module
Tests CSV loading and basic data validation
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data_ingestion import DataIngestorCSV


class TestDataIngestion:
    """Test suite for data ingestion"""
    
    def test_csv_ingestor_loads_file_successfully(self):
        """Test that CSV file loads without errors"""
        # Use local fallback for testing
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data file not found: {data_path}")
        
        ingestor = DataIngestorCSV()
        df = ingestor.ingest(data_path)
        
        assert isinstance(df, pd.DataFrame), "Result should be a DataFrame"
        assert len(df) > 0, "DataFrame should not be empty"
        assert len(df.columns) > 0, "DataFrame should have columns"
    
    def test_loaded_data_has_required_columns(self):
        """Test that loaded data contains critical columns"""
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data file not found: {data_path}")
        
        ingestor = DataIngestorCSV()
        df = ingestor.ingest(data_path)
        
        required_columns = ['CustomerId', 'CreditScore', 'Geography', 
                           'Gender', 'Age', 'Tenure', 'Balance', 'Exited']
        
        for col in required_columns:
            assert col in df.columns, f"Required column '{col}' not found"
    
    def test_loaded_data_has_correct_types(self):
        """Test that numeric columns are properly typed"""
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data file not found: {data_path}")
        
        ingestor = DataIngestorCSV()
        df = ingestor.ingest(data_path)
        
        # Check numeric columns
        assert pd.api.types.is_numeric_dtype(df['CreditScore']), "CreditScore should be numeric"
        assert pd.api.types.is_numeric_dtype(df['Age']), "Age should be numeric"
        assert pd.api.types.is_numeric_dtype(df['Balance']), "Balance should be numeric"
    
    def test_csv_with_invalid_path_raises_error(self):
        """Test that invalid file path raises appropriate error"""
        ingestor = DataIngestorCSV()
        
        with pytest.raises(Exception):
            ingestor.ingest("non_existent_file.csv")
    
    def test_loaded_data_shape_is_reasonable(self):
        """Test that loaded data has reasonable dimensions"""
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data file not found: {data_path}")
        
        ingestor = DataIngestorCSV()
        df = ingestor.ingest(data_path)
        
        # Should have multiple columns (at least 10)
        assert df.shape[1] >= 10, f"Expected at least 10 columns, got {df.shape[1]}"
        
        # Should have meaningful number of rows
        assert df.shape[0] >= 100, f"Expected at least 100 rows, got {df.shape[0]}"

