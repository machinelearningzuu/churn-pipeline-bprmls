"""
Outlier detection strategies for both pandas and PySpark DataFrames.
Students can compare IQR-based outlier detection implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict, Tuple
import pandas as pd  # Keep for educational comparison
# Manual PySpark availability flag - set to False to prioritize pandas
PYSPARK_AVAILABLE = False  # Set to True to enable PySpark, False for pandas-only

# Conditional PySpark imports
if PYSPARK_AVAILABLE:
    try:
        from pyspark.sql import DataFrame as SparkDataFrame, SparkSession
        from pyspark.sql import functions as F
        from pyspark.sql.types import BooleanType
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


class OutlierDetectionStrategy(ABC):
    """Abstract base class for outlier detection strategies."""
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize with SparkSession."""
        self.spark = spark or get_or_create_spark_session()
    
    @abstractmethod
    def detect_outliers(self, df: Union[pd.DataFrame, object], columns: List[str]) -> Union[pd.DataFrame, object]:
        """
        Detect outliers in specified columns.
        
        Args:
            df: Union[pd.DataFrame, object] (PySpark or pandas)
            columns: List of column names to check for outliers
            
        Returns:
            DataFrame with additional boolean columns indicating outliers
        """
        pass
    
    @abstractmethod
    def get_outlier_bounds(self, df: Union[pd.DataFrame, object], columns: List[str]) -> Dict[str, Tuple[float, float]]:
        """
        Get outlier bounds for specified columns.
        
        Args:
            df: Union[pd.DataFrame, object] (PySpark or pandas)
            columns: List of column names
            
        Returns:
            Dictionary mapping column names to (lower_bound, upper_bound) tuples
        """
        pass


