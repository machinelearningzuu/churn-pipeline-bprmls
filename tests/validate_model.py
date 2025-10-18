#!/usr/bin/env python3
"""
Model Performance Validation Script for CI/CD

Validates model performance against minimum thresholds:
- F1 Score >= 75%
- Accuracy >= 75%
- Precision >= 70%
- Recall >= 70%

If model doesn't meet thresholds, prevents deployment and reverts to previous model.

Exit codes:
- 0: Model meets all thresholds (deploy)
- 1: Model fails thresholds (block deployment)
"""

import sys
import os
import pickle
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ==========================================
# Performance Thresholds
# ==========================================

THRESHOLDS = {
    'f1_score': 0.75,        # Primary metric (HARD REQUIREMENT)
    'accuracy': 0.75,
    'precision': 0.70,
    'recall': 0.70,
    'roc_auc': 0.75
}


# ==========================================
# Validation Functions
# ==========================================

def load_model(model_path):
    """Load trained model"""
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        print(f"✅ Loaded model from: {model_path}")
        return model
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        sys.exit(1)


def load_test_data(data_path):
    """Load test dataset"""
    try:
        data = pd.read_pickle(data_path)
        print(f"✅ Loaded test data: {data_path}")
        return data
    except Exception as e:
        print(f"❌ Failed to load test data: {e}")
        sys.exit(1)


def evaluate_model(model, X_test, y_test):
    """Evaluate model performance"""
    print("\n🔍 Evaluating model performance...")
    
    try:
        # Get predictions
        y_pred = model.predict(X_test)
        
        # Get probabilities if available
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test)[:, 1]
        else:
            y_proba = y_pred
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 0.0
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Classification report
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        
        return metrics, cm, report
        
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def check_thresholds(metrics):
    """Check if metrics meet minimum thresholds"""
    print("\n🎯 Checking performance thresholds...")
    
    passed = True
    results = {}
    
    for metric_name, threshold in THRESHOLDS.items():
        value = metrics.get(metric_name, 0.0)
        meets_threshold = value >= threshold
        
        emoji = "✅" if meets_threshold else "❌"
        status = "PASS" if meets_threshold else "FAIL"
        
        print(f"   {emoji} {metric_name}: {value:.4f} (threshold: {threshold:.2f}) - {status}")
        
        results[metric_name] = {
            'value': value,
            'threshold': threshold,
            'passed': meets_threshold
        }
        
        if not meets_threshold:
            passed = False
            
            # F1 score is CRITICAL - must meet this
            if metric_name == 'f1_score':
                print(f"\n🔴 CRITICAL: F1 Score {value:.2%} below minimum {threshold:.2%}")
                print("   This model CANNOT be deployed!")
    
    return passed, results


def print_confusion_matrix(cm):
    """Print formatted confusion matrix"""
    print("\n📊 Confusion Matrix:")
    print("                 Predicted")
    print("                 0      1")
    print(f"   Actual  0  [{cm[0][0]:5d}  {cm[0][1]:5d}]")
    print(f"           1  [{cm[1][0]:5d}  {cm[1][1]:5d}]")
    
    # Calculate metrics from confusion matrix
    tn, fp, fn, tp = cm.ravel()
    
    print(f"\n   True Negatives:  {tn:5d}")
    print(f"   False Positives: {fp:5d}")
    print(f"   False Negatives: {fn:5d}")
    print(f"   True Positives:  {tp:5d}")


def compare_with_previous_model(current_metrics, previous_model_path=None):
    """Compare current model with previous deployed model"""
    if previous_model_path is None or not Path(previous_model_path).exists():
        print("\n ℹ️  No previous model found for comparison")
        return None
    
    try:
        print(f"\n📊 Comparing with previous model...")
        
        # Load previous metrics (assuming they're saved)
        metrics_file = Path(previous_model_path).parent / 'metrics.json'
        
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                previous_metrics = json.load(f)
            
            print("\n   Metric Comparison:")
            print("   " + "-" * 60)
            print(f"   {'Metric':<15} {'Previous':<12} {'Current':<12} {'Change':<12}")
            print("   " + "-" * 60)
            
            for metric_name in ['f1_score', 'accuracy', 'precision', 'recall', 'roc_auc']:
                prev_val = previous_metrics.get(metric_name, 0.0)
                curr_val = current_metrics.get(metric_name, 0.0)
                change = curr_val - prev_val
                
                emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                
                print(f"   {metric_name:<15} {prev_val:<12.4f} {curr_val:<12.4f} "
                      f"{emoji} {change:+.4f}")
            
            return previous_metrics
        else:
            print("   ⚠️  Previous metrics file not found")
            return None
            
    except Exception as e:
        print(f"   ⚠️  Error comparing models: {e}")
        return None


