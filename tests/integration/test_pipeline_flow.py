"""
Integration Tests for Pipeline Workflows
Tests end-to-end data processing and model training flows using pandas/sklearn
"""

import pytest
import pandas as pd
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.integration
class TestDataPipelineIntegration:
    """Integration tests for data processing pipeline"""
    
    def test_data_pipeline_end_to_end_local(self):
        """Test complete data pipeline with local data"""
        from src.data_ingestion import DataIngestorCSV
        from sklearn.preprocessing import StandardScaler
        
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data not available: {data_path}")
        
        # Step 1: Ingest data
        ingestor = DataIngestorCSV()
        df = ingestor.ingest(data_path)
        assert len(df) > 0, "Data ingestion failed"
        
        # Step 2: Select features
        feature_cols = ['CreditScore', 'Geography', 'Gender', 'Age', 
                       'Tenure', 'Balance', 'NumOfProducts']
        df_features = df[feature_cols].copy()
        
        # Step 3: Encode categorical features using pandas
        df_encoded = pd.get_dummies(df_features, columns=['Geography', 'Gender'], drop_first=False)
        assert len(df_encoded) == len(df), "Encoding should preserve row count"
        
        # Step 4: Scale numeric features using sklearn
        scaler = StandardScaler()
        numeric_cols = ['CreditScore', 'Age', 'Balance']
        df_scaled = df_encoded.copy()
        df_scaled[numeric_cols] = scaler.fit_transform(df_scaled[numeric_cols])
        
        # Verify pipeline output
        assert len(df_scaled) > 0, "Pipeline should produce output"
        assert df_scaled.isnull().sum().sum() < len(df) * 0.1, "Should have minimal nulls"
        
        # Check that scaling worked (mean should be very close to 0)
        for col in numeric_cols:
            if col in df_scaled.columns:
                assert abs(df_scaled[col].mean()) < 0.1, f"{col} mean should be close to 0"
    
    def test_pipeline_handles_missing_values(self):
        """Test that pipeline can handle data with missing values"""
        from src.data_ingestion import DataIngestorCSV
        
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data not available: {data_path}")
        
        ingestor = DataIngestorCSV()
        df = ingestor.ingest(data_path)
        
        # Count missing values
        missing_count = df.isnull().sum().sum()
        total_cells = df.shape[0] * df.shape[1]
        missing_pct = (missing_count / total_cells) * 100
        
        # Should have some data even if there are missing values
        assert len(df) > 0, "Should load data despite missing values"
        assert missing_pct < 50, f"Too many missing values: {missing_pct:.1f}%"
    
    def test_pipeline_preserves_data_integrity(self):
        """Test that pipeline transformations maintain data relationships"""
        from src.data_ingestion import DataIngestorCSV
        from sklearn.preprocessing import MinMaxScaler
        
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data not available: {data_path}")
        
        ingestor = DataIngestorCSV()
        df = ingestor.ingest(data_path)
        
        # Get a subset for testing
        df_subset = df[['CreditScore', 'Age', 'Balance']].head(100).dropna()
        original_row_count = len(df_subset)
        
        # Scale the data using sklearn
        scaler = MinMaxScaler()
        df_scaled = df_subset.copy()
        df_scaled[['CreditScore', 'Age', 'Balance']] = scaler.fit_transform(df_scaled[['CreditScore', 'Age', 'Balance']])
        
        # Row count should be preserved
        assert len(df_scaled) == original_row_count, "Scaling should preserve row count"
        
        # Relative ordering should be maintained (for CreditScore)
        if 'CreditScore' in df_scaled.columns:
            original_order = df_subset['CreditScore'].rank()
            scaled_order = df_scaled['CreditScore'].rank()
            assert original_order.equals(scaled_order), "Scaling should preserve ordering"


@pytest.mark.integration
@pytest.mark.requires_model
class TestModelTrainingIntegration:
    """Integration tests for model training workflow"""
    
    def test_model_training_with_sample_data(self):
        """Test that model can be trained on sample data"""
        from src.data_ingestion import DataIngestorCSV
        from sklearn.model_selection import train_test_split
        from sklearn.ensemble import RandomForestClassifier
        
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data not available: {data_path}")
        
        # Load and prepare data
        ingestor = DataIngestorCSV()
        df = ingestor.ingest(data_path)
        
        # Use a small sample for quick testing
        df_sample = df.head(500).dropna()
        
        if 'Exited' not in df_sample.columns:
            pytest.skip("Target column 'Exited' not found")
        
        # Prepare features (use only numeric for simplicity)
        numeric_features = ['CreditScore', 'Age', 'Tenure', 'Balance', 
                           'NumOfProducts', 'HasCrCard', 'IsActiveMember']
        
        X = df_sample[numeric_features]
        y = df_sample['Exited']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        model = RandomForestClassifier(n_estimators=10, random_state=42, max_depth=5)
        model.fit(X_train, y_train)
        
        # Verify model can make predictions
        predictions = model.predict(X_test)
        assert len(predictions) == len(X_test), "Should produce prediction for each sample"
        assert set(predictions).issubset({0, 1}), "Predictions should be binary"
        
        # Check basic accuracy (should be better than random)
        accuracy = (predictions == y_test).mean()
        assert accuracy > 0.5, f"Accuracy ({accuracy:.2f}) should be better than random"
    
    def test_model_produces_probability_scores(self):
        """Test that model can produce probability scores"""
        from src.data_ingestion import DataIngestorCSV
        from sklearn.model_selection import train_test_split
        from sklearn.ensemble import RandomForestClassifier
        
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data not available: {data_path}")
        
        # Load and prepare data
        ingestor = DataIngestorCSV()
        df = ingestor.ingest(data_path)
        df_sample = df.head(500).dropna()
        
        if 'Exited' not in df_sample.columns:
            pytest.skip("Target column 'Exited' not found")
        
        numeric_features = ['CreditScore', 'Age', 'Tenure', 'Balance']
        X = df_sample[numeric_features]
        y = df_sample['Exited']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        
        # Get probability scores
        probabilities = model.predict_proba(X_test)
        
        assert probabilities.shape[0] == len(X_test), "Should have proba for each sample"
        assert probabilities.shape[1] == 2, "Should have proba for both classes"
        assert (probabilities >= 0).all() and (probabilities <= 1).all(), "Probas should be in [0,1]"
        assert abs(probabilities.sum(axis=1) - 1.0).max() < 0.01, "Probas should sum to 1"

