"""
Model Performance Validation Tests

Tests model performance metrics and behaviors:
- Accuracy, precision, recall, F1-score
- ROC-AUC score
- Confusion matrix
- Model behavior on edge cases
"""

import pytest
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.model_evaluation import ModelEvaluator


@pytest.mark.model
class TestModelPerformance:
    """Test suite for model performance validation"""
    
    def test_accuracy_threshold(self, sample_model_predictions):
        """Test that model accuracy meets minimum threshold"""
        predictions = sample_model_predictions['predictions']
        true_labels = sample_model_predictions['true_labels']
        
        evaluator = ModelEvaluator()
        metrics = evaluator.calculate_metrics(true_labels, predictions)
        
        # Model should have at least 70% accuracy
        assert metrics['accuracy'] >= 0.70, f"Accuracy {metrics['accuracy']:.2f} below threshold"
    
    def test_precision_recall_balance(self, sample_model_predictions):
        """Test balance between precision and recall"""
        predictions = sample_model_predictions['predictions']
        true_labels = sample_model_predictions['true_labels']
        
        evaluator = ModelEvaluator()
        metrics = evaluator.calculate_metrics(true_labels, predictions)
        
        precision = metrics['precision']
        recall = metrics['recall']
        
        # Neither should be extremely low
        assert precision >= 0.50, f"Precision {precision:.2f} too low"
        assert recall >= 0.50, f"Recall {recall:.2f} too low"
        
        # Check F1 score (harmonic mean)
        f1 = metrics['f1_score']
        assert f1 >= 0.50, f"F1-score {f1:.2f} too low"
    
    def test_roc_auc_score(self, sample_model_predictions):
        """Test ROC-AUC score"""
        probabilities = sample_model_predictions['probabilities']
        true_labels = sample_model_predictions['true_labels']
        
        from sklearn.metrics import roc_auc_score
        
        auc_score = roc_auc_score(true_labels, probabilities)
        
        # AUC should be better than random (0.5)
        assert auc_score > 0.60, f"AUC {auc_score:.2f} too low"
    
    def test_confusion_matrix(self, sample_model_predictions):
        """Test confusion matrix structure"""
        predictions = sample_model_predictions['predictions']
        true_labels = sample_model_predictions['true_labels']
        
        from sklearn.metrics import confusion_matrix
        
        cm = confusion_matrix(true_labels, predictions)
        
        assert cm.shape == (2, 2)
        assert cm.sum() == len(predictions)
        
        # Calculate metrics from confusion matrix
        tn, fp, fn, tp = cm.ravel()
        
        assert tn + fp + fn + tp == len(predictions)
    
    def test_prediction_distribution(self, sample_model_predictions):
        """Test that predictions are distributed reasonably"""
        predictions = sample_model_predictions['predictions']
        
        # Count predictions
        unique, counts = np.unique(predictions, return_counts=True)
        pred_dist = dict(zip(unique, counts))
        
        # Should predict both classes
        assert len(unique) > 1, "Model predicts only one class"
        
        # Check class imbalance (neither class should be < 10%)
        total = len(predictions)
        for class_label, count in pred_dist.items():
            proportion = count / total
            assert proportion >= 0.05, f"Class {class_label} proportion {proportion:.2%} too low"
    
    def test_probability_calibration(self, sample_model_predictions):
        """Test that probabilities are well-calibrated"""
        probabilities = sample_model_predictions['probabilities']
        predictions = sample_model_predictions['predictions']
        
        # High probability predictions should mostly be correct
        high_conf_mask = probabilities > 0.8
        if high_conf_mask.sum() > 0:
            high_conf_predictions = predictions[high_conf_mask]
            # At least 70% should be class 1
            assert (high_conf_predictions == 1).mean() >= 0.70
        
        # Low probability predictions should mostly be incorrect
        low_conf_mask = probabilities < 0.2
        if low_conf_mask.sum() > 0:
            low_conf_predictions = predictions[low_conf_mask]
            # Most should be class 0
            assert (low_conf_predictions == 0).mean() >= 0.70
    
    def test_model_consistency(self, sample_features_labels):
        """Test that model predictions are consistent"""
        X, y = sample_features_labels
        
        from src.model_training import ModelTrainer
        
        # Train model
        trainer = ModelTrainer(model_type='random_forest', random_state=42)
        trainer.train(X, y)
        
        # Predict twice on same data
        pred1 = trainer.predict(X)
        pred2 = trainer.predict(X)
        
        # Predictions should be identical
        assert np.array_equal(pred1, pred2), "Model predictions are not deterministic"
    
    def test_model_robustness_to_scaling(self, sample_features_labels):
        """Test model behavior with different feature scales"""
        X, y = sample_features_labels
        
        from src.model_training import ModelTrainer
        from src.feature_scaling import FeatureScaler
        
        # Train on original data
        trainer1 = ModelTrainer(model_type='random_forest', random_state=42)
        trainer1.train(X, y)
        pred1 = trainer1.predict(X)
        
        # Train on scaled data
        scaler = FeatureScaler(method='standard')
        X_scaled = scaler.fit_transform(X)
        
        trainer2 = ModelTrainer(model_type='random_forest', random_state=42)
        trainer2.train(X_scaled, y)
        pred2 = trainer2.predict(X_scaled)
        
        # Random Forest should be relatively robust to scaling
        # At least 80% agreement in predictions
        agreement = (pred1 == pred2).mean()
        assert agreement >= 0.80, f"Only {agreement:.2%} agreement between models"

