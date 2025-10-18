"""
Centralized SparkSession management for the churn prediction pipeline.
Provides consistent Spark configuration across all modules with S3A support.
"""

import logging
from typing import Optional
from pyspark.sql import SparkSession
import sys
import os
sys.path.append(os.path.dirname(__file__))
from config import get_aws_region, get_s3_kms_arn

logger = logging.getLogger(__name__)


def _ms(val, default_ms):
    """Convert timeout values to milliseconds, handling 's' suffix"""
    # Accept "60s" style or "60000"
    if isinstance(val, str) and val.lower().endswith("s"):
        try:
            return str(int(float(val[:-1]) * 1000))
        except Exception:
            return str(default_ms)
    try:
        return str(int(val))
    except Exception:
        return str(default_ms)


def create_spark_session(
    app_name: str = "ChurnPredictionPipeline",
    master: str = "local[*]",
    config_options: Optional[dict] = None
) -> SparkSession:
    """
    Create or get an existing SparkSession with optimized configuration.
    
    Args:
        app_name: Name of the Spark application
        master: Spark master URL (default: local mode with all cores)
        config_options: Additional Spark configuration options
        
    Returns:
        SparkSession: Configured SparkSession instance
    """
    try:
        # Get AWS configuration
        aws_region = get_aws_region()
        kms_key_arn = get_s3_kms_arn()
        
        # Base configuration for optimal performance
        builder = SparkSession.builder \
            .appName(app_name) \
            .master(master) \
            .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.6,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.adaptive.skewJoin.enabled", "true") \
            .config("spark.sql.adaptive.localShuffleReader.enabled", "true") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .config("spark.sql.execution.arrow.pyspark.fallback.enabled", "true") \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .config("spark.sql.shuffle.partitions", "200") \
            .config("spark.sql.parquet.compression.codec", "snappy") \
            .config("spark.sql.parquet.mergeSchema", "false") \
            .config("spark.sql.parquet.filterPushdown", "true") \
            .config("spark.sql.csv.parser.columnPruning.enabled", "true") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.hadoop.fs.s3a.fast.upload", "true") \
            .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.EnvironmentVariableCredentialsProvider,com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
            .config("spark.hadoop.fs.s3a.endpoint", f"s3.{aws_region}.amazonaws.com") \
            .config("spark.hadoop.fs.s3a.connection.timeout", "60000") \
            .config("spark.hadoop.fs.s3a.connection.establish.timeout", "60000") \
            .config("spark.hadoop.fs.s3a.socket.timeout", "60000") \
            .config("spark.hadoop.fs.s3a.attempts.maximum", "20") \
            .config("spark.hadoop.fs.s3a.retry.limit", "20") \
            .config("spark.hadoop.fs.s3a.retry.interval", "1000") \
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "true") \
            .config("spark.hadoop.fs.s3a.threads.max", "10") \
            .config("spark.hadoop.fs.s3a.threads.core", "15") \
            .config("spark.hadoop.fs.s3a.threads.keepalivetime", "60000") \
            .config("spark.hadoop.fs.s3a.max.total.tasks", "5") \
            .config("spark.hadoop.fs.s3a.connection.ttl", "86400000") \
            .config("spark.hadoop.fs.s3a.multipart.purge.age", "86400000") \
            .config("spark.hadoop.fs.s3a.multipart.threshold", "67108864") \
            .config("spark.hadoop.fs.s3a.multipart.size", "67108864")
        
        # Add S3 encryption if KMS key is configured
        if kms_key_arn:
            builder = builder \
                .config("spark.hadoop.fs.s3a.server-side-encryption-algorithm", "SSE-KMS") \
                .config("spark.hadoop.fs.s3a.server-side-encryption.key", kms_key_arn)
        
        # Apply additional configuration if provided
        if config_options:
            for key, value in config_options.items():
                builder = builder.config(key, value)
        
        # Create or get existing session
        spark = builder.getOrCreate()
        
        # Set log level to reduce verbosity
        spark.sparkContext.setLogLevel("WARN")
        
        logger.info(f"✓ SparkSession created/retrieved: {app_name}")
        logger.info(f"  • Spark Version: {spark.version}")
        logger.info(f"  • Master: {spark.sparkContext.master}")
        logger.info(f"  • Default Parallelism: {spark.sparkContext.defaultParallelism}")
        
        return spark
        
    except Exception as e:
        logger.error(f"✗ Failed to create SparkSession: {str(e)}")
        raise


def stop_spark_session(spark: SparkSession) -> None:
    """
    Safely stop a SparkSession.
    
    Args:
        spark: SparkSession instance to stop
    """
    try:
        if spark and hasattr(spark, 'stop'):
            spark.stop()
            logger.info("✓ SparkSession stopped successfully")
    except Exception as e:
        logger.error(f"✗ Error stopping SparkSession: {str(e)}")


def get_spark_session_info(spark: SparkSession) -> dict:
    """
    Get information about the current SparkSession.
    
    Args:
        spark: Active SparkSession instance
        
    Returns:
        dict: Session information including version, config, etc.
    """
    try:
        info = {
            "version": spark.version,
            "app_name": spark.conf.get("spark.app.name"),
            "master": spark.sparkContext.master,
            "default_parallelism": spark.sparkContext.defaultParallelism,
            "executor_memory": spark.conf.get("spark.executor.memory", "default"),
            "executor_cores": spark.conf.get("spark.executor.cores", "default"),
            "adaptive_enabled": spark.conf.get("spark.sql.adaptive.enabled"),
            "arrow_enabled": spark.conf.get("spark.sql.execution.arrow.pyspark.enabled")
        }
        return info
    except Exception as e:
        logger.error(f"✗ Error getting SparkSession info: {str(e)}")
        return {}


def configure_spark_for_ml(spark: SparkSession) -> SparkSession:
    """
    Configure SparkSession specifically for ML workloads.
    
    Args:
        spark: Existing SparkSession instance
        
    Returns:
        SparkSession: Configured SparkSession
    """
    try:
        # ML-specific optimizations
        spark.conf.set("spark.ml.tuning.parallelism", "4")
        spark.conf.set("spark.sql.execution.arrow.maxRecordsPerBatch", "10000")
        spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10485760")  # 10MB
        
        logger.info("✓ SparkSession configured for ML workloads")
        return spark
        
    except Exception as e:
        logger.error(f"✗ Error configuring Spark for ML: {str(e)}")
        return spark


# Global session management (optional)
_global_spark_session = None


def get_or_create_spark_session(
    app_name: str = "ChurnPredictionPipeline",
    **kwargs
) -> SparkSession:
    """
    Get existing global SparkSession or create a new one.
    
    Args:
        app_name: Name of the Spark application
        **kwargs: Additional arguments for create_spark_session
        
    Returns:
        SparkSession: Active SparkSession instance
    """
    global _global_spark_session
    
    if _global_spark_session is None or _global_spark_session._jsc is None:
        _global_spark_session = create_spark_session(app_name, **kwargs)
    
    return _global_spark_session
