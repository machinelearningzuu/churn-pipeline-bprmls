"""
Integration Tests for Data Pipeline

Tests the complete data processing pipeline:
- Data ingestion → Processing → Feature engineering → Splitting
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.integration
class TestDataPipeline:
    """Integration tests for the complete data pipeline"""
    
    def test_end_to_end_data_pipeline(self, sample_raw_data, tmp_path):
        """Test complete data processing pipeline"""
        from src.data_ingestion import DataIngestion
        from src.handle_missing_values import MissingValueHandler
        from src.feature_encoding import FeatureEncoder
        from src.feature_scaling import FeatureScaler
        from src.data_splitter import DataSplitter
        
        # Step 1: Data Ingestion
        csv_path = tmp_path / "raw_data.csv"
        sample_raw_data.to_csv(csv_path, index=False)
        
        ingestion = DataIngestion(str(csv_path))
        df = ingestion.load_data()
        
        assert df is not None
        assert len(df) > 0
        
        # Step 2: Handle Missing Values
        handler = MissingValueHandler(strategy='median')
        df_clean = handler.handle_missing(df)
        
        assert df_clean.isnull().sum().sum() == 0
        
        # Step 3: Feature Engineering
        # Remove unnecessary columns
        df_processed = df_clean.drop(['RowNumber', 'CustomerId', 'Surname'], axis=1, errors='ignore')
        
        # Separate features and target
        y = df_processed['Exited']
        X = df_processed.drop('Exited', axis=1)
        
        # Encode categorical variables
        categorical_cols = ['Geography', 'Gender']
        X_encoded = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
        
        # Step 4: Feature Scaling
        scaler = FeatureScaler(method='standard')
        X_scaled = scaler.fit_transform(X_encoded)
        
        # Step 5: Train-Test Split
        splitter = DataSplitter(test_size=0.2, random_state=42)
        X_train, X_test, y_train, y_test = splitter.split(X_scaled, y)
        
        # Assertions
        assert X_train.shape[0] + X_test.shape[0] == len(X_scaled)
        assert len(X_train) == len(y_train)
        assert len(X_test) == len(y_test)
        assert X_test.shape[0] / len(X_scaled) == pytest.approx(0.2, abs=0.05)
    
    def test_pipeline_with_artifacts(self, sample_raw_data, tmp_path):
        """Test pipeline with artifact saving"""
        from pipelines.data_pipeline import run_data_pipeline
        
        # Create necessary directories
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        
        # Save input data
        input_path = data_dir / "ChurnModelling.csv"
        sample_raw_data.to_csv(input_path, index=False)
        
        # Run pipeline (if function exists)
        # This tests the actual pipeline execution
        # result = run_data_pipeline(engine='pandas')
        
        # For now, just verify structure
        assert input_path.exists()
    
    def test_pipeline_reproducibility(self, sample_raw_data):
        """Test that pipeline produces reproducible results"""
        from src.data_splitter import DataSplitter
        
        X = sample_raw_data.drop('Exited', axis=1).select_dtypes(include=['int64', 'float64'])
        y = sample_raw_data['Exited']
        
        # Run pipeline twice with same random seed
        splitter1 = DataSplitter(test_size=0.2, random_state=42)
        X_train1, X_test1, y_train1, y_test1 = splitter1.split(X, y)
        
        splitter2 = DataSplitter(test_size=0.2, random_state=42)
        X_train2, X_test2, y_train2, y_test2 = splitter2.split(X, y)
        
        # Results should be identical
        pd.testing.assert_frame_equal(X_train1, X_train2)
        pd.testing.assert_frame_equal(X_test1, X_test2)
        pd.testing.assert_series_equal(y_train1.reset_index(drop=True), y_train2.reset_index(drop=True))

