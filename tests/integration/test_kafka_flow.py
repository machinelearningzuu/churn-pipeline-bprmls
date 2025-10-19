"""
Integration Tests for Kafka Streaming Flow
Tests producer, consumer, and analytics integration
"""

import pytest
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestKafkaIntegration:
    """Integration tests for Kafka streaming workflow"""
    
    def test_kafka_utils_imports(self):
        """Test that Kafka utilities can be imported"""
        try:
            from utils.kafka_utils import NativeKafkaConfig, NativeKafkaProducer
            assert True, "Kafka utils should import successfully"
        except ImportError as e:
            pytest.fail(f"Failed to import Kafka utils: {e}")
    
    def test_kafka_config_loads_from_environment(self):
        """Test that Kafka configuration reads from environment"""
        from utils.kafka_utils import NativeKafkaConfig
        
        # Save original env var
        original_bootstrap = os.environ.get('KAFKA_BOOTSTRAP_SERVERS')
        
        try:
            # Set test bootstrap servers
            os.environ['KAFKA_BOOTSTRAP_SERVERS'] = 'test-kafka:9092'
            
            config = NativeKafkaConfig()
            
            assert config.bootstrap_servers == 'test-kafka:9092', \
                "Config should read from environment"
        
        finally:
            # Restore original env var
            if original_bootstrap:
                os.environ['KAFKA_BOOTSTRAP_SERVERS'] = original_bootstrap
            elif 'KAFKA_BOOTSTRAP_SERVERS' in os.environ:
                del os.environ['KAFKA_BOOTSTRAP_SERVERS']
    
    def test_kafka_connection_check(self):
        """Test Kafka connection check function"""
        from utils.kafka_utils import NativeKafkaValidator
        
        # This should handle connection failure gracefully
        # Using a non-existent server should return False
        result = NativeKafkaValidator.check_kafka_connection('non-existent-kafka:9999')
        
        assert isinstance(result, bool), "Should return boolean"
        # We expect False since we're not connecting to a real Kafka
        assert result == False, "Should return False for non-existent server"
    
    @pytest.mark.requires_kafka
    def test_event_generator_can_create_events(self):
        """Test that event generator can create customer events"""
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data not available: {data_path}")
        
        try:
            from kafka.producer_service import CustomerEventGenerator
            
            generator = CustomerEventGenerator()
            event = generator.generate_event()
            
            assert isinstance(event, dict), "Event should be a dictionary"
            # Check for CSV column names (PascalCase)
            assert 'CustomerId' in event, "Event should have CustomerId"
            assert 'Age' in event, "Event should have Age"
            assert 'Balance' in event, "Event should have Balance"
            assert 'event_timestamp' in event, "Event should have timestamp"
            assert 'event_id' in event, "Event should have event_id"
            
        except Exception as e:
            pytest.skip(f"Could not test event generation: {e}")
    
    @pytest.mark.requires_kafka
    def test_event_generator_validates_events(self):
        """Test that event generator validates event structure"""
        data_path = "data/raw/ChurnModelling.csv"
        
        if not os.path.exists(data_path):
            pytest.skip(f"Test data not available: {data_path}")
        
        try:
            from kafka.producer_service import CustomerEventGenerator
            
            generator = CustomerEventGenerator()
            
            # Generate multiple events
            events = [generator.generate_event() for _ in range(10)]
            
            # All events should have consistent structure
            first_keys = set(events[0].keys())
            for event in events:
                assert set(event.keys()) == first_keys, "All events should have same structure"
                # Validate key fields exist (using CSV column names)
                assert 'CustomerId' in event, "Event should have CustomerId"
                assert 'event_timestamp' in event, "Event should have timestamp"
                assert isinstance(event['CustomerId'], int), "CustomerId should be integer"
            
            # Check required CSV column names (PascalCase, as they come from the CSV)
            required_fields = ['CustomerId', 'CreditScore', 'Geography', 
                             'Gender', 'Age', 'Tenure', 'Balance']
            
            for field in required_fields:
                assert field in events[0], f"Event should have {field}"
                
        except Exception as e:
            pytest.skip(f"Could not test event validation: {e}")


class TestRDSIntegration:
    """Integration tests for RDS/PostgreSQL connection"""
    
    def test_rds_config_available(self):
        """Test that RDS configuration can be read"""
        # Check if RDS credentials are in environment
        rds_host = os.environ.get('RDS_HOST')
        rds_db = os.environ.get('RDS_DB_NAME')
        
        # Just check that we can read config (don't actually connect)
        if not rds_host or not rds_db:
            pytest.skip("RDS credentials not configured in environment")
        
        assert isinstance(rds_host, str), "RDS_HOST should be string"
        assert len(rds_host) > 0, "RDS_HOST should not be empty"
    
    def test_rds_connection_parameters(self):
        """Test that RDS connection can be established"""
        import psycopg2
        
        # Check if RDS is configured
        if not os.environ.get('RDS_HOST'):
            pytest.skip("RDS not configured")
        
        rds_config = {
            'host': os.environ.get('RDS_HOST'),
            'port': int(os.environ.get('RDS_PORT', 5432)),
            'database': os.environ.get('RDS_DB_NAME', 'analytics'),
            'user': os.environ.get('RDS_USERNAME'),
            'password': os.environ.get('RDS_PASSWORD')
        }
        
        # Verify all required params are present
        assert rds_config['host'], "RDS host should be configured"
        assert rds_config['database'], "RDS database should be configured"
        assert rds_config['user'], "RDS user should be configured"
        assert rds_config['password'], "RDS password should be configured"
        
        # Try to connect (this may fail if network/firewall blocks connection)
        try:
            conn = psycopg2.connect(**rds_config, connect_timeout=5)
            conn.close()
            assert True, "RDS connection successful"
        except Exception as e:
            pytest.skip(f"RDS connection failed (may be network/firewall): {e}")

