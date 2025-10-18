"""
Feature encoding strategies for PySpark DataFrames.
Supports nominal encoding (object, object) and ordinal encoding.
"""

import logging
import os
import json
from enum import Enum
from typing import Dict, List, Optional, Union
from abc import ABC, abstractmethod
import pandas as pd

# Manual PySpark availability flag - set to False to prioritize pandas
PYSPARK_AVAILABLE = False  # Set to True to enable PySpark, False for pandas-only

# Conditional PySpark imports
if PYSPARK_AVAILABLE:
    try:
        from pyspark.sql import DataFrame as SparkDataFrame, SparkSession
        from pyspark.sql import functions as F
        from pyspark.ml.feature import object, object, IndexToString
        from pyspark.ml import Pipeline
        from utils.spark_session import get_or_create_spark_session
    except ImportError:
        PYSPARK_AVAILABLE = False
        SparkDataFrame = None
        SparkSession = None
else:
    SparkDataFrame = None
    SparkSession = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FeatureEncodingStrategy(ABC):
    """Abstract base class for feature encoding strategies."""
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize with SparkSession."""
        self.spark = spark or get_or_create_spark_session()
    
    @abstractmethod
    def encode(self, df: Union[pd.DataFrame, object]) -> Union[pd.DataFrame, object]:
        """
        Encode features in the DataFrame.
        
        Args:
            df: PySpark DataFrame
            
        Returns:
            DataFrame with encoded features
        """
        pass


class VariableType(str, Enum):
    """Enumeration of variable types."""
    NOMINAL = 'nominal'
    ORDINAL = 'ordinal'


class NominalEncodingStrategy(FeatureEncodingStrategy):
    """
    Nominal encoding strategy using object.
    Creates numeric indices for categorical values.
    """
    
    def __init__(self, nominal_columns: List[str], one_hot: bool = False, spark: Optional[SparkSession] = None):
        """
        Initialize nominal encoding strategy.
        
        Args:
            nominal_columns: List of column names to encode
            one_hot: Whether to apply one-hot encoding after indexing
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.nominal_columns = nominal_columns
        self.one_hot = one_hot
        self.encoder_dicts = {}
        self.indexers = {}
        self.encoders = {}
        # Encoders will be saved to S3, no local directory needed
        logger.info(f"NominalEncodingStrategy initialized for columns: {nominal_columns}")
        logger.info(f"One-hot encoding: {one_hot}")
    
    def encode(self, df: Union[pd.DataFrame, object]) -> Union[pd.DataFrame, object]:
        """
        Apply nominal encoding to specified columns.
        
        Args:
            df: PySpark DataFrame
            
        Returns:
            DataFrame with encoded columns
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"NOMINAL ENCODING (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Starting nominal encoding for {len(self.nominal_columns)} columns")
        
        df_encoded = df
        stages = []
        
        for column in self.nominal_columns:
            logger.info(f"\n--- Processing column: {column} ---")
            
            # Check for missing values
            missing_count = df_encoded.filter(F.col(column).isNull()).count()
            if missing_count > 0:
                logger.warning(f"  ⚠ Column has {missing_count} missing values before encoding")
                # Fill missing values with a placeholder
                df_encoded = df_encoded.fillna({column: "MISSING"})
            
            # Get unique values
            unique_values = df_encoded.select(column).distinct().count()
            logger.info(f"  Unique values: {unique_values}")
            
            # Create object
            indexer = object(
                inputCol=column,
                outputCol=f"{column}_index",
                handleInvalid="keep"  # Keeps unseen labels as index = numLabels
            )
            
            # Fit the indexer
            indexer_model = indexer.fit(df_encoded)
            self.indexers[column] = indexer_model
            
            # Get the mapping
            labels = indexer_model.labels
            encoder_dict = {label: idx for idx, label in enumerate(labels)}
            self.encoder_dicts[column] = encoder_dict
            
            import inspect
            frame = inspect.currentframe()
            pipeline_timestamp = None
            
            # Try to get pipeline_timestamp from calling function
            try:
                caller_locals = frame.f_back.f_back.f_locals
                if 'pipeline_timestamp' in caller_locals:
                    pipeline_timestamp = caller_locals['pipeline_timestamp']
            except:
                pass
            
            if pipeline_timestamp is None:
                from datetime import datetime
                pipeline_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Try to save to S3, fallback to local if credentials not available
            try:
                encoder_s3_key = f"artifacts/data_artifacts/{pipeline_timestamp}/{column}_encoder.json"
                
                # Import S3 utilities
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
                from s3_io import put_bytes
                
                encoder_json = json.dumps(encoder_dict, indent=2).encode('utf-8')
                put_bytes(encoder_json, key=encoder_s3_key, content_type='application/json')
                logger.info(f"  ✓ Saved encoder to s3://{encoder_s3_key}")
                
            except Exception as s3_error:
                logger.error(f"❌ S3 encoder save failed: {s3_error}")
                logger.error("💡 Please check your AWS credentials and S3 bucket configuration")
                raise s3_error
            
            # Apply indexing
            df_encoded = indexer_model.transform(df_encoded)
            
            if self.one_hot:
                # Apply one-hot encoding
                encoder = object(
                    inputCol=f"{column}_index",
                    outputCol=f"{column}_vec"
                )
                encoder_model = encoder.fit(df_encoded)
                self.encoders[column] = encoder_model
                df_encoded = encoder_model.transform(df_encoded)
                
                # Drop intermediate index column and original column
                df_encoded = df_encoded.drop(column, f"{column}_index")
                logger.info(f"  ✓ Applied one-hot encoding to column '{column}'")
            else:
                # Replace original column with index
                df_encoded = df_encoded.drop(column).withColumnRenamed(f"{column}_index", column)
                logger.info(f"  ✓ Successfully encoded column '{column}' with {len(labels)} categories")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ NOMINAL ENCODING COMPLETE")
        logger.info(f"{'='*60}\n")
        return df_encoded
    
    def get_encoder_dicts(self) -> Dict[str, Dict[str, int]]:
        """Get the encoder dictionaries for all columns."""
        return self.encoder_dicts
    
    def get_indexers(self) -> Dict[str, object]:
        """Get the fitted object models."""
        return self.indexers


class OrdinalEncodingStrategy(FeatureEncodingStrategy):
    """
    Ordinal encoding strategy with custom ordering.
    Maps categorical values to ordered numeric values.
    """
    
    def __init__(self, ordinal_mappings: Dict[str, Dict[str, int]], spark: Optional[SparkSession] = None):
        """
        Initialize ordinal encoding strategy.
        
        Args:
            ordinal_mappings: Dictionary mapping column names to value->order mappings
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.ordinal_mappings = ordinal_mappings
        logger.info(f"OrdinalEncodingStrategy initialized for columns: {list(ordinal_mappings.keys())}")
    
    def encode(self, df: Union[pd.DataFrame, object]) -> Union[pd.DataFrame, object]:
        """
        Apply ordinal encoding to specified columns.
        
        Args:
            df: PySpark DataFrame
            
        Returns:
            DataFrame with encoded columns
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"ORDINAL ENCODING (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Starting ordinal encoding for {len(self.ordinal_mappings)} columns")
        
        df_encoded = df
        
        for column, mapping in self.ordinal_mappings.items():
            logger.info(f"\n--- Processing column: {column} ---")
            logger.info(f"  Mapping: {mapping}")
            
            # Get initial value distribution
            value_counts = df_encoded.groupBy(column).count().collect()
            initial_dist = {row[column]: row['count'] for row in value_counts}
            logger.info(f"  Before encoding: {initial_dist}")
            
            # Check for missing values
            missing_count = df_encoded.filter(F.col(column).isNull()).count()
            if missing_count > 0:
                logger.warning(f"  ⚠ Column has {missing_count} missing values before encoding")
            
            # Create mapping expression
            mapping_expr = F.when(F.col(column).isNull(), None)
            for value, code in mapping.items():
                mapping_expr = mapping_expr.when(F.col(column) == value, code)
            
            # Apply mapping
            df_encoded = df_encoded.withColumn(f"{column}_encoded", mapping_expr)
            
            # Check for unmapped values
            unmapped_count = df_encoded.filter(
                F.col(f"{column}_encoded").isNull() & F.col(column).isNotNull()
            ).count()
            if unmapped_count > 0:
                logger.warning(f"  ⚠ Column has {unmapped_count} unmapped values after encoding")
                # Optionally handle unmapped values
                df_encoded = df_encoded.withColumn(
                    f"{column}_encoded",
                    F.when(
                        F.col(f"{column}_encoded").isNull() & F.col(column).isNotNull(),
                        -1  # Default value for unmapped
                    ).otherwise(F.col(f"{column}_encoded"))
                )
            
            # Replace original column
            df_encoded = df_encoded.drop(column).withColumnRenamed(f"{column}_encoded", column)
            
            # Log encoded value distribution
            encoded_counts = df_encoded.groupBy(column).count().collect()
            encoded_dist = {row[column]: row['count'] for row in encoded_counts}
            logger.info(f"  ✓ Encoded with {len(mapping)} categories")
            logger.info(f"  After encoding: {encoded_dist}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ ORDINAL ENCODING COMPLETE")
        logger.info(f"{'='*60}\n")
        return df_encoded


class OneHotEncodingStrategy(FeatureEncodingStrategy):
    """
    One-hot encoding strategy for categorical variables.
    Creates binary columns for each category.
    """
    
    def __init__(self, categorical_columns: List[str], max_categories: int = 50, 
                 spark: Optional[SparkSession] = None):
        """
        Initialize one-hot encoding strategy.
        
        Args:
            categorical_columns: List of column names to encode
            max_categories: Maximum number of categories to encode per column
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.categorical_columns = categorical_columns
        self.max_categories = max_categories
        logger.info(f"OneHotEncodingStrategy initialized for columns: {categorical_columns}")
    
    def encode(self, df: Union[pd.DataFrame, object]) -> Union[pd.DataFrame, object]:
        """
        Apply one-hot encoding to specified columns.
        
        Args:
            df: PySpark DataFrame
            
        Returns:
            DataFrame with one-hot encoded columns
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"ONE-HOT ENCODING (PySpark)")
        logger.info(f"{'='*60}")
        
        df_encoded = df
        
        for column in self.categorical_columns:
            # Get unique values
            unique_count = df_encoded.select(column).distinct().count()
            
            if unique_count > self.max_categories:
                logger.warning(f"Column {column} has {unique_count} categories, exceeding max {self.max_categories}")
                continue
            
            # Use object + object
            indexer = object(inputCol=column, outputCol=f"{column}_index")
            encoder = object(inputCol=f"{column}_index", outputCol=f"{column}_vec")
            
            # Create pipeline
            pipeline = Pipeline(stages=[indexer, encoder])
            pipeline_model = pipeline.fit(df_encoded)
            df_encoded = pipeline_model.transform(df_encoded)
            
            # Drop intermediate columns
            df_encoded = df_encoded.drop(column, f"{column}_index")
            
            logger.info(f"✓ One-hot encoded column '{column}' with {unique_count} categories")
        
        logger.info(f"✓ ONE-HOT ENCODING COMPLETE")
        logger.info(f"{'='*60}\n")
        return df_encoded