#!/usr/bin/env python3
"""
Simple Model Performance Validation for CI/CD

Validates model against locally saved artifacts (no S3 needed).
This script runs after data and training pipelines generate artifacts.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, confusion_matrix
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import load_config

# Load config for thresholds
CONFIG = load_config()
if CONFIG and 'model_validation' in CONFIG:
    THRESHOLDS = CONFIG['model_validation']['performance_thresholds']
else:
    # Fallback defaults
    THRESHOLDS = {
        'accuracy': 0.75,      # HARD REQUIREMENT
        'precision': 0.65,
        'recall': 0.65,
        'f1_score': 0.60
    }

print("=" * 70)
print("🎯 MODEL PERFORMANCE VALIDATION")
print("=" * 70)
print()
print(f"📋 Performance Thresholds:")
print(f"   • Accuracy:  >= {THRESHOLDS['accuracy']:.2%} (HARD REQUIREMENT)")
print(f"   • Precision: >= {THRESHOLDS['precision']:.2%}")
print(f"   • Recall:    >= {THRESHOLDS['recall']:.2%}")
print(f"   • F1 Score:  >= {THRESHOLDS['f1_score']:.2%}")
print()


def load_artifacts():
    """Load model and test data from local artifacts"""
    print("📦 Loading artifacts from local storage...")
    
    # Paths to artifacts
    model_path = project_root / "artifacts" / "models" / "best_model.pkl"
    test_data_path = project_root / "artifacts" / "data" / "test_data.pkl"
    
    # Check if artifacts exist
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        print("   Run training pipeline first: make train-pipeline")
        sys.exit(1)
    
    if not test_data_path.exists():
        print(f"❌ Test data not found: {test_data_path}")
        print("   Run data+training pipeline first")
        sys.exit(1)
    
    # Load model
    print(f"   ✅ Loading model: {model_path}")
    model = joblib.load(model_path)
    
    # Load test data
    print(f"   ✅ Loading test data: {test_data_path}")
    test_data = joblib.load(test_data_path)
    
    return model, test_data


def calculate_metrics(y_true, y_pred, y_proba=None):
    """Calculate all performance metrics"""
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'f1_score': f1_score(y_true, y_pred, zero_division=0),
    }
    
    # Add ROC-AUC if probabilities available
    if y_proba is not None:
        try:
            metrics['roc_auc'] = roc_auc_score(y_true, y_proba)
        except:
            metrics['roc_auc'] = None
    
    return metrics


def validate_performance(metrics):
    """Check if metrics meet thresholds"""
    print()
    print("=" * 70)
    print("📊 MODEL PERFORMANCE METRICS")
    print("=" * 70)
    print()
    
    results = {}
    all_passed = True
    
    for metric_name, threshold in THRESHOLDS.items():
        metric_value = metrics.get(metric_name, 0.0)
        passed = metric_value >= threshold
        results[metric_name] = {
            'value': metric_value,
            'threshold': threshold,
            'passed': passed
        }
        
        # Emoji indicators
        status = "✅" if passed else "❌"
        
        # Highlight Accuracy
        if metric_name == 'accuracy':
            print(f"   {status} {metric_name.upper()}: {metric_value:.2%} (threshold: {threshold:.2%}) ⚠️ HARD REQUIREMENT")
        else:
            print(f"   {status} {metric_name.capitalize()}: {metric_value:.2%} (threshold: {threshold:.2%})")
        
        if not passed:
            all_passed = False
    
    # Add ROC-AUC if available (no threshold)
    if 'roc_auc' in metrics and metrics['roc_auc'] is not None:
        print(f"   ℹ️  ROC-AUC: {metrics['roc_auc']:.2%} (no threshold)")
    
    print()
    results['all_passed'] = all_passed
    return results


def save_report(metrics, validation_results):
    """Save validation report"""
    report_path = project_root / "reports" / "model_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        'metrics': {k: float(v) for k, v in metrics.items() if v is not None},
        'thresholds': THRESHOLDS,
        'validation': {
            k: {
                'value': float(v['value']),
                'threshold': float(v['threshold']),
                'passed': v['passed']
            }
            for k, v in validation_results.items()
            if k != 'all_passed'
        },
        'all_passed': validation_results['all_passed']
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"💾 Report saved: {report_path}")
    print()


def main():
    """Main validation logic"""
    try:
        # Load artifacts
        model, test_data = load_artifacts()
        
        # Extract test features and labels
        X_test = test_data['X_test']
        y_test = test_data['y_test']
        
        print()
        print(f"📊 Test data shape: {X_test.shape}")
        print(f"   • Features: {X_test.shape[1]}")
        print(f"   • Samples:  {X_test.shape[0]}")
        print()
        
        # Make predictions
        print("🔮 Making predictions...")
        y_pred = model.predict(X_test)
        
        # Get probabilities if available
        y_proba = None
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test)[:, 1]
        
        print("   ✅ Predictions complete")
        
        # Calculate metrics
        metrics = calculate_metrics(y_test, y_pred, y_proba)
        
        # Validate against thresholds
        validation_results = validate_performance(metrics)
        
        # Save report
        save_report(metrics, validation_results)
        
        # Final verdict
        print("=" * 70)
        if validation_results['all_passed']:
            print("🎉 MODEL VALIDATION PASSED!")
            print("   ✅ All performance metrics meet thresholds")
            print("   ✅ Model ready for deployment")
        else:
            print("❌ MODEL VALIDATION FAILED!")
            print("   ⚠️  Performance below acceptable thresholds")
            print("   ⚠️  Deployment BLOCKED")
            print()
            print("📋 Actions Required:")
            print("   1. Review model training logs")
            print("   2. Check for data quality issues")
            print("   3. Adjust hyperparameters or features")
            print("   4. Retrain model")
            print()
            print("🔄 To revert to previous model:")
            print("   - Use the last passing model from S3")
            print("   - Or adjust thresholds in config.yaml (not recommended)")
        print("=" * 70)
        print()
        
        # Exit with appropriate code
        sys.exit(0 if validation_results['all_passed'] else 1)
        
    except Exception as e:
        print()
        print(f"❌ Validation error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

