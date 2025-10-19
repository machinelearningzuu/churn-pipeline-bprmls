#!/usr/bin/env python3
"""
Kafka Analytics Service
Consumes predictions from Kafka and writes analytics to RDS PostgreSQL
"""

import json
import logging
import os
import sys
import time
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any
from collections import defaultdict

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from confluent_kafka import Consumer, KafkaError
from utils.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# Kafka configuration
KAFKA_CONFIG = config.get('kafka', {})
PREDICTIONS_TOPIC = KAFKA_CONFIG.get('topics', {}).get('predictions', 'churn-predictions')
BOOTSTRAP_SERVERS = KAFKA_CONFIG.get('bootstrap_servers', os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'))

# RDS configuration
RDS_CONFIG = config.get('rds', {})
RDS_HOST = RDS_CONFIG.get('host', os.getenv('RDS_HOST'))
RDS_PORT = RDS_CONFIG.get('port', int(os.getenv('RDS_PORT', 5432)))
RDS_DB = RDS_CONFIG.get('database', os.getenv('RDS_DB_NAME'))
RDS_USER = RDS_CONFIG.get('username', os.getenv('RDS_USERNAME'))
RDS_PASSWORD = RDS_CONFIG.get('password', os.getenv('RDS_PASSWORD'))

# Analytics configuration
ANALYTICS_CONFIG = config.get('analytics', {})
AGGREGATION_INTERVAL = ANALYTICS_CONFIG.get('aggregation_interval', 3600)  # 1 hour
HIGH_RISK_THRESHOLD = ANALYTICS_CONFIG.get('high_risk_threshold', 0.7)


class ChurnAnalyticsService:
    """Real-time churn prediction analytics service"""
    
    def __init__(self):
        self.db_conn = None
        self.last_hourly_aggregation = None
        self.last_daily_aggregation = None
        
    def initialize(self):
        """Initialize database connection"""
        try:
            logger.info("=" * 60)
            logger.info("INITIALIZING CHURN ANALYTICS SERVICE")
            logger.info("=" * 60)
            
            if not all([RDS_HOST, RDS_DB, RDS_USER, RDS_PASSWORD]):
                logger.error("❌ RDS credentials not configured")
                return False
            
            logger.info(f"Connecting to RDS: {RDS_HOST}:{RDS_PORT}/{RDS_DB}")
            self.db_conn = psycopg2.connect(
                host=RDS_HOST,
                port=RDS_PORT,
                database=RDS_DB,
                user=RDS_USER,
                password=RDS_PASSWORD
            )
            self.db_conn.autocommit = True
            logger.info("✅ RDS connection established")
            
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {str(e)}")
            return False
    
    def process_prediction(self, prediction: Dict[str, Any]):
        """
        Process individual prediction:
        1. Already written by consumer to churn_predictions
        2. Check if high-risk and write alert
        """
        try:
            risk_score = prediction.get('risk_score', 0.0)
            
            # High-risk alert
            if risk_score >= HIGH_RISK_THRESHOLD:
                self.write_high_risk_alert(prediction)
                
        except Exception as e:
            logger.error(f"Failed to process prediction: {e}")
    
    def ensure_connection(self):
        """Ensure database connection is alive, reconnect if needed"""
        try:
            # Check if connection exists and is alive
            if self.db_conn is None or self.db_conn.closed:
                logger.warning("⚠️  Database connection lost, reconnecting...")
                self.db_conn = psycopg2.connect(
                    host=RDS_HOST,
                    port=RDS_PORT,
                    database=RDS_DB,
                    user=RDS_USER,
                    password=RDS_PASSWORD
                )
                self.db_conn.autocommit = True
                logger.info("✅ Database connection restored")
                return True
            
            # Test connection with a simple query
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure connection: {e}")
            # Try to reconnect
            try:
                self.db_conn = psycopg2.connect(
                    host=RDS_HOST,
                    port=RDS_PORT,
                    database=RDS_DB,
                    user=RDS_USER,
                    password=RDS_PASSWORD
                )
                self.db_conn.autocommit = True
                logger.info("✅ Database connection restored")
                return True
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect: {reconnect_error}")
                return False
    
    def write_high_risk_alert(self, prediction: Dict[str, Any]):
        """Write high-risk customer alert to RDS"""
        try:
            # Ensure connection is alive
            if not self.ensure_connection():
                logger.error("Cannot write high-risk alert: no database connection")
                return
            
            cursor = self.db_conn.cursor()
            
            insert_query = """
                INSERT INTO high_risk_customers (
                    customer_id, risk_score, geography, gender, age, balance, detected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id, detected_at) 
                DO UPDATE SET risk_score = EXCLUDED.risk_score
            """
            
            cursor.execute(insert_query, (
                prediction.get('customer_id'),
                prediction.get('risk_score'),
                prediction.get('geography'),
                prediction.get('gender'),
                prediction.get('age'),
                prediction.get('balance'),
                datetime.utcnow()
            ))
            
            cursor.close()
            logger.info(f"🚨 High-risk alert: Customer {prediction.get('customer_id')} (risk: {prediction.get('risk_score'):.3f})")
            
        except Exception as e:
            logger.error(f"Failed to write high-risk alert: {e}")
    
    def aggregate_hourly_metrics(self):
        """Aggregate hourly metrics from churn_predictions table"""
        try:
            # Ensure connection is alive
            if not self.ensure_connection():
                logger.error("Cannot aggregate hourly metrics: no database connection")
                return
            
            cursor = self.db_conn.cursor()
            
            # Get current hour
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            
            # Check if already aggregated
            if self.last_hourly_aggregation == current_hour:
                return
            
            # Aggregate from churn_predictions
            aggregate_query = """
                INSERT INTO churn_metrics_hourly (
                    hour_timestamp, total_predictions, churn_count, churn_rate,
                    avg_risk_score, high_risk_count, avg_age, avg_balance, avg_tenure
                )
                SELECT 
                    DATE_TRUNC('hour', predicted_at) as hour_timestamp,
                    COUNT(*) as total_predictions,
                    SUM(prediction) as churn_count,
                    ROUND((SUM(prediction)::float / COUNT(*)::float * 100)::numeric, 2) as churn_rate,
                    ROUND(AVG(risk_score)::numeric, 4) as avg_risk_score,
                    SUM(CASE WHEN risk_score >= %s THEN 1 ELSE 0 END) as high_risk_count,
                    ROUND(AVG(age)::numeric, 1) as avg_age,
                    ROUND(AVG(balance)::numeric, 2) as avg_balance,
                    ROUND(AVG(tenure)::numeric, 1) as avg_tenure
                FROM churn_predictions
                WHERE predicted_at >= %s AND predicted_at < %s
                GROUP BY DATE_TRUNC('hour', predicted_at)
                ON CONFLICT (hour_timestamp) 
                DO UPDATE SET
                    total_predictions = EXCLUDED.total_predictions,
                    churn_count = EXCLUDED.churn_count,
                    churn_rate = EXCLUDED.churn_rate,
                    avg_risk_score = EXCLUDED.avg_risk_score,
                    high_risk_count = EXCLUDED.high_risk_count,
                    avg_age = EXCLUDED.avg_age,
                    avg_balance = EXCLUDED.avg_balance,
                    avg_tenure = EXCLUDED.avg_tenure
            """
            
            hour_start = current_hour - timedelta(hours=1)
            cursor.execute(aggregate_query, (HIGH_RISK_THRESHOLD, hour_start, current_hour))
            
            cursor.close()
            self.last_hourly_aggregation = current_hour
            logger.info(f"📊 Hourly metrics aggregated for {hour_start.strftime('%Y-%m-%d %H:00')}")
            
        except Exception as e:
            logger.error(f"Failed to aggregate hourly metrics: {e}")
    
    def aggregate_daily_metrics(self):
        """Aggregate daily metrics from churn_predictions table"""
        try:
            # Ensure connection is alive
            if not self.ensure_connection():
                logger.error("Cannot aggregate daily metrics: no database connection")
                return
            
            cursor = self.db_conn.cursor()
            
            # Get current date
            current_date = datetime.utcnow().date()
            
            # Check if already aggregated today
            if self.last_daily_aggregation == current_date:
                return
            
            # Aggregate from churn_predictions
            aggregate_query = """
                INSERT INTO churn_metrics_daily (
                    date, total_predictions, churn_count, churn_rate,
                    avg_risk_score, high_risk_count, avg_age, avg_balance, avg_tenure
                )
                SELECT 
                    DATE(predicted_at) as date,
                    COUNT(*) as total_predictions,
                    SUM(prediction) as churn_count,
                    ROUND((SUM(prediction)::float / COUNT(*)::float * 100)::numeric, 2) as churn_rate,
                    ROUND(AVG(risk_score)::numeric, 4) as avg_risk_score,
                    SUM(CASE WHEN risk_score >= %s THEN 1 ELSE 0 END) as high_risk_count,
                    ROUND(AVG(age)::numeric, 1) as avg_age,
                    ROUND(AVG(balance)::numeric, 2) as avg_balance,
                    ROUND(AVG(tenure)::numeric, 1) as avg_tenure
                FROM churn_predictions
                WHERE DATE(predicted_at) = %s
                GROUP BY DATE(predicted_at)
                ON CONFLICT (date) 
                DO UPDATE SET
                    total_predictions = EXCLUDED.total_predictions,
                    churn_count = EXCLUDED.churn_count,
                    churn_rate = EXCLUDED.churn_rate,
                    avg_risk_score = EXCLUDED.avg_risk_score,
                    high_risk_count = EXCLUDED.high_risk_count,
                    avg_age = EXCLUDED.avg_age,
                    avg_balance = EXCLUDED.avg_balance,
                    avg_tenure = EXCLUDED.avg_tenure
            """
            
            yesterday = current_date - timedelta(days=1)
            cursor.execute(aggregate_query, (HIGH_RISK_THRESHOLD, yesterday))
            
            cursor.close()
            self.last_daily_aggregation = current_date
            logger.info(f"📊 Daily metrics aggregated for {yesterday.strftime('%Y-%m-%d')}")
            
        except Exception as e:
            logger.error(f"Failed to aggregate daily metrics: {e}")
    
    def run_continuous(self):
        """Run continuous analytics processing"""
        logger.info("=" * 60)
        logger.info("🔄 STARTING CONTINUOUS ANALYTICS")
        logger.info(f"Predictions Topic: {PREDICTIONS_TOPIC}")
        logger.info(f"High-risk Threshold: {HIGH_RISK_THRESHOLD}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Configure consumer
        consumer_config = {
            'bootstrap.servers': BOOTSTRAP_SERVERS,
            'group.id': 'churn-analytics',
            'auto.offset.reset': 'latest',
            'enable.auto.commit': True
        }
        
        consumer = Consumer(consumer_config)
        consumer.subscribe([PREDICTIONS_TOPIC])
        
        total_processed = 0
        last_aggregation_check = time.time()
        
        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                
                if msg is None:
                    # No message, check if time to aggregate
                    if time.time() - last_aggregation_check >= 300:  # Every 5 minutes
                        self.aggregate_hourly_metrics()
                        self.aggregate_daily_metrics()
                        last_aggregation_check = time.time()
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Consumer error: {msg.error()}")
                    continue
                
                try:
                    prediction = json.loads(msg.value().decode('utf-8'))
                    self.process_prediction(prediction)
                    total_processed += 1
                    
                    if total_processed % 100 == 0:
                        logger.info(f"📈 Processed {total_processed} predictions")
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode message: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue
                
        except KeyboardInterrupt:
            logger.info(f"\n🛑 Analytics service stopped")
            logger.info(f"Total processed: {total_processed} predictions")
        finally:
            consumer.close()
    
    def close(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
        logger.info("✅ Analytics service shutdown complete")


def main():
    """Main function"""
    try:
        logger.info("🚀 KAFKA CHURN ANALYTICS SERVICE")
        
        service = ChurnAnalyticsService()
        if not service.initialize():
            return 1
        
        service.run_continuous()
        return 0
        
    except Exception as e:
        logger.error(f"❌ Analytics service failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    finally:
        if 'service' in locals():
            service.close()


if __name__ == "__main__":
    exit(main())