class IQROutlierDetection(OutlierDetectionStrategy):
    """IQR-based outlier detection strategy."""
    
    def __init__(self, threshold: float = 1.5, spark: Optional[SparkSession] = None):
        """
        Initialize IQR outlier detection.
        
        Args:
            threshold: IQR multiplier for outlier bounds (default: 1.5)
            spark: Optional SparkSession
        """
        super().__init__(spark)
        self.threshold = threshold
        logger.info(f"Initialized IQROutlierDetection with threshold: {threshold}")
    
    def get_outlier_bounds(self, df: Union[pd.DataFrame, object], columns: List[str]) -> Dict[str, Tuple[float, float]]:
        """
        Calculate outlier bounds using IQR method.
        
        Args:
            df: PySpark DataFrame
            columns: List of column names
            
        Returns:
            Dictionary mapping column names to (lower_bound, upper_bound) tuples
        """
        bounds = {}
        
        for col in columns:
            quantiles = df.approxQuantile(col, [0.25, 0.75], 0.01)
            Q1, Q3 = quantiles[0], quantiles[1]
            IQR = Q3 - Q1
            
            lower_bound = Q1 - self.threshold * IQR
            upper_bound = Q3 + self.threshold * IQR
            
            bounds[col] = (lower_bound, upper_bound)
            
            logger.info(f"  Column '{col}': Q1={Q1:.2f}, Q3={Q3:.2f}, IQR={IQR:.2f}")
            logger.info(f"  Bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
        
        return bounds
    
    def detect_outliers(self, df: Union[pd.DataFrame, object], columns: List[str]) -> Union[pd.DataFrame, object]:
        """
        Detect outliers using IQR method.
        
        Args:
            df: PySpark DataFrame
            columns: List of column names to check for outliers
            
        Returns:
            DataFrame with additional boolean columns '{col}_outlier' indicating outliers
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"OUTLIER DETECTION - IQR METHOD (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Starting IQR outlier detection for columns: {columns}")
        
        # Get outlier bounds
        bounds = self.get_outlier_bounds(df, columns)
        
        # Add outlier indicator columns
        result_df = df
        total_outliers = 0
        
        for col in columns:
            logger.info(f"\n--- Processing column: {col} ---")
            
            lower_bound, upper_bound = bounds[col]
            
            # Create outlier indicator column
            outlier_col = f"{col}_outlier"
            
                    result_df = result_df.withColumn(
                outlier_col,
                (F.col(col) < lower_bound) | (F.col(col) > upper_bound)
            )
            
            # Count outliers
            outlier_count = result_df.filter(F.col(outlier_col)).count()
            total_rows = result_df.count()
            
            outlier_percentage = (outlier_count / total_rows * 100) if total_rows > 0 else 0
            
            logger.info(f"  ✓ Found {outlier_count} outliers ({outlier_percentage:.2f}%)")
            total_outliers += outlier_count
        
        logger.info(f"\n{'='*60}")
        logger.info(f'✓ OUTLIER DETECTION COMPLETE - Total outlier instances: {total_outliers}')
        logger.info(f"{'='*60}\n")
        
        return result_df


class OutlierDetector:
    """Main outlier detector class that uses different strategies."""
    
    def __init__(self, strategy: OutlierDetectionStrategy):
        """
        Initialize outlier detector with a specific strategy.
        
        Args:
            strategy: OutlierDetectionStrategy instance
        """
        self._strategy = strategy
        logger.info(f"OutlierDetector initialized with strategy: {strategy.__class__.__name__}")
    
    def detect_outliers(self, df: Union[pd.DataFrame, object], selected_columns: List[str]) -> Union[pd.DataFrame, object]:
        """
        Detect outliers in selected columns.
        
        Args:
            df: Union[pd.DataFrame, object] (PySpark or pandas)
            selected_columns: List of column names to check
            
        Returns:
            DataFrame with outlier indicator columns
        """
        logger.info(f"Detecting outliers in {len(selected_columns)} columns")
        return self._strategy.detect_outliers(df, selected_columns)
    
    def handle_outliers(self, df: Union[pd.DataFrame, object], selected_columns: List[str], 
                       method: str = 'remove', min_outliers: int = 2) -> Union[pd.DataFrame, object]:
        """
        Handle outliers using specified method.
        
        Args:
            df: Union[pd.DataFrame, object] (PySpark or pandas)
            selected_columns: List of column names to check
            method: Method to handle outliers ('remove' or 'cap')
            min_outliers: Minimum number of outlier columns to remove a row
            
        Returns:
            DataFrame with outliers handled
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"OUTLIER HANDLING - {method.upper()} (PySpark)")
        logger.info(f"{'='*60}")
        logger.info(f"Handling outliers using method: {method}")
        
            # initial_rows = len(df)
        
            initial_rows = df.count()
        
        if method == 'remove':
            # Add outlier indicator columns
            df_with_outliers = self.detect_outliers(df, selected_columns)
            
            # Count outliers per row
            outlier_columns = [f"{col}_outlier" for col in selected_columns]
            
            outlier_count_expr = sum(F.col(col).cast("int") for col in outlier_columns)
            
            # Add outlier count column
            df_with_count = df_with_outliers.withColumn("outlier_count", outlier_count_expr)
            
            # Filter rows with fewer outliers than threshold
            cleaned_df = df_with_count.filter(F.col("outlier_count") < min_outliers)
            
            # Remove temporary columns
            cleaned_df = cleaned_df.drop("outlier_count")
            for col in outlier_columns:
                cleaned_df = cleaned_df.drop(col)
            
                    # rows_removed = rows_to_remove.sum()
            
                    rows_removed = initial_rows - cleaned_df.count()
            removal_percentage = (rows_removed / initial_rows * 100) if initial_rows > 0 else 0
            
            logger.info(f"✓ Removed {rows_removed} rows with {min_outliers}+ outliers ({removal_percentage:.2f}%)")
            logger.info(f"✓ Remaining rows: {cleaned_df.count()} ({(cleaned_df.count()/initial_rows*100):.2f}%)")
            
        elif method == 'cap':
            # Cap outliers at bounds
            bounds = self._strategy.get_outlier_bounds(df, selected_columns)
            cleaned_df = df
            
            for col in selected_columns:
                lower_bound, upper_bound = bounds[col]
                
                # Cap values at bounds
                cleaned_df = cleaned_df.withColumn(
                    col,
                    F.when(F.col(col) < lower_bound, lower_bound)
                    .when(F.col(col) > upper_bound, upper_bound)
                    .otherwise(F.col(col))
                )
                
            logger.info(f"✓ Capped outliers at IQR bounds for {len(selected_columns)} columns")
            
        else:
            raise ValueError(f"Unknown outlier handling method: {method}")
        
        logger.info(f"{'='*60}\n")
        return cleaned_df