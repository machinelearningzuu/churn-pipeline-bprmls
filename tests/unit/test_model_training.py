"""
Unit Tests for Model Training Module

Tests model training functionality including:
- Model initialization
- Training process
- Hyperparameter validation
- Model serialization
"""

import pytest
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.model_training import ModelTrainer


@pytest.mark.unit
class TestModelTraining:
    """Test suite for model training"""
    
    def test_model_initialization(self):
        """Test model initialization with default parameters"""
        trainer = ModelTrainer(model_type='random_forest')
        
        assert trainer.model is not None
        assert trainer.model_type == 'random_forest'
    
    def test_train_random_forest(self, sample_features_labels):
        """Test training a Random Forest model"""
        X, y = sample_features_labels
        
        trainer = ModelTrainer(model_type='random_forest')
        trainer.train(X, y)
        
        assert trainer.model is not None
        assert hasattr(trainer.model, 'predict')
    
    def test_train_xgboost(self, sample_features_labels):
        """Test training an XGBoost model"""
        X, y = sample_features_labels
        
        trainer = ModelTrainer(model_type='xgboost')
        trainer.train(X, y)
        
        assert trainer.model is not None
        assert hasattr(trainer.model, 'predict')
    
    def test_train_logistic_regression(self, sample_features_labels):
        """Test training a Logistic Regression model"""
        X, y = sample_features_labels
        
        trainer = ModelTrainer(model_type='logistic')
        trainer.train(X, y)
        
        assert trainer.model is not None
        assert hasattr(trainer.model, 'predict')
    
    def test_predict(self, sample_features_labels):
        """Test model prediction"""
        X, y = sample_features_labels
        
        trainer = ModelTrainer(model_type='random_forest')
        trainer.train(X, y)
        
        predictions = trainer.predict(X)
        
        assert len(predictions) == len(X)
        assert set(predictions).issubset({0, 1})
    
    def test_predict_proba(self, sample_features_labels):
        """Test probability prediction"""
        X, y = sample_features_labels
        
        trainer = ModelTrainer(model_type='random_forest')
        trainer.train(X, y)
        
        probabilities = trainer.predict_proba(X)
        
        assert probabilities.shape == (len(X), 2)
        assert np.all(probabilities >= 0)
        assert np.all(probabilities <= 1)
        assert np.allclose(probabilities.sum(axis=1), 1)
    
    def test_model_save_load(self, sample_features_labels, tmp_path):
        """Test model serialization and deserialization"""
        X, y = sample_features_labels
        
        # Train and save model
        trainer = ModelTrainer(model_type='random_forest')
        trainer.train(X, y)
        
        model_path = tmp_path / "model.pkl"
        trainer.save_model(str(model_path))
        
        assert model_path.exists()
        
        # Load model and verify
        loaded_trainer = ModelTrainer(model_type='random_forest')
        loaded_trainer.load_model(str(model_path))
        
        # Predictions should be the same
        original_pred = trainer.predict(X)
        loaded_pred = loaded_trainer.predict(X)
        
        assert np.array_equal(original_pred, loaded_pred)
    
    def test_feature_importance(self, sample_features_labels):
        """Test feature importance extraction"""
        X, y = sample_features_labels
        
        trainer = ModelTrainer(model_type='random_forest')
        trainer.train(X, y)
        
        importances = trainer.get_feature_importance()
        
        assert importances is not None
        assert len(importances) == X.shape[1]
        assert all(importances >= 0)
    
    def test_invalid_model_type(self):
        """Test handling of invalid model type"""
        with pytest.raises(ValueError):
            ModelTrainer(model_type='invalid_model')
    
    def test_train_without_data(self):
        """Test that training without data raises error"""
        trainer = ModelTrainer(model_type='random_forest')
        
        with pytest.raises(ValueError):
            trainer.train(None, None)

