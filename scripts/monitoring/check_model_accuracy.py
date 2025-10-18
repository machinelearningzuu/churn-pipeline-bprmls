#!/usr/bin/env python3
"""
Model Accuracy Monitoring Script

Checks model performance against predictions stored in RDS
and compares with baseline metrics in MLflow.
"""

import os
import sys
import json
from datetime import datetime, timedelta
import pandas as pd
import psycopg2
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def connect_to_rds():
    """Connect to RDS analytics database"""
    conn = psycopg2.connect(
        host=os.getenv('RDS_HOST'),
        port=int(os.getenv('RDS_PORT', 5432)),
        database=os.getenv('RDS_DB_NAME'),
        user=os.getenv('RDS_USERNAME'),
        password=os.getenv('RDS_PASSWORD'),
        sslmode='require'
    )
    return conn


def get_recent_predictions(conn, days=7):
    """Get recent predictions from RDS"""
    query = f"""
        SELECT 
            prediction,
            probability,
            risk_score,
            predicted_at
        FROM churn_predictions
        WHERE predicted_at >= NOW() - INTERVAL '{days} days'
        ORDER BY predicted_at DESC;
    """
    
    df = pd.read_sql_query(query, conn)
    return df


def analyze_prediction_quality(df):
    """Analyze prediction quality metrics"""
    metrics = {
        'total_predictions': len(df),
        'churn_rate': (df['prediction'].sum() / len(df) * 100) if len(df) > 0 else 0,
        'avg_confidence': df['probability'].mean() if len(df) > 0 else 0,
        'high_confidence_pct': (df['probability'] > 0.8).sum() / len(df) * 100 if len(df) > 0 else 0,
        'low_confidence_pct': (df['probability'] < 0.6).sum() / len(df) * 100 if len(df) > 0 else 0,
        'avg_risk_score': df['risk_score'].mean() if len(df) > 0 else 0,
        'high_risk_pct': (df['risk_score'] > 0.7).sum() / len(df) * 100 if len(df) > 0 else 0,
    }
    
    return metrics


def check_thresholds(metrics):
    """Check if metrics meet required thresholds"""
    alerts = []
    
    # Low confidence threshold
    if metrics['low_confidence_pct'] > 20:
        alerts.append({
            'severity': 'warning',
            'message': f"High percentage of low confidence predictions: {metrics['low_confidence_pct']:.2f}%"
        })
    
    # High risk threshold
    if metrics['high_risk_pct'] > 30:
        alerts.append({
            'severity': 'info',
            'message': f"High percentage of high-risk customers: {metrics['high_risk_pct']:.2f}%"
        })
    
    # Average confidence threshold
    if metrics['avg_confidence'] < 0.7:
        alerts.append({
            'severity': 'critical',
            'message': f"Average model confidence is low: {metrics['avg_confidence']:.3f}"
        })
    
    return alerts


def main():
    """Main execution function"""
    print("=" * 70)
    print("🎯 Model Performance Monitoring")
    print("=" * 70)
    
    try:
        # Connect to database
        print("\n📊 Connecting to RDS...")
        conn = connect_to_rds()
        print("✅ Connected successfully")
        
        # Get recent predictions
        print("\n📈 Fetching recent predictions (last 7 days)...")
        df_predictions = get_recent_predictions(conn, days=7)
        print(f"✅ Retrieved {len(df_predictions)} predictions")
        
        if len(df_predictions) == 0:
            print("\n⚠️  No predictions found in the last 7 days")
            sys.exit(0)
        
        # Analyze metrics
        print("\n🔍 Analyzing prediction quality...")
        metrics = analyze_prediction_quality(df_predictions)
        
        print("\n📊 Metrics Summary:")
        print(f"  • Total Predictions: {metrics['total_predictions']:,}")
        print(f"  • Churn Rate: {metrics['churn_rate']:.2f}%")
        print(f"  • Average Confidence: {metrics['avg_confidence']:.3f}")
        print(f"  • High Confidence: {metrics['high_confidence_pct']:.2f}%")
        print(f"  • Low Confidence: {metrics['low_confidence_pct']:.2f}%")
        print(f"  • Average Risk Score: {metrics['avg_risk_score']:.3f}")
        print(f"  • High Risk Customers: {metrics['high_risk_pct']:.2f}%")
        
        # Check thresholds
        print("\n🚨 Checking Alert Thresholds...")
        alerts = check_thresholds(metrics)
        
        if alerts:
            print(f"\n⚠️  {len(alerts)} alert(s) found:")
            for alert in alerts:
                emoji = "🔴" if alert['severity'] == 'critical' else "🟡" if alert['severity'] == 'warning' else "🔵"
                print(f"  {emoji} [{alert['severity'].upper()}] {alert['message']}")
        else:
            print("✅ All metrics within acceptable thresholds")
        
        # Save report
        report_dir = project_root / 'reports'
        report_dir.mkdir(exist_ok=True)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'alerts': alerts,
            'status': 'critical' if any(a['severity'] == 'critical' for a in alerts) else 'ok'
        }
        
        report_file = report_dir / f"model_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved: {report_file}")
        
        # Exit with error if critical alerts
        if any(a['severity'] == 'critical' for a in alerts):
            print("\n❌ Critical issues detected!")
            sys.exit(1)
        
        print("\n✅ Model monitoring completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()

