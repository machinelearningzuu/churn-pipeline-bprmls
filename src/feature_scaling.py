"""
Feature scaling strategies for PySpark DataFrames.
Supports object and object transformations.
"""

import logging
from enum import Enum
from typing import List, Optional, Union, Dict
from abc import ABC, abstractmethod
import pandas as pd
# Manual PySpark availability flag - set to False to prioritize pandas
PYSPARK_AVAILABLE = False  # Set to True to enable PySpark, False for pandas-only

# Conditional PySpark imports
if PYSPARK_AVAILABLE:
    try:
        from pyspark.sql import DataFrame as SparkDataFrame, SparkSession
        from pyspark.sql import functions as F
        from pyspark.ml.feature import object, object, VectorAssembler
        from pyspark.ml import Pipeline
    except ImportError:
        PYSPARK_AVAILABLE = False
        SparkDataFrame = None
        SparkSession = None
else:
    SparkDataFrame = None
    SparkSession = None
from utils.spark_session import get_or_create_spark_session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FeatureScalingStrategy(ABC):
    """Abstract base class for feature scaling strategies."""
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize with SparkSession."""
        self.spark = spark or get_or_create_spark_session()
        self.fitted_model = None
    
    @abstractmethod
    def scale(self, df: Union[pd.DataFrame, object], columns_to_scale: List[str]) -> Union[pd.DataFrame, object]:
        """
        Scale specified columns in the DataFrame.
        
        Args:
            df: PySpark DataFrame
            columns_to_scale: List of column names to scale
            
        Returns:
            DataFrame with scaled features
        """
        pass


class ScalingType(str, Enum):
    """Enumeration of scaling types."""
    MINMAX = 'minmax'
    STANDARD = 'standard'


class MinMaxScalingStrategy(FeatureScalingStrategy):
    """Min-Max scaling strategy to scale features to [0, 1] range."""
    
    def __init__(self, output_col_suffix: str = "_scaled", spark: Optional[SparkSession] = None):
        """
        Initialize Min-Max scaling strategy.
        
        Args:
            output_col_suffix: Suffix to add to scaled column names
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.output_col_suffix = output_col_suffix
        self.scaler_models = {}
        logger.info("MinMaxScalingStrategy initialized (PySpark)")
    
    def scale(self, df: Union[pd.DataFrame, object], columns_to_scale: List[str]) -> Union[pd.DataFrame, object]:
        """
        Apply Min-Max scaling to specified columns.
        
        Args:
            df: PySpark DataFrame
            columns_to_scale: List of column names to scale
            
        Returns:
            DataFrame with scaled columns
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"FEATURE SCALING - MIN-MAX (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f'Starting Min-Max scaling for {len(columns_to_scale)} columns: {columns_to_scale}')
        
        # Log statistics before scaling
        logger.info(f"\nStatistics BEFORE scaling:")
        for col in columns_to_scale:
            stats = df.select(
                F.min(col).alias('min'),
                F.max(col).alias('max'),
                F.mean(col).alias('mean'),
                F.stddev(col).alias('std')
            ).collect()[0]
            
            logger.info(f"  {col}: Min={stats['min']:.2f}, Max={stats['max']:.2f}, "
                       f"Mean={stats['mean']:.2f}, Std={stats['std']:.2f}")
        
        df_scaled = df
        
        # Scale each column individually to maintain column structure
        for col in columns_to_scale:
            # Create a vector column for this feature
            vector_col = f"{col}_vec"
            assembler = VectorAssembler(inputCols=[col], outputCol=vector_col)
            
            # Create object
            scaled_vec_col = f"{col}_scaled_vec"
            scaler = object(inputCol=vector_col, outputCol=scaled_vec_col)
            
            # Create pipeline
            pipeline = Pipeline(stages=[assembler, scaler])
            
            # Fit and transform
            pipeline_model = pipeline.fit(df_scaled)
            df_scaled = pipeline_model.transform(df_scaled)
            
            # Extract scalar value from vector
            get_value_udf = F.udf(lambda x: float(x[0]) if x is not None else None, "double")
            df_scaled = df_scaled.withColumn(
                f"{col}{self.output_col_suffix}",
                get_value_udf(F.col(scaled_vec_col))
            )
            
            # Drop intermediate columns and original column
            df_scaled = df_scaled.drop(vector_col, scaled_vec_col, col)
            
            # Rename scaled column to original name
            df_scaled = df_scaled.withColumnRenamed(f"{col}{self.output_col_suffix}", col)
            
            # Store the scaler model
            self.scaler_models[col] = pipeline_model.stages[1]  # object model
            
            # Log scaler parameters
            scaler_model = self.scaler_models[col]
            logger.info(f"\nScaler Parameters for {col}:")
            logger.info(f"  Original Min: {scaler_model.originalMin}")
            logger.info(f"  Original Max: {scaler_model.originalMax}")
        
        # Log statistics after scaling
        logger.info(f"\nStatistics AFTER scaling:")
        for col in columns_to_scale:
            stats = df_scaled.select(
                F.min(col).alias('min'),
                F.max(col).alias('max'),
                F.mean(col).alias('mean'),
                F.stddev(col).alias('std')
            ).collect()[0]
            
            logger.info(f"  {col}: Min={stats['min']:.4f}, Max={stats['max']:.4f}, "
                       f"Mean={stats['mean']:.4f}, Std={stats['std']:.4f}")
            
            # Check if scaling worked correctly
            if abs(stats['min']) > 0.001 or abs(stats['max'] - 1.0) > 0.001:
                logger.warning(f"  ⚠ Column '{col}' may not be properly scaled to [0,1] range")
        
        logger.info(f"\n{'='*60}")
        logger.info(f'✓ MIN-MAX SCALING COMPLETE - {len(columns_to_scale)} columns processed')
        logger.info(f"{'='*60}\n")
        
        return df_scaled
    
    def get_scaler_models(self) -> Dict[str, object]:
        """Get the fitted scaler models for each column."""
        return self.scaler_models


class StandardScalingStrategy(FeatureScalingStrategy):
    """Standard scaling strategy to scale features to zero mean and unit variance."""
    
    def __init__(self, with_mean: bool = True, with_std: bool = True, 
                 output_col_suffix: str = "_scaled", spark: Optional[SparkSession] = None):
        """
        Initialize Standard scaling strategy.
        
        Args:
            with_mean: Whether to center the data before scaling
            with_std: Whether to scale the data to unit variance
            output_col_suffix: Suffix to add to scaled column names
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.with_mean = with_mean
        self.with_std = with_std
        self.output_col_suffix = output_col_suffix
        self.scaler_models = {}
        logger.info(f"StandardScalingStrategy initialized (PySpark) - "
                   f"with_mean={with_mean}, with_std={with_std}")
    
    def scale(self, df: Union[pd.DataFrame, object], columns_to_scale: List[str]) -> Union[pd.DataFrame, object]:
        """
        Apply Standard scaling to specified columns.
        
        Args:
            df: PySpark DataFrame
            columns_to_scale: List of column names to scale
            
        Returns:
            DataFrame with scaled columns
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"FEATURE SCALING - STANDARD (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f'Starting Standard scaling for {len(columns_to_scale)} columns')
        
        df_scaled = df
        
        # Scale each column individually
        for col in columns_to_scale:
            # Create a vector column for this feature
            vector_col = f"{col}_vec"
            assembler = VectorAssembler(inputCols=[col], outputCol=vector_col)
            
            # Create object
            scaled_vec_col = f"{col}_scaled_vec"
            scaler = object(
                inputCol=vector_col, 
                outputCol=scaled_vec_col,
                withMean=self.with_mean,
                withStd=self.with_std
            )
            
            # Create pipeline
            pipeline = Pipeline(stages=[assembler, scaler])
            
            # Fit and transform
            pipeline_model = pipeline.fit(df_scaled)
            df_scaled = pipeline_model.transform(df_scaled)
            
            # Extract scalar value from vector
            get_value_udf = F.udf(lambda x: float(x[0]) if x is not None else None, "double")
            df_scaled = df_scaled.withColumn(
                f"{col}{self.output_col_suffix}",
                get_value_udf(F.col(scaled_vec_col))
            )
            
            # Drop intermediate columns and original column
            df_scaled = df_scaled.drop(vector_col, scaled_vec_col, col)
            
            # Rename scaled column to original name
            df_scaled = df_scaled.withColumnRenamed(f"{col}{self.output_col_suffix}", col)
            
            # Store the scaler model
            self.scaler_models[col] = pipeline_model.stages[1]  # object model
        
        logger.info(f"✓ STANDARD SCALING COMPLETE - {len(columns_to_scale)} columns processed")
        logger.info(f"{'='*60}\n")
        
        return df_scaled


class VectorScalingStrategy(FeatureScalingStrategy):
    """
    Scaling strategy that works with vector columns.
    More efficient when scaling many features together.
    """
    
    def __init__(self, scaling_type: ScalingType = ScalingType.MINMAX, 
                 spark: Optional[SparkSession] = None):
        """
        Initialize vector scaling strategy.
        
        Args:
            scaling_type: Type of scaling to apply
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.scaling_type = scaling_type
        logger.info(f"VectorScalingStrategy initialized with {scaling_type} scaling")
    
    def scale(self, df: Union[pd.DataFrame, object], columns_to_scale: List[str]) -> Union[pd.DataFrame, object]:
        """
        Apply scaling to multiple columns as a vector.
        
        Args:
            df: PySpark DataFrame
            columns_to_scale: List of column names to scale
            
        Returns:
            DataFrame with scaled features in a vector column
        """
        # Assemble features into a vector
        assembler = VectorAssembler(inputCols=columns_to_scale, outputCol="features")
        
        # Choose scaler based on type
        if self.scaling_type == ScalingType.MINMAX:
            scaler = object(inputCol="features", outputCol="scaled_features")
        else:
            scaler = object(inputCol="features", outputCol="scaled_features")
        
        # Create pipeline
        pipeline = Pipeline(stages=[assembler, scaler])
        
        # Fit and transform
        pipeline_model = pipeline.fit(df)
        df_scaled = pipeline_model.transform(df)
        
        self.fitted_model = pipeline_model
        
        logger.info(f"✓ Vector scaling complete for {len(columns_to_scale)} features")
        
        return df_scaled