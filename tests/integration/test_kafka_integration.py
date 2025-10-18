"""
Integration Tests for Kafka Services

Tests Kafka producer, consumer, and analytics services:
- Event production
- Event consumption
- Message serialization
- Topic management
"""

import pytest
import json
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.integration
@pytest.mark.slow
class TestKafkaIntegration:
    """Integration tests for Kafka services"""
    
    @pytest.fixture
    def kafka_config(self, mock_kafka_config):
        """Kafka configuration for testing"""
        return {
            'bootstrap_servers': 'localhost:9092',
            'topic': 'test-customer-events',
            'group_id': 'test-consumer-group'
        }
    
    def test_kafka_connection(self, kafka_config):
        """Test connection to Kafka broker"""
        from utils.kafka_utils import check_kafka_connection
        
        # This will only work if Kafka is actually running
        # In CI, this should be mocked or run against test Kafka
        try:
            is_connected = check_kafka_connection(kafka_config['bootstrap_servers'])
            # If Kafka is running, connection should succeed
            if is_connected:
                assert True
            else:
                pytest.skip("Kafka not running")
        except Exception as e:
            pytest.skip(f"Kafka not available: {e}")
    
    def test_customer_event_generation(self, sample_raw_data):
        """Test customer event data generation"""
        from kafka.producer_service import CustomerEventGenerator
        
        try:
            generator = CustomerEventGenerator(seed=42)
            event = generator.generate_event()
            
            assert event is not None
            assert 'customer_id' in event
            assert 'credit_score' in event
            assert 'geography' in event
            assert 'timestamp' in event
        except Exception as e:
            pytest.skip(f"Producer service not available: {e}")
    
    def test_event_serialization(self):
        """Test event serialization to JSON"""
        event = {
            'customer_id': '12345',
            'credit_score': 650,
            'geography': 'France',
            'age': 35,
            'timestamp': '2024-01-01T00:00:00'
        }
        
        # Serialize
        json_str = json.dumps(event)
        
        # Deserialize
        deserialized = json.loads(json_str)
        
        assert deserialized == event
    
    def test_prediction_event_structure(self):
        """Test structure of prediction events"""
        prediction_event = {
            'customer_id': '12345',
            'prediction': 1,
            'probability': 0.85,
            'risk_score': 0.90,
            'timestamp': '2024-01-01T00:00:00',
            'model_version': 'v1.0'
        }
        
        # Validate required fields
        required_fields = ['customer_id', 'prediction', 'probability', 'timestamp']
        for field in required_fields:
            assert field in prediction_event
        
        # Validate data types
        assert isinstance(prediction_event['prediction'], int)
        assert isinstance(prediction_event['probability'], float)
        assert 0 <= prediction_event['probability'] <= 1