def generate_report(metrics, threshold_results, cm, report, output_path='reports/model_validation_report.json'):
    """Generate detailed validation report"""
    report_dir = Path(output_path).parent
    report_dir.mkdir(parents=True, exist_ok=True)
    
    validation_report = {
        'timestamp': datetime.now().isoformat(),
        'metrics': {k: float(v) for k, v in metrics.items()},
        'thresholds': threshold_results,
        'confusion_matrix': cm.tolist(),
        'classification_report': report,
        'deployment_approved': all(r['passed'] for r in threshold_results.values())
    }
    
    with open(output_path, 'w') as f:
        json.dump(validation_report, f, indent=2)
    
    print(f"\n💾 Validation report saved: {output_path}")
    
    return validation_report


# ==========================================
# Main Execution
# ==========================================

def main():
    """Main validation function"""
    print("=" * 70)
    print("🎯 MODEL PERFORMANCE VALIDATION")
    print("=" * 70)
    
    # Get paths from command line arguments or use defaults
    model_path = sys.argv[1] if len(sys.argv) > 1 else 'artifacts/models/best_model.pkl'
    test_data_path = sys.argv[2] if len(sys.argv) > 2 else 'artifacts/data/test_data.pkl'
    previous_model_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"\n📁 Model: {model_path}")
    print(f"📁 Test Data: {test_data_path}")
    
    if not Path(model_path).exists():
        print(f"❌ Model file not found: {model_path}")
        sys.exit(1)
    
    if not Path(test_data_path).exists():
        print(f"❌ Test data file not found: {test_data_path}")
        sys.exit(1)
    
    # Load model and data
    model = load_model(model_path)
    test_data = load_test_data(test_data_path)
    
    # Separate features and labels
    if isinstance(test_data, dict):
        X_test = test_data['X_test']
        y_test = test_data['y_test']
    elif isinstance(test_data, tuple):
        X_test, y_test = test_data
    else:
        print("❌ Unexpected test data format")
        sys.exit(1)
    
    print(f"   Test samples: {len(X_test)}")
    print(f"   Features: {X_test.shape[1]}")
    print(f"   Churn rate: {y_test.mean():.2%}")
    
    # Evaluate model
    metrics, cm, report = evaluate_model(model, X_test, y_test)
    
    # Print metrics
    print("\n📊 Performance Metrics:")
    print(f"   Accuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"   Precision: {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
    print(f"   Recall:    {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
    print(f"   F1 Score:  {metrics['f1_score']:.4f} ({metrics['f1_score']*100:.2f}%)")
    print(f"   ROC-AUC:   {metrics['roc_auc']:.4f}")
    
    # Print confusion matrix
    print_confusion_matrix(cm)
    
    # Check thresholds
    passed, threshold_results = check_thresholds(metrics)
    
    # Compare with previous model
    compare_with_previous_model(metrics, previous_model_path)
    
    # Generate report
    validation_report = generate_report(metrics, threshold_results, cm, report)
    
    # Final decision
    print("\n" + "=" * 70)
    print("🎯 VALIDATION DECISION")
    print("=" * 70)
    
    if passed:
        print("\n✅ MODEL APPROVED FOR DEPLOYMENT")
        print(f"   F1 Score: {metrics['f1_score']:.2%} >= {THRESHOLDS['f1_score']:.2%}")
        print(f"   All metrics meet minimum thresholds")
        print("\n🚀 Proceeding with deployment...")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n❌ MODEL REJECTED - DOES NOT MEET REQUIREMENTS")
        print(f"   F1 Score: {metrics['f1_score']:.2%} < {THRESHOLDS['f1_score']:.2%}")
        
        failed_metrics = [k for k, v in threshold_results.items() if not v['passed']]
        print(f"   Failed metrics: {', '.join(failed_metrics)}")
        
        print("\n🔄 REVERTING TO PREVIOUS MODEL")
        print("   Deployment blocked to maintain system quality")
        print("   Please retrain model or adjust thresholds")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()

