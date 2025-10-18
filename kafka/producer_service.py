#!/usr/bin/env python3
"""
Simplified Kafka Producer for ML Pipeline
Streams real customer data for churn prediction
"""

import json
import logging
import time
import random
import argparse
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.kafka_utils import NativeKafkaProducer, validate_native_setup, create_topic, NativeKafkaConfig, check_kafka_connection
from utils.config import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomerEventGenerator:
    """Generate customer events from real ChurnModelling.csv dataset"""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
        
        # Load customer dataset
        # In Docker, data is at /app/data/raw; locally it's in project_root/data/raw
        in_docker = os.path.exists('/.dockerenv') or os.environ.get('RUNNING_IN_DOCKER') == 'true'
        if in_docker:
            data_path = '/app/data/raw/ChurnModelling.csv'
        else:
            data_path = os.path.join(project_root, 'data/raw/ChurnModelling.csv')
        self.dataset = pd.read_csv(data_path).dropna()
        
        # Remove target variable for streaming
        if 'Exited' in self.dataset.columns:
            self.features = self.dataset.drop('Exited', axis=1)
            self.labels = self.dataset['Exited']
        else:
            self.features = self.dataset.copy()
            self.labels = None
            
        logger.info(f"Loaded {len(self.dataset)} customer records")
    
    def generate_event(self) -> Dict[str, Any]:
        """Generate single customer event"""
        # Sample random customer
        idx = random.randint(0, len(self.features) - 1)
        row = self.features.iloc[idx]
        
        # Convert to JSON-serializable format
        event = {}
        for col, value in row.items():
            if pd.isna(value):
                event[col] = None
            elif isinstance(value, (np.integer, np.int64)):
                event[col] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                event[col] = float(value)
            else:
                event[col] = str(value)
        
        # Add metadata
        event.update({
            'event_timestamp': datetime.utcnow().isoformat(),
            'event_id': f"evt_{idx}_{int(time.time())}",
            'true_churn_label': int(self.labels.iloc[idx]) if self.labels is not None else None
        })
        
        return event
    
    def generate_batch(self, num_events: int) -> List[Dict[str, Any]]:
        """Generate batch of events"""
        return [self.generate_event() for _ in range(num_events)]


class MLKafkaProducer:
    """Simplified ML Kafka Producer"""
    
    def __init__(self, enable_logging: bool = True):
        # In Docker, validate connection only; native setup check not needed
        in_docker = os.path.exists('/.dockerenv') or os.environ.get('RUNNING_IN_DOCKER') == 'true'
        
        if not in_docker:
            validation = validate_native_setup()
            if not validation['setup_valid']:
                raise RuntimeError("Kafka setup invalid")
        else:
            # In Docker, just check connection using standalone function
            if not check_kafka_connection():
                bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
                raise RuntimeError(f"Cannot connect to Kafka at {bootstrap_servers}")
        
        self.producer = NativeKafkaProducer()
        self.generator = CustomerEventGenerator()
        self.enable_logging = enable_logging
        
        if enable_logging:
            print("\n📊 KAFKA ML PRODUCER")
            print("=" * 60)
    
    def _log_event(self, event: Dict[str, Any], success: bool, count: int):
        """Log event if logging enabled"""
        if not self.enable_logging:
            return
            
        status = "✅" if success else "❌"
        customer_id = str(event.get('CustomerId', 'N/A'))[:8]
        geography = str(event.get('Geography', 'N/A'))[:5]
        age = str(event.get('Age', 'N/A'))[:2]
        
        print(f"{status} Event {count:3d}: Customer {customer_id} | {geography} | Age {age}")
    
    def setup_topic(self) -> bool:
        """Setup customer events topic"""
        return create_topic('customer-events', partitions=1, replication_factor=1)
    
    def produce_batch(self, topic: str = 'customer-events', num_events: int = 100) -> int:
        """Produce batch of events"""
        logger.info(f"📦 Producing {num_events} events")
        
        events = self.generator.generate_batch(num_events)
        successful = 0
        
        for i, event in enumerate(events):
            success = self.producer.send_message(
                topic=topic,
                message=event,
                key=str(event['CustomerId'])
            )
            
            if success:
                successful += 1
            
            self._log_event(event, success, i + 1)
            
            if (i + 1) % 50 == 0:
                logger.info(f"📊 Sent {successful}/{i+1} events")
        
        if self.enable_logging:
            print("=" * 60)
            print(f"✅ Batch completed: {successful}/{num_events} events sent")
        
        logger.info(f"✅ Batch completed: {successful}/{num_events} events")
        return successful
    
    def produce_stream(self, topic: str = 'customer-events', 
                      rate: int = 1, duration: int = 300) -> int:
        """Produce streaming events"""
        logger.info(f"🌊 Streaming {rate} events/sec for {duration}s")
        
        start_time = time.time()
        total_events = 0
        successful = 0
        
        try:
            while time.time() - start_time < duration:
                batch_start = time.time()
                
                # Send events for this second
                for _ in range(rate):
                    event = self.generator.generate_event()
                    
                    success = self.producer.send_message(
                        topic=topic,
                        message=event,
                        key=str(event['CustomerId'])
                    )
                    
                    total_events += 1
                    if success:
                        successful += 1
                    
                    self._log_event(event, success, total_events)
                
                # Progress logging every 30 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 30 == 0 and elapsed > 0:
                    rate_actual = successful / elapsed
                    logger.info(f"📈 Progress: {successful} events, rate: {rate_actual:.1f}/sec")
                
                # Maintain target rate
                sleep_time = max(0, 1.0 - (time.time() - batch_start))
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            if self.enable_logging:
                print("=" * 60)
                print(f"✅ Streaming completed: {successful}/{total_events} events")
            
            logger.info(f"✅ Streaming completed: {successful}/{total_events} events")
            return successful
            
        except KeyboardInterrupt:
            logger.info("🛑 Streaming stopped by user")
            return successful
    
    def close(self):
        """Close producer"""
        self.producer.close()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Kafka Producer for ML Pipeline")
    parser.add_argument('--mode', choices=['streaming', 'batch'], default='streaming')
    parser.add_argument('--topic', default='customer-events')
    parser.add_argument('--rate', type=int, default=1, help='Events per second')
    parser.add_argument('--duration', type=int, default=300, help='Duration in seconds')
    parser.add_argument('--num-events', type=int, default=100, help='Number of events')
    parser.add_argument('--setup-topics', action='store_true')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--quiet', action='store_true', help='Disable event logging')
    
    args = parser.parse_args()
    
    try:
        # Validate if requested
        if args.validate:
            validation = validate_native_setup()
            if validation['setup_valid']:
                logger.info("✅ Kafka setup valid")
                return 0
            else:
                logger.error("❌ Kafka setup invalid")
                return 1
        
        # Initialize producer
        producer = MLKafkaProducer(enable_logging=not args.quiet)
        
        # Setup topics if requested
        if args.setup_topics:
            if producer.setup_topic():
                logger.info("✅ Topic setup completed")
            else:
                logger.error("❌ Topic setup failed")
                return 1
        
        # Execute based on mode
        if args.mode == 'streaming':
            producer.produce_stream(args.topic, args.rate, args.duration)
        else:  # batch
            producer.produce_batch(args.topic, args.num_events)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return 1
    finally:
        if 'producer' in locals():
            producer.close()


if __name__ == "__main__":
    exit(main())
